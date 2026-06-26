#!/usr/bin/env python3
"""Guard StatusContract v2+ source consolidation without requiring Odoo."""

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
STATUS_PATH = ROOT / "addons/smart_core/core/unified_page_contract_v2_status.py"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_status_module():
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    core_pkg.__path__ = [str(CORE_DIR)]
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.core.unified_page_contract_v2_status_guard_target",
        STATUS_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load status module from {STATUS_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows if isinstance(row, dict) and row.get(key)}


def compare_subset(actual: dict[str, Any], expected: dict[str, Any], path: str, errors: list[str]) -> None:
    for key, expected_value in expected.items():
        if actual.get(key) != expected_value:
            fail(errors, f"{path}.{key}: expected {expected_value!r}, got {actual.get(key)!r}")


def registry_path(value: dict[str, Any], path: tuple[str, ...]) -> Any:
    node: Any = value
    for item in path:
        if not isinstance(node, dict):
            return None
        node = node.get(item)
    return node


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--enum-registry", required=True, type=Path)
    args = parser.parse_args()

    target = load_status_module()
    source = load_json(args.fixture)
    snapshot = load_json(args.snapshot)
    registry = load_json(args.enum_registry)
    status = target.build_status_contract_v2(source, render_profile="edit")
    expected = snapshot.get("expected") if isinstance(snapshot.get("expected"), dict) else {}
    errors: list[str] = []

    for key in ("globalStatus", "containerStatus", "widgetStatus", "buttonStatus", "selectorStatus"):
        if key not in status:
            fail(errors, f"statusContract missing {key}")

    auth_levels = registry_path(registry, ("authLevel",))
    if set(getattr(target, "AUTH_LEVELS", set())) != set(auth_levels or []):
        fail(errors, "status AUTH_LEVELS must match enum_registry.authLevel")

    compare_subset(status.get("globalStatus") or {}, expected.get("globalStatus") or {}, "globalStatus", errors)
    if (status.get("globalStatus") or {}).get("pageAuth") not in auth_levels:
        fail(errors, "globalStatus.pageAuth must be listed in enum_registry.authLevel")

    actual_widgets = index_by(status.get("widgetStatus") or [], "widgetId")
    for widget_id, expected_row in (expected.get("widgetStatus") or {}).items():
        if widget_id not in actual_widgets:
            fail(errors, f"widgetStatus missing {widget_id}")
            continue
        compare_subset(actual_widgets[widget_id], expected_row, f"widgetStatus.{widget_id}", errors)

    actual_buttons = index_by(status.get("buttonStatus") or [], "btnId")
    for btn_id, expected_row in (expected.get("buttonStatus") or {}).items():
        if btn_id not in actual_buttons:
            fail(errors, f"buttonStatus missing {btn_id}")
            continue
        compare_subset(actual_buttons[btn_id], expected_row, f"buttonStatus.{btn_id}", errors)

    actual_containers = index_by(status.get("containerStatus") or [], "containerId")
    for container_id, expected_row in (expected.get("containerStatus") or {}).items():
        if container_id not in actual_containers:
            fail(errors, f"containerStatus missing {container_id}")
            continue
        compare_subset(actual_containers[container_id], expected_row, f"containerStatus.{container_id}", errors)

    actual_selectors = index_by(status.get("selectorStatus") or [], "selector")
    for selector, expected_row in (expected.get("selectorStatus") or {}).items():
        if selector not in actual_selectors:
            fail(errors, f"selectorStatus missing {selector}")
            continue
        compare_subset(actual_selectors[selector], expected_row, f"selectorStatus.{selector}", errors)

    for row in status.get("widgetStatus") or []:
        if row.get("reason_code") or row.get("reason"):
            fail(errors, f"{row.get('widgetId')}: reason must be normalized to reasonCode")
        if row.get("auth") not in auth_levels:
            fail(errors, f"{row.get('widgetId')}: auth must be listed in enum_registry.authLevel")

    if errors:
        print("Unified Page Contract v2+ status guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Page Contract v2+ status guard passed: widgets=%d buttons=%d" % (
        len(status.get("widgetStatus") or []),
        len(status.get("buttonStatus") or []),
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
