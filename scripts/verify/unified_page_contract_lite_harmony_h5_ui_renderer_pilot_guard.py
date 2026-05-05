#!/usr/bin/env python3
"""Guard the harmony_h5 Lite UI renderer pilot path."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "docs/architecture/unified_page_contract_lite/snapshots/project_tree_lite_adapter_snapshot_v1.json"
INPUT_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalRendererInput.ts"
RENDERER_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalRenderer.ts"
MAKEFILE_PATH = ROOT / "Makefile"

FORBIDDEN_TOKENS = (
    "role_code",
    "roleSurface",
    "default_route",
    "permissions",
    "permission",
    "groups",
    "capability",
    "router",
    "fetch(",
    "axios",
    "jsonrpc",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def iter_containers(containers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for container in containers:
        found.append(container)
        found.extend(iter_containers(container.get("children") or []))
    return found


def collect_widgets(contract: dict[str, Any]) -> list[dict[str, Any]]:
    widgets: list[dict[str, Any]] = []
    for container in iter_containers(contract["layoutContract"].get("containerList") or []):
        widgets.extend(container.get("widgetList") or [])
    return widgets


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value.strip()))


def create_renderer_input(contract: dict[str, Any]) -> dict[str, Any]:
    widgets = collect_widgets(contract)
    widget_ids = unique([str(widget["widgetId"]) for widget in widgets])
    field_codes = unique([str(widget["fieldCode"]) for widget in widgets])
    action_ids = unique([str(action["actionId"]) for action in contract["actionContract"].get("actionRuleList") or []])
    return {
        "clientType": contract["pageInfo"]["clientType"],
        "pageId": contract["pageInfo"]["pageId"],
        "sceneKey": contract["pageInfo"]["sceneKey"],
        "model": contract["pageInfo"]["model"],
        "viewType": contract["pageInfo"]["viewType"],
        "contractVersion": contract["pageInfo"]["contractVersion"],
        "widgetIds": widget_ids,
        "fieldCodes": field_codes,
        "actionIds": action_ids,
        "widgetCount": len(widget_ids),
        "fieldCount": len(field_codes),
        "actionCount": len(action_ids),
    }


def create_renderer_output(renderer_input: dict[str, Any]) -> dict[str, Any]:
    field_nodes = [
        {"nodeId": f"node.{widget_id}", "kind": "field", "sourceId": widget_id, "order": index}
        for index, widget_id in enumerate(renderer_input["widgetIds"])
    ]
    action_nodes = [
        {
            "nodeId": f"node.{action_id}",
            "kind": "action",
            "sourceId": action_id,
            "order": len(field_nodes) + index,
        }
        for index, action_id in enumerate(renderer_input["actionIds"])
    ]
    nodes = field_nodes + action_nodes
    return {
        "clientType": renderer_input["clientType"],
        "pageId": renderer_input["pageId"],
        "sceneKey": renderer_input["sceneKey"],
        "model": renderer_input["model"],
        "viewType": renderer_input["viewType"],
        "contractVersion": renderer_input["contractVersion"],
        "nodes": nodes,
        "nodeCount": len(nodes),
        "fieldNodeCount": len(field_nodes),
        "actionNodeCount": len(action_nodes),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    for path in (args.contract, INPUT_PATH, RENDERER_PATH, MAKEFILE_PATH):
        if not path.exists():
            errors.append(f"missing file: {path}")

    contract = read_json(args.contract) if args.contract.exists() else {}
    harmony_contract = copy.deepcopy(contract)
    if harmony_contract:
        harmony_contract["pageInfo"]["clientType"] = "harmony_h5"
    renderer_input = create_renderer_input(harmony_contract) if harmony_contract else {}
    renderer_output = create_renderer_output(renderer_input) if renderer_input else {}

    if renderer_output.get("clientType") != "harmony_h5":
        errors.append("renderer output clientType must be harmony_h5")
    if renderer_output.get("contractVersion") != "2.0.0":
        errors.append("renderer output contractVersion must be 2.0.0")
    if renderer_output.get("viewType") not in {"tree", "list"}:
        errors.append(f"harmony_h5 UI renderer pilot must use tree/list view, got {renderer_output.get('viewType')!r}")
    if renderer_output.get("fieldNodeCount") != renderer_input.get("widgetCount"):
        errors.append("field node count must match renderer input widget count")
    if renderer_output.get("actionNodeCount") != renderer_input.get("actionCount"):
        errors.append("action node count must match renderer input action count")
    if renderer_output.get("nodeCount") != renderer_input.get("widgetCount", 0) + renderer_input.get("actionCount", 0):
        errors.append("node count must equal field nodes plus action nodes")

    input_text = read_text(INPUT_PATH) if INPUT_PATH.exists() else ""
    renderer_text = read_text(RENDERER_PATH) if RENDERER_PATH.exists() else ""
    makefile = read_text(MAKEFILE_PATH) if MAKEFILE_PATH.exists() else ""
    for label, text in (("renderer_input", input_text), ("renderer", renderer_text)):
        found = sorted(token for token in FORBIDDEN_TOKENS if token in text)
        if found:
            errors.append(f"{label} contains forbidden semantic/runtime tokens: {found}")
    for token in (
        "createLiteTerminalRendererInput",
        "createLiteTerminalRendererOutput",
        "createLiteTerminalRendererOutputSnapshot",
        "verify.unified_page_contract.lite.harmony_h5_ui_renderer_pilot.host",
    ):
        if token not in makefile + input_text + renderer_text:
            errors.append(f"missing UI renderer pilot token: {token}")

    report = {
        "ok": not errors,
        "clientType": "harmony_h5",
        "contract": str(args.contract.relative_to(ROOT)) if args.contract.is_absolute() else str(args.contract),
        "rendererInput": renderer_input,
        "rendererOutput": renderer_output,
        "decision": "harmony_h5_ui_renderer_pilot_ready_page_integration_pending" if not errors else "blocked",
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite harmony_h5 UI renderer pilot failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite harmony_h5 UI renderer pilot passed")
    print("- decision: harmony_h5_ui_renderer_pilot_ready_page_integration_pending")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
