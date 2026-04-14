#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


CONTRACT_CSV = Path("tmp/raw/contract/contract.csv")
RAW_PROJECT_CSV = Path("tmp/raw/project/project.csv")
PROJECT_SAMPLE_30_CSV = Path("data/migration_samples/project_sample_v1.csv")
PROJECT_SAMPLE_100_CSV = Path("artifacts/migration/project_create_only_expand_post_write_snapshot_v1.csv")
PARTNER_BASELINE_JSON = Path("artifacts/migration/contract_partner_baseline_v1.json")
OUTPUT_JSON = Path("artifacts/migration/contract_mapping_dry_run_result_v1.json")

OWN_COMPANY_NAMES = {"四川保盛建设集团有限公司", "My Company"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def clean_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def read_project_ids() -> tuple[set[str], set[str]]:
    raw_ids = {
        clean_text(row.get("ID"))
        for row in read_csv(RAW_PROJECT_CSV)
        if clean_text(row.get("ID"))
    }
    written_ids: set[str] = set()
    for path in (PROJECT_SAMPLE_30_CSV, PROJECT_SAMPLE_100_CSV):
        if not path.exists():
            continue
        for row in read_csv(path):
            identity = clean_text(row.get("legacy_project_id"))
            if identity:
                written_ids.add(identity)
    return raw_ids, written_ids


def read_partner_index() -> dict[str, list[dict[str, object]]]:
    data = json.loads(PARTNER_BASELINE_JSON.read_text(encoding="utf-8"))
    index: dict[str, list[dict[str, object]]] = {}
    for row in data.get("partners") or []:
        for key in (row.get("display_name"), row.get("name")):
            name = clean_text(key)
            if name:
                index.setdefault(name, []).append(row)
    return index


def infer_direction(row: dict[str, str]) -> tuple[str, str, str]:
    fbf = clean_text(row.get("FBF"))
    cbf = clean_text(row.get("CBF"))
    fbf_is_own = fbf in OWN_COMPANY_NAMES
    cbf_is_own = cbf in OWN_COMPANY_NAMES
    if cbf_is_own and not fbf_is_own:
        return "out", fbf, "CBF is own company; FBF is counterparty"
    if fbf_is_own and not cbf_is_own:
        return "in", cbf, "FBF is own company; CBF is counterparty"
    return "defer", "", "direction requires manual mapping"


def main() -> int:
    contract_rows = read_csv(CONTRACT_CSV)
    raw_project_ids, written_project_ids = read_project_ids()
    partner_index = read_partner_index()

    direction_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()
    del_counter: Counter[str] = Counter()
    htlx_counter: Counter[str] = Counter()
    project_raw_match = 0
    project_written_match = 0
    partner_exact_match = 0
    partner_defer = 0
    safe_skeleton_candidates = []
    rows = []

    for row in contract_rows:
        legacy_id = clean_text(row.get("Id"))
        xmid = clean_text(row.get("XMID"))
        direction, counterparty, direction_reason = infer_direction(row)
        partner_matches = partner_index.get(counterparty, []) if counterparty else []
        raw_project_matched = xmid in raw_project_ids
        written_project_matched = xmid in written_project_ids
        deleted = clean_text(row.get("DEL")) == "1"
        subject = clean_text(row.get("HTBT")) or clean_text(row.get("DJBH")) or clean_text(row.get("HTBH"))

        direction_counter[direction] += 1
        status_counter[clean_text(row.get("DJZT")) or "<EMPTY>"] += 1
        del_counter[clean_text(row.get("DEL")) or "<EMPTY>"] += 1
        htlx_counter[clean_text(row.get("HTLX")) or "<EMPTY>"] += 1
        project_raw_match += 1 if raw_project_matched else 0
        project_written_match += 1 if written_project_matched else 0
        partner_exact_match += 1 if partner_matches else 0
        partner_defer += 1 if not partner_matches else 0

        safe_candidate = (
            bool(legacy_id)
            and bool(subject)
            and written_project_matched
            and direction in {"out", "in"}
            and len(partner_matches) == 1
            and not deleted
        )
        if safe_candidate:
            safe_skeleton_candidates.append(legacy_id)
        rows.append(
            {
                "legacy_contract_id": legacy_id,
                "legacy_project_id": xmid,
                "project_match": "known_written" if written_project_matched else "raw_only" if raw_project_matched else "missing",
                "subject": subject,
                "contract_no": clean_text(row.get("HTBH")),
                "direction": direction,
                "direction_reason": direction_reason,
                "counterparty_text": counterparty,
                "partner_match_type": "exact" if partner_matches else "defer",
                "partner_candidates": [
                    {"id": item.get("id"), "display_name": item.get("display_name")}
                    for item in partner_matches[:3]
                ],
                "legacy_status": clean_text(row.get("DJZT")),
                "legacy_deleted": clean_text(row.get("DEL")),
                "safe_skeleton_candidate": safe_candidate,
            }
        )

    result = {
        "status": "PASS",
        "mode": "contract_mapping_dry_run_no_db_write",
        "source_file": str(CONTRACT_CSV),
        "row_count": len(contract_rows),
        "project_mapping": {
            "raw_project_id_count": len(raw_project_ids),
            "known_written_project_id_count": len(written_project_ids),
            "raw_project_match_rows": project_raw_match,
            "known_written_project_match_rows": project_written_match,
            "known_written_project_match_rate": round(project_written_match / len(contract_rows), 4),
        },
        "direction_mapping": {
            "type": "dictionary/text_rule",
            "counts": dict(sorted(direction_counter.items())),
            "rule": "CBF own company -> out; FBF own company -> in; otherwise defer",
        },
        "partner_mapping": {
            "type": "text_match",
            "exact_match_rows": partner_exact_match,
            "defer_rows": partner_defer,
            "exact_match_rate": round(partner_exact_match / len(contract_rows), 4),
        },
        "status_mapping": {
            "type": "dictionary",
            "legacy_status_counts": dict(status_counter.most_common()),
            "decision": "defer workflow state; first safe slice should create draft only",
        },
        "deletion_mapping": {
            "type": "dictionary",
            "legacy_del_counts": dict(del_counter.most_common()),
            "decision": "DEL=1 must be excluded from first safe slice",
        },
        "category_mapping": {
            "type": "dictionary",
            "legacy_htlx_counts": dict(htlx_counter.most_common(20)),
            "decision": "defer category_id until dictionary mapping is frozen",
        },
        "safe_slice": {
            "candidate_rows": len(safe_skeleton_candidates),
            "candidate_rate": round(len(safe_skeleton_candidates) / len(contract_rows), 4),
            "allowed_target_fields": [
                "subject",
                "type",
                "project_id",
                "partner_id",
                "date_contract",
                "date_start",
                "date_end",
                "note"
            ],
            "deferred_target_fields": [
                "name",
                "category_id",
                "contract_type_id",
                "tax_id explicit mapping",
                "amount fields",
                "line_ids",
                "state replay",
                "attachments"
            ],
        },
        "sample_rows": rows[:50],
        "blocking_reasons": [
            "target construction.contract has no legacy_contract_id field confirmed for exact rollback/upsert",
            "partner exact match rate is insufficient for full import",
            "only known-written project matches may be used for bounded create-only",
            "tax and computed amount semantics are not frozen",
            "contract line source is not identified",
        ],
        "next_step": "contract field alignment for legacy identity, then small sample dry-run using safe_skeleton_candidates",
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "CONTRACT_MAPPING_DRY_RUN="
        + json.dumps(
            {
                "status": result["status"],
                "rows": result["row_count"],
                "project_known_written_matches": result["project_mapping"]["known_written_project_match_rows"],
                "direction_counts": result["direction_mapping"]["counts"],
                "partner_exact_match_rows": result["partner_mapping"]["exact_match_rows"],
                "safe_skeleton_candidates": result["safe_slice"]["candidate_rows"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
