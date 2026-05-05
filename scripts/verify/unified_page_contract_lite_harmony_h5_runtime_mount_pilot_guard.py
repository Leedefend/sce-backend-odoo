#!/usr/bin/env python3
"""Guard the harmony_h5 Lite runtime mount pilot path."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "docs/architecture/unified_page_contract_lite/snapshots/project_tree_lite_adapter_snapshot_v1.json"
PAGE_INTEGRATION_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalPageIntegration.ts"
RUNTIME_MOUNT_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalRuntimeMount.ts"
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


def create_page_integration(contract: dict[str, Any]) -> dict[str, Any]:
    widgets = collect_widgets(contract)
    widget_ids = unique([str(widget["widgetId"]) for widget in widgets])
    action_ids = unique([str(action["actionId"]) for action in contract["actionContract"].get("actionRuleList") or []])
    node_count = len(widget_ids) + len(action_ids)
    return {
        "clientType": contract["pageInfo"]["clientType"],
        "pageId": contract["pageInfo"]["pageId"],
        "sceneKey": contract["pageInfo"]["sceneKey"],
        "model": contract["pageInfo"]["model"],
        "viewType": contract["pageInfo"]["viewType"],
        "contractVersion": contract["pageInfo"]["contractVersion"],
        "rootNodeId": f"root.{contract['pageInfo']['pageId']}",
        "mountedNodeCount": node_count,
        "ready": node_count > 0,
    }


def create_runtime_mount(page_integration: dict[str, Any]) -> dict[str, Any]:
    return {
        "clientType": page_integration["clientType"],
        "pageId": page_integration["pageId"],
        "sceneKey": page_integration["sceneKey"],
        "model": page_integration["model"],
        "viewType": page_integration["viewType"],
        "contractVersion": page_integration["contractVersion"],
        "rootNodeId": page_integration["rootNodeId"],
        "mountedNodeCount": page_integration["mountedNodeCount"],
        "status": "mounted",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    for path in (args.contract, PAGE_INTEGRATION_PATH, RUNTIME_MOUNT_PATH, MAKEFILE_PATH):
        if not path.exists():
            errors.append(f"missing file: {path}")

    contract = read_json(args.contract) if args.contract.exists() else {}
    harmony_contract = copy.deepcopy(contract)
    if harmony_contract:
        harmony_contract["pageInfo"]["clientType"] = "harmony_h5"
    page_integration = create_page_integration(harmony_contract) if harmony_contract else {}
    runtime_mount = create_runtime_mount(page_integration) if page_integration else {}

    if runtime_mount.get("clientType") != "harmony_h5":
        errors.append("runtime mount clientType must be harmony_h5")
    if runtime_mount.get("contractVersion") != "2.0.0":
        errors.append("runtime mount contractVersion must be 2.0.0")
    if runtime_mount.get("viewType") not in {"tree", "list"}:
        errors.append(f"harmony_h5 runtime mount pilot must use tree/list view, got {runtime_mount.get('viewType')!r}")
    if runtime_mount.get("rootNodeId") != "root.project.tree":
        errors.append(f"unexpected rootNodeId: {runtime_mount.get('rootNodeId')!r}")
    if runtime_mount.get("mountedNodeCount") != page_integration.get("mountedNodeCount"):
        errors.append("runtime mounted node count must match page integration mounted node count")
    if runtime_mount.get("status") != "mounted":
        errors.append("runtime mount status must be mounted")

    page_integration_text = read_text(PAGE_INTEGRATION_PATH) if PAGE_INTEGRATION_PATH.exists() else ""
    runtime_mount_text = read_text(RUNTIME_MOUNT_PATH) if RUNTIME_MOUNT_PATH.exists() else ""
    makefile = read_text(MAKEFILE_PATH) if MAKEFILE_PATH.exists() else ""
    for label, text in (("page_integration", page_integration_text), ("runtime_mount", runtime_mount_text)):
        found = sorted(token for token in FORBIDDEN_TOKENS if token in text)
        if found:
            errors.append(f"{label} contains forbidden semantic/runtime tokens: {found}")
    for token in (
        "createLiteTerminalPageIntegration",
        "createLiteTerminalRuntimeMount",
        "createLiteTerminalRuntimeMountSnapshot",
        "verify.unified_page_contract.lite.harmony_h5_runtime_mount_pilot.host",
    ):
        if token not in makefile + page_integration_text + runtime_mount_text:
            errors.append(f"missing runtime mount pilot token: {token}")

    report = {
        "ok": not errors,
        "clientType": "harmony_h5",
        "contract": str(args.contract.relative_to(ROOT)) if args.contract.is_absolute() else str(args.contract),
        "pageIntegration": page_integration,
        "runtimeMount": runtime_mount,
        "decision": "harmony_h5_runtime_mount_pilot_ready_compile_pending" if not errors else "blocked",
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite harmony_h5 runtime mount pilot failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite harmony_h5 runtime mount pilot passed")
    print("- decision: harmony_h5_runtime_mount_pilot_ready_compile_pending")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
