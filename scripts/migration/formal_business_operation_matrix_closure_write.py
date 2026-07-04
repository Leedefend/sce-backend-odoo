# -*- coding: utf-8 -*-
"""Close first formal business operation matrix gaps.

Run with:
    MIGRATION_REPLAY_DB_ALLOWLIST=sc_demo \
    odoo shell -d sc_demo -c /path/to/odoo.conf --no-http \
      < scripts/migration/formal_business_operation_matrix_closure_write.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from odoo.addons.smart_core.handlers.form_field_configuration import (
    _business_config_contract_name,
    _business_config_view_orchestration_payload,
    _upsert_view_orchestration_field_rows,
)


MATERIAL_INBOUND_FIELDS = [
    "name",
    "project_id",
    "business_category_id",
    "operation_strategy",
    "inbound_date",
    "material_name_summary",
    "material_spec_summary",
    "material_uom_summary",
    "total_qty",
    "unit_price_summary",
    "amount_total",
    "acceptance_id",
    "supplier_id",
    "warehouse_id",
    "dest_location_id",
    "keeper_id",
    "line_note_summary",
    "state",
    "source_created_by",
    "source_created_at",
]

EXPENSE_DEPOSIT_FIELDS = [
    "name",
    "project_id",
    "business_category_id",
    "claim_type",
    "guarantee_type",
    "expense_type",
    "document_date",
    "partner_id",
    "amount",
    "summary",
    "state",
    "requester_id",
    "source_created_by",
    "source_created_at",
]

EXPENSE_DEPOSIT_SEARCH = [
    "project_id",
    "business_category_id",
    "claim_type",
    "guarantee_type",
    "expense_type",
    "partner_id",
    "state",
    "document_date",
]

EXPENSE_DEPOSIT_GROUP_BY = [
    "project_id",
    "business_category_id",
    "claim_type",
    "guarantee_type",
    "state",
]


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def _valid_names(model: str, names: list[str]) -> list[str]:
    fields = set(getattr(env[model], "_fields", {}) or {})  # noqa: F821
    return [name for name in names if name in fields]


def _upsert_contract(*, model: str, view_type: str, action_id: int, payload: dict):
    Contract = env["ui.business.config.contract"].sudo()  # noqa: F821
    name = _business_config_contract_name(model, view_type, action_id, 0)
    domain = [
        ("name", "=", name),
        ("company_id", "=", env.company.id),  # noqa: F821
        ("view_type", "=", view_type),
        ("action_id", "=", action_id),
        ("view_id", "=", False),
        ("role_key", "=", False),
    ]
    vals = {
        "name": name,
        "model": model,
        "view_type": view_type,
        "action_id": action_id,
        "view_id": False,
        "role_key": False,
        "contract_json": payload,
        "status": "published",
    }
    rec = Contract.search(domain, limit=1)
    if rec:
        rec.write(vals)
    else:
        rec = Contract.create(vals)
    rec.action_publish()
    return rec


def _publish_form_contract(model: str, action_id: int, fields: list[str], *, group_title: str):
    rows = [
        {"name": name, "sequence": (index + 1) * 10, "group_title": group_title}
        for index, name in enumerate(_valid_names(model, fields))
    ]
    _upsert_view_orchestration_field_rows(
        env,  # noqa: F821
        model=model,
        view_type="form",
        action_id=action_id,
        view_id=0,
        rows=rows,
        form_columns=2,
        group_columns={group_title: 2},
    )
    rec = env["ui.business.config.contract"].sudo().search([  # noqa: F821
        ("name", "=", _business_config_contract_name(model, "form", action_id, 0)),
        ("company_id", "=", env.company.id),  # noqa: F821
    ], limit=1)
    if rec and rec.status != "published":
        rec.action_publish()
    return rec


def _publish_list_search_contracts(model: str, action_id: int, columns: list[str], filters: list[str], group_by: list[str]):
    tree_payload = _business_config_view_orchestration_payload(
        view_type="tree",
        names=_valid_names(model, columns),
    )
    tree = _upsert_contract(model=model, view_type="tree", action_id=action_id, payload=tree_payload)

    search_payload = _business_config_view_orchestration_payload(
        view_type="search",
        names=_valid_names(model, filters),
        search_key="filters",
    )
    search_payload = _business_config_view_orchestration_payload(
        view_type="search",
        names=_valid_names(model, group_by),
        existing=search_payload,
        search_key="group_by",
    )
    search = _upsert_contract(model=model, view_type="search", action_id=action_id, payload=search_payload)
    return tree, search


def _write_action(action, vals: dict) -> dict:
    before = {
        "res_model": action.res_model,
        "domain": action.domain,
        "context": action.context,
        "view_mode": action.view_mode,
    }
    action.write(vals)
    after = {
        "res_model": action.res_model,
        "domain": action.domain,
        "context": action.context,
        "view_mode": action.view_mode,
    }
    return {"before": before, "after": after}


def run() -> dict:
    ensure_allowed_db()
    result = {"database": env.cr.dbname, "changes": {}}  # noqa: F821

    material_action = env.ref("smart_construction_core.action_sc_material_inbound_handling")  # noqa: F821
    material_form = _publish_form_contract(
        "sc.material.inbound",
        material_action.id,
        MATERIAL_INBOUND_FIELDS,
        group_title="入库办理",
    )
    result["changes"]["material_inbound_form_contract_id"] = material_form.id if material_form else 0

    payment_action = env.ref("smart_construction_core.action_sc_payment_deposit_return")  # noqa: F821
    result["changes"]["payment_deposit_return_action"] = _write_action(payment_action, {
        "name": "付款还保证金",
        "res_model": "sc.expense.claim",
        "view_mode": "tree,form",
        "view_id": False,
        "search_view_id": env.ref("smart_construction_core.view_sc_expense_claim_deposit_cash_search").id,  # noqa: F821
        "domain": "[('claim_type', '=', 'deposit_pay'), ('expense_type', '=', '付款还保证金')]",
        "context": "{'default_claim_type': 'deposit_pay', 'default_expense_type': '付款还保证金', 'default_summary': '付款还保证金', 'search_default_active_rows': 1, 'search_default_deposit_payment': 1, 'search_default_group_project': 1}",
    })
    payment_form = _publish_form_contract(
        "sc.expense.claim",
        payment_action.id,
        EXPENSE_DEPOSIT_FIELDS,
        group_title="付款还保证金",
    )
    payment_tree, payment_search = _publish_list_search_contracts(
        "sc.expense.claim",
        payment_action.id,
        EXPENSE_DEPOSIT_FIELDS,
        EXPENSE_DEPOSIT_SEARCH,
        EXPENSE_DEPOSIT_GROUP_BY,
    )
    result["changes"]["payment_deposit_return_contract_ids"] = {
        "form": payment_form.id if payment_form else 0,
        "tree": payment_tree.id,
        "search": payment_search.id,
    }

    refund_action = env.ref("smart_construction_core.action_sc_payment_deposit_return_refund_formal", raise_if_not_found=False)  # noqa: F821
    if not refund_action:
        refund_action = env["ir.actions.act_window"].sudo().create({  # noqa: F821
            "name": "付款还保证金退回",
            "type": "ir.actions.act_window",
            "res_model": "sc.expense.claim",
            "view_mode": "tree,form",
            "search_view_id": env.ref("smart_construction_core.view_sc_expense_claim_deposit_cash_search").id,  # noqa: F821
            "domain": "[('claim_type', '=', 'deposit_refund'), ('expense_type', '=', '付款还保证金退回')]",
            "context": "{'default_claim_type': 'deposit_refund', 'default_expense_type': '付款还保证金退回', 'default_summary': '付款还保证金退回', 'search_default_active_rows': 1, 'search_default_deposit_refund': 1, 'search_default_group_project': 1}",
        })
        env["ir.model.data"].sudo().create({  # noqa: F821
            "module": "smart_construction_core",
            "name": "action_sc_payment_deposit_return_refund_formal",
            "model": "ir.actions.act_window",
            "res_id": refund_action.id,
            "noupdate": False,
        })
        result["changes"]["payment_deposit_return_refund_action_created"] = refund_action.id
    else:
        result["changes"]["payment_deposit_return_refund_action"] = _write_action(refund_action, {
            "name": "付款还保证金退回",
            "res_model": "sc.expense.claim",
            "view_mode": "tree,form",
            "view_id": False,
            "search_view_id": env.ref("smart_construction_core.view_sc_expense_claim_deposit_cash_search").id,  # noqa: F821
            "domain": "[('claim_type', '=', 'deposit_refund'), ('expense_type', '=', '付款还保证金退回')]",
            "context": "{'default_claim_type': 'deposit_refund', 'default_expense_type': '付款还保证金退回', 'default_summary': '付款还保证金退回', 'search_default_active_rows': 1, 'search_default_deposit_refund': 1, 'search_default_group_project': 1}",
        })
    refund_menu = env.ref("smart_construction_core.menu_sc_payment_deposit_return_refund_formal")  # noqa: F821
    refund_menu.write({"action": "ir.actions.act_window,%s" % refund_action.id, "active": True})
    refund_form = _publish_form_contract(
        "sc.expense.claim",
        refund_action.id,
        EXPENSE_DEPOSIT_FIELDS,
        group_title="付款还保证金退回",
    )
    refund_tree, refund_search = _publish_list_search_contracts(
        "sc.expense.claim",
        refund_action.id,
        EXPENSE_DEPOSIT_FIELDS,
        EXPENSE_DEPOSIT_SEARCH,
        EXPENSE_DEPOSIT_GROUP_BY,
    )
    result["changes"]["payment_deposit_return_refund_contract_ids"] = {
        "form": refund_form.id if refund_form else 0,
        "tree": refund_tree.id,
        "search": refund_search.id,
    }

    tax_menu = env.ref("smart_construction_core.menu_sc_tax_certificate_registration_user")  # noqa: F821
    before_active = bool(tax_menu.active)
    tax_menu.write({"active": True})
    result["changes"]["tax_certificate_menu_active"] = {"before": before_active, "after": bool(tax_menu.active)}

    env.cr.commit()  # noqa: F821
    output = artifact_root() / "formal_business_operation_matrix_closure_result_v1.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print("[formal_business_operation_matrix_closure] %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


run()
