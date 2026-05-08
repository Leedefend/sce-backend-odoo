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
expense_payment_facts, expense_payment_facts_presence = load_json(
    "business_expense_contract_payment_fact_acceptance_v1.json",
    required=False,
)
attachment_custody, attachment_custody_presence = load_json(
    "history_attachment_custody_probe_result_v1.json",
    required=False,
)
business_fact_residual, business_fact_residual_presence = load_json(
    "fresh_db_legacy_business_fact_residual_replay_write_result_v1.json",
    required=False,
)
full_legacy_loss_scan, full_legacy_loss_scan_presence = load_json(
    "legacy_db_full_business_fact_loss_scan_v1.json",
    required=False,
)
remaining_fact_family_screen, remaining_fact_family_screen_presence = load_json(
    "legacy_db_remaining_business_fact_family_screen_v1.json",
    required=False,
)
multi_db_fact_scan, multi_db_fact_scan_presence = load_json(
    "legacy_multi_db_business_fact_scan_summary_v1.json",
    required=False,
)
multi_db_key_collision, multi_db_key_collision_presence = load_json(
    "legacy_multi_db_replay_key_collision_probe_v1.json",
    required=False,
)

post_visible = (postcheck or {}).get("visible_business_fact_reconciliation") or {}
cleanup_summary = (cleanup or {}).get("summary") or {}
legacy_summary = (legacy_source or {}).get("summary") or {}
additional_facts_summary = (additional_facts or {}).get("summary") or {}
expense_taxonomy_summary = (expense_taxonomy or {}).get("summary") or {}
expense_contract_subtypes_summary = (expense_contract_subtypes or {}).get("summary") or {}
expense_payment_facts_summary = (expense_payment_facts or {}).get("summary") or {}
attachment_custody_summary = (attachment_custody or {}).get("counts") or {}
business_fact_residual_family_counts = (business_fact_residual or {}).get("family_counts") or {}
business_fact_residual_source_counts = (business_fact_residual or {}).get("source_database_counts") or {}
full_legacy_loss_scan_summary = (full_legacy_loss_scan or {}).get("summary") or {}
remaining_fact_family_screen_summary = (remaining_fact_family_screen or {}).get("summary") or {}
multi_db_fact_scan_totals = (multi_db_fact_scan or {}).get("totals") or {}
multi_db_key_collision_summary = (multi_db_key_collision or {}).get("summary") or {}

business_fact_residual_expected_rows = multi_db_fact_scan_totals.get("candidate_rows")
business_fact_residual_coverage = {
    "expected_rows": business_fact_residual_expected_rows,
    "actual_rows": (business_fact_residual or {}).get("after"),
    "expected_active_rows": None,
    "actual_active_rows": (business_fact_residual or {}).get("active_rows"),
    "row_delta": (
        ((business_fact_residual or {}).get("after") or 0) - business_fact_residual_expected_rows
        if business_fact_residual_expected_rows is not None and business_fact_residual is not None
        else None
    ),
    "active_row_delta": None,
}

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
    "expense_payment_facts": {
        "presence": expense_payment_facts_presence,
        "status": status_of(expense_payment_facts, expense_payment_facts_presence),
        "counts": expense_payment_facts_summary.get("counts"),
        "amounts": expense_payment_facts_summary.get("amounts"),
        "settlement_boundary": expense_payment_facts_summary.get("settlement_boundary"),
    },
    "attachment_custody": {
        "presence": attachment_custody_presence,
        "status": status_of(attachment_custody, attachment_custody_presence),
        "legacy_file_index_rows": attachment_custody_summary.get("legacy_file_index_rows"),
        "legacy_url_attachments": attachment_custody_summary.get("legacy_url_attachments"),
        "receipt_invoice_attachment_runtime_records": attachment_custody_summary.get(
            "receipt_invoice_attachment_runtime_records"
        ),
        "legacy_attachment_backfill_runtime_records": attachment_custody_summary.get(
            "legacy_attachment_backfill_runtime_records"
        ),
        "gap_count": sum(1 for value in ((attachment_custody or {}).get("gaps") or {}).values() if value),
    },
    "business_fact_residual": {
        "presence": business_fact_residual_presence,
        "status": status_of(business_fact_residual, business_fact_residual_presence),
        "input_rows": (business_fact_residual or {}).get("input_rows"),
        "after": (business_fact_residual or {}).get("after"),
        "active_rows": (business_fact_residual or {}).get("active_rows"),
        "source_database_counts": business_fact_residual_source_counts,
        "family_counts": business_fact_residual_family_counts,
        "coverage": business_fact_residual_coverage,
    },
    "full_legacy_loss_scan": {
        "presence": full_legacy_loss_scan_presence,
        "status": status_of(full_legacy_loss_scan, full_legacy_loss_scan_presence),
        "non_empty_tables": full_legacy_loss_scan_summary.get("non_empty_tables"),
        "candidate_tables": full_legacy_loss_scan_summary.get("candidate_tables"),
        "candidate_rows": full_legacy_loss_scan_summary.get("candidate_rows"),
        "top_candidate": ((full_legacy_loss_scan_summary.get("top_candidates") or [{}])[0] or {}).get("table"),
    },
    "remaining_fact_family_screen": {
        "presence": remaining_fact_family_screen_presence,
        "status": status_of(remaining_fact_family_screen, remaining_fact_family_screen_presence),
        "screened_tables": remaining_fact_family_screen_summary.get("screened_tables"),
        "screened_rows": remaining_fact_family_screen_summary.get("screened_rows"),
        "screened_active_rows": remaining_fact_family_screen_summary.get("screened_active_rows"),
        "top_family": ((remaining_fact_family_screen_summary.get("families") or [{}])[0] or {}).get("family"),
    },
    "multi_db_fact_scan": {
        "presence": multi_db_fact_scan_presence,
        "status": status_of(multi_db_fact_scan, multi_db_fact_scan_presence),
        "source_count": multi_db_fact_scan_totals.get("source_count"),
        "candidate_tables": multi_db_fact_scan_totals.get("candidate_tables"),
        "candidate_rows": multi_db_fact_scan_totals.get("candidate_rows"),
        "screened_tables": multi_db_fact_scan_totals.get("screened_tables"),
        "screened_rows": multi_db_fact_scan_totals.get("screened_rows"),
        "screened_active_rows": multi_db_fact_scan_totals.get("screened_active_rows"),
        "sources": (multi_db_fact_scan or {}).get("sources"),
    },
    "multi_db_key_collision": {
        "presence": multi_db_key_collision_presence,
        "status": status_of(multi_db_key_collision, multi_db_key_collision_presence),
        "common_candidate_tables": (multi_db_key_collision or {}).get("common_candidate_tables"),
        "checked_tables": (multi_db_key_collision or {}).get("checked_tables"),
        "collision_table_count": multi_db_key_collision_summary.get("collision_table_count"),
        "collision_key_sample_count": multi_db_key_collision_summary.get("collision_key_sample_count"),
        "requires_source_database_in_replay_key": multi_db_key_collision_summary.get(
            "requires_source_database_in_replay_key"
        ),
        "decision": (multi_db_key_collision or {}).get("decision"),
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
if expense_payment_facts_presence == "present" and summary["expense_payment_facts"]["status"] != "PASS":
    errors.append({"error": "expense_payment_facts_failed", "status": summary["expense_payment_facts"]["status"]})
if attachment_custody_presence == "present" and summary["attachment_custody"]["status"] != "PASS":
    errors.append({"error": "attachment_custody_failed", "status": summary["attachment_custody"]["status"]})
if business_fact_residual_presence == "present" and summary["business_fact_residual"]["status"] != "PASS":
    errors.append({"error": "business_fact_residual_failed", "status": summary["business_fact_residual"]["status"]})
if business_fact_residual_presence == "present" and multi_db_fact_scan_presence == "present":
    if business_fact_residual_coverage["row_delta"] != 0:
        errors.append({"error": "business_fact_residual_row_coverage_mismatch", **business_fact_residual_coverage})
if full_legacy_loss_scan_presence == "present" and summary["full_legacy_loss_scan"]["status"] != "PASS":
    errors.append({"error": "full_legacy_loss_scan_failed", "status": summary["full_legacy_loss_scan"]["status"]})
if remaining_fact_family_screen_presence == "present" and summary["remaining_fact_family_screen"]["status"] != "PASS":
    errors.append(
        {"error": "remaining_fact_family_screen_failed", "status": summary["remaining_fact_family_screen"]["status"]}
    )
if multi_db_fact_scan_presence == "present" and summary["multi_db_fact_scan"]["status"] != "PASS":
    errors.append({"error": "multi_db_fact_scan_failed", "status": summary["multi_db_fact_scan"]["status"]})
if multi_db_key_collision_presence == "present" and summary["multi_db_key_collision"]["status"] != "PASS":
    errors.append({"error": "multi_db_key_collision_failed", "status": summary["multi_db_key_collision"]["status"]})

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
            "expense_payment_facts": summary["expense_payment_facts"]["status"],
            "attachment_custody": summary["attachment_custody"]["status"],
            "business_fact_residual": summary["business_fact_residual"]["status"],
            "full_legacy_loss_scan": summary["full_legacy_loss_scan"]["status"],
            "remaining_fact_family_screen": summary["remaining_fact_family_screen"]["status"],
            "multi_db_fact_scan": summary["multi_db_fact_scan"]["status"],
            "multi_db_key_collision": summary["multi_db_key_collision"]["status"],
            "artifact_root": str(ARTIFACT_ROOT),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
