#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_strong_evidence_dry_run_input_v1.csv")
CURRENT_PARTNER_BASELINE = Path("artifacts/migration/contract_partner_baseline_v1.json")
OUTPUT_JSON = Path("artifacts/migration/partner_strong_evidence_dry_run_result_v1.json")

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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_partner_index() -> tuple[dict[str, list[dict[str, object]]], dict[str, list[dict[str, object]]]]:
    if not CURRENT_PARTNER_BASELINE.exists():
        return {}, {}
    data = json.loads(CURRENT_PARTNER_BASELINE.read_text(encoding="utf-8"))
    exact: dict[str, list[dict[str, object]]] = {}
    normalized: dict[str, list[dict[str, object]]] = {}
    for partner in data.get("partners") or []:
        for key in ("display_name", "name"):
            name = clean_text(partner.get(key))
            if not name:
                continue
            exact.setdefault(name, []).append(partner)
            n = norm_name(name)
            if n:
                normalized.setdefault(n, []).append(partner)
    return exact, normalized


def main() -> int:
    rows = read_csv(INPUT_CSV)
    exact, normalized = load_partner_index()
    result_rows = []
    action_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    seen_legacy_ids: set[str] = set()

    for row in rows:
        legacy_id = clean_text(row.get("legacy_partner_id"))
        name = clean_text(row.get("partner_name"))
        blockers = []
        if not legacy_id:
            blockers.append("missing_legacy_partner_id")
        if legacy_id in seen_legacy_ids:
            blockers.append("duplicate_legacy_partner_id")
        seen_legacy_ids.add(legacy_id)
        if not name:
            blockers.append("missing_partner_name")

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
        result_rows.append(
            {
                "legacy_partner_id": legacy_id,
                "partner_name": name,
                "dry_run_action": action,
                "blockers": blockers,
                "matched_partner_ids": [
                    item.get("id")
                    for item in (exact_matches or norm_matches)
                ],
                "linked_contract_count": int(row.get("linked_contract_count") or 0),
                "linked_repayment_rows": int(row.get("linked_repayment_rows") or 0),
                "manual_confirm_required": True,
            }
        )

    result = {
        "status": "PASS",
        "mode": "partner_strong_evidence_no_db_write_dry_run",
        "input_rows": len(rows),
        "action_counts": dict(sorted(action_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "create_candidate_rows": action_counts.get("create_candidate", 0),
        "reuse_candidate_rows": action_counts.get("reuse_existing_exact", 0) + action_counts.get("reuse_existing_normalized", 0),
        "manual_review_rows": action_counts.get("manual_review_existing_duplicate", 0),
        "reject_rows": action_counts.get("reject", 0),
        "rows": result_rows,
        "decision": "NO-GO for real partner creation; dry-run only",
        "next_step": "manual review dry-run result and define partner legacy identity field before trial write",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PARTNER_STRONG_EVIDENCE_DRY_RUN="
        + json.dumps(
            {
                "status": result["status"],
                "input_rows": result["input_rows"],
                "action_counts": result["action_counts"],
                "decision": result["decision"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
