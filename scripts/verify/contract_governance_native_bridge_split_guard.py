#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
NATIVE_BRIDGE = ROOT / "addons/smart_core/utils/contract_governance_native_bridge.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 3932


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    governance_text = _read(GOVERNANCE)
    bridge_text = _read(NATIVE_BRIDGE)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not bridge_text:
        errors.append(f"missing native bridge module: {NATIVE_BRIDGE.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_native_bridge_module()",
            "contract_governance_native_bridge.py",
            "_native_bridge._USER_SURFACE_ACTION_MAX = _USER_SURFACE_ACTION_MAX",
            "_native_bridge.ensure_scene_contract_v1_envelope(data)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing native bridge split token: {token}")

    if bridge_text:
        for token in [
            "def normalize_native_view_contract_surface(",
            "def normalize_scene_semantic_surface(",
            "def search_surface_from_contract(",
            "def scene_actions_from_contract(",
            "def ensure_scene_contract_v1_envelope(",
        ]:
            if token not in bridge_text:
                errors.append(f"native bridge module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in bridge_text:
                errors.append(f"native bridge module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_native_bridge_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_native_bridge_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_native_bridge_split_under_guard")
        data = {
            "search": {"filters": [{"key": "state"}]},
            "buttons": [{"key": "open"}],
            "list_profile": {
                "columns": ["name"],
                "column_labels": {"name": "名称"},
                "row_primary": "name",
                "status_field": "state",
            },
        }
        governance._ensure_scene_contract_v1_envelope(data)
        scene_contract = data.get("scene_contract_v1") or {}
        if scene_contract.get("contract_version") != "v1":
            errors.append("scene contract envelope must set version v1")
        if not (scene_contract.get("search_surface") or {}).get("filters"):
            errors.append("scene contract envelope must derive search_surface filters")
        if not (scene_contract.get("actions") or {}).get("primary_actions"):
            errors.append("scene contract envelope must derive primary actions")
        list_semantics = ((scene_contract.get("semantic_page") or {}).get("list_semantics") or {})
        if list_semantics.get("row_primary") != "name":
            errors.append("scene contract envelope must bridge list profile semantics")

    if errors:
        print("[contract_governance_native_bridge_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_native_bridge_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
