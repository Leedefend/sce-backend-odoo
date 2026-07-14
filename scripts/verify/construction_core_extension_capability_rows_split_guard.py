#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
ROWS = ROOT / "addons/smart_construction_core/core_extension_capability_rows.py"
CI = ROOT / "make/ci.mk"

MAX_CORE_EXTENSION_LINES = 3145


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
    core_text = _read(CORE_EXTENSION)
    rows_text = _read(ROWS)
    ci_text = _read(CI)

    if not core_text:
        errors.append(f"missing core extension file: {CORE_EXTENSION.relative_to(ROOT)}")
    if not rows_text:
        errors.append(f"missing capability rows module: {ROWS.relative_to(ROOT)}")

    if core_text:
        line_count = len(core_text.splitlines())
        if line_count > MAX_CORE_EXTENSION_LINES:
            errors.append(f"core_extension.py line budget exceeded: {line_count} > {MAX_CORE_EXTENSION_LINES}")
        for token in [
            "core_extension_capability_rows as _capability_rows",
            "return _capability_rows.normalize_capability_rows(capabilities)",
            "_capability_rows.normalize_capability_rows(capabilities),",
            "registry_list_capabilities_for_user(env, user)",
            "registry_list_capabilities_for_user_with_timings(env, user)",
        ]:
            if token not in core_text:
                errors.append(f"core_extension.py missing capability rows split token: {token}")

    if rows_text:
        for token in [
            "def normalize_capability_row(",
            "def normalize_capability_rows(",
            '"source_module": "smart_construction_core"',
            '"owner_trace": "smart_construction_core.get_capability_contributions"',
            '"safe_fallback": "workspace.home"',
            '"contract_type": "entry_contract"',
        ]:
            if token not in rows_text:
                errors.append(f"capability rows module missing token: {token}")
        for forbidden in ("env[", ".search(", ".write(", ".create(", ".unlink(", "requests.", "register_", "from odoo"):
            if forbidden in rows_text:
                errors.append(f"capability rows module must remain pure normalization; forbidden token: {forbidden}")

    if "python3 scripts/verify/construction_core_extension_capability_rows_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run construction_core_extension_capability_rows_split_guard.py")

    if not errors:
        rows = _load(ROWS, "construction_core_extension_capability_rows_under_guard")
        normalized = rows.normalize_capability_rows([
            {
                "key": "project.dashboard",
                "ui_label": "项目驾驶舱",
                "group_key": "project_management",
                "intent": "project.dashboard.enter",
                "entry_target": {"scene_key": "project.management", "target_mode": "scene"},
                "required_roles": ["pm", ""],
                "required_groups": ["group.pm"],
                "sequence": 8,
                "tags": ["project"],
            },
            {"key": ""},
            "invalid",
        ])
        if len(normalized) != 1:
            errors.append("capability rows must skip invalid rows")
        elif normalized[0].get("binding", {}).get("scene", {}).get("entry_scene_key") != "project.management":
            errors.append("capability rows must preserve entry scene binding")
        elif normalized[0].get("permission", {}).get("required_roles") != ["pm"]:
            errors.append("capability rows must preserve cleaned required roles")
        elif normalized[0].get("runtime", {}).get("safe_fallback") != "workspace.home":
            errors.append("capability rows must preserve runtime fallback")

    if errors:
        print("[construction_core_extension_capability_rows_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[construction_core_extension_capability_rows_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
