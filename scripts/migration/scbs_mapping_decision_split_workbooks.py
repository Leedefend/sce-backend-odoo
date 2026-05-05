"""Split the SCBS mapping decision workbook into review-focused CSV files."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


ACTION_ORDER = {
    "manual_partner_required": "01_manual_partner_required",
    "review_non_counterparty_label": "02_review_non_counterparty_label",
    "choose_target_partner": "03_choose_target_partner",
    "ignore_or_conflict_test_value": "04_ignore_or_conflict_test_value",
    "ignore_if_not_real_project": "05_ignore_if_not_real_project",
    "confirm_or_ignore_business_entity": "06_confirm_or_ignore_business_entity",
    "confirm_or_ignore_platform_entity": "07_confirm_or_ignore_platform_entity",
    "review_same_name_legacy_ids": "08_review_same_name_legacy_ids",
    "confirm_or_ignore_project": "09_confirm_or_ignore_project",
    "confirm_or_ignore_partner": "10_confirm_or_ignore_partner",
}


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path("/tmp")


def input_csv_path(artifacts: Path) -> Path:
    raw = os.getenv("SCBS_MAPPING_DECISION_CSV")
    if raw:
        return Path(raw)
    return artifacts / "scbs_mapping_decision_workbook_v1.csv"


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_action_name(action: str) -> str:
    return ACTION_ORDER.get(action, "99_" + "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in action or "blank"))


def main() -> None:
    artifacts = artifact_root()
    source_csv = input_csv_path(artifacts)
    result_json = artifacts / "scbs_mapping_decision_split_workbooks_result_v1.json"
    manifest_csv = artifacts / "scbs_mapping_decision_split_workbooks_manifest_v1.csv"
    fieldnames, rows = read_rows(source_csv)
    if not fieldnames:
        raise RuntimeError({"empty_or_invalid_workbook": str(source_csv)})

    buckets: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        action = (row.get("suggested_action") or "blank").strip() or "blank"
        buckets.setdefault(action, []).append(row)

    manifest_rows: list[dict[str, object]] = []
    for action, action_rows in sorted(buckets.items(), key=lambda item: safe_action_name(item[0])):
        output = artifacts / f"scbs_mapping_decision_{safe_action_name(action)}_v1.csv"
        write_csv(output, fieldnames, action_rows)
        fact_rows = sum(int(float(row.get("fact_rows") or 0)) for row in action_rows)
        fact_amount = round(sum(float(row.get("fact_amount") or 0.0) for row in action_rows), 2)
        with_target = sum(1 for row in action_rows if (row.get("target_id") or "").strip())
        manifest_rows.append(
            {
                "suggested_action": action,
                "file": str(output),
                "mapping_rows": len(action_rows),
                "fact_rows": fact_rows,
                "fact_amount": fact_amount,
                "with_target": with_target,
            }
        )

    write_csv(
        manifest_csv,
        ["suggested_action", "file", "mapping_rows", "fact_rows", "fact_amount", "with_target"],
        manifest_rows,
    )
    payload = {
        "status": "PASS",
        "source_csv": str(source_csv),
        "manifest_csv": str(manifest_csv),
        "split_files": len(manifest_rows),
        "mapping_rows": len(rows),
        "manifest": manifest_rows,
    }
    write_json(result_json, payload)
    print("SCBS_MAPPING_DECISION_SPLIT_WORKBOOKS=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
