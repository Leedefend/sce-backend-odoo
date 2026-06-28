#!/usr/bin/env python3
"""Guard the v2+ backend assembler without requiring an Odoo runtime."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import types
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CORE_DIR = ROOT / "addons/smart_core/core"
ASSEMBLER_PATH = ROOT / "addons/smart_core/core/unified_page_contract_v2_assembler.py"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_assembler():
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    core_pkg.__path__ = [str(CORE_DIR)]
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.core.unified_page_contract_v2_assembler_guard_target",
        ASSEMBLER_PATH,
    )
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


def registry_path(value: dict[str, Any], path: tuple[str, ...]) -> Any:
    node: Any = value
    for item in path:
        if not isinstance(node, dict):
            return None
        node = node.get(item)
    return node


def validate_contract(
    payload: dict[str, Any],
    *,
    expected_source_type: str,
    snapshot: dict[str, Any],
    registry: dict[str, Any],
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
    optional = {"formStructureContract"}
    payload_keys = set(payload.keys())
    if not required <= payload_keys or payload_keys - required - optional:
        fail(errors, f"contract top-level mismatch: {sorted(payload.keys())}")
    if payload.get("pageInfo", {}).get("contractVersion") != "2.1.0":
        fail(errors, "contractVersion must be 2.1.0")
    meta = payload.get("meta", {}) if isinstance(payload.get("meta"), dict) else {}
    if meta.get("sourceType") != expected_source_type:
        fail(errors, f"meta.sourceType must be {expected_source_type}")
    if "compat" in meta:
        fail(errors, "meta.compat must be removed")
    page_info = payload.get("pageInfo", {}) if isinstance(payload.get("pageInfo"), dict) else {}
    layout = payload.get("layoutContract", {}) if isinstance(payload.get("layoutContract"), dict) else {}
    enum_checks = (
        ("pageInfo.clientType", page_info.get("clientType"), ("clientType", "stable")),
        ("pageInfo.viewType", page_info.get("viewType"), ("viewType",)),
        ("pageInfo.layoutType", page_info.get("layoutType"), ("layoutType",)),
        ("pageInfo.renderMode", page_info.get("renderMode"), ("renderMode",)),
        ("layoutContract.layoutType", layout.get("layoutType"), ("layoutType",)),
        ("layoutContract.adaptMode", layout.get("adaptMode"), ("adaptMode",)),
    )
    for label, value, registry_key_path in enum_checks:
        if value not in (registry_path(registry, registry_key_path) or []):
            fail(errors, f"{expected_source_type}: {label} must be listed in enum_registry.{'.'.join(registry_key_path)}")
    container_count = len(payload.get("layoutContract", {}).get("containerTree") or [])
    widget_status = payload.get("statusContract", {}).get("widgetStatus") or []
    widget_status_count = len(widget_status)
    action_count = len(payload.get("actionContract", {}).get("actionRuleList") or [])
    if container_count < int(snapshot.get("minContainerCount") or 0):
        fail(errors, f"{expected_source_type}: container snapshot below baseline")
    if widget_status_count < int(snapshot.get("minWidgetStatusCount") or 0):
        fail(errors, f"{expected_source_type}: widget status snapshot below baseline")
    expected_widget_ids = [
        str(item)
        for item in snapshot.get("expectedWidgetIds") or []
        if str(item)
    ]
    if expected_widget_ids:
        actual_widget_ids = {
            str(row.get("widgetId"))
            for row in widget_status
            if isinstance(row, dict) and str(row.get("widgetId"))
        }
        for widget_id in expected_widget_ids:
            if widget_id not in actual_widget_ids:
                fail(errors, f"{expected_source_type}: expected widgetStatus {widget_id!r} missing")
    if action_count < int(snapshot.get("minActionCount") or 0):
        fail(errors, f"{expected_source_type}: action snapshot below baseline")
    expected_form_structure = snapshot.get("requiresFormStructureContract") is True
    if expected_form_structure:
        structure = payload.get("formStructureContract") if isinstance(payload.get("formStructureContract"), dict) else {}
        if structure.get("source") != "ui.contract.v2.form_structure_contract":
            fail(errors, f"{expected_source_type}: formStructureContract source missing")
        slots = structure.get("slots") if isinstance(structure.get("slots"), list) else []
        if not slots:
            fail(errors, f"{expected_source_type}: formStructureContract slots missing")
        if not _layout_has_form_structure(payload.get("layoutContract", {}).get("containerTree") or []):
            fail(errors, f"{expected_source_type}: layout projection missing formStructure metadata")
    for legacy_key in ("scene_contract_v1", "page_orchestration_v1", "ui_contract", "api_onchange"):
        if legacy_key in payload:
            fail(errors, f"legacy key leaked at top-level: {legacy_key}")
    for node_path, node in walk(payload):
        if isinstance(node, dict):
            for key in node:
                if str(key).lower() in {"script", "function", "eval", "jsonlogic", "workflowdsl", "frontendprivate"}:
                    fail(errors, f"forbidden executable/private key {key!r} at {node_path}")
            if "containerType" in node and node["containerType"] not in (registry_path(registry, ("containerType",)) or []):
                fail(errors, f"{node_path}.containerType must be listed in enum_registry.containerType")
            if "widgetType" in node and node["widgetType"] not in (registry_path(registry, ("widgetType",)) or []):
                fail(errors, f"{node_path}.widgetType must be listed in enum_registry.widgetType")


def _layout_has_form_structure(rows: list[Any]) -> bool:
    for row in rows:
        if not isinstance(row, dict):
            continue
        if isinstance(row.get("formStructure"), dict) or isinstance(row.get("formStructureRole"), dict):
            return True
        for key in ("children", "pages", "tabs", "nodes", "items"):
            if _layout_has_form_structure(row.get(key) if isinstance(row.get(key), list) else []):
                return True
    return False


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
    if meta.get("sourceType") != "api.onchange":
        fail(errors, "patch meta.sourceType must be api.onchange")
    if "compat" in meta:
        fail(errors, "patch meta.compat must be removed")
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
    parser.add_argument("--enum-registry", required=True, type=Path)
    args = parser.parse_args()
    target = load_assembler()
    errors: list[str] = []
    snapshot = load_json(args.snapshot)
    registry = load_json(args.enum_registry)
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
        expected_source_type="scene_contract_v1",
        snapshot=source_snapshots.get("scene_contract_v1") or {},
        registry=registry,
        errors=errors,
    )
    validate_contract(
        page_contract,
        expected_source_type="page_orchestration_v1",
        snapshot=source_snapshots.get("page_orchestration_v1") or {},
        registry=registry,
        errors=errors,
    )
    validate_contract(
        ui_contract,
        expected_source_type="ui.contract",
        snapshot=source_snapshots.get("ui_contract") or {},
        registry=registry,
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
