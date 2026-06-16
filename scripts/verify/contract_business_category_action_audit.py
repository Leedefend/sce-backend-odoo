#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGETS = [
    ROOT / "addons" / "smart_construction_core" / "views" / "core" / "contract_views.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "menu_business_taxonomy.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "support" / "user_confirmed_formal_list_views.xml",
]


CATEGORY_ACTIONS = {
    "contract.income": {
        "label": "收入合同",
        "model": "construction.contract.income",
        "action": "action_construction_contract_income",
        "context": {"default_type": "out", "default_business_category_code": "contract.income"},
        "domain_tokens": ["business_category_id.code", "contract.income"],
        "forbidden_domain_tokens": ["legacy_contract_id", "legacy_income_surface_visible"],
    },
    "contract.expense": {
        "label": "支出合同",
        "model": "construction.contract.expense",
        "action": "action_construction_contract_expense",
        "context": {"default_type": "in", "default_business_category_code": "contract.expense"},
        "domain_tokens": ["business_category_id.code", "contract.expense"],
    },
    "settlement.income": {
        "label": "收入合同结算",
        "model": "sc.settlement.order",
        "action": "action_sc_settlement_order_income",
        "context": {"default_settlement_type": "in", "default_business_category_code": "settlement.income"},
        "domain_tokens": ["business_category_id.code", "settlement.income"],
        "forbidden_domain_tokens": ["settlement_type", "legacy_fact_model", "legacy_fact_type"],
    },
    "settlement.expense": {
        "label": "支出合同结算",
        "model": "sc.settlement.order",
        "action": "action_sc_settlement_order_expense",
        "context": {"default_settlement_type": "out", "default_business_category_code": "settlement.expense"},
        "domain_tokens": ["business_category_id.code", "settlement.expense"],
        "forbidden_domain_tokens": ["settlement_type", "legacy_fact_model", "legacy_fact_type"],
    },
}


def _parse_context(raw: str) -> dict:
    try:
        value = ast.literal_eval(raw or "{}")
    except (SyntaxError, ValueError) as exc:
        raise AssertionError(f"invalid context literal: {raw!r}: {exc}") from exc
    if not isinstance(value, dict):
        raise AssertionError(f"context is not a dict: {raw!r}")
    return value


def _field_value(field: ET.Element) -> str:
    if "ref" in field.attrib:
        return field.attrib["ref"].strip()
    if "eval" in field.attrib:
        return field.attrib["eval"].strip()
    return (field.text or "").strip()


def _collect() -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for target in TARGETS:
        tree = ET.parse(target)
        for node in tree.getroot().findall(".//record"):
            if node.attrib.get("model") != "ir.actions.act_window":
                continue
            xmlid = node.attrib.get("id")
            if not xmlid:
                continue
            record = records.setdefault(xmlid, {})
            for field in node.findall("field"):
                name = field.attrib.get("name")
                if name:
                    record[name] = _field_value(field)
    return records


def main() -> int:
    records = _collect()
    failures: list[str] = []
    rows: list[dict] = []

    for code, expected in CATEGORY_ACTIONS.items():
        action_id = expected["action"]
        record = records.get(action_id)
        if record is None:
            failures.append(f"{code}: missing action {action_id}")
            continue
        name = record.get("name", "")
        model = record.get("res_model", "")
        context = _parse_context(record.get("context", "{}"))
        domain = record.get("domain", "")
        if expected["label"] and name and name != expected["label"]:
            failures.append(f"{code}: expected action name {expected['label']!r}, got {name!r}")
        if model and model != expected["model"]:
            failures.append(f"{code}: expected model {expected['model']!r}, got {model!r}")
        for key, value in expected["context"].items():
            if context.get(key) != value:
                failures.append(f"{code}: context[{key}] expected {value!r}, got {context.get(key)!r}")
        for token in expected["domain_tokens"]:
            if token not in domain:
                failures.append(f"{code}: domain missing token {token!r}")
        for token in expected.get("forbidden_domain_tokens", []):
            if token in domain:
                failures.append(f"{code}: domain still contains fallback token {token!r}")
        rows.append({"code": code, "action": action_id, "label": name, "model": model})

    result = {
        "audit": "contract_business_category_action_audit",
        "targets": [str(target.relative_to(ROOT)) for target in TARGETS],
        "status": "PASS" if not failures else "FAIL",
        "category_count": len(CATEGORY_ACTIONS),
        "rows": rows,
        "failures": failures,
    }
    print("CONTRACT_BUSINESS_CATEGORY_ACTION_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
