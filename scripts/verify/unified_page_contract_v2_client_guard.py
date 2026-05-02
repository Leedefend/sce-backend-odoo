#!/usr/bin/env python3
"""Guard client trimming for Unified Page Contract v2+."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CLIENT_PATH = ROOT / "addons/smart_core/core/unified_page_contract_v2_client.py"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_client_module():
    spec = importlib.util.spec_from_file_location("unified_page_contract_v2_client_guard_target", CLIENT_PATH)
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
    if stable != snapshot.get("stableClientTypes"):
        fail(errors, "stable client types must match enum registry and snapshot")
    if reserved != snapshot.get("reservedClientTypes"):
        fail(errors, "reserved client types must match enum registry and snapshot")
    if target.resolve_client_type({"X-SC-Client-Type": "mobile_app"}, {}) != "web_pc":
        fail(errors, "mobile_app must remain reserved and default to web_pc in Batch-G")
    if target.resolve_client_type({"X-SC-Client-Type": "wx_mini"}, {}) != "wx_mini":
        fail(errors, "wx_mini resolver failed")

    matrix = {}
    for client in stable:
        matrix[client] = target.trim_unified_page_contract_v2(source, client_type=client)
        expected = snapshot.get("expected", {}).get(client) or {}
        layout = matrix[client].get("layoutContract") or {}
        hints = layout.get("layoutHints") or {}
        if matrix[client].get("pageInfo", {}).get("clientType") != client:
            fail(errors, f"{client}: pageInfo.clientType mismatch")
        if layout.get("adaptMode") != expected.get("adaptMode"):
            fail(errors, f"{client}: adaptMode mismatch")
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

    if errors:
        print("Unified Page Contract v2+ client guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Page Contract v2+ client guard passed: clients=%d" % len(stable))
    return 0


if __name__ == "__main__":
    sys.exit(main())
