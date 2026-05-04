#!/usr/bin/env python3
"""Guard the platform-level Unified Page Contract v2 intent."""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLER_PATH = ROOT / "addons/smart_core/handlers/ui_contract_v2.py"
ASSEMBLER_PATH = ROOT / "addons/smart_core/core/unified_page_contract_v2_assembler.py"
CLIENT_PATH = ROOT / "addons/smart_core/core/unified_page_contract_v2_client.py"
FORBIDDEN_INDUSTRY_PATH = ROOT / "addons/smart_construction_core/handlers/mobile_contract.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _literal_assignments(tree: ast.AST) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            out[node.targets[0].id] = node.value.value
    return out


def main() -> int:
    errors: list[str] = []
    if not HANDLER_PATH.exists():
        _fail(errors, "smart_core must expose ui_contract_v2 handler")
    if FORBIDDEN_INDUSTRY_PATH.exists():
        _fail(errors, "mobile contract protocol must not live in smart_construction_core")

    source = HANDLER_PATH.read_text(encoding="utf-8") if HANDLER_PATH.exists() else ""
    tree = ast.parse(source or "\n")
    assignments = _literal_assignments(tree)
    if assignments.get("INTENT_TYPE") != "ui.contract.v2":
        _fail(errors, "handler INTENT_TYPE must be ui.contract.v2")
    if "UiContractHandler" not in source:
        _fail(errors, "v2 intent must use ui.contract as source authority")
    if "assemble_unified_page_contract_v2" not in source:
        _fail(errors, "v2 intent must assemble Unified Page Contract v2")
    if "trim_unified_page_contract_v2" not in source:
        _fail(errors, "v2 intent must apply terminal client trimming")
    if "resolve_delivery_profile" not in source:
        _fail(errors, "v2 intent must resolve terminal delivery profile")
    if "include_source_compat=client_type not in MOBILE_CLIENT_TYPES" not in source:
        _fail(errors, "mobile compact delivery must not expose full source compat payload")
    for forbidden in ("mobile_contract", "mobileContract", "deviceContract", "construction.contract.mobile"):
        if forbidden in source:
            _fail(errors, f"handler must not introduce mobile private schema: {forbidden}")

    assembler = _load(ASSEMBLER_PATH, "upc_v2_intent_guard_assembler")
    client = _load(CLIENT_PATH, "upc_v2_intent_guard_client")
    sample = {
        "ui_contract": {
            "title": "契约运行",
            "model": "construction.contract",
            "view_type": "tree",
            "fields": {
                "name": {"string": "名称", "type": "char"},
                "partner_id": {"string": "供应商", "type": "many2one"},
            },
            "buttons": [{"name": "action_confirm", "string": "确认", "type": "object"}],
        },
        "model": "construction.contract",
        "view_type": "tree",
        "domain_raw": "[('state','=','draft')]",
        "context_raw": "{'search_default_my': 1}",
    }
    contract = assembler.assemble_unified_page_contract_v2(sample, source_type="ui.contract", client_type="harmony_h5")
    contract = client.trim_unified_page_contract_v2(
        contract,
        client_type="harmony_h5",
        delivery_profile="mobile_compact",
        max_widgets=1,
        max_actions=1,
        include_source_compat=False,
    )
    expected_keys = {
        "pageInfo",
        "layoutContract",
        "statusContract",
        "actionContract",
        "dataContract",
        "runtimeContract",
        "meta",
    }
    if set(contract.keys()) != expected_keys:
        _fail(errors, "v2 contract top-level keys drifted")
    if contract.get("pageInfo", {}).get("contractVersion") != "2.1.0":
        _fail(errors, "v2 contract version must stay 2.1.0")
    if contract.get("pageInfo", {}).get("clientType") != "harmony_h5":
        _fail(errors, "harmony_h5 client type must survive v2 assembly and trimming")
    if contract.get("layoutContract", {}).get("adaptMode") != "mobile":
        _fail(errors, "harmony_h5 must use mobile adapt mode")
    primary_source = (((contract.get("dataContract") or {}).get("dataSource") or {}).get("primary") or {})
    if primary_source.get("intent") != "api.data":
        _fail(errors, "list/tree v2 contracts must declare primary api.data dataSource")
    primary_params = primary_source.get("params") if isinstance(primary_source.get("params"), dict) else {}
    if primary_params.get("model") != "construction.contract":
        _fail(errors, "primary dataSource must carry model from contract source")
    if "fields" not in primary_params:
        _fail(errors, "primary dataSource must carry explicit fields")
    if primary_params.get("domain_raw") != "[('state','=','draft')]":
        _fail(errors, "primary dataSource must inherit domain_raw from v2 source")
    if primary_params.get("context_raw") != "{'search_default_my': 1}":
        _fail(errors, "primary dataSource must inherit context_raw from v2 source")
    actions = (contract.get("actionContract", {}) or {}).get("actionRuleList") or []
    if not actions or actions[0].get("label") != "确认" or actions[0].get("intent") != "execute_button":
        _fail(errors, "v2 action rules must carry renderable label and intent from source contract")
    if (actions[0].get("button") or {}).get("name") != "action_confirm":
        _fail(errors, "v2 execute_button action rules must carry original button name")
    widgets = ((contract.get("layoutContract", {}).get("containerTree") or [{}])[0].get("widgetList") or [])
    if len(widgets) != 1:
        _fail(errors, "mobile_compact must trim delivered widgets")
    compat = contract.get("meta", {}).get("compat") or {}
    if compat.get("ui_contract", {}).get("delivery") != "omitted_for_mobile_compact":
        _fail(errors, "mobile_compact must replace full ui_contract compat with source fingerprint")
    delivery_trim = contract.get("meta", {}).get("deliveryTrim") or {}
    if delivery_trim.get("omitted", {}).get("widgets", 0) < 1:
        _fail(errors, "mobile_compact must report omitted widgets")

    form_sample = {
        "ui_contract": {
            "title": "合同表单",
            "model": "construction.contract",
            "view_type": "form",
            "fields": {
                "name": {"string": "名称", "type": "char"},
                "amount_final": {"string": "金额", "type": "monetary"},
            },
        },
        "model": "construction.contract",
        "view_type": "form",
        "record_id": 42,
    }
    form_contract = assembler.assemble_unified_page_contract_v2(form_sample, source_type="ui.contract", client_type="harmony_h5")
    form_primary = (((form_contract.get("dataContract") or {}).get("dataSource") or {}).get("primary") or {})
    form_params = form_primary.get("params") if isinstance(form_primary.get("params"), dict) else {}
    if form_params.get("op") != "read" or form_params.get("ids") != [42]:
        _fail(errors, "form v2 contracts with record_id must declare primary api.data read dataSource")
    action_sample = {
        "ui_contract": {
            "title": "合同表单",
            "model": "construction.contract",
            "view_type": "form",
            "fields": {"name": {"string": "名称", "type": "char"}},
            "buttons": [
                {
                    "key": "module.action_contract",
                    "kind": "open",
                    "label": "打开合同",
                    "intent": "open",
                    "payload": {"action_id": 99, "view_mode": "tree,form"},
                    "target_model": "construction.contract",
                },
                {
                    "key": "module.server_action_contract",
                    "kind": "server",
                    "label": "服务端动作",
                    "intent": "execute",
                    "payload": {"server_action_id": 77, "xml_id": "module.server_action_contract"},
                },
            ],
        },
        "model": "construction.contract",
        "view_type": "form",
        "record_id": 42,
    }
    action_contract = assembler.assemble_unified_page_contract_v2(action_sample, source_type="ui.contract", client_type="harmony_h5")
    action_rules = (action_contract.get("actionContract") or {}).get("actionRuleList") or []
    open_rule = next((row for row in action_rules if row.get("label") == "打开合同"), {})
    server_rule = next((row for row in action_rules if row.get("label") == "服务端动作"), {})
    if open_rule.get("intent") != "ui.contract" or (open_rule.get("target") or {}).get("action_id") != 99:
        _fail(errors, "v2 open actions must become ui.contract targets")
    if (server_rule.get("button") or {}).get("type") != "server_action" or (server_rule.get("button") or {}).get("server_action_id") != 77:
        _fail(errors, "v2 server actions must preserve server_action button metadata")

    if errors:
        print("Unified Page Contract v2 intent guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Unified Page Contract v2 intent guard passed: platform ui.contract.v2 is the only terminal entry")
    return 0


if __name__ == "__main__":
    sys.exit(main())
