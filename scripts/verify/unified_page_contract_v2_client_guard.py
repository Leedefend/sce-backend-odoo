#!/usr/bin/env python3
"""Guard client trimming for Unified Page Contract v2+."""

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
CLIENT_PATH = ROOT / "addons/smart_core/core/unified_page_contract_v2_client.py"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_client_module():
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    core_pkg.__path__ = [str(CORE_DIR)]
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.core.unified_page_contract_v2_client_guard_target",
        CLIENT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load client module from {CLIENT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--enum-registry", required=True, type=Path)
    args = parser.parse_args()

    target = load_client_module()
    source = load_json(args.fixture)
    snapshot = load_json(args.snapshot)
    registry = load_json(args.enum_registry)
    errors: list[str] = []

    stable = registry.get("clientType", {}).get("stable") or []
    reserved = registry.get("clientType", {}).get("reserved") or []
    adapt_modes = registry.get("adaptMode") or []
    if stable != snapshot.get("stableClientTypes"):
        fail(errors, "stable client types must match enum registry and snapshot")
    if reserved != snapshot.get("reservedClientTypes"):
        fail(errors, "reserved client types must match enum registry and snapshot")
    if tuple(stable) != getattr(target, "STABLE_CLIENT_TYPES", ()):
        fail(errors, "client STABLE_CLIENT_TYPES must match enum_registry.clientType.stable")
    if tuple(reserved) != getattr(target, "RESERVED_CLIENT_TYPES", ()):
        fail(errors, "client RESERVED_CLIENT_TYPES must match enum_registry.clientType.reserved")
    if not set(getattr(target, "MOBILE_CLIENT_TYPES", set())).issubset(set(stable)):
        fail(errors, "client MOBILE_CLIENT_TYPES must be a subset of enum_registry.clientType.stable")
    if "pc" not in adapt_modes or "mobile" not in adapt_modes:
        fail(errors, "enum_registry.adaptMode must include pc and mobile for client trimming")
    if target.resolve_client_type({"X-SC-Client-Type": "mobile_app"}, {}) != "web_pc":
        fail(errors, "mobile_app must remain reserved and default to web_pc in Batch-G")
    if target.resolve_client_type({"X-SC-Client-Type": "wx_mini"}, {}) != "wx_mini":
        fail(errors, "wx_mini resolver failed")

    matrix = {}
    for client in stable:
        matrix[client] = target.trim_unified_page_contract_v2(source, client_type=client, delivery_profile="full")
        expected = snapshot.get("expected", {}).get(client) or {}
        layout = matrix[client].get("layoutContract") or {}
        hints = layout.get("layoutHints") or {}
        if matrix[client].get("pageInfo", {}).get("clientType") != client:
            fail(errors, f"{client}: pageInfo.clientType mismatch")
        if layout.get("adaptMode") != expected.get("adaptMode"):
            fail(errors, f"{client}: adaptMode mismatch")
        if layout.get("adaptMode") not in adapt_modes:
            fail(errors, f"{client}: adaptMode must be listed in enum_registry.adaptMode")
        if hints.get("columns") != expected.get("columns"):
            fail(errors, f"{client}: layout columns mismatch")
        if hints.get("mobileCollapse") != expected.get("mobileCollapse"):
            fail(errors, f"{client}: mobileCollapse mismatch")
        registry_rows = layout.get("componentRegistry") or {}
        for key, row in registry_rows.items():
            if not row.get("selectedAdapter"):
                fail(errors, f"{client}: component {key} missing selectedAdapter")

    drift = target.find_client_semantic_drift(matrix)
    for issue in drift:
        fail(errors, issue)

    compact = target.trim_unified_page_contract_v2(
        source,
        client_type="harmony_h5",
        delivery_profile="mobile_compact",
        max_widgets=1,
        max_actions=1,
    )
    compact_layout = compact.get("layoutContract") or {}
    compact_widgets = ((compact_layout.get("containerTree") or [{}])[0].get("widgetList") or [])
    if len(compact_widgets) != 1:
        fail(errors, "mobile_compact must trim widget delivery")
    compact_trim = compact.get("meta", {}).get("deliveryTrim") or {}
    if compact_trim.get("deliveryProfile") != "mobile_compact":
        fail(errors, "mobile_compact must report delivery profile")
    if compact_trim.get("omitted", {}).get("widgets", 0) < 1:
        fail(errors, "mobile_compact must report omitted widgets")
    if compact.get("meta", {}).get("sourceType") != "ui.contract":
        fail(errors, "mobile_compact sourceType must stay ui.contract")
    if "compat" in (compact.get("meta") or {}):
        fail(errors, "mobile_compact meta.compat must be removed")

    if errors:
        print("Unified Page Contract v2+ client guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Page Contract v2+ client guard passed: clients=%d" % len(stable))
    return 0


if __name__ == "__main__":
    sys.exit(main())
