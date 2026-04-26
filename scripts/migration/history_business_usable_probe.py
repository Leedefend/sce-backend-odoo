#!/usr/bin/env python3
"""Read-only business usability probe after history continuity replay."""

from __future__ import annotations

import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_replay_manifest_v1.json").exists():
            return candidate
    return Path.cwd()


REPO_ROOT = repo_root()


def resolve_artifact_root() -> Path:
    candidates = []
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(REPO_ROOT / "artifacts/migration")
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


ARTIFACT_ROOT = resolve_artifact_root()
OUTPUT_JSON = ARTIFACT_ROOT / "history_business_usable_probe_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "history_business_usable_probe_report_v1.md"


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# History Business Usable Probe v1",
        "",
        f"Status: {payload['status']}",
        "",
        "## Decision",
        "",
        f"`{payload['decision']}`",
        "",
        "## Core Counts",
        "",
        "```json",
        json.dumps(payload["counts"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Promotion Gaps",
        "",
        "```json",
        json.dumps(payload["promotion_gaps"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sample Runtime Records",
        "",
        "```json",
        json.dumps(payload["sample_runtime_records"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Notes",
        "",
        "- This probe is read-only and does not mutate runtime business objects.",
        "- It evaluates whether replayed historical facts have crossed from carrier-only evidence to user-visible runtime surfaces.",
        "- A non-ready result means promotion work is still required before claiming user business continuity.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def model_exists(model_name: str) -> bool:
    return model_name in env  # noqa: F821


def field_exists(model_name: str, field_name: str) -> bool:
    if not model_exists(model_name):
        return False
    return field_name in env[model_name]._fields  # noqa: F821


def count(model_name: str, domain=None, *, required_fields=None, active_test=True) -> int | None:
    if not model_exists(model_name):
        return None
    required_fields = required_fields or []
    if any(not field_exists(model_name, field_name) for field_name in required_fields):
        return None
    Model = env[model_name].sudo().with_context(active_test=active_test)  # noqa: F821
    try:
        return int(Model.search_count(domain or []))
    except Exception:
        return None


def sample_id(model_name: str, domain=None, *, required_fields=None, active_test=True) -> int | None:
    if not model_exists(model_name):
        return None
    required_fields = required_fields or []
    if any(not field_exists(model_name, field_name) for field_name in required_fields):
        return None
    Model = env[model_name].sudo().with_context(active_test=active_test)  # noqa: F821
    try:
        rec = Model.search(domain or [], order="id asc", limit=1)
        return int(rec.id) if rec else None
    except Exception:
        return None


def grouped_state_counts(model_name: str, domain=None, *, state_field: str = "state") -> dict[str, int] | None:
    if not model_exists(model_name) or not field_exists(model_name, state_field):
        return None
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    try:
        rows = Model.read_group(domain or [], [state_field], [state_field], lazy=False)
    except Exception:
        return None
    result: dict[str, int] = {}
    for row in rows:
        raw = row.get(state_field)
        if isinstance(raw, (tuple, list)):
            raw = raw[0]
        key = str(raw or "__empty__").strip() or "__empty__"
        result[key] = int(row.get("__count") or 0)
    return dict(sorted(result.items(), key=lambda item: item[0]))


def migrated_payment_request_domain() -> list[tuple[str, str, str]]:
    if field_exists("payment.request", "note"):
        return [("note", "ilike", "[migration:")]
    if field_exists("payment.request", "legacy_request_id"):
        return [("legacy_request_id", "!=", False)]
    return []


def project_task_assigned_domain() -> list[object] | None:
    if not model_exists("project.task"):
        return None
    clauses: list[list[tuple[str, str, object]]] = []
    if field_exists("project.task", "user_id"):
        clauses.append([("user_id", "!=", False)])
    if field_exists("project.task", "user_ids"):
        clauses.append([("user_ids", "!=", False)])
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return ["|"] + clauses[0] + clauses[1]


counts = {
    "legacy_users": count("res.users", [("login", "like", "legacy_%")], active_test=False),
    "legacy_active_users": count("res.users", [("login", "like", "legacy_%"), ("active", "=", True)], active_test=False),
    "legacy_user_roles": count("sc.legacy.user.role", [], active_test=False),
    "legacy_user_roles_projected": count(
        "sc.legacy.user.role",
        [("projection_state", "=", "projected")],
        required_fields=["projection_state"],
        active_test=False,
    ),
    "legacy_user_project_scopes_current": count(
        "sc.legacy.user.project.scope",
        [("scope_state", "=", "current")],
        active_test=False,
    ),
    "legacy_user_project_scopes_current_with_project": count(
        "sc.legacy.user.project.scope",
        [("scope_state", "=", "current"), ("project_id", "!=", False)],
        required_fields=["project_id"],
        active_test=False,
    ),
    "legacy_user_project_scopes_access_applied": count(
        "sc.legacy.user.project.scope",
        [("project_access_applied", "=", True)],
        required_fields=["project_access_applied"],
        active_test=False,
    ),
    "legacy_users_with_runtime_capability_groups": count(
        "res.users",
        [("login", "like", "legacy_%"), ("groups_id.name", "ilike", "SC 能力")],
        active_test=False,
    ),
    "legacy_project_followers": count(
        "project.project",
        [("legacy_project_id", "!=", False), ("message_partner_ids.user_ids.login", "like", "legacy_%")],
        required_fields=["legacy_project_id", "message_partner_ids"],
        active_test=False,
    ),
    "partner_anchors": count("res.partner", [("legacy_partner_id", "!=", False)]),
    "project_runtime_records": count("project.project", [("legacy_project_id", "!=", False)]),
    "project_records_with_owner_link": count(
        "project.project",
        [("legacy_project_id", "!=", False), "|", ("user_id", "!=", False), ("manager_id", "!=", False)],
        required_fields=["legacy_project_id", "user_id", "manager_id"],
    ),
    "project_member_carrier": count("sc.project.member.staging", []),
    "contract_runtime_records": count("construction.contract", [("legacy_contract_id", "!=", False)]),
    "contract_records_with_partner_link": count(
        "construction.contract",
        [("legacy_contract_id", "!=", False), ("partner_id", "!=", False)],
        required_fields=["legacy_contract_id", "partner_id"],
    ),
    "contract_summary_lines": count(
        "construction.contract.line",
        [("note", "ilike", "summary line from legacy contract header amount")],
        required_fields=["note"],
    ),
    "supplier_contract_runtime_records": count(
        "construction.contract",
        [("type", "=", "in"), ("note", "ilike", "[migration:supplier_contract_header]")],
        required_fields=["type", "note"],
    ),
    "supplier_contract_line_runtime_records": count(
        "construction.contract.line",
        [("note", "ilike", "[migration:supplier_contract_summary_line]")],
        required_fields=["note"],
    ),
    "payment_request_runtime_records": count("payment.request", migrated_payment_request_domain()),
    "payment_request_with_project_link": count(
        "payment.request",
        migrated_payment_request_domain() + [("project_id", "!=", False)],
        required_fields=["project_id"],
    ),
    "payment_request_with_contract_link": count(
        "payment.request",
        migrated_payment_request_domain() + [("contract_id", "!=", False)],
        required_fields=["contract_id"],
    ),
    "payment_request_with_partner_link": count(
        "payment.request",
        migrated_payment_request_domain() + [("partner_id", "!=", False)],
        required_fields=["partner_id"],
    ),
    "payment_request_line_runtime_records": count("payment.request.line", []),
    "actual_outflow_runtime_records": count(
        "payment.request",
        [("note", "ilike", "[migration:actual_outflow]")],
        required_fields=["note"],
    ),
    "legacy_actual_outflow_cash_requests": count(
        "payment.request",
        [("note", "ilike", "[migration:actual_outflow_core]"), ("amount", ">", 0)],
        required_fields=["note", "amount"],
    ),
    "legacy_receipt_cash_requests": count(
        "payment.request",
        [("note", "ilike", "[migration:receipt_core]"), ("amount", ">", 0)],
        required_fields=["note", "amount"],
    ),
    "treasury_ledger_runtime_records": count("sc.treasury.ledger", []),
    "treasury_ledger_legacy_actual_outflow": count(
        "sc.treasury.ledger",
        [("source_kind", "=", "legacy_actual_outflow")],
        required_fields=["source_kind"],
    ),
    "treasury_ledger_legacy_receipt": count(
        "sc.treasury.ledger",
        [("source_kind", "=", "legacy_receipt")],
        required_fields=["source_kind"],
    ),
    "receipt_invoice_line_runtime_records": count("sc.receipt.invoice.line", []),
    "receipt_invoice_attachment_runtime_records": count(
        "ir.attachment",
        [("res_model", "=", "sc.receipt.invoice.line"), ("type", "=", "url")],
        required_fields=["res_model", "type"],
    ),
    "legacy_attachment_backfill_runtime_records": count(
        "ir.attachment",
        [("description", "ilike", "[migration:legacy_attachment_backfill]")],
        required_fields=["description"],
    ),
    "legacy_file_index_rows": count("sc.legacy.file.index", [], active_test=False),
    "legacy_file_index_with_path": count(
        "sc.legacy.file.index",
        [("file_path", "!=", False)],
        required_fields=["file_path"],
        active_test=False,
    ),
    "legacy_url_attachments": count(
        "ir.attachment",
        ["&", ("type", "=", "url"), "|", ("url", "like", "legacy-file://%"), ("url", "like", "legacy-file-id://%")],
        required_fields=["type", "url"],
        active_test=False,
    ),
    "legacy_receipt_income_facts": count("sc.legacy.receipt.income.fact", []),
    "legacy_receipt_residual_facts": count("sc.legacy.receipt.residual.fact", [], active_test=False),
    "legacy_receipt_residual_with_project": count(
        "sc.legacy.receipt.residual.fact",
        [("project_id", "!=", False)],
        required_fields=["project_id"],
        active_test=False,
    ),
    "receipt_income_runtime_records": count("sc.receipt.income", [], active_test=False),
    "receipt_income_legacy_records": count(
        "sc.receipt.income",
        [("source_origin", "=", "legacy")],
        required_fields=["source_origin"],
        active_test=False,
    ),
    "receipt_income_legacy_with_project": count(
        "sc.receipt.income",
        [("source_origin", "=", "legacy"), ("project_id", "!=", False)],
        required_fields=["source_origin", "project_id"],
        active_test=False,
    ),
    "legacy_expense_deposit_facts": count("sc.legacy.expense.deposit.fact", []),
    "legacy_expense_reimbursement_lines": count("sc.legacy.expense.reimbursement.line", [], active_test=False),
    "legacy_expense_reimbursement_lines_with_project": count(
        "sc.legacy.expense.reimbursement.line",
        [("project_id", "!=", False)],
        required_fields=["project_id"],
        active_test=False,
    ),
    "expense_claim_runtime_records": count("sc.expense.claim", [], active_test=False),
    "expense_claim_legacy_records": count(
        "sc.expense.claim",
        [("source_origin", "=", "legacy")],
        required_fields=["source_origin"],
        active_test=False,
    ),
    "expense_claim_legacy_with_project": count(
        "sc.expense.claim",
        [("source_origin", "=", "legacy"), ("project_id", "!=", False)],
        required_fields=["source_origin", "project_id"],
        active_test=False,
    ),
    "legacy_material_category_rows": count("sc.legacy.material.category", [], active_test=False),
    "legacy_material_detail_rows": count("sc.legacy.material.detail", [], active_test=False),
    "legacy_material_detail_with_category": count(
        "sc.legacy.material.detail",
        [("category_id", "!=", False)],
        required_fields=["category_id"],
        active_test=False,
    ),
    "legacy_material_detail_promoted": count(
        "sc.legacy.material.detail",
        [("promotion_state", "=", "promoted")],
        required_fields=["promotion_state"],
        active_test=False,
    ),
    "product_templates_from_legacy_material": count(
        "product.template",
        [("legacy_material_detail_id", "!=", False)],
        required_fields=["legacy_material_detail_id"],
        active_test=False,
    ),
    "legacy_purchase_contract_facts": count("sc.legacy.purchase.contract.fact", [], active_test=False),
    "legacy_purchase_contract_with_project": count(
        "sc.legacy.purchase.contract.fact",
        [("project_id", "!=", False)],
        required_fields=["project_id"],
        active_test=False,
    ),
    "legacy_purchase_contract_with_partner_text": count(
        "sc.legacy.purchase.contract.fact",
        [("partner_name", "!=", False)],
        required_fields=["partner_name"],
        active_test=False,
    ),
    "legacy_invoice_tax_facts": count("sc.legacy.invoice.tax.fact", []),
    "legacy_invoice_registration_lines": count("sc.legacy.invoice.registration.line", []),
    "legacy_deduction_adjustment_lines": count("sc.legacy.deduction.adjustment.line", []),
    "legacy_deduction_adjustment_lines_with_project": count(
        "sc.legacy.deduction.adjustment.line",
        [("project_id", "!=", False)],
        required_fields=["project_id"],
        active_test=False,
    ),
    "settlement_adjustment_runtime_records": count("sc.settlement.adjustment", [], active_test=False),
    "settlement_adjustment_legacy_records": count(
        "sc.settlement.adjustment",
        [("source_origin", "=", "legacy")],
        required_fields=["source_origin"],
        active_test=False,
    ),
    "settlement_adjustment_legacy_with_project": count(
        "sc.settlement.adjustment",
        [("source_origin", "=", "legacy"), ("project_id", "!=", False)],
        required_fields=["source_origin", "project_id"],
        active_test=False,
    ),
    "legacy_fund_confirmation_lines": count("sc.legacy.fund.confirmation.line", []),
    "legacy_financing_loan_facts": count("sc.legacy.financing.loan.fact", []),
    "legacy_fund_daily_snapshot_facts": count("sc.legacy.fund.daily.snapshot.fact", []),
    "legacy_fund_daily_line_facts": count("sc.legacy.fund.daily.line", [], active_test=False),
    "legacy_fund_daily_line_with_project": count(
        "sc.legacy.fund.daily.line",
        [("project_id", "!=", False)],
        required_fields=["project_id"],
        active_test=False,
    ),
    "treasury_reconciliation_runtime_records": count("sc.treasury.reconciliation", [], active_test=False),
    "treasury_reconciliation_legacy_records": count(
        "sc.treasury.reconciliation",
        [("source_origin", "=", "legacy")],
        required_fields=["source_origin"],
        active_test=False,
    ),
    "treasury_reconciliation_legacy_with_project": count(
        "sc.treasury.reconciliation",
        [("source_origin", "=", "legacy"), ("project_id", "!=", False)],
        required_fields=["source_origin", "project_id"],
        active_test=False,
    ),
    "legacy_workflow_audit_facts": count("sc.legacy.workflow.audit", []),
    "history_todo_total": count("sc.history.todo", [], active_test=False),
    "history_todo_open": count(
        "sc.history.todo",
        [("state", "in", ["todo", "acknowledged"])],
        required_fields=["state"],
        active_test=False,
    ),
    "mail_activity_total": count("mail.activity", [], active_test=False),
    "mail_activity_for_history_models": count(
        "mail.activity",
        [("res_model", "in", ["payment.request", "construction.contract", "project.project", "project.task"])],
        required_fields=["res_model"],
        active_test=False,
    ),
    "mail_activity_assigned_legacy_users": count(
        "mail.activity",
        [("user_id.login", "like", "legacy_%")],
        required_fields=["user_id"],
        active_test=False,
    ),
    "mail_activity_on_payment_requests": count(
        "mail.activity",
        [("res_model", "=", "payment.request")],
        required_fields=["res_model"],
        active_test=False,
    ),
    "mail_activity_on_contracts": count(
        "mail.activity",
        [("res_model", "=", "construction.contract")],
        required_fields=["res_model"],
        active_test=False,
    ),
    "mail_activity_on_projects": count(
        "mail.activity",
        [("res_model", "=", "project.project")],
        required_fields=["res_model"],
        active_test=False,
    ),
    "tier_review_total": count("tier.review", [], active_test=False),
    "tier_review_pending": count(
        "tier.review",
        [("state", "not in", ["approved", "rejected", "cancel", "done"])],
        required_fields=["state"],
        active_test=False,
    ),
    "project_task_total": count("project.task", []),
    "project_task_assigned": count(
        "project.task",
        project_task_assigned_domain() or [],
        active_test=False,
    ) if project_task_assigned_domain() else None,
}

counts["payment_request_state_distribution"] = grouped_state_counts(
    "payment.request",
    migrated_payment_request_domain(),
)

sample_runtime_records = {
    "project_project_id": sample_id("project.project", [("legacy_project_id", "!=", False)], required_fields=["legacy_project_id"]),
    "construction_contract_id": sample_id("construction.contract", [("legacy_contract_id", "!=", False)], required_fields=["legacy_contract_id"]),
    "payment_request_id": sample_id("payment.request", migrated_payment_request_domain()),
    "payment_request_line_id": sample_id("payment.request.line", []),
    "receipt_invoice_line_id": sample_id("sc.receipt.invoice.line", []),
    "receipt_invoice_attachment_id": sample_id(
        "ir.attachment",
        [("res_model", "=", "sc.receipt.invoice.line"), ("type", "=", "url")],
        required_fields=["res_model", "type"],
        active_test=False,
    ),
    "legacy_file_index_id": sample_id("sc.legacy.file.index", [], active_test=False),
    "legacy_invoice_registration_line_id": sample_id("sc.legacy.invoice.registration.line", [], active_test=False),
    "receipt_income_id": sample_id("sc.receipt.income", [], active_test=False),
    "legacy_expense_deposit_fact_id": sample_id("sc.legacy.expense.deposit.fact", [], active_test=False),
    "legacy_expense_reimbursement_line_id": sample_id("sc.legacy.expense.reimbursement.line", [], active_test=False),
    "expense_claim_id": sample_id("sc.expense.claim", [], active_test=False),
    "legacy_material_detail_id": sample_id("sc.legacy.material.detail", [], active_test=False),
    "legacy_purchase_contract_fact_id": sample_id("sc.legacy.purchase.contract.fact", [], active_test=False),
    "legacy_deduction_adjustment_line_id": sample_id("sc.legacy.deduction.adjustment.line", [], active_test=False),
    "settlement_adjustment_id": sample_id("sc.settlement.adjustment", [], active_test=False),
    "legacy_fund_confirmation_line_id": sample_id("sc.legacy.fund.confirmation.line", [], active_test=False),
    "legacy_financing_loan_fact_id": sample_id("sc.legacy.financing.loan.fact", [], active_test=False),
    "legacy_fund_daily_snapshot_fact_id": sample_id("sc.legacy.fund.daily.snapshot.fact", [], active_test=False),
    "legacy_fund_daily_line_id": sample_id("sc.legacy.fund.daily.line", [], active_test=False),
    "treasury_reconciliation_id": sample_id("sc.treasury.reconciliation", [], active_test=False),
    "treasury_ledger_id": sample_id("sc.treasury.ledger", [], active_test=False),
    "legacy_workflow_audit_id": sample_id("sc.legacy.workflow.audit", []),
    "history_todo_id": sample_id("sc.history.todo", [], active_test=False),
    "mail_activity_id": sample_id("mail.activity", [], active_test=False),
    "tier_review_id": sample_id("tier.review", [], active_test=False),
}

promotion_gaps = {
    "runtime_list_form_missing": [
        key
        for key in ("project_project_id", "construction_contract_id", "payment_request_id")
        if not sample_runtime_records.get(key)
    ],
    "project_member_owner_promotion_gap": bool(
        (counts.get("project_member_carrier") or 0) > 0
        and (counts.get("project_records_with_owner_link") or 0) == 0
    ),
    "contract_partner_runtime_gap": bool(
        (counts.get("contract_runtime_records") or 0) > 0
        and (counts.get("contract_records_with_partner_link") or 0) == 0
    ),
    "payment_request_runtime_link_gap": bool(
        (counts.get("payment_request_runtime_records") or 0) > 0
        and (
            (counts.get("payment_request_with_project_link") or 0) == 0
            or (counts.get("payment_request_with_contract_link") or 0) == 0
        )
    ),
    "workflow_audit_without_actionable_runtime": bool(
        (counts.get("legacy_workflow_audit_facts") or 0) > 0
        and (counts.get("history_todo_total") or 0) == 0
        and (counts.get("mail_activity_total") or 0) == 0
        and (counts.get("tier_review_total") or 0) == 0
    ),
    "no_actionable_todo_surface": bool(
        (counts.get("history_todo_total") or 0) == 0
        and (counts.get("mail_activity_total") or 0) == 0
        and (counts.get("tier_review_total") or 0) == 0
    ),
    "payment_request_no_pending_runtime_states": bool(
        (counts.get("payment_request_runtime_records") or 0) > 0
        and sum(
            int((counts.get("payment_request_state_distribution") or {}).get(state) or 0)
            for state in ("submit", "approve", "approved")
        ) == 0
    ),
    "payment_receipt_execution_surface_gap": bool(
        ((counts.get("legacy_actual_outflow_cash_requests") or 0) + (counts.get("legacy_receipt_cash_requests") or 0)) > 0
        and (counts.get("treasury_ledger_runtime_records") or 0) == 0
    ),
    "attachment_custody_surface_gap": bool(
        (counts.get("legacy_file_index_rows") or 0) > 0
        and (counts.get("legacy_url_attachments") or 0) == 0
    ),
    "invoice_tax_runtime_surface_gap": bool(
        (counts.get("legacy_invoice_tax_facts") or 0) > 0
        and (counts.get("legacy_invoice_registration_lines") or 0) == 0
    ),
    "receipt_income_runtime_surface_gap": bool(
        ((counts.get("legacy_receipt_income_facts") or 0) + (counts.get("legacy_receipt_residual_with_project") or 0)) > 0
        and (counts.get("receipt_income_legacy_with_project") or 0) == 0
    ),
    "settlement_adjustment_runtime_surface_gap": bool(
        (counts.get("legacy_deduction_adjustment_lines_with_project") or 0) > 0
        and (counts.get("settlement_adjustment_legacy_with_project") or 0) == 0
    ),
    "treasury_reconciliation_surface_gap": bool(
        (
            (counts.get("legacy_financing_loan_facts") or 0)
            + (counts.get("legacy_fund_daily_snapshot_facts") or 0)
            + (counts.get("legacy_fund_daily_line_facts") or 0)
        ) > 0
        and (
            not sample_runtime_records.get("treasury_ledger_id")
            or not sample_runtime_records.get("legacy_financing_loan_fact_id")
            or not sample_runtime_records.get("legacy_fund_daily_snapshot_fact_id")
            or not sample_runtime_records.get("legacy_fund_daily_line_id")
            or (counts.get("treasury_reconciliation_legacy_with_project") or 0) == 0
        )
    ),
    "expense_deposit_runtime_surface_gap": bool(
        ((counts.get("legacy_expense_deposit_facts") or 0) + (counts.get("legacy_expense_reimbursement_lines") or 0)) > 0
        and (
            not sample_runtime_records.get("legacy_expense_deposit_fact_id")
            or not sample_runtime_records.get("legacy_expense_reimbursement_line_id")
        )
    ),
    "expense_claim_runtime_surface_gap": bool(
        (
            (counts.get("legacy_expense_deposit_facts") or 0)
            + (counts.get("legacy_expense_reimbursement_lines_with_project") or 0)
        ) > 0
        and (counts.get("expense_claim_legacy_with_project") or 0) == 0
    ),
    "material_catalog_runtime_surface_gap": bool(
        (counts.get("legacy_material_detail_rows") or 0) > 0
        and (
            not sample_runtime_records.get("legacy_material_detail_id")
            or counts.get("legacy_material_detail_promoted") is None
            or counts.get("product_templates_from_legacy_material") is None
        )
    ),
    "purchase_contract_runtime_surface_gap": bool(
        (counts.get("legacy_purchase_contract_facts") or 0) > 0
        and not sample_runtime_records.get("legacy_purchase_contract_fact_id")
    ),
    "legacy_user_access_runtime_gap": bool(
        (counts.get("legacy_user_roles") or 0) > 0
        and (
            (counts.get("legacy_user_roles_projected") or 0) == 0
            or (counts.get("legacy_users_with_runtime_capability_groups") or 0) == 0
            or (
                (counts.get("legacy_user_project_scopes_current_with_project") or 0) > 0
                and (counts.get("legacy_user_project_scopes_access_applied") or 0) == 0
            )
        )
    ),
}

failing_gaps = [
    key
    for key, value in promotion_gaps.items()
    if (isinstance(value, list) and value) or (isinstance(value, bool) and value)
]

decision = "history_business_usable_ready"
if promotion_gaps["runtime_list_form_missing"]:
    decision = "history_business_usable_runtime_gap"
elif failing_gaps:
    decision = "history_business_usable_visible_but_promotion_gaps"

payload = {
    "status": "PASS",
    "mode": "history_business_usable_probe",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "counts": counts,
    "sample_runtime_records": sample_runtime_records,
    "promotion_gaps": promotion_gaps,
    "decision": decision,
}

write_json(OUTPUT_JSON, payload)
write_report(OUTPUT_REPORT, payload)
print(
    "HISTORY_BUSINESS_USABLE_PROBE="
    + json.dumps(
        {
            "status": payload["status"],
            "database": payload["database"],
            "decision": payload["decision"],
            "gap_count": len(failing_gaps),
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
