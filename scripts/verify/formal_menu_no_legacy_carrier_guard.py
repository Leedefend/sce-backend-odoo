#!/usr/bin/env python3
"""Guard formal product menus from regressing to legacy carrier actions."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "scripts/verify/baselines/formal_business_product_menu_policy_v1.json"
MENU_XML = ROOT / "addons/smart_construction_core/views/menu_business_taxonomy.xml"
USER_XML = ROOT / "addons/smart_construction_core/views/support/legacy_user_context_views.xml"
PROBE = ROOT / "scripts/migration/history_business_usable_probe.py"

FORMAL_MENUS = {
    "smart_construction_core.menu_sc_arrival_confirmation": "sc.receipt.income",
    "smart_construction_core.menu_sc_legacy_fuel_card_fact_acceptance": "sc.fund.account.operation",
    "smart_construction_core.menu_sc_legacy_fuel_card_recharge_fact_acceptance": "sc.fund.account.operation",
    "smart_construction_core.menu_sc_company_user_roster_formal": "res.users",
    "smart_construction_core.menu_sc_material_rental_in_acceptance": "sc.material.rental.order",
    "smart_construction_core.menu_sc_material_rental_return_acceptance": "sc.material.rental.order",
    "smart_construction_core.menu_sc_self_funding_advance_income": "sc.self.funding.registration",
    "smart_construction_core.menu_sc_self_funding_advance_refund": "sc.self.funding.registration",
}

ACTION_XMLIDS = {
    "smart_construction_core.action_sc_receipt_income_arrival_confirmation": "sc.receipt.income",
    "smart_construction_core.action_sc_fuel_card_registration_formal": "sc.fund.account.operation",
    "smart_construction_core.action_sc_fuel_card_recharge_formal": "sc.fund.account.operation",
    "smart_construction_core.action_sc_company_user_roster_formal": "res.users",
    "smart_construction_core.action_sc_material_rental_in_acceptance": "sc.material.rental.order",
    "smart_construction_core.action_sc_material_rental_return_acceptance": "sc.material.rental.order",
    "smart_construction_core.action_sc_self_funding_registration_income": "sc.self.funding.registration",
    "smart_construction_core.action_sc_self_funding_registration_refund": "sc.self.funding.registration",
}


def iter_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_dicts(child)


def baseline_errors() -> list[str]:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    errors: list[str] = []
    seen = {key: 0 for key in FORMAL_MENUS}
    for item in iter_dicts(payload):
        xmlid = item.get("menu_xmlid") or item.get("menu_key") or item.get("page_key") or item.get("target_page_key")
        if xmlid not in FORMAL_MENUS:
            continue
        seen[xmlid] += 1
        expected = FORMAL_MENUS[xmlid]
        for field in ("res_model", "fact_model", "model"):
            value = item.get(field)
            if value and value != expected:
                errors.append(f"{xmlid} baseline {field}={value!r}, expected {expected!r}")
        action_xmlid = item.get("action_xmlid")
        if action_xmlid and ACTION_XMLIDS.get(action_xmlid) != expected:
            errors.append(f"{xmlid} baseline action_xmlid={action_xmlid!r} does not target {expected!r}")
    for xmlid, count in seen.items():
        if count == 0:
            errors.append(f"{xmlid} missing from formal product baseline")
    return errors


def xml_action_errors() -> list[str]:
    errors: list[str] = []
    for path in (MENU_XML, USER_XML):
        root = ET.fromstring(path.read_text(encoding="utf-8"))
        for record in root.findall(".//record"):
            action_id = record.attrib.get("id", "")
            full_xmlid = f"smart_construction_core.{action_id}" if action_id else ""
            if full_xmlid not in ACTION_XMLIDS:
                continue
            expected = ACTION_XMLIDS[full_xmlid]
            res_model = ""
            for field in record.findall("field"):
                if field.attrib.get("name") == "res_model":
                    res_model = (field.text or "").strip()
            if res_model != expected:
                errors.append(f"{full_xmlid} XML res_model={res_model!r}, expected {expected!r}")
    return errors


def probe_whitelist_errors() -> list[str]:
    text = PROBE.read_text(encoding="utf-8")
    errors = []
    for xmlid in FORMAL_MENUS:
        short = xmlid.split(".", 1)[1]
        if re.search(rf"['\"]smart_construction_core\.{re.escape(short)}['\"]", text):
            errors.append(f"{xmlid} must not be allowed as a legacy carrier whitelist entry")
    return errors


def main() -> int:
    errors = baseline_errors() + xml_action_errors() + probe_whitelist_errors()
    payload = {
        "guard": "formal_menu_no_legacy_carrier_guard",
        "checked_menu_count": len(FORMAL_MENUS),
        "errors": errors,
        "status": "FAIL" if errors else "PASS",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
