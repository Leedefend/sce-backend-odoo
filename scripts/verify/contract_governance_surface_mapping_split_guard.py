#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
SURFACE_MAPPING = ROOT / "addons/smart_core/utils/contract_governance_surface_mapping.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 3690


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
    surface_mapping_text = _read(SURFACE_MAPPING)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not surface_mapping_text:
        errors.append(f"missing surface mapping module: {SURFACE_MAPPING.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_surface_mapping_module()",
            "contract_governance_surface_mapping.py",
            "return _surface_mapping.collect_surface_snapshot(data)",
            "return _surface_mapping.build_surface_mapping(native_snapshot, governed_snapshot)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing surface mapping split token: {token}")

    if surface_mapping_text:
        for token in [
            "def collect_layout_snapshot(",
            "def collect_action_snapshot(",
            "def collect_surface_snapshot(",
            "def build_surface_mapping(",
            '"native_to_governed"',
            '"reordered": reordered',
        ]:
            if token not in surface_mapping_text:
                errors.append(f"surface mapping module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in surface_mapping_text:
                errors.append(f"surface mapping module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_surface_mapping_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_surface_mapping_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_surface_mapping_split_under_guard")
        native = governance._collect_surface_snapshot(
            {
                "fields": {"name": {}, "state": {}},
                "views": {
                    "form": {
                        "layout": [
                            {"type": "field", "name": "name"},
                            {"type": "field", "name": "state"},
                        ],
                        "header_buttons": [{"key": "archive"}],
                        "field_modifiers": {"state": {}},
                    }
                },
                "buttons": [{"payload": {"method": "action_confirm"}}],
            }
        )
        governed = governance._collect_surface_snapshot(
            {
                "fields": {"name": {}, "stage_id": {}},
                "views": {
                    "form": {
                        "layout": [
                            {"type": "field", "name": "stage_id"},
                            {"type": "field", "name": "name"},
                        ],
                        "header_buttons": [{"key": "archive"}],
                        "field_modifiers": {"stage_id": {}},
                    }
                },
                "buttons": [{"payload": {"method": "action_confirm"}}],
            }
        )
        mapping = governance._build_surface_mapping(native, governed).get("native_to_governed") or {}
        fields = mapping.get("fields") or {}
        if fields.get("removed") != ["state"] or fields.get("added") != ["stage_id"]:
            errors.append("surface mapping must report field additions and removals")
        layout_fields = mapping.get("layout_fields") or {}
        if layout_fields.get("reordered"):
            errors.append("layout mapping with additions/removals must not be marked reordered-only")

    if errors:
        print("[contract_governance_surface_mapping_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_surface_mapping_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
