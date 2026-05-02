#!/usr/bin/env python3
"""Guard the frozen Lite v2.0 frontend consumption contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


TOP_LEVEL = {"pageInfo", "layoutContract", "statusContract", "actionContract", "dataContract", "meta"}
FORBIDDEN_KEYS = {
    "runtimeContract",
    "componentRegistry",
    "capabilities",
    "selectorStatus",
    "dependencyGraph",
    "dataSource",
    "subscription",
    "stream",
    "hydration",
    "scheduler",
    "aiEnvelope",
    "workflowDsl",
    "jsonLogic",
    "script",
    "function",
    "eval",
    "expression",
}

REQUIRED_DOC_TOKENS = (
    "frozen for frontend pilot implementation",
    "unified_page_contract_lite_v2_0_frontend_consumption_frozen",
    "This batch does not modify frontend implementation.",
    "contractVersion = 2.0.0",
    "pageInfo",
    "layoutContract",
    "statusContract",
    "actionContract",
    "dataContract",
    "meta",
    "dispatchMode = server",
    "merge",
    "replace",
    "load_contract opt-in preview",
    "project.project:tree",
    "schema/types -> store/adapter -> page renderer",
    "runtimeContract",
    "componentRegistry",
    "selectorStatus",
    "dependencyGraph",
    "make verify.unified_page_contract.lite.contract_freeze_v2_0",
    "make verify.unified_page_contract.lite.frontend_pilot_readiness",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def walk(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def missing_tokens(text: str, tokens: tuple[str, ...]) -> list[str]:
    return [token for token in tokens if token not in text]


def schema_ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-doc", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--example", required=True, type=Path)
    parser.add_argument("--patch", required=True, type=Path)
    parser.add_argument("--makefile", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []

    freeze_text = args.freeze_doc.read_text(encoding="utf-8")
    missing_doc_tokens = missing_tokens(freeze_text, REQUIRED_DOC_TOKENS)
    if missing_doc_tokens:
        errors.append(f"freeze doc missing required tokens: {missing_doc_tokens}")

    makefile_text = args.makefile.read_text(encoding="utf-8")
    for target in (
        "verify.unified_page_contract.lite.contract_freeze_v2_0",
        "verify.unified_page_contract.lite.frontend_pilot_readiness",
        "verify.unified_page_contract.lite",
    ):
        if target not in makefile_text:
            errors.append(f"Makefile missing target token: {target}")

    schema = load_json(args.schema)
    example = load_json(args.example)
    patch = load_json(args.patch)

    if set(schema.get("required") or []) != TOP_LEVEL:
        errors.append("schema top-level required keys must match frozen Lite v2.0 shape")
    if set(schema.get("properties") or {}) != TOP_LEVEL:
        errors.append("schema top-level properties must match frozen Lite v2.0 shape")
    if schema.get("additionalProperties") is not False:
        errors.append("schema top-level must forbid additionalProperties")

    defs = schema.get("$defs", {})
    page_info = defs.get("pageInfo", {})
    if page_info.get("properties", {}).get("contractVersion", {}).get("const") != "2.0.0":
        errors.append("pageInfo.contractVersion must be const 2.0.0")

    required_defs = {
        "pageInfo",
        "layoutContract",
        "container",
        "widget",
        "statusContract",
        "widgetStatus",
        "buttonStatus",
        "actionContract",
        "actionRule",
        "dataContract",
        "meta",
    }
    missing_defs = sorted(required_defs - set(defs))
    if missing_defs:
        errors.append(f"schema missing frozen defs: {missing_defs}")

    for name in required_defs:
        node = defs.get(name, {})
        if isinstance(node, dict) and node.get("additionalProperties") is not False:
            errors.append(f"schema def {name} must forbid additionalProperties")

    status_contract = defs.get("statusContract", {})
    if set(status_contract.get("properties") or {}) != {"widgetStatus", "buttonStatus"}:
        errors.append("statusContract must only expose widgetStatus/buttonStatus")

    data_contract = defs.get("dataContract", {})
    if set(data_contract.get("properties") or {}) != {"mainData", "relationData", "dictData"}:
        errors.append("dataContract must only expose mainData/relationData/dictData")

    action_rule = defs.get("actionRule", {})
    dispatch_mode = action_rule.get("properties", {}).get("dispatchMode", {})
    if dispatch_mode.get("enum") != ["server"]:
        errors.append("actionRule.dispatchMode must be server-only")

    if set(example) != TOP_LEVEL:
        errors.append("example top-level keys must match frozen Lite v2.0 shape")
    if example.get("pageInfo", {}).get("contractVersion") != "2.0.0":
        errors.append("example pageInfo.contractVersion must be 2.0.0")
    for rule in example.get("actionContract", {}).get("actionRuleList", []):
        if rule.get("dispatchMode") != "server":
            errors.append(f"example action {rule.get('actionId')} must use server dispatch")

    if patch.get("updateType") != "partial":
        errors.append("patch updateType must be partial")
    if patch.get("operation") not in {"merge", "replace"}:
        errors.append("patch operation must be merge or replace")
    if not {"statusPatch", "dataPatch", "layoutPatch"}.issubset(patch):
        errors.append("patch must contain statusPatch/dataPatch/layoutPatch")

    for source_name, payload in (("schema", schema), ("example", example), ("patch", patch)):
        for node_path, node in walk(payload):
            if not isinstance(node, dict):
                continue
            for key in node:
                if key in FORBIDDEN_KEYS:
                    errors.append(f"{source_name}: forbidden key {key!r} at {node_path}")

    report = {
        "ok": not errors,
        "decision": "unified_page_contract_lite_v2_0_frontend_consumption_frozen" if not errors else "blocked",
        "contract_version": "2.0.0",
        "top_level": sorted(TOP_LEVEL),
        "patch_operations": ["merge", "replace"],
        "frontend_implementation_modified": False,
        "missing_doc_tokens": missing_doc_tokens,
        "errors": errors,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if errors:
        print("Unified Semantic Page Contract Lite v2.0 freeze guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite v2.0 freeze guard passed")
    print("- decision: unified_page_contract_lite_v2_0_frontend_consumption_frozen")
    print("- contractVersion: 2.0.0")
    print("- frontend implementation modified: false")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
