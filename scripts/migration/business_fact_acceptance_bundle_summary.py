#!/usr/bin/env python3
"""Summarize business fact acceptance bundle artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path


ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration/business_fact_upgrade"))
OUTPUT_JSON = ARTIFACT_ROOT / "business_fact_acceptance_bundle_summary_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "business_fact_acceptance_bundle_summary_v1.md"


def load_json(name: str, *, required: bool) -> tuple[dict[str, object] | None, str]:
    path = ARTIFACT_ROOT / name
    if not path.exists():
        if required:
            return None, "missing"
        return None, "skipped"
    return json.loads(path.read_text(encoding="utf-8")), "present"


def status_of(payload: dict[str, object] | None, presence: str) -> str:
    if payload is None:
        return presence.upper()
    return str(payload.get("status") or "UNKNOWN")


postcheck, postcheck_presence = load_json("fresh_db_business_fact_replay_postcheck_result_v1.json", required=True)
cleanup, cleanup_presence = load_json("business_fact_visible_balance_cleanup_result_v1.json", required=True)
legacy_source, legacy_source_presence = load_json(
    "business_fact_visible_balance_legacy_source_probe_result_v1.json",
    required=False,
)
additional_facts, additional_facts_presence = load_json(
    "business_fact_additional_fact_inventory_v1.json",
    required=False,
)
expense_taxonomy, expense_taxonomy_presence = load_json(
    "business_expense_fact_taxonomy_acceptance_v1.json",
    required=False,
)
expense_contract_subtypes, expense_contract_subtypes_presence = load_json(
    "business_expense_contract_subtype_evidence_v1.json",
    required=False,
)

post_visible = (postcheck or {}).get("visible_business_fact_reconciliation") or {}
cleanup_summary = (cleanup or {}).get("summary") or {}
legacy_summary = (legacy_source or {}).get("summary") or {}
additional_facts_summary = (additional_facts or {}).get("summary") or {}
expense_taxonomy_summary = (expense_taxonomy or {}).get("summary") or {}
expense_contract_subtypes_summary = (expense_contract_subtypes or {}).get("summary") or {}

summary = {
    "artifact_root": str(ARTIFACT_ROOT),
    "postcheck": {
        "presence": postcheck_presence,
        "status": status_of(postcheck, postcheck_presence),
        "contract_total": ((postcheck or {}).get("counts") or {}).get("construction.contract.total"),
        "income_contracts": ((postcheck or {}).get("counts") or {}).get("construction.contract.income_wrapper"),
        "expense_contracts": ((postcheck or {}).get("counts") or {}).get("construction.contract.expense_wrapper"),
        "contract_lines": ((postcheck or {}).get("counts") or {}).get("construction.contract.line"),
        "visible_fact_mismatches": post_visible.get("invoice_receipt_mismatch_count"),
        "visible_balance_observations": post_visible.get("visible_balance_observation_count"),
    },
    "cleanup": {
        "presence": cleanup_presence,
        "status": status_of(cleanup, cleanup_presence),
        "visible_balance_observations": cleanup_summary.get("visible_balance_observation_count"),
        "classification_counts": cleanup_summary.get("classification_counts"),
        "invoice_receipt_mismatches": cleanup_summary.get("invoice_receipt_mismatch_count"),
        "db_writes": cleanup_summary.get("db_writes"),
    },
    "legacy_source": {
        "presence": legacy_source_presence,
        "status": status_of(legacy_source, legacy_source_presence),
        "source_contract_rows_found": legacy_summary.get("source_contract_rows_found"),
        "receipt_linked_rows": legacy_summary.get("receipt_linked_rows"),
        "invoice_linked_rows": legacy_summary.get("invoice_linked_rows"),
        "decisions": legacy_summary.get("decisions"),
    },
    "additional_facts": {
        "presence": additional_facts_presence,
        "status": status_of(additional_facts, additional_facts_presence),
        "lane_count": additional_facts_summary.get("lane_count"),
        "present_lanes": additional_facts_summary.get("present_lanes"),
        "missing_lanes": additional_facts_summary.get("missing_lanes"),
        "pass_lanes": additional_facts_summary.get("pass_lanes"),
        "payload_present_lanes": additional_facts_summary.get("payload_present_lanes"),
        "payload_missing_lanes": additional_facts_summary.get("payload_missing_lanes"),
    },
    "expense_taxonomy": {
        "presence": expense_taxonomy_presence,
        "status": status_of(expense_taxonomy, expense_taxonomy_presence),
        "action_count": expense_taxonomy_summary.get("action_count"),
        "menu_count": expense_taxonomy_summary.get("menu_count"),
        "db_writes": expense_taxonomy_summary.get("db_writes"),
        "fact_counts": expense_taxonomy_summary.get("fact_counts"),
    },
    "expense_contract_subtypes": {
        "presence": expense_contract_subtypes_presence,
        "status": status_of(expense_contract_subtypes, expense_contract_subtypes_presence),
        "supplier_subject_counts": (
            (expense_contract_subtypes_summary.get("supplier_contract_payload") or {}).get("subject_counts")
        ),
        "recommended_subjects": expense_contract_subtypes_summary.get(
            "recommended_user_facing_expense_contract_subjects"
        ),
    },
}

errors = []
if postcheck_presence != "present":
    errors.append({"error": "missing_required_artifact", "artifact": "fresh_db_business_fact_replay_postcheck_result_v1.json"})
if cleanup_presence != "present":
    errors.append({"error": "missing_required_artifact", "artifact": "business_fact_visible_balance_cleanup_result_v1.json"})
for key in ("postcheck", "cleanup"):
    if summary[key]["status"] != "PASS":
        errors.append({"error": "acceptance_step_failed", "step": key, "status": summary[key]["status"]})
if legacy_source_presence == "present" and summary["legacy_source"]["status"] != "PASS":
    errors.append({"error": "legacy_source_probe_failed", "status": summary["legacy_source"]["status"]})
if additional_facts_presence == "present" and summary["additional_facts"]["status"] != "PASS":
    errors.append({"error": "additional_fact_inventory_failed", "status": summary["additional_facts"]["status"]})
if expense_taxonomy_presence == "present" and summary["expense_taxonomy"]["status"] != "PASS":
    errors.append({"error": "expense_fact_taxonomy_failed", "status": summary["expense_taxonomy"]["status"]})
if expense_contract_subtypes_presence == "present" and summary["expense_contract_subtypes"]["status"] != "PASS":
    errors.append(
        {"error": "expense_contract_subtype_evidence_failed", "status": summary["expense_contract_subtypes"]["status"]}
    )

status = "PASS" if not errors else "FAIL"
payload = {
    "status": status,
    "mode": "business_fact_acceptance_bundle_summary",
    "summary": summary,
    "errors": errors,
    "decision": "business_fact_acceptance_bundle_passed" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
report = f"""# Business Fact Acceptance Bundle Summary v1

Status: {status}

## Summary

```json
{json.dumps(summary, ensure_ascii=False, indent=2)}
```

## Errors

```json
{json.dumps(errors, ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`
"""
OUTPUT_REPORT.write_text(report, encoding="utf-8")

print(
    "BUSINESS_FACT_ACCEPTANCE_BUNDLE_SUMMARY="
    + json.dumps(
        {
            "status": status,
            "postcheck": summary["postcheck"]["status"],
            "cleanup": summary["cleanup"]["status"],
            "legacy_source": summary["legacy_source"]["status"],
            "additional_facts": summary["additional_facts"]["status"],
            "expense_taxonomy": summary["expense_taxonomy"]["status"],
            "expense_contract_subtypes": summary["expense_contract_subtypes"]["status"],
            "artifact_root": str(ARTIFACT_ROOT),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
