#!/usr/bin/env python3
"""Guard the pure backend Lite adapter skeleton."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "addons" / "smart_core" / "core" / "unified_page_contract_lite_adapter.py"
TOP_LEVEL = {"pageInfo", "layoutContract", "statusContract", "actionContract", "dataContract", "meta"}
FORBIDDEN_KEYS = {
    "runtimeContract",
    "componentRegistry",
    "capabilities",
    "dataSource",
    "dependencyGraph",
    "selectorStatus",
    "patchOperations",
    "hydration",
    "virtualization",
    "scheduler",
    "aiEnvelope",
    "script",
    "function",
    "eval",
    "expression",
    "jsonLogic",
    "workflowDsl",
    "loop",
    "stream",
    "subscription",
    "consistency",
    "actionType",
    "chainAction",
    "conditionBranch",
}
DRIFT_SUFFIX = re.compile(r"(\.|:|-)(admin|user|role|web_pc|wx_mini|harmony_h5|readonly|editable|hidden|visible)$")
ADAPTER_FORBIDDEN_TOKENS = (
    "BaseIntentHandler",
    "INTENT_TYPE",
    "request",
    "from odoo",
    "import odoo",
    "env[",
    ".sudo(",
    ".search(",
    ".write(",
    ".create(",
    ".unlink(",
)
ADAPTER_FORBIDDEN_SOURCE_ALIASES = (
    'source.get("head")',
    "source.get('head')",
    'source.get("meta")',
    "source.get('meta')",
    'source.get("model")',
    "source.get('model')",
    'source.get("view_type")',
    "source.get('view_type')",
    'source.get("values")',
    "source.get('values')",
    'source.get("mainData")',
    "source.get('mainData')",
    'source.get("relationData")',
    "source.get('relationData')",
    'source.get("dictData")',
    "source.get('dictData')",
    'source.get("options")',
    "source.get('options')",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_adapter():
    spec = importlib.util.spec_from_file_location("unified_page_contract_lite_adapter_guard_target", ADAPTER)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Lite adapter module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def walk(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def validate_contract(payload: dict[str, Any], errors: list[str]) -> None:
    if set(payload.keys()) != TOP_LEVEL:
        errors.append(f"Lite contract top-level mismatch: {sorted(payload.keys())}")
    if payload.get("pageInfo", {}).get("contractVersion") != "2.0.0":
        errors.append("Lite contractVersion must be 2.0.0")
    if set(payload.get("statusContract", {}).keys()) != {"widgetStatus", "buttonStatus"}:
        errors.append("statusContract must only contain widgetStatus/buttonStatus")
    if set(payload.get("dataContract", {}).keys()) != {"mainData", "relationData", "dictData"}:
        errors.append("dataContract must only contain mainData/relationData/dictData")
    for rule in payload.get("actionContract", {}).get("actionRuleList", []):
        if not isinstance(rule, dict):
            continue
        if rule.get("dispatchMode") != "server":
            errors.append(f"{rule.get('actionId')}: dispatchMode must be server")
    validate_stable_ids(payload, errors)


def validate_patch(payload: dict[str, Any], errors: list[str]) -> None:
    if payload.get("updateType") != "partial":
        errors.append("Lite patch updateType must be partial")
    if payload.get("operation") not in {"replace", "merge"}:
        errors.append("Lite patch operation must be replace or merge")
    if set(payload.keys()) != {"updateType", "operation", "statusPatch", "dataPatch", "layoutPatch"}:
        errors.append(f"Lite patch keys mismatch: {sorted(payload.keys())}")
    status_patch = payload.get("statusPatch")
    data_patch = payload.get("dataPatch")
    if not isinstance(status_patch, dict) or set(status_patch.keys()) != {"widgetStatus", "buttonStatus"}:
        errors.append("statusPatch must only contain widgetStatus/buttonStatus")
    if not isinstance(data_patch, dict) or set(data_patch.keys()) != {"mainData", "relationData", "dictData"}:
        errors.append("dataPatch must only contain mainData/relationData/dictData")
    validate_patch_layering(payload, errors)


def validate_forbidden(payload: Any, errors: list[str], source: str) -> None:
    for node_path, node in walk(payload):
        if not isinstance(node, dict):
            continue
        for key in node:
            if key in FORBIDDEN_KEYS:
                errors.append(f"{source}: forbidden key {key!r} at {node_path}")


def validate_stable_ids(payload: dict[str, Any], errors: list[str]) -> None:
    ids: list[tuple[str, Any]] = [
        ("pageInfo.pageId", payload.get("pageInfo", {}).get("pageId")),
        ("pageInfo.sceneKey", payload.get("pageInfo", {}).get("sceneKey")),
    ]
    for node_path, node in walk(payload.get("layoutContract", {})):
        if isinstance(node, dict):
            for key in ("containerId", "widgetId", "fieldCode"):
                if key in node:
                    ids.append((f"{node_path}.{key}", node.get(key)))
    for node_path, node in walk(payload.get("statusContract", {})):
        if isinstance(node, dict):
            for key in ("widgetId", "btnId"):
                if key in node:
                    ids.append((f"{node_path}.{key}", node.get(key)))
    for index, rule in enumerate(payload.get("actionContract", {}).get("actionRuleList", [])):
        if isinstance(rule, dict):
            ids.append((f"actionRuleList[{index}].actionId", rule.get("actionId")))
            ids.append((f"actionRuleList[{index}].sourceWidgetId", rule.get("sourceWidgetId")))
    seen: set[str] = set()
    for path, value in ids:
        text = str(value or "").strip()
        if not text:
            errors.append(f"{path} must not be empty")
            continue
        if DRIFT_SUFFIX.search(text):
            errors.append(f"{path} has role/client/status drift suffix: {text}")
        unique_key = f"{path}:{text}"
        if unique_key in seen:
            errors.append(f"{path} duplicated id binding: {text}")
        seen.add(unique_key)


def validate_patch_layering(payload: dict[str, Any], errors: list[str]) -> None:
    data_patch = payload.get("dataPatch") if isinstance(payload.get("dataPatch"), dict) else {}
    status_patch = payload.get("statusPatch") if isinstance(payload.get("statusPatch"), dict) else {}
    for node_path, node in walk(data_patch):
        if not isinstance(node, dict):
            continue
        for key in node:
            if key in {"widgetStatus", "buttonStatus", "readonly", "required", "invisible", "disabled", "modifiers_patch"}:
                errors.append(f"dataPatch must not carry status key {key!r} at {node_path}")
    for node_path, node in walk(status_patch):
        if not isinstance(node, dict):
            continue
        for key in node:
            if key in {"mainData", "relationData", "dictData", "patch", "linePatches"}:
                errors.append(f"statusPatch must not carry data key {key!r} at {node_path}")


def validate_adapter_is_side_effect_free(errors: list[str]) -> None:
    text = ADAPTER.read_text(encoding="utf-8")
    for token in ADAPTER_FORBIDDEN_TOKENS:
        if token in text:
            errors.append(f"adapter contains forbidden runtime/public-intent token: {token}")
    for token in ADAPTER_FORBIDDEN_SOURCE_ALIASES:
        if token in text:
            errors.append(f"adapter contains forbidden raw source alias token: {token}")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract-source", required=True, type=Path)
    parser.add_argument("--contract-snapshot", required=True, type=Path)
    parser.add_argument("--contract-case", nargs=2, action="append", metavar=("SOURCE", "SNAPSHOT"), default=[])
    parser.add_argument("--patch-source", required=True, type=Path)
    parser.add_argument("--patch-snapshot", required=True, type=Path)
    parser.add_argument("--patch-case", nargs=2, action="append", metavar=("SOURCE", "SNAPSHOT"), default=[])
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()

    errors: list[str] = []
    validate_adapter_is_side_effect_free(errors)
    adapter = load_adapter()

    contract_cases = [(args.contract_source, args.contract_snapshot)]
    contract_cases.extend((Path(source), Path(snapshot)) for source, snapshot in args.contract_case)
    actual_contracts = []
    for source_path, snapshot_path in contract_cases:
        contract_source = load_json(source_path)
        expected_contract = load_json(snapshot_path)
        actual_contract = adapter.build_lite_contract(contract_source, client_type="web_pc")
        actual_contracts.append((actual_contract, snapshot_path))
        if actual_contract != expected_contract:
            errors.append(f"generated Lite contract does not match snapshot: {snapshot_path}")
    patch_cases = [(args.patch_source, args.patch_snapshot)]
    patch_cases.extend((Path(source), Path(snapshot)) for source, snapshot in args.patch_case)
    actual_patches = []
    for source_path, snapshot_path in patch_cases:
        patch_source = load_json(source_path)
        expected_patch = load_json(snapshot_path)
        actual_patch = adapter.build_lite_patch(patch_source)
        actual_patches.append((actual_patch, snapshot_path))
        if actual_patch != expected_patch:
            errors.append(f"generated Lite patch does not match snapshot: {snapshot_path}")

    for actual_contract, _snapshot_path in actual_contracts:
        validate_contract(actual_contract, errors)
        validate_forbidden(actual_contract, errors, "contract")
    for actual_patch, _snapshot_path in actual_patches:
        validate_patch(actual_patch, errors)
        validate_forbidden(actual_patch, errors, "patch")
    view_types = sorted({
        str(contract.get("pageInfo", {}).get("viewType") or "")
        for contract, _snapshot_path in actual_contracts
    })
    if len(actual_contracts) < 3:
        errors.append("adapter guard requires at least 3 contract cases")
    for required_view_type in ("form", "tree", "search"):
        if required_view_type not in view_types:
            errors.append(f"adapter guard missing viewType coverage: {required_view_type}")
    coverage_report = {
        "ok": not errors,
        "contract_case_count": len(actual_contracts),
        "view_types": view_types,
        "patch_case_count": len(actual_patches),
        "patch_has_status": any(bool(patch.get("statusPatch", {}).get("widgetStatus")) for patch, _ in actual_patches),
        "patch_has_button_status": any(bool(patch.get("statusPatch", {}).get("buttonStatus")) for patch, _ in actual_patches),
        "patch_has_relation_status": any(
            any(".task_ids." in str(row.get("widgetId") or "") for row in patch.get("statusPatch", {}).get("widgetStatus", []))
            for patch, _ in actual_patches
        ),
        "patch_has_data": any(
            bool(patch.get("dataPatch", {}).get("mainData") or patch.get("dataPatch", {}).get("relationData"))
            for patch, _ in actual_patches
        ),
        "side_effect_free": not any("forbidden runtime/public-intent token" in error for error in errors),
        "snapshots": [str(snapshot_path) for _contract, snapshot_path in actual_contracts]
        + [str(snapshot_path) for _patch, snapshot_path in actual_patches],
    }
    if len(actual_patches) < 2:
        errors.append("adapter guard requires at least 2 patch cases")
    if not coverage_report["patch_has_button_status"]:
        errors.append("adapter guard missing buttonStatus patch coverage")
    if not coverage_report["patch_has_relation_status"]:
        errors.append("adapter guard missing relation row widgetStatus patch coverage")
    if args.report:
        write_report(args.report, coverage_report)

    if errors:
        print("Unified Semantic Page Contract Lite adapter guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Semantic Page Contract Lite adapter guard passed")
    for _actual_contract, snapshot_path in actual_contracts:
        print(f"- contract snapshot: {snapshot_path}")
    for _actual_patch, snapshot_path in actual_patches:
        print(f"- patch snapshot: {snapshot_path}")
    if args.report:
        print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
