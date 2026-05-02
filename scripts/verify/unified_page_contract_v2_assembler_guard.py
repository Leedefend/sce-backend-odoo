#!/usr/bin/env python3
"""Guard the v2+ backend assembler without requiring an Odoo runtime."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ASSEMBLER_PATH = ROOT / "addons/smart_core/core/unified_page_contract_v2_assembler.py"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_assembler():
    spec = importlib.util.spec_from_file_location("unified_page_contract_v2_assembler_guard_target", ASSEMBLER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load assembler from {ASSEMBLER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def walk(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def validate_contract(
    payload: dict[str, Any],
    *,
    expected_compat_key: str,
    snapshot: dict[str, Any],
    errors: list[str],
) -> None:
    required = {
        "pageInfo",
        "layoutContract",
        "statusContract",
        "actionContract",
        "dataContract",
        "runtimeContract",
        "meta",
    }
    if set(payload.keys()) != required:
        fail(errors, f"contract top-level mismatch: {sorted(payload.keys())}")
    if payload.get("pageInfo", {}).get("contractVersion") != "2.1.0":
        fail(errors, "contractVersion must be 2.1.0")
    compat = payload.get("meta", {}).get("compat")
    if not isinstance(compat, dict) or expected_compat_key not in compat:
        fail(errors, f"meta.compat must contain {expected_compat_key}")
    container_count = len(payload.get("layoutContract", {}).get("containerTree") or [])
    widget_status_count = len(payload.get("statusContract", {}).get("widgetStatus") or [])
    action_count = len(payload.get("actionContract", {}).get("actionRuleList") or [])
    if container_count < int(snapshot.get("minContainerCount") or 0):
        fail(errors, f"{expected_compat_key}: container snapshot below baseline")
    if widget_status_count < int(snapshot.get("minWidgetStatusCount") or 0):
        fail(errors, f"{expected_compat_key}: widget status snapshot below baseline")
    if action_count < int(snapshot.get("minActionCount") or 0):
        fail(errors, f"{expected_compat_key}: action snapshot below baseline")
    for legacy_key in ("scene_contract_v1", "page_orchestration_v1", "ui_contract", "api_onchange"):
        if legacy_key in payload and legacy_key != expected_compat_key:
            fail(errors, f"legacy key leaked at top-level: {legacy_key}")
    for node_path, node in walk(payload):
        if isinstance(node, dict):
            for key in node:
                if str(key).lower() in {"script", "function", "eval", "jsonlogic", "workflowdsl", "frontendprivate"}:
                    fail(errors, f"forbidden executable/private key {key!r} at {node_path}")


def validate_patch(payload: dict[str, Any], snapshot: dict[str, Any], errors: list[str]) -> None:
    if payload.get("updateType") != "partial":
        fail(errors, "patch updateType must be partial")
    if snapshot.get("updateType") and payload.get("updateType") != snapshot.get("updateType"):
        fail(errors, "patch updateType does not match snapshot")
    for key in ("layoutPatch", "statusPatch", "dataPatch", "runtimePatch", "meta"):
        if key not in payload:
            fail(errors, f"patch missing {key}")
    meta = payload.get("meta", {})
    if meta.get("contractVersion") != "2.1.0":
        fail(errors, "patch contractVersion must be 2.1.0")
    compat = meta.get("compat")
    if not isinstance(compat, dict) or "api_onchange" not in compat:
        fail(errors, "patch meta.compat.api_onchange is required")
    if "api_onchange" in payload:
        fail(errors, "api_onchange leaked at patch top-level")
    if len(payload.get("dataPatch") or {}) < int(snapshot.get("minDataPatchKeys") or 0):
        fail(errors, "patch dataPatch snapshot below baseline")
    widget_status = payload.get("statusPatch", {}).get("widgetStatus") or []
    if len(widget_status) < int(snapshot.get("minWidgetStatusCount") or 0):
        fail(errors, "patch widgetStatus snapshot below baseline")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    args = parser.parse_args()
    target = load_assembler()
    errors: list[str] = []
    snapshot = load_json(args.snapshot)
    source_snapshots = snapshot.get("sources") if isinstance(snapshot.get("sources"), dict) else {}

    scene_source = load_json(args.fixtures / "scene_contract_v1_source.json")
    page_source = load_json(args.fixtures / "page_orchestration_v1_source.json")
    ui_source = load_json(args.fixtures / "ui_contract_source.json")
    onchange_source = load_json(args.fixtures / "api_onchange_source.json")

    scene_contract = target.assemble_unified_page_contract_v2(scene_source, source_type="scene_contract_v1")
    page_contract = target.assemble_unified_page_contract_v2(page_source, source_type="page_orchestration_v1")
    ui_contract = target.assemble_unified_page_contract_v2(ui_source, source_type="ui.contract")
    onchange_patch = target.assemble_unified_page_patch_v2(onchange_source, action_id="project.name.change")

    validate_contract(
        scene_contract,
        expected_compat_key="scene_contract_v1",
        snapshot=source_snapshots.get("scene_contract_v1") or {},
        errors=errors,
    )
    validate_contract(
        page_contract,
        expected_compat_key="page_orchestration_v1",
        snapshot=source_snapshots.get("page_orchestration_v1") or {},
        errors=errors,
    )
    validate_contract(
        ui_contract,
        expected_compat_key="ui_contract",
        snapshot=source_snapshots.get("ui_contract") or {},
        errors=errors,
    )
    validate_patch(onchange_patch, source_snapshots.get("api_onchange") or {}, errors)

    if not scene_contract.get("layoutContract", {}).get("containerTree"):
        fail(errors, "scene_contract_v1 mapping must produce containerTree")
    if not page_contract.get("actionContract", {}).get("actionRuleList"):
        fail(errors, "page_orchestration_v1 mapping must produce actionRuleList")
    if not ui_contract.get("statusContract", {}).get("widgetStatus"):
        fail(errors, "ui.contract mapping must produce widgetStatus")
    if not onchange_patch.get("dataPatch"):
        fail(errors, "api.onchange mapping must produce dataPatch")

    if errors:
        print("Unified Page Contract v2+ assembler guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Unified Page Contract v2+ assembler guard passed: sources=4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
