#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


CURRENT_PARTNER_BASELINE = Path("artifacts/migration/contract_partner_baseline_v1.json")
OUTPUT_JSON = Path("artifacts/migration/partner_rebuild_importer_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_rebuild_importer_rows_v1.csv")
EXPECTED_COLUMNS = {
    "legacy_partner_id",
    "partner_name",
    "company_credit_code",
    "company_tax_no",
    "source",
    "source_evidence",
    "linked_contract_count",
    "linked_repayment_rows",
}
ORG_SUFFIXES = ("有限责任公司", "股份有限公司", "集团有限公司", "有限公司", "公司")


def clean_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def norm_name(value: object) -> str:
    text = clean_text(value)
    text = re.sub(r"[（）()·,，.。/、\s\\-]", "", text)
    for suffix in ORG_SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    return text


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def load_partner_index() -> tuple[dict[str, list[dict[str, object]]], dict[str, list[dict[str, object]]]]:
    data = json.loads(CURRENT_PARTNER_BASELINE.read_text(encoding="utf-8"))
    exact: dict[str, list[dict[str, object]]] = {}
    normalized: dict[str, list[dict[str, object]]] = {}
    for partner in data.get("partners") or []:
        for key in ("display_name", "name"):
            name = clean_text(partner.get(key))
            if not name:
                continue
            exact.setdefault(name, []).append(partner)
            normalized.setdefault(norm_name(name), []).append(partner)
    return exact, normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="No-DB partner rebuild importer dry-run")
    parser.add_argument("--mode", choices=["dry-run"], required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    columns, rows = read_csv(input_path)
    missing_columns = sorted(EXPECTED_COLUMNS - set(columns))
    if missing_columns:
        raise SystemExit(f"Missing required input columns: {', '.join(missing_columns)}")

    exact, normalized = load_partner_index()
    seen_legacy_ids: set[str] = set()
    action_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    audit_rows = []

    for idx, row in enumerate(rows, start=1):
        legacy_id = clean_text(row.get("legacy_partner_id"))
        name = clean_text(row.get("partner_name"))
        source = clean_text(row.get("source"))
        blockers = []
        if not legacy_id:
            blockers.append("missing_legacy_partner_id")
        if legacy_id in seen_legacy_ids:
            blockers.append("duplicate_legacy_partner_id")
        seen_legacy_ids.add(legacy_id)
        if not name:
            blockers.append("missing_partner_name")
        if source != "T_Base_CooperatCompany":
            blockers.append("unsupported_source")

        exact_matches = exact.get(name, []) if name else []
        norm_matches = normalized.get(norm_name(name), []) if name else []
        if blockers:
            action = "reject"
        elif len(exact_matches) == 1:
            action = "reuse_existing_exact"
        elif len(exact_matches) > 1:
            action = "manual_review_existing_duplicate"
            blockers.append("existing_exact_duplicate")
        elif len(norm_matches) == 1:
            action = "reuse_existing_normalized"
        elif len(norm_matches) > 1:
            action = "manual_review_existing_duplicate"
            blockers.append("existing_normalized_duplicate")
        else:
            action = "create_candidate"

        action_counts[action] += 1
        for blocker in blockers:
            blocker_counts[blocker] += 1
        audit_rows.append(
            {
                "run_id": args.run_id,
                "row_no": idx,
                "legacy_partner_id": legacy_id,
                "partner_name": name,
                "source": source,
                "dry_run_action": action,
                "blockers": ";".join(blockers),
                "matched_partner_ids": ";".join(str(item.get("id")) for item in (exact_matches or norm_matches)),
                "linked_contract_count": clean_text(row.get("linked_contract_count")),
                "linked_repayment_rows": clean_text(row.get("linked_repayment_rows")),
            }
        )

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0].keys()))
        writer.writeheader()
        writer.writerows(audit_rows)

    result = {
        "status": "PASS",
        "mode": "no_db_partner_rebuild_importer",
        "run_id": args.run_id,
        "input": str(input_path),
        "input_rows": len(rows),
        "output_rows": len(audit_rows),
        "action_counts": dict(sorted(action_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "output_csv": str(OUTPUT_CSV),
        "decision": "NO-GO for write mode; no-DB importer shape validated",
        "next_step": "define partner write-mode gate and small-sample authorization criteria",
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_REBUILD_IMPORTER=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
