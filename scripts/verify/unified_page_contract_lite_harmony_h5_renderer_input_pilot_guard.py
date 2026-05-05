#!/usr/bin/env python3
"""Guard the harmony_h5 Lite renderer-input pilot path."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "docs/architecture/unified_page_contract_lite/snapshots/project_tree_lite_adapter_snapshot_v1.json"
STORE_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalStore.ts"
INPUT_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalRendererInput.ts"
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


def create_boundary(contract: dict[str, Any]) -> dict[str, Any]:
    widgets = collect_widgets(contract)
    return {
        "clientType": contract["pageInfo"]["clientType"],
        "pageId": contract["pageInfo"]["pageId"],
        "sceneKey": contract["pageInfo"]["sceneKey"],
        "model": contract["pageInfo"]["model"],
        "viewType": contract["pageInfo"]["viewType"],
        "contractVersion": contract["pageInfo"]["contractVersion"],
        "widgetIds": [str(widget["widgetId"]) for widget in widgets],
        "fieldCodes": [str(widget["fieldCode"]) for widget in widgets],
        "actionIds": [str(action["actionId"]) for action in contract["actionContract"].get("actionRuleList") or []],
    }


def create_renderer_input(boundary: dict[str, Any]) -> dict[str, Any]:
    widget_ids = unique(boundary["widgetIds"])
    field_codes = unique(boundary["fieldCodes"])
    action_ids = unique(boundary["actionIds"])
    return {
        "clientType": boundary["clientType"],
        "pageId": boundary["pageId"],
        "sceneKey": boundary["sceneKey"],
        "model": boundary["model"],
        "viewType": boundary["viewType"],
        "contractVersion": boundary["contractVersion"],
        "widgetIds": widget_ids,
        "fieldCodes": field_codes,
        "actionIds": action_ids,
        "widgetCount": len(widget_ids),
        "fieldCount": len(field_codes),
        "actionCount": len(action_ids),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    for path in (args.contract, STORE_PATH, INPUT_PATH, MAKEFILE_PATH):
        if not path.exists():
            errors.append(f"missing file: {path}")

    contract = read_json(args.contract) if args.contract.exists() else {}
    harmony_contract = copy.deepcopy(contract)
    if harmony_contract:
        harmony_contract["pageInfo"]["clientType"] = "harmony_h5"
    boundary = create_boundary(harmony_contract) if harmony_contract else {}
    renderer_input = create_renderer_input(boundary) if boundary else {}

    if renderer_input.get("clientType") != "harmony_h5":
        errors.append("renderer input clientType must be harmony_h5")
    if renderer_input.get("contractVersion") != "2.0.0":
        errors.append("renderer input contractVersion must be 2.0.0")
    if renderer_input.get("viewType") not in {"tree", "list"}:
        errors.append(f"harmony_h5 pilot must use tree/list view, got {renderer_input.get('viewType')!r}")
    if renderer_input.get("widgetCount", 0) < 1:
        errors.append("harmony_h5 renderer input must expose at least one widget")
    if renderer_input.get("fieldCount", 0) < 1:
        errors.append("harmony_h5 renderer input must expose at least one field")
    if renderer_input.get("actionCount", 0) < 1:
        errors.append("harmony_h5 renderer input must expose at least one action")

    store_text = read_text(STORE_PATH) if STORE_PATH.exists() else ""
    input_text = read_text(INPUT_PATH) if INPUT_PATH.exists() else ""
    makefile = read_text(MAKEFILE_PATH) if MAKEFILE_PATH.exists() else ""
    for label, text in (("store", store_text), ("renderer_input", input_text)):
        found = sorted(token for token in FORBIDDEN_TOKENS if token in text)
        if found:
            errors.append(f"{label} contains forbidden semantic/runtime tokens: {found}")
    for token in (
        "createLiteTerminalContractStore",
        "createLiteTerminalRendererInputSnapshot",
        "verify.unified_page_contract.lite.harmony_h5_renderer_input_pilot.host",
    ):
        if token not in makefile + store_text + input_text:
            errors.append(f"missing pilot token: {token}")

    report = {
        "ok": not errors,
        "clientType": "harmony_h5",
        "contract": str(args.contract.relative_to(ROOT)) if args.contract.is_absolute() else str(args.contract),
        "boundary": boundary,
        "rendererInput": renderer_input,
        "decision": "harmony_h5_renderer_input_ready_ui_renderer_pending" if not errors else "blocked",
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite harmony_h5 renderer input pilot failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite harmony_h5 renderer input pilot passed")
    print("- decision: harmony_h5_renderer_input_ready_ui_renderer_pending")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
