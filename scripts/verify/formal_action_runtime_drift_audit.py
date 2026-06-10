#!/usr/bin/env python3
"""Audit high-risk formal action overrides for runtime drift.

The user-confirmed formal list files load after the product taxonomy and can
override action domains and view bindings. This gate catches the recurrent
failure mode where an override leaves a formal menu bound to an empty legacy
domain or an unexpected list view.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from xml.etree import ElementTree as ET

from odoo.tools.safe_eval import safe_eval


OUTPUT_JSON_NAME = "formal_action_runtime_drift_audit_v1.json"
MODULE = "smart_construction_core"
ADDON_ROOT_CANDIDATES = [
    Path("/mnt/extra-addons/smart_construction_core"),
    Path.cwd() / "addons" / "smart_construction_core",
]
HIGH_RISK_XML_FILES = [
    "views/support/user_confirmed_formal_list_alignment_views.xml",
    "views/support/user_confirmed_formal_list_views.xml",
]
EXPECTED_NON_EMPTY_ACTIONS = {
    "action_sc_labor_usage_ticket",
    "action_sc_labor_usage_casual",
    "action_sc_expense_claim_deduction_bill",
    "action_sc_payment_execution_company_finance_expense",
    "action_sc_payment_deposit_return",
    "action_sc_salary_registration",
    "action_construction_contract_expense_execution",
    "action_sc_material_quote_user_confirmed",
    "action_sc_subcontract_request_user_confirmed",
    "action_sc_equipment_usage_shift_user_confirmed",
    "action_payment_request_user_payment_apply",
    "action_sc_payment_execution_partner_payment",
    "action_sc_legacy_fuel_card_fact",
    "action_sc_legacy_fuel_card_recharge_fact",
    "action_sc_legacy_fuel_card_refuel_fact",
    "action_construction_contract_income_construction",
    "action_sc_material_inbound",
    "action_sc_material_rental_in_acceptance",
    "action_sc_material_rental_return_acceptance",
    "action_sc_construction_diary",
    "action_sc_receipt_income_engineering_progress",
    "action_sc_invoice_input_report_user",
    "action_sc_invoice_registration_user",
    "action_sc_settlement_order_income",
    "action_sc_settlement_order_expense",
}
EXPECTED_ACTION_CONTRACTS = {
    "action_sc_receipt_income_engineering_progress": {
        "name": "工程进度款收入登记",
        "res_model": "sc.receipt.income",
        "view_name": "sc.receipt.income.engineering.progress.user.confirmed.tree",
        "field_names": [
            "p1_visible_06fa8c6f628f",
            "p1_visible_3e7255522b33",
            "p1_visible_00381a68b952",
            "p1_visible_8cd973ab9373",
            "p1_visible_205fcc1bc5d4",
            "p1_visible_8fa8662ad38f",
            "p1_visible_71e47f617269",
            "p1_visible_49a5d541678c",
            "p1_visible_2ff90909b29b",
            "p1_visible_807b71479e35",
            "p1_visible_0d20172efa91",
            "p1_visible_e0361480e3a5",
            "p1_visible_99f6fe6c41ad",
            "p1_visible_ee6a4d9e2956",
            "p1_visible_dfc25d77dc39",
        ],
    },
}


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/formal_action_runtime_drift/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def addon_root() -> Path:
    for candidate in ADDON_ROOT_CANDIDATES:
        if candidate.exists():
            return candidate
    raise RuntimeError({"addon_root_missing": [str(item) for item in ADDON_ROOT_CANDIDATES]})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def action_records() -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    root = addon_root()
    for relative in HIGH_RISK_XML_FILES:
        path = root / relative
        xml_root = ET.fromstring(path.read_text(encoding="utf-8"))
        for node in xml_root.findall(".//record[@model='ir.actions.act_window']"):
            action_id = node.get("id") or ""
            if not action_id:
                continue
            fields = {field.get("name") or "": (field.text or "").strip() for field in node.findall("field")}
            records[action_id] = {
                "file": relative,
                "xml_domain": fields.get("domain", ""),
                "xml_name": fields.get("name", ""),
                "has_view_override": "view_id" in fields or "view_ids" in fields,
            }
    return records


def tree_field_names(view) -> list[str]:
    if not view:
        return []
    root = ET.fromstring(view.arch_db.encode("utf-8"))
    return [node.get("name") or "" for node in root.iter("field")]


rows = []
failures = []
for action_id, spec in sorted(action_records().items()):
    xmlid = f"{MODULE}.{action_id}"
    action = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
    if not action:
        failures.append({"action_xmlid": xmlid, "reason": "missing_action", **spec})
        continue
    domain = safe_eval(action.domain or "[]")
    count = None
    count_error = None
    if action.res_model in env:  # noqa: F821
        try:
            count = int(env[action.res_model].sudo().search_count(domain))  # noqa: F821
        except Exception as exc:  # pragma: no cover - executed inside Odoo shell
            count_error = f"{type(exc).__name__}: {str(exc)[:240]}"
    else:
        count_error = "missing_res_model"

    tree_bindings = action.view_ids.filtered(lambda item: item.view_mode == "tree").sorted("sequence")
    primary_tree = action.view_id if action.view_id.type == "tree" else (tree_bindings[0].view_id if tree_bindings else False)
    row = {
        "action_xmlid": xmlid,
        "action_id": int(action.id),
        "name": action.name,
        "res_model": action.res_model,
        "domain": action.domain or "",
        "record_count": count,
        "count_error": count_error,
        "primary_tree": primary_tree.name if primary_tree else "",
        "field_count": len(tree_field_names(primary_tree)) if primary_tree else 0,
        **spec,
    }
    rows.append(row)

    if count_error:
        failures.append({"reason": "domain_count_error", **row})
    if action_id in EXPECTED_NON_EMPTY_ACTIONS and count == 0:
        failures.append({"reason": "empty_high_risk_formal_action_domain", **row})

    expected = EXPECTED_ACTION_CONTRACTS.get(action_id)
    if expected:
        actual_fields = tree_field_names(primary_tree)
        for key in ("name", "res_model"):
            if row[key] != expected[key]:
                failures.append({"reason": f"wrong_{key}", "expected": expected[key], **row})
        if row["primary_tree"] != expected["view_name"]:
            failures.append({"reason": "wrong_primary_tree", "expected": expected["view_name"], **row})
        if actual_fields != expected["field_names"]:
            failures.append(
                {
                    "reason": "wrong_tree_fields",
                    "expected_fields": expected["field_names"],
                    "actual_fields": actual_fields,
                    **row,
                }
            )

payload = {
    "status": "FAIL" if failures else "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "formal_action_runtime_drift_audit",
    "audited_actions": len(rows),
    "failure_count": len(failures),
    "failures": failures,
    "rows": rows,
}
write_json(artifact_root() / OUTPUT_JSON_NAME, payload)
print("FORMAL_ACTION_RUNTIME_DRIFT_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if failures:
    raise RuntimeError({"formal_action_runtime_drift_audit_failed": failures})
