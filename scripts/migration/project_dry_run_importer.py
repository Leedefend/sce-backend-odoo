#!/usr/bin/env python3
"""Dry-run project skeleton importer.

This tool intentionally does not import data, connect to Odoo, call ORM, or
write any database state. It only validates the frozen safe-slice CSV and emits
a JSON plan with create/update/error classifications.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SAFE_FIELDS = [
    "legacy_project_id",
    "legacy_parent_id",
    "name",
    "short_name",
    "project_environment",
    "legacy_company_id",
    "legacy_company_name",
    "legacy_specialty_type_id",
    "specialty_type_name",
    "legacy_price_method",
    "business_nature",
    "detail_address",
    "project_profile",
    "project_area",
    "legacy_is_shared_base",
    "legacy_sort",
    "legacy_attachment_ref",
    "project_overview",
    "legacy_project_nature",
    "legacy_is_material_library",
    "other_system_id",
    "other_system_code",
]

SOURCE_TO_SAFE = {
    "ID": "legacy_project_id",
    "PID": "legacy_parent_id",
    "XMMC": "name",
    "SHORT_NAME": "short_name",
    "PROJECT_ENV": "project_environment",
    "COMPANYID": "legacy_company_id",
    "COMPANYNAME": "legacy_company_name",
    "SPECIALTY_TYPE_ID": "legacy_specialty_type_id",
    "SPECIALTY_TYPE_NAME": "specialty_type_name",
    "PRICE_METHOD": "legacy_price_method",
    "NATURE": "business_nature",
    "DETAIL_ADDRESS": "detail_address",
    "PROFILE": "project_profile",
    "AREA": "project_area",
    "IS_SHARED_BASE": "legacy_is_shared_base",
    "SORT": "legacy_sort",
    "FJ": "legacy_attachment_ref",
    "PROJECTOVERVIEW": "project_overview",
    "PROJECT_NATURE": "legacy_project_nature",
    "IS_MACHINTERIAL_LIBRARY": "legacy_is_material_library",
    "OTHER_SYSTEM_ID": "other_system_id",
    "OTHER_SYSTEM_CODE": "other_system_code",
}

NULL_VALUES = {"", "null", "none", "n/a", "na"}
SINGLE_LINE_FIELDS = set(SAFE_FIELDS) - {"project_profile", "project_overview"}


@dataclass(frozen=True)
class ExistingIdentity:
    legacy_project_id: str


def _clean_value(value: str | None, *, single_line: bool) -> str:
    raw = "" if value is None else str(value)
    raw = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
    if raw.lower() in NULL_VALUES:
        return ""
    if single_line:
        raw = raw.replace("\n", " ")
        raw = re.sub(r"[ \t]+", " ", raw)
    return raw


def _clean_row(row: dict[str, str]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for field in SAFE_FIELDS:
        cleaned[field] = _clean_value(
            row.get(field),
            single_line=field in SINGLE_LINE_FIELDS,
        )
    return cleaned


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise SystemExit(f"CSV has no header: {path}")
        return [dict(row) for row in reader]


def _load_existing(path: Path | None) -> set[str]:
    if not path:
        return set()
    rows = _read_csv(path)
    return {
        _clean_value(row.get("legacy_project_id"), single_line=True)
        for row in rows
        if _clean_value(row.get("legacy_project_id"), single_line=True)
    }


def _validate_header(fieldnames: Iterable[str] | None) -> list[str]:
    actual = list(fieldnames or [])
    missing = [field for field in SAFE_FIELDS if field not in actual]
    extra = [field for field in actual if field not in SAFE_FIELDS]
    errors = []
    if missing:
        errors.append(f"missing safe fields: {', '.join(missing)}")
    if extra:
        errors.append(f"unsafe extra fields: {', '.join(extra)}")
    return errors


def run_dry_run(input_path: Path, output_path: Path, existing_path: Path | None = None) -> dict:
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header_errors = _validate_header(reader.fieldnames)
        raw_rows = [dict(row) for row in reader]

    existing_ids = _load_existing(existing_path)
    cleaned_rows = [_clean_row(row) for row in raw_rows]
    id_counts = Counter(row["legacy_project_id"] for row in cleaned_rows if row["legacy_project_id"])

    results = []
    errors = []
    creates = 0
    updates = 0

    for index, row in enumerate(cleaned_rows, start=2):
        row_errors = []
        if not row["legacy_project_id"]:
            row_errors.append("missing legacy_project_id")
        if not row["name"]:
            row_errors.append("missing name")
        if row["legacy_project_id"] and id_counts[row["legacy_project_id"]] > 1:
            row_errors.append("duplicate legacy_project_id in input")

        action = "error"
        if not row_errors:
            if row["legacy_project_id"] in existing_ids:
                action = "update"
                updates += 1
            else:
                action = "create"
                creates += 1

        result = {
            "line": index,
            "legacy_project_id": row["legacy_project_id"],
            "name": row["name"],
            "action": action,
            "errors": row_errors,
        }
        results.append(result)
        for error in row_errors:
            errors.append({"line": index, "legacy_project_id": row["legacy_project_id"], "error": error})

    payload = {
        "status": "PASS" if not header_errors and not errors else "FAIL",
        "mode": "dry_run_no_db_no_orm",
        "input": str(input_path),
        "existing_id_source": str(existing_path) if existing_path else None,
        "row_count": len(cleaned_rows),
        "safe_field_count": len(SAFE_FIELDS),
        "summary": {
            "create": creates,
            "update": updates,
            "error": len({item["line"] for item in errors}),
            "header_error": len(header_errors),
        },
        "header_errors": header_errors,
        "errors": errors,
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def build_sample(source_path: Path, output_path: Path, *, limit: int = 30) -> None:
    if limit < 20 or limit > 50:
        raise SystemExit("sample limit must be between 20 and 50")
    source_rows = _read_csv(source_path)

    selected: list[dict[str, str]] = []
    seen_company: set[str] = set()
    seen_env: set[str] = set()

    for raw in source_rows:
        company = _clean_value(raw.get("COMPANYNAME"), single_line=True)
        env = _clean_value(raw.get("PROJECT_ENV"), single_line=True)
        if company not in seen_company or (env and env not in seen_env):
            selected.append(raw)
            seen_company.add(company)
            seen_env.add(env)
        if len(selected) >= limit:
            break

    for raw in source_rows:
        if len(selected) >= limit:
            break
        if raw not in selected:
            selected.append(raw)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SAFE_FIELDS)
        writer.writeheader()
        for raw in selected[:limit]:
            safe_row = {target: "" for target in SAFE_FIELDS}
            for source, target in SOURCE_TO_SAFE.items():
                safe_row[target] = _clean_value(
                    raw.get(source),
                    single_line=target in SINGLE_LINE_FIELDS,
                )
            writer.writerow(safe_row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run safe project skeleton import.")
    parser.add_argument("--input", required=True, help="Safe-slice CSV path.")
    parser.add_argument("--output", required=True, help="Dry-run JSON result path.")
    parser.add_argument("--existing-identities", help="Optional CSV with legacy_project_id column.")
    parser.add_argument("--build-sample-from", help="Legacy source CSV for sample generation.")
    parser.add_argument("--sample-size", type=int, default=30, help="Sample size, 20 to 50.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if args.build_sample_from:
        build_sample(Path(args.build_sample_from), input_path, limit=args.sample_size)

    payload = run_dry_run(
        input_path=input_path,
        output_path=output_path,
        existing_path=Path(args.existing_identities) if args.existing_identities else None,
    )
    print(
        "project_dry_run_importer",
        payload["status"],
        "rows=%s" % payload["row_count"],
        "create=%s" % payload["summary"]["create"],
        "update=%s" % payload["summary"]["update"],
        "error=%s" % payload["summary"]["error"],
    )
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
