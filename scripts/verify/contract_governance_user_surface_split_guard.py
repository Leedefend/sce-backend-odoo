#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
USER_SURFACE = ROOT / "addons/smart_core/utils/contract_governance_user_surface.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 4535

USER_SURFACE_FUNCTIONS = [
    "strip_user_mode_fields",
    "pick_fields",
    "sanitize_capability_for_user",
    "sanitize_scene_for_user",
    "is_numeric_token",
    "contains_noise_marker",
    "is_noisy_filter_row",
    "sanitize_user_search_filters",
    "is_noisy_action_row",
    "classify_user_surface_action_group",
    "build_user_surface_action_groups",
    "sanitize_user_action_rows",
    "apply_user_surface_noise_reduction",
]


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
    user_surface_text = _read(USER_SURFACE)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not user_surface_text:
        errors.append(f"missing user-surface module: {USER_SURFACE.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_user_surface_module()",
            "contract_governance_user_surface.py",
            "return _user_surface.strip_user_mode_fields(obj)",
            "return _user_surface.sanitize_capability_for_user(item)",
            "return _user_surface.build_user_surface_action_groups(rows)",
            "_user_surface.apply_user_surface_noise_reduction(data)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing user-surface facade token: {token}")

    if user_surface_text:
        for function_name in USER_SURFACE_FUNCTIONS:
            if f"def {function_name}(" not in user_surface_text:
                errors.append(f"user-surface module missing function: {function_name}")
        for forbidden in ("odoo.", "http", "requests.", "env[", ".write(", ".search("):
            if forbidden in user_surface_text:
                errors.append(f"user-surface module must stay pure; forbidden token: {forbidden}")

    if "python3 scripts/verify/contract_governance_user_surface_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_user_surface_split_guard.py")

    if not errors:
        user_surface = _load(USER_SURFACE, "contract_governance_user_surface_under_guard")
        payload = {
            "route": "/s/projects",
            "action_xmlid": "private.action",
            "nested": {"menu_xmlid": "private.menu", "keep": "ok"},
        }
        stripped = user_surface.strip_user_mode_fields(payload)
        if "action_xmlid" in stripped or "menu_xmlid" in stripped.get("nested", {}):
            errors.append("strip_user_mode_fields must remove internal xmlid fields recursively")
        if user_surface.classify_user_surface_action_group({"key": "submit", "label": "提交审批"}) != "workflow":
            errors.append("action classifier must keep workflow classification")
        rows = user_surface.sanitize_user_action_rows(
            [
                {"key": "1", "label": "1"},
                {"key": "batch", "label": "批量删除", "selection": "multi"},
                {"key": "open_dashboard", "label": "查看驾驶舱"},
                {"key": "open_dashboard", "label": "查看驾驶舱"},
            ],
            max_count=2,
        )
        if [row.get("key") for row in rows] != ["batch", "open_dashboard"]:
            errors.append("sanitize_user_action_rows must remove numeric/noisy/duplicate rows and preserve multi rows")
        data = {"search": {"filters": [{"key": "demo_filter", "label": "demo"}, {"key": "status", "label": "状态"}]}}
        user_surface.sanitize_user_search_filters(data)
        if data.get("search", {}).get("filters") != [{"key": "status", "label": "状态"}]:
            errors.append("sanitize_user_search_filters must remove demo/noise filters")

    if errors:
        print("[contract_governance_user_surface_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_user_surface_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
