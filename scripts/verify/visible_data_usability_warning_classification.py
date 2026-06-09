#!/usr/bin/env python3
"""Classify visible-data usability warnings into actionable coverage buckets.

The visible matrix is intentionally broad: it reports empty visible business
fields, but it cannot by itself decide whether the field is migration metadata,
a derived field, a fact already covered by a stronger value-level probe, or a
real model-specific continuity gap.  This classifier keeps that boundary
explicit so release decisions are not made from a single warning count.
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_BASE = Path(os.getenv("SYSTEMIC_FIELD_GAP_ARTIFACT_BASE") or REPO_ROOT / "artifacts/migration")
OUTPUT_ROOT = Path(
    os.getenv("MIGRATION_ARTIFACT_ROOT")
    or REPO_ROOT / "artifacts/migration/visible_data_usability_warning_classification_v1"
)

ENTRY_METADATA_FIELDS = {"source_created_by", "source_created_at"}
CONTRACT_HISTORY_VALUE_FIELDS = {
    "engineering_category_text",
    "affiliated_person",
    "engineering_address",
    "engineering_content",
    "contract_duration_text",
    "contract_payment_method_text",
    "entry_user_text",
    "entry_time",
    "attachment_text",
}
DERIVED_OR_SYSTEM_FIELDS = {
    "visible_unreceived_rate",
    "display_order",
    "approval_info",
    "legacy_external_contract_no",
    "category_id",
    "hierarchy_code",
    "single_name",
    "unit_name",
    "major_name",
    "category",
    "version",
    "code_division",
    "code_subdivision",
    "cost_item_id",
    "spec",
    "structure_id",
    "task_id",
    "remark",
    "warning_message",
    "wbs_id",
}
SOURCE_SCOPE_EXCLUDED_FIELDS = {
    ("sc.receipt.income", "sc.legacy.receipt.income.fact"): {
        "contract_id",
        "payment_method",
        "receiving_account",
        "receiving_account_name",
        "receiving_account_no",
        "receiving_bank_name",
        "bill_no",
        "invoice_ref",
    },
    ("sc.receipt.income", "sc.legacy.fund.confirmation.line"): {
        "contract_id",
        "payment_method",
        "receiving_account",
        "receiving_account_name",
        "receiving_account_no",
        "receiving_bank_name",
        "bill_no",
        "invoice_ref",
    },
    ("sc.receipt.income", "sc.legacy.receipt.residual.fact"): {
        "receiving_account_name",
        "receiving_account_no",
        "receiving_bank_name",
        "bill_no",
    },
    ("sc.expense.claim", "sc.legacy.deduction.adjustment.line"): {
        "partner_id",
        "payment_method",
        "receipt_account_name",
        "payee_account",
        "payee_bank",
    },
    ("sc.expense.claim", "sc.legacy.account.transaction.line"): {
        "partner_id",
        "payment_method",
        "receipt_account_name",
        "payee_account",
        "payee_bank",
    },
    ("sc.material.inbound", "sc.legacy.material.stock.fact"): {
        "acceptance_id",
    },
    ("sc.material.inbound", "sc.legacy.scbs.fact.staging"): {
        "acceptance_id",
    },
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_files(filename: str) -> list[Path]:
    if ARTIFACT_BASE.is_file() and ARTIFACT_BASE.name == filename:
        return [ARTIFACT_BASE]
    if ARTIFACT_BASE.is_dir():
        return sorted(ARTIFACT_BASE.rglob(filename), key=lambda item: item.stat().st_mtime, reverse=True)
    return []


def _latest_json(filename: str) -> tuple[Path | None, dict[str, Any] | None]:
    files = _candidate_files(filename)
    if not files:
        return None, None
    return files[0], _read_json(files[0])


def _fields(issue: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for item in issue.get("fields") or []:
        field = item.get("field")
        if field:
            values.add(str(field))
    if not values and issue.get("detail"):
        values.update(part.strip() for part in str(issue["detail"]).split(",") if part.strip())
    return values


def _status(payload: dict[str, Any] | None) -> str | None:
    if not payload:
        return None
    value = payload.get("status")
    if value:
        return str(value)
    if payload.get("ok") is True:
        return "PASS"
    if payload.get("ok") is False:
        return "FAIL"
    return None


def _classify_issue(
    issue: dict[str, Any],
    *,
    entry_metadata_pass: bool,
    contract_value_pass: bool,
    settlement_contract_pass: bool,
    material_plan_note_pass: bool,
    material_rfq_source_pass: bool,
) -> tuple[str, str, set[str]]:
    fields = _fields(issue)
    business_fields = fields - ENTRY_METADATA_FIELDS - DERIVED_OR_SYSTEM_FIELDS

    source_breakdown = issue.get("source_breakdown") or []
    if source_breakdown:
        source_uncovered: set[str] = set()
        model = str(issue.get("model") or "")
        for source in source_breakdown:
            source_model = str(source.get("legacy_source_model") or "")
            source_fields = {str(item.get("field")) for item in source.get("fields") or [] if item.get("field")}
            source_business_fields = source_fields - ENTRY_METADATA_FIELDS - DERIVED_OR_SYSTEM_FIELDS
            source_uncovered.update(source_business_fields - SOURCE_SCOPE_EXCLUDED_FIELDS.get((model, source_model), set()))
        if not source_uncovered:
            return "covered_by_source_scope_rule", "source_model_does_not_carry_these_business_fields", set()
        business_fields = source_uncovered

    if fields and fields <= ENTRY_METADATA_FIELDS:
        if entry_metadata_pass:
            return "covered_by_formal_entry_metadata_gate", "metadata_only_and_gate_passed", set()
        return "metadata_gate_required", "metadata_only_but_gate_missing_or_failed", business_fields

    if fields and not business_fields:
        return "covered_by_scene_scope_rule", "scene_fields_are_optional_or_derived_without_source_gap", set()

    if issue.get("model") == "construction.contract":
        uncovered = business_fields - CONTRACT_HISTORY_VALUE_FIELDS
        if contract_value_pass and not uncovered:
            return "covered_by_contract_history_value_gate", "targeted_contract_gate_passed", set()
        if contract_value_pass and uncovered:
            return "contract_warning_partly_covered", "contract_gate_passed_but_some_fields_need_rule", uncovered
        return "contract_value_gate_required", "contract_targeted_gate_missing_or_failed", business_fields

    if issue.get("model") == "sc.settlement.order" and settlement_contract_pass:
        return "covered_by_settlement_contract_surface_gate", "targeted_settlement_contract_surface_gate_passed", set()

    if issue.get("model") == "project.material.plan" and business_fields == {"legacy_visible_10"} and material_plan_note_pass:
        return "covered_by_material_plan_visible_note_gate", "targeted_material_plan_visible_note_gate_passed", set()

    if (
        issue.get("model") == "sc.material.rfq"
        and business_fields <= {"due_date", "purchase_request_id", "source_material_plan_id"}
        and material_rfq_source_pass
    ):
        return "covered_by_material_rfq_source_coverage_gate", "targeted_material_rfq_source_coverage_gate_passed", set()

    if fields and business_fields:
        return "requires_model_specific_business_value_gate", "business_fields_need_source_value_rule_or_backfill", business_fields

    return "unclassified_visible_warning", "manual_review_required", business_fields


def main() -> int:
    visible_path, visible = _latest_json("visible_data_usability_matrix_probe_result_v1.json")
    if not visible_path or not visible:
        raise SystemExit(f"missing visible matrix under {ARTIFACT_BASE}")

    entry_path, entry = _latest_json("formal_entry_metadata_audit_result_v1.json")
    contract_path, contract = _latest_json("construction_contract_history_value_gap_probe_result_v1.json")
    settlement_path, settlement = _latest_json("settlement_contract_surface_audit_result_v1.json")
    material_plan_path, material_plan = _latest_json("material_plan_visible_note_audit_result_v1.json")
    material_rfq_path, material_rfq = _latest_json("material_rfq_source_coverage_audit_result_v1.json")
    project_path, project = _latest_json("project_migration_field_continuity_gap_probe_result_v1.json")
    formal_path, formal = _latest_json("formal_business_backfill_audit_probe_result_v1.json")

    entry_metadata_pass = _status(entry) == "PASS"
    contract_value_pass = _status(contract) == "PASS"
    settlement_contract_pass = _status(settlement) == "PASS"
    material_plan_note_pass = _status(material_plan) == "PASS"
    material_rfq_source_pass = _status(material_rfq) == "PASS"

    rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()
    unresolved_models: Counter[str] = Counter()
    unresolved_fields: Counter[str] = Counter()

    for issue in visible.get("issues") or []:
        bucket, reason, unresolved = _classify_issue(
            issue,
            entry_metadata_pass=entry_metadata_pass,
            contract_value_pass=contract_value_pass,
            settlement_contract_pass=settlement_contract_pass,
            material_plan_note_pass=material_plan_note_pass,
            material_rfq_source_pass=material_rfq_source_pass,
        )
        bucket_counts[bucket] += 1
        if unresolved:
            unresolved_models[str(issue.get("model") or "")] += 1
            for field in sorted(unresolved):
                unresolved_fields[f"{issue.get('model')}.{field}"] += 1
        rows.append(
            {
                "bucket": bucket,
                "reason": reason,
                "model": issue.get("model"),
                "model_label": issue.get("model_label"),
                "action_name": issue.get("action_name"),
                "menu": issue.get("menu"),
                "record_count": issue.get("record_count"),
                "fields": ",".join(sorted(_fields(issue))),
                "unresolved_business_fields": ",".join(sorted(unresolved)),
            }
        )

    unresolved_count = sum(
        count
        for bucket, count in bucket_counts.items()
        if bucket
        in {
            "requires_model_specific_business_value_gate",
            "metadata_gate_required",
            "contract_value_gate_required",
            "contract_warning_partly_covered",
            "unclassified_visible_warning",
        }
    )
    payload = {
        "status": "PASS" if unresolved_count == 0 else "ACTION_REQUIRED",
        "decision": "visible_warnings_classified",
        "visible_matrix": str(visible_path),
        "entry_metadata_audit": str(entry_path) if entry_path else None,
        "contract_history_value_probe": str(contract_path) if contract_path else None,
        "settlement_contract_surface_audit": str(settlement_path) if settlement_path else None,
        "material_plan_visible_note_audit": str(material_plan_path) if material_plan_path else None,
        "material_rfq_source_coverage_audit": str(material_rfq_path) if material_rfq_path else None,
        "project_migration_field_continuity_probe": str(project_path) if project_path else None,
        "formal_business_backfill_audit": str(formal_path) if formal_path else None,
        "visible_warning_count": int(visible.get("warning_count") or 0),
        "classified_warning_count": len(rows),
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "unresolved_business_warning_count": unresolved_count,
        "unresolved_model_counts": dict(sorted(unresolved_models.items())),
        "unresolved_field_counts": dict(sorted(unresolved_fields.items())),
        "rows": rows,
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "visible_data_usability_warning_classification_result_v1.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (OUTPUT_ROOT / "visible_data_usability_warning_classification_rows_v1.csv").open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "bucket",
                "reason",
                "model",
                "model_label",
                "action_name",
                "menu",
                "record_count",
                "fields",
                "unresolved_business_fields",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("VISIBLE_DATA_USABILITY_WARNING_CLASSIFICATION=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
