#!/usr/bin/env python3
"""Build a menu-driven visible data and usability matrix.

This script is intended to run inside ``odoo shell``.  It uses the current
user-visible menu/action facts as the source of truth, then checks whether each
business page has usable view structures, search controls, access rights, and
historical business-data coverage for fields that are available in native
views.  Coverage gaps are data-carrying signals; they must not be interpreted
as a reason to remove fields from list views.  Column visibility remains a user
preference concern.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

from lxml import etree
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


DEFAULT_MENU_ROOTS = ("智慧施工管理平台", "项目", "业务配置")
DEFAULT_MODEL_PREFIXES = ("project.", "sc.", "construction.", "tender.", "payment.", "hr.department")
SKIP_FIELD_TYPES = {"binary", "html"}
SKIP_COMPLETENESS_FIELD_TYPES = SKIP_FIELD_TYPES | {"one2many", "many2many"}
NUMERIC_FIELD_TYPES = {"integer", "float", "monetary"}
SKIP_COMPLETENESS_FIELD_NAMES = {
    "active",
    "display_name",
    "is_favorite",
    "message_ids",
    "message_follower_ids",
    "activity_ids",
    "attachment_ids",
    "task_properties",
}
SCENE_COMPLETENESS_FIELD_EXCLUDES = {
    ("project.project", None, None): {
        "analytic_account_id",
        "date",
        "date_start",
        "business_nature",
    },
    ("project.task", None, None): {
        "partner_id",
        "date_deadline",
        "date_last_stage_update",
        "stage_id",
    },
    ("project.cost.code", None, None): {
        "parent_id",
    },
    ("hr.department", None, None): {
        "manager_id",
    },
    ("tender.guarantee", None, None): {
        "bank_account_id",
        "receipt_bank_account_id",
    },
    ("sc.legacy.material.category", None, None): {
        "parent_id",
        "uom_text",
    },
    ("sc.expense.claim", "claim_type", "expense"): {
        "guarantee_project_name",
        "guarantee_type",
        "payment_account_name",
        "payer_account",
        "payer_bank",
    },
    ("sc.dashboard.cockpit.fact", "fact_type", "fund_cockpit"): {
        "project_id",
        "partner_id",
        "requester_id",
        "handler_id",
    },
    ("project.project.stage", None, None): {
        "mail_template_id",
        "sms_template_id",
    },
    ("sc.payment.execution", "source_kind", "actual_outflow"): {
        "handler_name",
    },
    ("sc.document.admin.document", "fact_type", "company_document_archive"): {
        "certificate_name",
        "certificate_no",
        "valid_until",
        "borrow_user_id",
        "borrow_date",
        "expected_return_date",
    },
    ("sc.document.admin.document", "fact_type", "certificate_registration"): {
        "borrow_user_id",
        "borrow_date",
        "expected_return_date",
    },
    ("sc.document.admin.document", "fact_type", "document_borrow"): {
        "certificate_name",
        "certificate_no",
        "valid_until",
    },
    ("sc.hr.payroll.document", "fact_type", "salary_registration"): {
        "employee_user_id",
    },
    ("sc.hr.payroll.document", "fact_type", "social_registration"): {
        "employee_user_id",
    },
    ("sc.hr.payroll.document", "fact_type", "subsidy"): {
        "document_no",
        "employee_user_id",
        "payer_unit",
        "legacy_document_no",
    },
}
SOURCE_COMPLETENESS_FIELD_EXCLUDES = {
    ("sc.payment.execution", "legacy_source_model", "payment.request.line"): {
        "payment_method",
        "bank_account",
        "payment_account_name",
        "payment_account_no",
        "payment_bank_name",
        "receipt_account_name",
        "receipt_account_no",
        "receipt_bank_name",
        "handler_name",
    },
    ("sc.payment.execution", "legacy_source_model", "sc.legacy.scbs.fact.staging"): {
        "payment_method",
        "bank_account",
        "payment_account_name",
        "payment_account_no",
        "payment_bank_name",
        "receipt_account_name",
        "receipt_account_no",
        "receipt_bank_name",
        "handler_name",
    },
    ("sc.payment.execution", "legacy_source_model", "sc.legacy.payment.residual.fact"): {
        "payment_account_name",
        "payment_account_no",
        "payment_bank_name",
        "receipt_account_name",
        "receipt_account_no",
        "receipt_bank_name",
    },
    ("sc.receipt.income", "legacy_source_model", "sc.legacy.receipt.income.fact"): {
        "contract_id",
        "payment_method",
        "receiving_account",
        "receiving_account_name",
        "receiving_account_no",
        "receiving_bank_name",
        "bill_no",
        "invoice_ref",
        "creator_name",
        "created_time",
    },
    ("sc.receipt.income", "legacy_source_model", "sc.legacy.receipt.residual.fact"): {
        "receiving_account_name",
        "receiving_account_no",
        "receiving_bank_name",
        "bill_no",
    },
    ("sc.treasury.ledger", "source_kind", "legacy_actual_outflow"): {
        "settlement_id",
    },
    ("sc.treasury.ledger", "source_kind", "legacy_receipt"): {
        "settlement_id",
    },
    ("sc.general.contract", "legacy_source_model", "sc.legacy.scbs.fact.staging"): {
        "submitted_time",
        "contact_name",
        "contact_phone",
        "sign_status",
        "contract_attribute",
        "pricing_mode",
        "subcontract_mode",
        "handler_id",
        "engineering_address",
    },
    ("sc.general.contract", "legacy_source_model", "sc.legacy.purchase.contract.fact"): {
        "contract_attribute",
        "pricing_mode",
        "sign_status",
        "subcontract_mode",
        "engineering_address",
    },
    ("sc.invoice.registration", "legacy_source_model", "sc.legacy.invoice.tax.fact"): {
        "contract_id",
        "settlement_id",
        "voucher_no",
    },
    ("sc.invoice.registration", "legacy_source_model", "sc.legacy.invoice.registration.line"): {
        "settlement_id",
    },
    ("sc.subcontract.register", "legacy_fact_model", "sc.legacy.labor.subcontract.fact"): {
        "request_id",
        "contract_id",
    },
    ("sc.construction.diary", "source_origin", "legacy"): {
        "construction_unit",
        "weather",
    },
    ("sc.material.price", "source_model", "sc.legacy.material.stock.fact"): {
        "supplier_id",
        "expiry_date",
    },
    ("sc.material.catalog", "source_origin", "legacy_stock_projection"): {
        "spec_model",
        "aux_uom_text",
        "short_pinyin",
    },
    ("sc.material.catalog", "source_origin", "legacy"): {
        "spec_model",
        "aux_uom_text",
        "short_pinyin",
    },
    ("sc.material.inbound", "legacy_fact_model", "sc.legacy.material.stock.fact"): {
        "acceptance_id",
        "material_name_summary",
        "material_spec_summary",
        "material_uom_summary",
        "unit_price_summary",
        "line_note_summary",
    },
    ("sc.legacy.tender.registration.fact", "source_table", "P_ZTB_GCBMGL"): {
        "owner_name",
        "tender_status",
    },
}
SOURCE_COMPLETENESS_DOMAIN_EXCLUDES = {
    ("payment.request", "settlement_id"): [
        ("legacy_source_table:T_FK_Supplier", [("legacy_source_table", "=", "T_FK_Supplier")]),
        ("legacy_source_table:C_ZFSQGL", [("legacy_source_table", "=", "C_ZFSQGL")]),
        ("note:[migration:actual_outflow_core]", [("note", "ilike", "[migration:actual_outflow_core]")]),
        ("note:[migration:outflow_request_core]", [("note", "ilike", "[migration:outflow_request_core]")]),
        ("note:[migration:receipt_core]", [("note", "ilike", "[migration:receipt_core]")]),
    ],
    ("sc.settlement.adjustment", "settlement_id"): [
        ("source_origin:legacy", [("source_origin", "=", "legacy")]),
    ],
    ("project.project", "location"): [
        (
            "project_without_address_source",
            [
                "|",
                ("detail_address", "=", False),
                ("detail_address", "=", ""),
            ],
        ),
    ],
    ("sc.receipt.income", "contract_id"): [
        (
            "legacy_residual_without_contract_legacy_id",
            [
                ("legacy_source_model", "=", "sc.legacy.receipt.residual.fact"),
                ("note", "not ilike", "legacy_contract_id="),
            ],
        ),
    ],
    ("sc.receipt.income", "invoice_ref"): [
        (
            "legacy_residual_without_invoice_ref",
            [
                ("legacy_source_model", "=", "sc.legacy.receipt.residual.fact"),
                ("note", "not ilike", "invoice_ref="),
            ],
        ),
    ],
    ("sc.invoice.registration", "contract_id"): [
        (
            "legacy_invoice_line_without_contract_legacy_id",
            [
                ("legacy_source_model", "=", "sc.legacy.invoice.registration.line"),
                ("note", "not ilike", "legacy_contract_id="),
            ],
        ),
    ],
    ("sc.invoice.registration", "voucher_no"): [
        (
            "legacy_invoice_line_without_voucher_no",
            [
                ("legacy_source_model", "=", "sc.legacy.invoice.registration.line"),
                ("note", "not ilike", "voucher_no="),
            ],
        ),
    ],
    ("tender.bid", "owner_id"): [
        (
            "legacy_owner_name_empty",
            ["|", ("legacy_owner_name", "=", False), ("legacy_owner_name", "=", "")],
        ),
    ],
}

LEGACY_SOURCE_EXPECTATIONS = {
    ("project.budget", "项目预算"): [
        (
            "legacy_material_budget_with_project",
            "SELECT COUNT(*) FROM sc_legacy_material_stock_fact "
            "WHERE active AND fact_type = 'material_budget_item' AND project_id IS NOT NULL",
        )
    ],
    ("construction.work.breakdown", "工程结构"): [
        (
            "legacy_wbs_qdkm_relation",
            "SELECT COUNT(*) FROM sc_legacy_business_fact_residual "
            "WHERE active AND source_table = 'SGBW_QDKM'",
        )
    ],
    ("project.cost.code", "成本科目"): [
        (
            "legacy_material_cost_relation_with_project",
            "SELECT COUNT(DISTINCT material_code) FROM sc_legacy_material_stock_fact "
            "WHERE active AND fact_type = 'material_cost_relation' "
            "AND project_id IS NOT NULL AND NULLIF(material_code, '') IS NOT NULL",
        )
    ],
    ("sc.office.admin.document", "请假/休假审批单"): [
        (
            "legacy_residual_leave_approval",
            "SELECT COUNT(*) FROM sc_legacy_business_fact_residual "
            "WHERE source_table = 'BGGL_HBZJ_XZD_QJXJSPB'",
        )
    ],
    ("sc.office.admin.document", "印章使用审批表"): [
        (
            "legacy_residual_seal_approval",
            "SELECT COUNT(*) FROM sc_legacy_business_fact_residual "
            "WHERE source_table IN ('BGGL_XZD_YZSYSPB', 'BGGL_QSJRW_GZQS')",
        )
    ],
    ("sc.hr.payroll.document", "社保人员登记"): [
        (
            "legacy_residual_social_registration",
            "SELECT COUNT(*) FROM sc_legacy_business_fact_residual "
            "WHERE source_table IN ('D_SCBSJS_BGGL_XZ_SBRY', 'fresh_db_legacy_salary_line')",
        )
    ],
    ("sc.hr.payroll.document", "奖金"): [
        (
            "legacy_residual_hr_bonus",
            "SELECT COUNT(*) FROM sc_legacy_business_fact_residual "
            "WHERE source_table IN ('fresh_db_legacy_hr_subsidy', 'fresh_db_legacy_hr_bonus')",
        )
    ],
    ("tender.doc.purchase", "投标报名费申请"): [
        (
            "legacy_tender_document_fee",
            "SELECT COUNT(*) FROM sc_legacy_tender_registration_fact "
            "WHERE active AND COALESCE(document_fee_amount, 0) <> 0",
        )
    ],
    ("tender.bid", "中标记录"): [
        (
            "legacy_tender_won",
            "SELECT COUNT(*) FROM sc_legacy_tender_registration_fact "
            "WHERE active AND (tender_status ILIKE '%中标%' OR document_state ILIKE '%中标%')",
        )
    ],
    ("sc.settlement.order", "收入合同结算"): [
        (
            "legacy_income_settlement",
            "SELECT COUNT(*) FROM sc_legacy_income_invoice_fact "
            "WHERE active AND fact_type IN ('income_settlement', 'settlement')",
        )
    ],
    ("sc.material.purchase.request", "采购申请"): [
        (
            "legacy_material_purchase_request",
            "SELECT COUNT(*) FROM sc_legacy_material_stock_fact "
            "WHERE active AND fact_type IN ('material_purchase_request', 'purchase_request')",
        )
    ],
    ("sc.material.acceptance", "材料进场验收"): [
        (
            "legacy_material_acceptance",
            "SELECT COUNT(*) FROM sc_legacy_material_stock_fact "
            "WHERE active AND fact_type IN ('material_acceptance', 'stock_acceptance')",
        )
    ],
    ("sc.material.rfq", "询比价"): [
        (
            "legacy_material_rfq",
            "SELECT COUNT(*) FROM sc_legacy_material_stock_fact "
            "WHERE active AND fact_type IN ('material_rfq', 'rfq')",
        )
    ],
    ("sc.material.settlement", "材料结算"): [
        (
            "legacy_material_settlement",
            "SELECT COUNT(*) FROM sc_legacy_material_stock_fact "
            "WHERE active AND fact_type IN ('material_settlement', 'stock_settlement')",
        )
    ],
    ("sc.labor.plan", "劳务计划"): [
        (
            "legacy_labor_plan",
            "SELECT COUNT(*) FROM sc_legacy_labor_subcontract_fact "
            "WHERE active AND fact_type IN ('labor_plan')",
        )
    ],
    ("sc.labor.request", "劳务申请"): [
        (
            "legacy_labor_request",
            "SELECT COUNT(*) FROM sc_legacy_labor_subcontract_fact "
            "WHERE active AND fact_type IN ('labor_request')",
        )
    ],
    ("sc.attendance.checkin", "考勤记录"): [
        (
            "legacy_labor_usage_with_project",
            "SELECT COUNT(*) FROM sc_legacy_labor_subcontract_fact "
            "WHERE active AND fact_type = 'labor_usage' AND project_id IS NOT NULL",
        )
    ],
    ("sc.equipment.request", "设备申请"): [
        (
            "legacy_equipment_request",
            "SELECT COUNT(*) FROM sc_legacy_equipment_lease_fact "
            "WHERE active AND fact_type IN ('equipment_request')",
        )
    ],
    ("sc.material.rental.plan", "租赁计划"): [
        (
            "legacy_rental_plan",
            "SELECT COUNT(*) FROM sc_legacy_equipment_lease_fact "
            "WHERE active AND fact_type IN ('rental_plan')",
        )
    ],
    ("sc.subcontract.plan", "分包计划"): [
        (
            "legacy_subcontract_plan",
            "SELECT COUNT(*) FROM sc_legacy_labor_subcontract_fact "
            "WHERE active AND fact_type IN ('subcontract_plan')",
        )
    ],
    ("sc.subcontract.request", "分包申请"): [
        (
            "legacy_subcontract_request",
            "SELECT COUNT(*) FROM sc_legacy_labor_subcontract_fact "
            "WHERE active AND fact_type IN ('subcontract_request')",
        )
    ],
}


def _artifact_root() -> Path:
    candidates = []
    env_root = os.getenv("VISIBLE_MATRIX_ARTIFACT_ROOT") or os.getenv("MIGRATION_ARTIFACT_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(Path("/mnt/artifacts/visible_data_usability_closure"))
    candidates.append(Path(f"/tmp/visible_data_usability_closure/{env.cr.dbname}"))  # noqa: F821
    for root in candidates:
        try:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return root
        except Exception:
            continue
    raise RuntimeError({"artifact_root_unavailable": [str(path) for path in candidates]})


def _as_list(value):
    return value if isinstance(value, list) else []


def _norm(value) -> str:
    return str(value or "").strip()


def _menu_path(menu) -> str:
    names = []
    current = menu
    while current:
        names.append(current.name)
        current = current.parent_id
    return " / ".join(reversed(names))


def _safe_eval(value, fallback):
    if not value:
        return fallback
    if isinstance(value, (list, tuple, dict)):
        return value
    try:
        return safe_eval(str(value), {"uid": user.id, "user": user, "context": {}})  # noqa: F821
    except Exception:
        return fallback


def _view_candidates(action, view_type: str):
    Views = env["ir.ui.view"].sudo()  # noqa: F821
    out = []
    for action_view in action.view_ids:
        if action_view.view_mode == view_type and action_view.view_id:
            out.append(action_view.view_id)
    if action.view_id and action.view_id.type == view_type:
        out.append(action.view_id)
    default_view = Views.search(
        [("model", "=", action.res_model), ("type", "=", view_type)],
        order="priority, id",
        limit=1,
    )
    if default_view:
        out.append(default_view)
    seen = set()
    unique = []
    for view in out:
        if view.id not in seen:
            unique.append(view)
            seen.add(view.id)
    return unique


def _resolved_arch(model, view, view_type: str) -> str:
    try:
        data = model.get_view(view_id=view.id if view else False, view_type=view_type)
        arch = data.get("arch") if isinstance(data, dict) else ""
        if arch:
            return arch
    except Exception:
        pass
    return view.arch_db or "" if view else ""


def _parse_view(model, view, view_type: str):
    arch = _resolved_arch(model, view, view_type)
    try:
        return etree.fromstring(arch.encode("utf-8"))
    except Exception:
        return None


def _is_static_invisible_node(node) -> bool:
    raw_values = [
        node.get("invisible"),
        node.get("column_invisible"),
    ]
    for raw in raw_values:
        if _norm(raw).lower() in {"1", "true", "yes"}:
            return True
    modifiers = node.get("modifiers")
    if modifiers:
        try:
            data = json.loads(modifiers)
        except Exception:
            data = {}
        if data.get("invisible") is True or data.get("column_invisible") is True:
            return True
    return False


def _field_names_from_view(view, model):
    root = _parse_view(model, view, view.type if view else "")
    if root is None:
        return []
    names = []
    for node in root.xpath(".//field[@name]"):
        if _is_static_invisible_node(node):
            continue
        name = node.get("name")
        field = model._fields.get(name or "")
        if not field or field.type in SKIP_FIELD_TYPES:
            continue
        if name not in names:
            names.append(name)
    return names


def _search_controls(view, model):
    root = _parse_view(model, view, "search")
    if root is None:
        return {"filters": 0, "group_by": 0, "fields": 0}
    filters = 0
    group_by = 0
    for node in root.xpath(".//filter"):
        filters += 1
        context_raw = node.get("context") or ""
        if "group_by" in context_raw:
            group_by += 1
    return {
        "filters": filters,
        "group_by": group_by,
        "fields": len(root.xpath(".//field[@name]")),
    }


def _is_empty(value) -> bool:
    if value is False or value is None:
        return True
    if value in ("", [], ()):
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _sample_domain(action):
    domain = _safe_eval(action.domain, [])
    return domain if isinstance(domain, list) else []


def _action_context(action):
    context = _safe_eval(action.context, {})
    return context if isinstance(context, dict) else {}


def _primary_view_type(view_modes):
    for mode in view_modes:
        if mode == "list":
            return "tree"
        if mode in {"tree", "form", "kanban"}:
            return mode
    return "tree"


def _is_create_surface(action, view_modes) -> bool:
    context = _action_context(action)
    if view_modes != ["form"]:
        return False
    return any(str(key).startswith("default_") for key in context) or bool(context.get("intake_mode"))


def _field_empty_domain(field):
    if field.type in {"char", "text", "selection"}:
        return ["|", (field.name, "=", False), (field.name, "=", "")]
    return [(field.name, "=", False)]


def _source_excluded_terms(model_name, field_name):
    return [
        (source_field, source)
        for (target_model, source_field, source), fields in SOURCE_COMPLETENESS_FIELD_EXCLUDES.items()
        if target_model == model_name and field_name in fields
    ]


def _field_effective_domain(model, domain, field_name):
    excluded_terms = [
        (source_field, source)
        for source_field, source in _source_excluded_terms(model._name, field_name)
        if source_field in model._fields
    ]
    domain_exclusions = [
        (label, exclude_domain)
        for label, exclude_domain in SOURCE_COMPLETENESS_DOMAIN_EXCLUDES.get((model._name, field_name), [])
        if all(not isinstance(term, (list, tuple)) or term[0] in model._fields for term in exclude_domain)
    ]
    if not excluded_terms and not domain_exclusions:
        return domain, []
    exclusions = []
    labels = []
    for source_field, source in excluded_terms:
        exclusions.append(["!", (source_field, "=", source)])
        labels.append(f"{source_field}:{source}")
    for label, exclude_domain in domain_exclusions:
        exclusions.append(["!"] + exclude_domain)
        labels.append(label)
    effective_domain = expression.AND([domain, *exclusions])
    return effective_domain, labels


def _field_completeness(model, domain, field_names, total):
    rows = []
    if not total or not field_names:
        return rows
    checked_fields = []
    for name in field_names:
        field = model._fields.get(name)
        if (
            field
            and field.store
            and field.type not in SKIP_COMPLETENESS_FIELD_TYPES
            and name not in SKIP_COMPLETENESS_FIELD_NAMES
        ):
            checked_fields.append(name)
    checked_fields = list(dict.fromkeys(checked_fields))
    for name in checked_fields:
        field = model._fields.get(name)
        if not field:
            continue
        effective_domain, excluded_sources = _field_effective_domain(model, domain, name)
        if excluded_sources:
            try:
                effective_total = model.search_count(effective_domain)
            except Exception:
                effective_total = total
        else:
            effective_total = total
        if not effective_total:
            continue
        if field.type == "boolean" or field.type in NUMERIC_FIELD_TYPES:
            empty_count = 0
        else:
            try:
                empty_count = model.search_count(expression.AND([effective_domain, _field_empty_domain(field)]))
            except Exception:
                empty_count = effective_total
        rows.append(
            {
                "field": name,
                "label": field.string,
                "type": field.type,
                "required": bool(field.required),
                "empty_count": empty_count,
                "sample_count": effective_total,
                "action_record_count": total,
                "empty_ratio": round(empty_count / effective_total, 4) if effective_total else 0,
                "coverage_basis": (
                    "source_applicable_action_count" if excluded_sources else "action_domain_full_count"
                ),
                "excluded_legacy_source_models": excluded_sources,
            }
        )
    return rows


def _domain_equals(domain, field_name, value) -> bool:
    for item in domain:
        if isinstance(item, (list, tuple)) and len(item) >= 3:
            if item[0] == field_name and item[1] == "=" and item[2] == value:
                return True
    return False


def _scene_excluded_fields(model_name, domain):
    excluded = set()
    for (target_model, field_name, value), fields in SCENE_COMPLETENESS_FIELD_EXCLUDES.items():
        if target_model != model_name:
            continue
        if not field_name:
            excluded.update(fields)
        elif _domain_equals(domain, field_name, value):
            excluded.update(fields)
    return excluded


def _access_matrix(model):
    out = {}
    for mode in ("read", "create", "write", "unlink"):
        try:
            out[mode] = bool(model.check_access_rights(mode, raise_exception=False))
        except Exception:
            out[mode] = False
    return out


def _source_breakdown(model, base_domain, fields):
    if "legacy_source_model" not in model._fields:
        return []
    try:
        groups = model.read_group(base_domain, ["legacy_source_model"], ["legacy_source_model"], lazy=False)
    except Exception:
        return []
    out = []
    for group in sorted(groups, key=lambda item: item.get("__count", 0), reverse=True)[:8]:
        source = group.get("legacy_source_model") or False
        source_domain = expression.AND([base_domain, [("legacy_source_model", "=", source)]])
        total = int(group.get("__count") or 0)
        field_rows = []
        for item in fields[:12]:
            field = model._fields.get(item.get("field"))
            if not field or not field.store or field.type == "boolean" or field.type in NUMERIC_FIELD_TYPES:
                continue
            try:
                empty_count = model.search_count(expression.AND([source_domain, _field_empty_domain(field)]))
            except Exception:
                empty_count = total
            field_rows.append(
                {
                    "field": field.name,
                    "empty_count": empty_count,
                    "empty_ratio": round(empty_count / total, 4) if total else 0,
                    "record_count": total,
                }
            )
        out.append(
            {
                "legacy_source_model": source or "",
                "record_count": total,
                "fields": field_rows,
            }
        )
    return out


def _source_query_count(sql):
    table_names = sorted(set(part for part in sql.replace("\n", " ").split() if part.startswith("sc_")))
    for table in table_names:
        try:
            env.cr.execute("SELECT to_regclass(%s)", (table,))  # noqa: F821
            if not env.cr.fetchone()[0]:  # noqa: F821
                return 0
        except Exception:
            return 0
    try:
        env.cr.execute(sql)  # noqa: F821
        row = env.cr.fetchone()  # noqa: F821
        return int(row[0] or 0) if row else 0
    except Exception:
        env.cr.rollback()  # noqa: F821
        return 0


def _legacy_source_signal(row):
    rules = LEGACY_SOURCE_EXPECTATIONS.get((row["model"], row.get("action_name")))
    if rules is None:
        rules = LEGACY_SOURCE_EXPECTATIONS.get((row["model"], None))
    if rules is None:
        return {"known": False, "count": None, "sources": []}
    sources = []
    total = 0
    for label, sql in rules:
        count = _source_query_count(sql)
        sources.append({"source": label, "count": count})
        total += count
    return {"known": True, "count": total, "sources": sources}


def _issue(kind, severity, row, detail="", **extra):
    return {
        "kind": kind,
        "severity": severity,
        "menu": row["menu"],
        "action_id": row["action_id"],
        "action_name": row.get("action_name"),
        "model": row["model"],
        "model_label": row.get("model_label"),
        "view_mode": row.get("view_mode"),
        "record_count": row.get("record_count"),
        "sample_count": row.get("sample_count"),
        "detail": detail,
        **extra,
    }


login = os.getenv("AUDIT_LOGIN", "wutao")
menu_roots = tuple(
    part.strip()
    for part in os.getenv("AUDIT_MENU_ROOTS", ",".join(DEFAULT_MENU_ROOTS)).split(",")
    if part.strip()
)
model_prefixes = tuple(
    part.strip()
    for part in os.getenv("VISIBLE_MATRIX_MODEL_PREFIXES", ",".join(DEFAULT_MODEL_PREFIXES)).split(",")
    if part.strip()
)
limit_actions = int(os.getenv("VISIBLE_MATRIX_LIMIT_ACTIONS", "120"))
sample_limit = int(os.getenv("VISIBLE_MATRIX_SAMPLE_LIMIT", "20"))

Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
Menu = env["ir.ui.menu"].sudo()  # noqa: F821
user = Users.search([("login", "=", login)], limit=1)

visible_menu_count = 0
scoped_menu_count = 0
actions = []
if user:
    visible_ids = Menu.with_user(user)._visible_menu_ids(debug=False)
    visible_menu_count = len(visible_ids)
    for menu in Menu.browse(visible_ids):
        path = _menu_path(menu)
        if menu_roots and not any(path == root or path.startswith(root + " / ") for root in menu_roots):
            continue
        scoped_menu_count += 1
        action_ref = menu.action
        if not action_ref or action_ref._name != "ir.actions.act_window":
            continue
        action = action_ref.sudo()
        if not action.res_model or not action.view_mode:
            continue
        if model_prefixes and not action.res_model.startswith(model_prefixes):
            continue
        actions.append((path, menu, action))
        if len(actions) >= limit_actions:
            break

matrix = []
issues = []
unmapped_empty_surfaces = []
summary_by_model = defaultdict(int)
summary_by_kind = defaultdict(int)

for path, menu, action in actions:
    model = env[action.res_model].with_user(user)  # noqa: F821
    view_modes = [_norm(mode) for mode in (action.view_mode or "").split(",") if _norm(mode)]
    native_view_types = {"tree" if mode == "list" else mode for mode in view_modes}
    primary_view_type = _primary_view_type(view_modes)
    is_create_surface = _is_create_surface(action, view_modes)
    view_fields = {}
    view_ids = {}
    search_controls = {"filters": 0, "group_by": 0, "fields": 0}
    for view_type in ("tree", "form", "kanban", "search"):
        candidates = _view_candidates(action, view_type)
        view = candidates[0] if candidates else False
        view_ids[view_type] = view.id if view else 0
        if view and view_type == "search":
            search_controls = _search_controls(view, model)
        elif view and view_type in {"tree", "form", "kanban"}:
            view_fields[view_type] = _field_names_from_view(view, model)
        else:
            view_fields[view_type] = []

    visible_field_names = []
    for names in view_fields.values():
        for name in names:
            if name not in visible_field_names:
                visible_field_names.append(name)
    primary_field_names = view_fields.get(primary_view_type) or visible_field_names

    access = _access_matrix(model)
    domain = _sample_domain(action)
    records = model.search(domain, limit=sample_limit) if access.get("read") else model.browse()
    try:
        record_count = model.search_count(domain) if access.get("read") else 0
    except Exception:
        record_count = len(records)
    try:
        unrestricted_record_count = env[action.res_model].sudo().search_count(domain)  # noqa: F821
    except Exception:
        unrestricted_record_count = record_count
    legacy_source_signal = {"known": False, "count": None, "sources": []}
    if not is_create_surface and record_count == 0 and not unrestricted_record_count:
        legacy_source_signal = _legacy_source_signal(
            {
                "model": action.res_model,
                "action_name": action.name,
            }
        )
    scene_excluded_fields = _scene_excluded_fields(action.res_model, domain)
    completeness_field_names = [name for name in primary_field_names if name not in scene_excluded_fields]
    completeness = [] if is_create_surface else _field_completeness(model, domain, completeness_field_names, record_count)
    required_empty = [
        row for row in completeness if row["required"] and row["sample_count"] and row["empty_count"] > 0
    ]
    high_empty = [
        row
        for row in completeness
        if not row["required"] and row["sample_count"] >= 5 and row["empty_ratio"] >= 0.8
    ][:12]

    row = {
        "menu_id": menu.id,
        "menu": path,
        "action_id": action.id,
        "action_name": action.name,
        "model": action.res_model,
        "model_label": model._description,
        "view_mode": action.view_mode,
        "native_view_types": sorted(native_view_types),
        "primary_view_type": primary_view_type,
        "is_create_surface": is_create_surface,
        "view_ids": view_ids,
        "view_field_counts": {key: len(value) for key, value in view_fields.items()},
        "search_controls": search_controls,
        "access": access,
        "record_count": record_count,
        "unrestricted_record_count": unrestricted_record_count,
        "legacy_source_fact_count": legacy_source_signal.get("count"),
        "legacy_source_fact_known": bool(legacy_source_signal.get("known")),
        "legacy_source_breakdown": legacy_source_signal.get("sources") or [],
        "sample_count": len(records),
        "visible_field_count": len(visible_field_names),
        "column_visibility_policy": "user_preference_controls_display; matrix_only_reports_data_coverage",
        "scene_excluded_fields": sorted(scene_excluded_fields),
        "required_empty": required_empty[:20],
        "business_data_coverage_gaps": high_empty,
    }
    matrix.append(row)
    summary_by_model[action.res_model] += 1

    if "tree" in native_view_types and not view_fields["tree"]:
        issues.append(_issue("missing_list_structure", "error", row))
    if "form" in native_view_types and not view_fields["form"]:
        issues.append(_issue("missing_form_structure", "error", row))
    if "kanban" in native_view_types and not view_fields["kanban"]:
        issues.append(_issue("missing_kanban_structure", "warning", row))
    if not access.get("read"):
        issues.append(_issue("read_access_unavailable", "error", row))
    if (
        not is_create_surface
        and record_count == 0
        and not action.res_model.startswith(("project.project.stage", "project.tags"))
    ):
        if unrestricted_record_count:
            issues.append(
                _issue(
                    "records_exist_but_current_user_cannot_see",
                    "warning",
                    row,
                    detail=str(unrestricted_record_count),
                    unrestricted_record_count=unrestricted_record_count,
                    interpretation="data_exists_but_record_rules_or_project_scope_hide_it_for_audit_user",
                )
            )
        elif legacy_source_signal.get("known") and legacy_source_signal.get("count"):
            issues.append(
                _issue(
                    "legacy_facts_not_projected_to_business_surface",
                    "warning",
                    row,
                    detail=str(legacy_source_signal.get("count")),
                    legacy_source_breakdown=legacy_source_signal.get("sources") or [],
                    interpretation="legacy_source_facts_exist_but_target_business_surface_is_empty",
                )
            )
        elif not legacy_source_signal.get("known"):
            unmapped_empty_surfaces.append(
                {
                    "menu": row["menu"],
                    "action_id": row["action_id"],
                    "action_name": row.get("action_name"),
                    "model": row["model"],
                    "model_label": row.get("model_label"),
                    "interpretation": "empty_surface_with_no_mapped_legacy_source_expectation",
                }
            )
    if required_empty:
        issues.append(
            _issue(
                "required_business_field_unfilled",
                "error",
                row,
                ",".join(item["field"] for item in required_empty[:8]),
                fields=required_empty[:8],
                source_breakdown=_source_breakdown(model, domain, required_empty[:8]),
                interpretation="data_integrity_gap_not_column_visibility_decision",
            )
        )
    if high_empty:
        issues.append(
            _issue(
                "historical_business_data_coverage_gap",
                "warning",
                row,
                ",".join(item["field"] for item in high_empty[:8]),
                fields=high_empty[:12],
                source_breakdown=_source_breakdown(model, domain, high_empty[:12]),
                interpretation="data_carrying_gap_not_column_visibility_decision",
            )
        )
    if "search" in native_view_types and not any(search_controls.values()):
        issues.append(_issue("missing_search_controls", "warning", row))

for item in issues:
    summary_by_kind[item["kind"]] += 1

payload = {
    "ok": bool(user) and scoped_menu_count > 0 and not any(item["severity"] == "error" for item in issues),
    "database": env.cr.dbname,  # noqa: F821
    "login": login,
    "menu_roots": menu_roots,
    "model_prefixes": model_prefixes,
    "visible_menu_count": visible_menu_count,
    "scoped_menu_count": scoped_menu_count,
    "scanned_action_count": len(matrix),
    "issue_count": len(issues),
    "error_count": sum(1 for item in issues if item["severity"] == "error"),
    "warning_count": sum(1 for item in issues if item["severity"] == "warning"),
    "issue_summary": dict(sorted(summary_by_kind.items())),
    "unmapped_empty_surface_count": len(unmapped_empty_surfaces),
    "unmapped_empty_surfaces": unmapped_empty_surfaces[:200],
    "model_summary": dict(sorted(summary_by_model.items())),
    "issues": issues[:500],
    "matrix": matrix,
}

output = _artifact_root() / "visible_data_usability_matrix_probe_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("VISIBLE_DATA_USABILITY_MATRIX=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))

if not user:
    raise RuntimeError({"visible_data_usability_matrix": "missing user", "login": login})
if scoped_menu_count <= 0:
    raise RuntimeError(
        {
            "visible_data_usability_matrix": "no scoped visible menus",
            "login": login,
            "menu_roots": menu_roots,
            "visible_menu_count": visible_menu_count,
        }
    )
