#!/usr/bin/env python3
"""Guard the wx_mini Lite page integration pilot path."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "docs/architecture/unified_page_contract_lite/snapshots/project_tree_lite_adapter_snapshot_v1.json"
RENDERER_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalRenderer.ts"
PAGE_INTEGRATION_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalPageIntegration.ts"
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


def create_renderer_output(contract: dict[str, Any]) -> dict[str, Any]:
    widgets = collect_widgets(contract)
    widget_ids = unique([str(widget["widgetId"]) for widget in widgets])
    action_ids = unique([str(action["actionId"]) for action in contract["actionContract"].get("actionRuleList") or []])
    field_nodes = [
        {"nodeId": f"node.{widget_id}", "kind": "field", "sourceId": widget_id, "order": index}
        for index, widget_id in enumerate(widget_ids)
    ]
    action_nodes = [
        {
            "nodeId": f"node.{action_id}",
            "kind": "action",
            "sourceId": action_id,
            "order": len(field_nodes) + index,
        }
        for index, action_id in enumerate(action_ids)
    ]
    nodes = field_nodes + action_nodes
    return {
        "clientType": contract["pageInfo"]["clientType"],
        "pageId": contract["pageInfo"]["pageId"],
        "sceneKey": contract["pageInfo"]["sceneKey"],
        "model": contract["pageInfo"]["model"],
        "viewType": contract["pageInfo"]["viewType"],
        "contractVersion": contract["pageInfo"]["contractVersion"],
        "nodes": nodes,
        "nodeCount": len(nodes),
        "fieldNodeCount": len(field_nodes),
        "actionNodeCount": len(action_nodes),
    }


def create_page_integration(renderer_output: dict[str, Any]) -> dict[str, Any]:
    return {
        "clientType": renderer_output["clientType"],
        "pageId": renderer_output["pageId"],
        "sceneKey": renderer_output["sceneKey"],
        "model": renderer_output["model"],
        "viewType": renderer_output["viewType"],
        "contractVersion": renderer_output["contractVersion"],
        "rootNodeId": f"root.{renderer_output['pageId']}",
        "mountedNodes": renderer_output["nodes"],
        "mountedNodeCount": renderer_output["nodeCount"],
        "ready": renderer_output["nodeCount"] > 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    for path in (args.contract, RENDERER_PATH, PAGE_INTEGRATION_PATH, MAKEFILE_PATH):
        if not path.exists():
            errors.append(f"missing file: {path}")

    contract = read_json(args.contract) if args.contract.exists() else {}
    wx_contract = copy.deepcopy(contract)
    if wx_contract:
        wx_contract["pageInfo"]["clientType"] = "wx_mini"
    renderer_output = create_renderer_output(wx_contract) if wx_contract else {}
    page_integration = create_page_integration(renderer_output) if renderer_output else {}

    if page_integration.get("clientType") != "wx_mini":
        errors.append("page integration clientType must be wx_mini")
    if page_integration.get("contractVersion") != "2.0.0":
        errors.append("page integration contractVersion must be 2.0.0")
    if page_integration.get("viewType") not in {"tree", "list"}:
        errors.append(f"wx_mini page integration pilot must use tree/list view, got {page_integration.get('viewType')!r}")
    if page_integration.get("rootNodeId") != "root.project.tree":
        errors.append(f"unexpected rootNodeId: {page_integration.get('rootNodeId')!r}")
    if page_integration.get("mountedNodeCount") != renderer_output.get("nodeCount"):
        errors.append("mounted node count must match renderer output node count")
    if page_integration.get("ready") is not True:
        errors.append("page integration must be ready")

    renderer_text = read_text(RENDERER_PATH) if RENDERER_PATH.exists() else ""
    page_integration_text = read_text(PAGE_INTEGRATION_PATH) if PAGE_INTEGRATION_PATH.exists() else ""
    makefile = read_text(MAKEFILE_PATH) if MAKEFILE_PATH.exists() else ""
    for label, text in (("renderer", renderer_text), ("page_integration", page_integration_text)):
        found = sorted(token for token in FORBIDDEN_TOKENS if token in text)
        if found:
            errors.append(f"{label} contains forbidden semantic/runtime tokens: {found}")
    for token in (
        "createLiteTerminalRendererOutput",
        "createLiteTerminalPageIntegration",
        "createLiteTerminalPageIntegrationSnapshot",
        "verify.unified_page_contract.lite.wx_mini_page_integration_pilot.host",
    ):
        if token not in makefile + renderer_text + page_integration_text:
            errors.append(f"missing page integration pilot token: {token}")

    report = {
        "ok": not errors,
        "clientType": "wx_mini",
        "contract": str(args.contract.relative_to(ROOT)) if args.contract.is_absolute() else str(args.contract),
        "rendererOutput": renderer_output,
        "pageIntegration": page_integration,
        "decision": "wx_mini_page_integration_pilot_ready_runtime_mount_pending" if not errors else "blocked",
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite wx_mini page integration pilot failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite wx_mini page integration pilot passed")
    print("- decision: wx_mini_page_integration_pilot_ready_runtime_mount_pending")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
