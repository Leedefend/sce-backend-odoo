#!/usr/bin/env python3
"""Runtime guard for the productized actual payment registration form."""

from __future__ import annotations

import json

from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler


MENU_XMLID = "smart_construction_core.menu_sc_payment_execution"
ACTION_XMLID = "smart_construction_core.action_sc_payment_execution_actual_outflow"
MODEL = "sc.payment.execution"
MAX_FORM_FIELDS = 45
REQUIRED_FIELDS = {
    "name",
    "state",
    "business_category_id",
    "project_id",
    "partner_id",
    "payment_request_id",
    "date_payment",
    "paid_amount",
    "payment_method",
    "document_no",
    "kingdee_document_no",
}
FORBIDDEN_FIELDS = {
    "partner_payment_status_display",
    "partner_payment_payee_unit",
    "partner_payment_attachment_text",
    "company_finance_status_display",
    "company_finance_document_no",
    "company_finance_attachment_text",
    "uc_formal_b4846969514c",
    "uc_formal_a0f538ecc456",
}


def _text(value) -> str:
    return str(value or "").strip()


def _unwrap(result):
    return result.to_legacy_dict() if hasattr(result, "to_legacy_dict") else (result if isinstance(result, dict) else {})


def _field_names(nodes) -> list[str]:
    names = []
    for node in nodes if isinstance(nodes, list) else []:
        if not isinstance(node, dict):
            continue
        node_type = _text(node.get("type") or node.get("containerType")).lower()
        name = _text(node.get("name") or node.get("field"))
        if name and (node_type == "field" or node.get("field")):
            names.append(name)
        for key in ("children", "pages", "tabs", "nodes", "items", "widgetList"):
            names.extend(_field_names(node.get(key)))
    return names


def main() -> int:
    env_obj = globals()["env"]
    menu = env_obj.ref(MENU_XMLID)
    action = env_obj.ref(ACTION_XMLID)
    if menu.action != action:
        raise AssertionError("menu action mismatch: %s -> %s" % (MENU_XMLID, menu.action.display_name))

    payload = {
        "action_id": int(action.id),
        "menu_id": int(menu.id),
        "model": MODEL,
        "view_type": "form",
        "op": "model",
    }
    result = _unwrap(UiContractV2Handler(env=env_obj, su_env=env_obj["ir.model"].sudo().env, payload=payload).handle(payload, None))
    if not result.get("ok"):
        raise AssertionError("ui contract failed: %s" % result)

    layout = (((result.get("data") or {}).get("layoutContract") or {}).get("containerTree") or [])
    fields = _field_names(layout)
    unique_fields = set(fields)
    missing = sorted(REQUIRED_FIELDS - unique_fields)
    forbidden = sorted(FORBIDDEN_FIELDS & unique_fields)
    if len(fields) > MAX_FORM_FIELDS or missing or forbidden:
        raise AssertionError(json.dumps({
            "field_count": len(fields),
            "fields": fields,
            "forbidden_fields": forbidden,
            "max_form_fields": MAX_FORM_FIELDS,
            "missing_required_fields": missing,
        }, ensure_ascii=False, sort_keys=True))

    print("[payment_execution_form_productization_runtime_guard] PASS " + json.dumps({
        "action_id": int(action.id),
        "field_count": len(fields),
        "menu_id": int(menu.id),
        "unique_field_count": len(unique_fields),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
