#!/usr/bin/env python3
"""Summarize additional business fact replay payloads already built as artifacts."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


REPO_ROOT = Path(os.getenv("ROOT_DIR", Path.cwd()))
SOURCE_ROOT = Path(os.getenv("BUSINESS_FACT_ADDITIONAL_ARTIFACT_SOURCE_ROOT", str(REPO_ROOT / "artifacts/migration")))
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(SOURCE_ROOT / "business_fact_upgrade")))
OUTPUT_JSON = ARTIFACT_ROOT / "business_fact_additional_fact_inventory_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "business_fact_additional_fact_inventory_v1.md"


LANES = [
    {
        "lane": "receipt_core",
        "path": "fresh_db_receipt_core_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "actual_outflow",
        "path": "fresh_db_actual_outflow_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "actual_outflow_line",
        "path": "fresh_db_actual_outflow_line_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "distinct_parent_actual_outflow_ids", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "actual_outflow_residual",
        "path": "fresh_db_actual_outflow_residual_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "outflow_request",
        "path": "fresh_db_outflow_request_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
    {
        "lane": "outflow_request_line",
        "path": "fresh_db_outflow_request_line_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "legacy_receipt_income",
        "path": "fresh_db_legacy_receipt_income_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "legacy_receipt_residual",
        "path": "fresh_db_legacy_receipt_residual_replay_adapter_result_v1.json",
        "row_keys": ["active_rows", "receipt_rows", "total_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_invoice_tax",
        "path": "fresh_db_legacy_invoice_tax_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "receipt_invoice_line",
        "path": "fresh_db_receipt_invoice_line_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "receipt_invoice_attachment",
        "path": "fresh_db_receipt_invoice_attachment_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "legacy_invoice_registration_line",
        "path": "fresh_db_legacy_invoice_registration_line_replay_adapter_result_v1.json",
        "row_keys": ["total_rows", "header_rows", "active_header_rows", "orphan_line_rows"],
        "amount_keys": ["amount_no_tax", "tax_amount", "amount_total"],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_invoice_surcharge",
        "path": "fresh_db_legacy_invoice_surcharge_replay_adapter_result_v1.json",
        "row_keys": ["expected_rows", "output_rows", "input_rows"],
        "amount_keys": ["output_surcharge_amount", "input_surcharge_amount"],
        "decision_keys": [],
    },
    {
        "lane": "legacy_tax_deduction",
        "path": "fresh_db_legacy_tax_deduction_replay_adapter_result_v1.json",
        "row_keys": ["expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "legacy_fund_confirmation_line",
        "path": "fresh_db_legacy_fund_confirmation_line_replay_adapter_result_v1.json",
        "row_keys": ["total_rows", "header_rows", "active_header_rows", "orphan_line_rows"],
        "amount_keys": ["current_actual_amount", "accumulated_actual_amount"],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_fund_daily_snapshot",
        "path": "fresh_db_legacy_fund_daily_snapshot_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "legacy_payment_residual",
        "path": "fresh_db_legacy_payment_residual_replay_adapter_result_v1.json",
        "row_keys": ["total_rows", "outflow_request_rows", "actual_outflow_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_self_funding",
        "path": "fresh_db_legacy_self_funding_replay_adapter_result_v1.json",
        "row_keys": ["expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "legacy_expense_deposit",
        "path": "fresh_db_legacy_expense_deposit_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "legacy_expense_reimbursement_line",
        "path": "fresh_db_legacy_expense_reimbursement_line_replay_adapter_result_v1.json",
        "row_keys": ["total_rows", "header_rows", "active_header_rows", "orphan_line_rows"],
        "amount_keys": ["line_amount", "header_approved_amount"],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_financing_loan",
        "path": "fresh_db_legacy_financing_loan_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "legacy_account_master",
        "path": "fresh_db_legacy_account_master_replay_adapter_result_v1.json",
        "row_keys": ["account_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
        "payload_checks": [{"csv_key": "csv", "expected_key": "account_rows"}],
    },
    {
        "lane": "legacy_account_transaction",
        "path": "fresh_db_legacy_account_transaction_replay_adapter_result_v1.json",
        "row_keys": ["rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
        "payload_checks": [{"csv_key": "csv", "expected_key": "rows"}],
    },
    {
        "lane": "legacy_fund_daily_line",
        "path": "fresh_db_legacy_fund_daily_line_replay_adapter_result_v1.json",
        "row_keys": ["total_rows", "header_rows", "active_header_rows", "line_rows", "orphan_line_rows"],
        "amount_keys": ["daily_income_sum", "daily_expense_sum", "current_account_balance_sum"],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_project_fund_balance",
        "path": "fresh_db_legacy_project_fund_balance_replay_adapter_result_v1.json",
        "row_keys": ["expected_rows"],
        "amount_keys": ["actual_available_balance"],
        "decision_keys": [],
    },
    {
        "lane": "legacy_deduction_adjustment_line",
        "path": "fresh_db_legacy_deduction_adjustment_line_replay_adapter_result_v1.json",
        "row_keys": ["total_rows", "header_rows", "active_header_rows", "orphan_line_rows"],
        "amount_keys": ["current_actual_amount", "current_planned_amount"],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_construction_diary_line",
        "path": "fresh_db_legacy_construction_diary_line_replay_adapter_result_v1.json",
        "row_keys": ["total_rows", "header_rows", "active_header_rows", "orphan_line_rows", "with_attachment_path_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_task_evidence",
        "path": "fresh_db_legacy_task_evidence_replay_adapter_result_v1.json",
        "row_keys": ["total_rows", "active_rows", "done_rows", "read_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_file_index",
        "path": "fresh_db_legacy_file_index_replay_adapter_result_v1.json",
        "row_keys": [
            "base_system_file_rows",
            "bill_file_rows",
            "total_rows",
            "base_system_file_active_rows",
            "bill_file_active_rows",
        ],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_material_catalog",
        "path": "fresh_db_legacy_material_catalog_replay_adapter_result_v1.json",
        "row_keys": ["category_rows", "detail_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
        "payload_checks": [
            {"csv_key": "category_csv", "expected_key": "category_rows"},
            {"csv_key": "detail_csv", "expected_key": "detail_rows"},
        ],
    },
    {
        "lane": "legacy_supplier_contract_pricing",
        "path": "fresh_db_legacy_supplier_contract_pricing_replay_adapter_result_v1.json",
        "row_keys": ["expected_rows", "pricing_method_rows", "distinct_pricing_methods"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "legacy_purchase_contract",
        "path": "fresh_db_legacy_purchase_contract_replay_adapter_result_v1.json",
        "row_keys": ["total_rows", "active_rows", "project_count", "partner_text_count"],
        "amount_keys": ["amount_sum"],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_tender_registration",
        "path": "fresh_db_legacy_tender_registration_replay_adapter_result_v1.json",
        "row_keys": ["total_rows", "active_rows", "project_count"],
        "amount_keys": ["guarantee_amount_sum", "document_fee_amount_sum"],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_labor_subcontract",
        "path": "fresh_db_legacy_labor_subcontract_replay_adapter_result_v1.json",
        "row_keys": ["total_rows", "active_rows"],
        "amount_keys": ["amount_total_sum"],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_material_stock",
        "path": "fresh_db_legacy_material_stock_replay_adapter_result_v1.json",
        "row_keys": ["total_rows", "active_rows", "material_rows"],
        "amount_keys": ["qty_sum", "amount_total_sum"],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_equipment_lease",
        "path": "fresh_db_legacy_equipment_lease_replay_adapter_result_v1.json",
        "row_keys": ["total_rows", "active_rows"],
        "amount_keys": ["amount_total_sum"],
        "decision_keys": ["decision"],
    },
    {
        "lane": "supplier_contract",
        "path": "fresh_db_supplier_contract_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
    {
        "lane": "supplier_contract_line",
        "path": "fresh_db_supplier_contract_line_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
    {
        "lane": "legacy_attachment_backfill",
        "path": "fresh_db_legacy_attachment_backfill_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "legacy_workflow_audit",
        "path": "fresh_db_legacy_workflow_audit_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": [],
    },
    {
        "lane": "legacy_user_context",
        "path": "fresh_db_legacy_user_context_replay_adapter_result_v1.json",
        "row_keys": ["department_rows", "profile_rows", "role_rows"],
        "amount_keys": [],
        "decision_keys": [],
        "payload_checks": [
            {"csv_key": "department_csv", "expected_key": "department_rows"},
            {"csv_key": "profile_csv", "expected_key": "profile_rows"},
            {"csv_key": "role_csv", "expected_key": "role_rows"},
        ],
    },
    {
        "lane": "legacy_user_project_scope",
        "path": "fresh_db_legacy_user_project_scope_replay_adapter_result_v1.json",
        "row_keys": ["current_rows", "history_rows", "total_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
    {
        "lane": "project_anchor",
        "path": "fresh_db_project_anchor_replay_adapter_result_v1.json",
        "row_keys": [
            "asset_xml_rows",
            "project_master_source_rows",
            "contract_visible_project_anchor_rows",
            "created_evidence_rows",
            "replay_payload_rows",
        ],
        "amount_keys": ["deferred_contract_project_gap_amount_sum"],
        "decision_keys": ["decision"],
    },
    {
        "lane": "project_member_neutral",
        "path": "fresh_db_project_member_neutral_replay_adapter_result_v1.json",
        "row_keys": ["completed_source_rows", "replay_payload_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
    {
        "lane": "partner_l4",
        "path": "fresh_db_partner_l4_replay_adapter_result_v1.json",
        "row_keys": ["created_evidence_rows", "replay_payload_rows", "write_result_files"],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
    {
        "lane": "contract_counterparty_partner",
        "path": "fresh_db_contract_counterparty_partner_replay_adapter_result_v1.json",
        "row_keys": ["candidate_contract_rows", "replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
    {
        "lane": "receipt_counterparty_partner",
        "path": "fresh_db_receipt_counterparty_partner_replay_adapter_result_v1.json",
        "row_keys": ["candidate_receipt_rows", "replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
    {
        "lane": "contract_line",
        "path": "fresh_db_contract_line_replay_adapter_result_v1.json",
        "row_keys": ["replay_payload_rows", "expected_rows"],
        "amount_keys": [],
        "decision_keys": ["decision"],
    },
]


def load_payload(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def pick(payload: dict[str, object], keys: list[str]) -> dict[str, object]:
    return {key: payload.get(key) for key in keys if key in payload}


def int_value(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def resolve_payload_csv(value: object) -> Path | None:
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        return path
    if path.parts[:2] == ("artifacts", "migration"):
        return REPO_ROOT / path
    return SOURCE_ROOT / path


def csv_data_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        total = sum(1 for _row in csv.reader(handle))
    return max(total - 1, 0)


def expected_payload_rows(payload: dict[str, object]) -> int | None:
    for key in ("replay_payload_rows", "expected_rows", "total_rows"):
        value = int_value(payload.get(key))
        if value is not None:
            return value
    return None


def payload_checks_for(lane: dict[str, object], payload: dict[str, object]) -> list[dict[str, object]]:
    configured = lane.get("payload_checks")
    if isinstance(configured, list) and configured:
        return [dict(item) for item in configured if isinstance(item, dict)]
    csv_value = payload.get("payload_csv") or payload.get("row_artifact") or payload.get("csv") or ""
    if not csv_value:
        return []
    return [{"csv_value": csv_value, "expected_rows": expected_payload_rows(payload)}]


rows: list[dict[str, object]] = []
errors: list[dict[str, object]] = []
for lane in LANES:
    path = SOURCE_ROOT / str(lane["path"])
    payload = load_payload(path)
    if payload is None:
        row = {
            "lane": lane["lane"],
            "presence": "missing",
            "status": "MISSING",
            "source_artifact": str(path),
        }
        errors.append({"error": "missing_additional_business_fact_artifact", "lane": lane["lane"], "path": str(path)})
    else:
        payload_checks = []
        for check in payload_checks_for(lane, payload):
            csv_value = check.get("csv_value") or payload.get(str(check.get("csv_key") or "")) or ""
            payload_path = resolve_payload_csv(csv_value)
            expected_rows = check.get("expected_rows")
            if expected_rows is None and check.get("expected_key"):
                expected_rows = int_value(payload.get(str(check["expected_key"])))
            payload_presence = "not_declared"
            payload_row_count = None
            if payload_path is None:
                payload_checks.append(
                    {
                        "csv": "",
                        "presence": payload_presence,
                        "data_rows": payload_row_count,
                        "expected_rows": expected_rows,
                    }
                )
                continue
            payload_presence = "present" if payload_path.exists() else "missing"
            if payload_path.exists():
                payload_row_count = csv_data_rows(payload_path)
            else:
                errors.append(
                    {
                        "error": "missing_additional_business_fact_payload_csv",
                        "lane": lane["lane"],
                        "path": str(payload_path),
                    }
                )
            if payload_row_count is not None and expected_rows is not None and payload_row_count != expected_rows:
                errors.append(
                    {
                        "error": "additional_business_fact_payload_row_count_mismatch",
                        "lane": lane["lane"],
                        "actual": payload_row_count,
                        "expected": expected_rows,
                        "path": str(payload_path),
                    }
                )
            payload_checks.append(
                {
                    "csv": str(payload_path),
                    "presence": payload_presence,
                    "data_rows": payload_row_count,
                    "expected_rows": expected_rows,
                }
            )

        status = payload.get("status") or ("PASS" if payload.get("decision") else "UNKNOWN")
        row = {
            "lane": lane["lane"],
            "presence": "present",
            "status": status,
            "mode": payload.get("mode") or "",
            "source_artifact": str(path),
            "row_counts": pick(payload, list(lane["row_keys"])),
            "amounts": pick(payload, list(lane["amount_keys"])),
            "decisions": pick(payload, list(lane["decision_keys"])),
            "payload_csv": ";".join(check["csv"] for check in payload_checks),
            "payload_presence": "missing"
            if any(check["presence"] == "missing" for check in payload_checks)
            else ("present" if payload_checks else "not_declared"),
            "payload_data_rows": sum(int(check["data_rows"] or 0) for check in payload_checks)
            if payload_checks
            else None,
            "payload_expected_rows": sum(int(check["expected_rows"] or 0) for check in payload_checks)
            if payload_checks
            else None,
            "payload_checks": payload_checks,
        }
        if row["status"] != "PASS":
            errors.append({"error": "additional_business_fact_artifact_not_pass", "lane": lane["lane"], "status": row["status"]})
    rows.append(row)

summary = {
    "source_root": str(SOURCE_ROOT),
    "artifact_root": str(ARTIFACT_ROOT),
    "lane_count": len(rows),
    "present_lanes": sum(1 for row in rows if row["presence"] == "present"),
    "missing_lanes": sum(1 for row in rows if row["presence"] == "missing"),
    "pass_lanes": sum(1 for row in rows if row["status"] == "PASS"),
    "non_pass_lanes": sum(1 for row in rows if row["status"] not in {"PASS"}),
    "payload_declared_lanes": sum(1 for row in rows if row.get("payload_presence") in {"present", "missing"}),
    "payload_present_lanes": sum(1 for row in rows if row.get("payload_presence") == "present"),
    "payload_missing_lanes": sum(1 for row in rows if row.get("payload_presence") == "missing"),
}

status = "PASS" if not errors else "FAIL"
payload = {
    "status": status,
    "mode": "business_fact_additional_fact_inventory",
    "summary": summary,
    "lanes": rows,
    "errors": errors,
    "decision": "additional_business_fact_inventory_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
report = f"""# Business Fact Additional Fact Inventory v1

Status: {status}

## Summary

```json
{json.dumps(summary, ensure_ascii=False, indent=2)}
```

## Lanes

```json
{json.dumps(rows, ensure_ascii=False, indent=2)}
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
    "BUSINESS_FACT_ADDITIONAL_FACT_INVENTORY="
    + json.dumps(
        {
            "status": status,
            "lane_count": summary["lane_count"],
            "present_lanes": summary["present_lanes"],
            "missing_lanes": summary["missing_lanes"],
            "pass_lanes": summary["pass_lanes"],
            "payload_present_lanes": summary["payload_present_lanes"],
            "payload_missing_lanes": summary["payload_missing_lanes"],
            "artifact_root": str(ARTIFACT_ROOT),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
