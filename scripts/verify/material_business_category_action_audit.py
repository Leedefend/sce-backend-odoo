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
    ROOT / "addons" / "smart_construction_core" / "views" / "core" / "material_plan_views.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "core" / "material_acceptance_views.xml",
]


CATEGORY_ACTIONS = {
    "material.plan": {
        "label": "我的物资计划",
        "model": "project.material.plan",
        "action": "action_project_material_plan_my",
        "context": {"default_business_category_code": "material.plan"},
        "domain_tokens": ["business_category_id.code", "material.plan"],
    },
    "material.purchase.request": {
        "label": "采购申请",
        "model": "sc.material.purchase.request",
        "action": "action_sc_material_purchase_request",
        "context": {"default_business_category_code": "material.purchase.request"},
        "domain_tokens": ["business_category_id.code", "material.purchase.request"],
    },
    "material.acceptance": {
        "label": "材料进场验收",
        "model": "sc.material.acceptance",
        "action": "action_sc_material_acceptance",
        "context": {"default_business_category_code": "material.acceptance"},
        "domain_tokens": ["business_category_id.code", "material.acceptance"],
    },
    "material.rfq": {
        "label": "询比价",
        "model": "sc.material.rfq",
        "action": "action_sc_material_rfq",
        "context": {"default_business_category_code": "material.rfq"},
        "domain_tokens": ["business_category_id.code", "material.rfq"],
    },
    "material.inbound": {
        "label": "入库办理",
        "model": "sc.material.inbound",
        "action": "action_sc_material_inbound_handling",
        "context": {"default_business_category_code": "material.inbound"},
        "domain_tokens": ["business_category_id.code", "material.inbound"],
    },
    "material.outbound": {
        "label": "出库单",
        "model": "sc.material.outbound",
        "action": "action_sc_material_outbound",
        "context": {"default_outbound_type": "issue", "default_business_category_code": "material.outbound"},
        "domain_tokens": ["business_category_id.code", "material.outbound", "outbound_type", "issue"],
    },
    "material.return": {
        "label": "退库办理",
        "model": "sc.material.outbound",
        "action": "action_sc_material_return",
        "context": {"default_outbound_type": "return", "default_business_category_code": "material.return"},
        "domain_tokens": ["business_category_id.code", "material.return", "outbound_type", "return"],
    },
    "material.transfer": {
        "label": "材料调拨",
        "model": "sc.material.outbound",
        "action": "action_sc_material_transfer",
        "context": {"default_outbound_type": "transfer", "default_business_category_code": "material.transfer"},
        "domain_tokens": ["business_category_id.code", "material.transfer", "outbound_type", "transfer"],
    },
    "material.loss": {
        "label": "材料损耗",
        "model": "sc.material.outbound",
        "action": "action_sc_material_loss",
        "context": {"default_outbound_type": "loss", "default_business_category_code": "material.loss"},
        "domain_tokens": ["business_category_id.code", "material.loss", "outbound_type", "loss"],
    },
    "material.settlement": {
        "label": "材料结算",
        "model": "sc.material.settlement",
        "action": "action_sc_material_settlement",
        "context": {"default_business_category_code": "material.settlement"},
        "domain_tokens": ["business_category_id.code", "material.settlement"],
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
        rows.append({"code": code, "action": action_id, "label": name, "model": model})

    result = {
        "audit": "material_business_category_action_audit",
        "targets": [str(target.relative_to(ROOT)) for target in TARGETS],
        "status": "PASS" if not failures else "FAIL",
        "category_count": len(CATEGORY_ACTIONS),
        "rows": rows,
        "failures": failures,
    }
    print("MATERIAL_BUSINESS_CATEGORY_ACTION_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
