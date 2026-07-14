#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
POLICY_MAPS = ROOT / "addons/smart_construction_core/core_extension_policy_maps.py"
CI = ROOT / "make/ci.mk"

MAX_CORE_EXTENSION_LINES = 3763


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
    policy_text = _read(POLICY_MAPS)
    ci_text = _read(CI)

    if not core_text:
        errors.append(f"missing core extension file: {CORE_EXTENSION.relative_to(ROOT)}")
    if not policy_text:
        errors.append(f"missing policy maps module: {POLICY_MAPS.relative_to(ROOT)}")

    if core_text:
        line_count = len(core_text.splitlines())
        if line_count > MAX_CORE_EXTENSION_LINES:
            errors.append(f"core_extension.py line budget exceeded: {line_count} > {MAX_CORE_EXTENSION_LINES}")
        for token in [
            "core_extension_policy_maps as _policy_maps",
            "ROLE_SURFACE_OVERRIDES = _policy_maps.ROLE_SURFACE_OVERRIDES",
            "NAV_MENU_SCENE_MAP = _policy_maps.NAV_MENU_SCENE_MAP",
            "FILE_ATTACHMENT_ALLOWED_MODEL_EXACT = _policy_maps.FILE_ATTACHMENT_ALLOWED_MODEL_EXACT",
            "API_DATA_WRITE_ALLOWLIST = _policy_maps.API_DATA_WRITE_ALLOWLIST",
            "API_DATA_UNLINK_POLICIES = _policy_maps.API_DATA_UNLINK_POLICIES",
            "CRITICAL_SCENE_TARGET_OVERRIDES = _policy_maps.CRITICAL_SCENE_TARGET_OVERRIDES",
            "INDUSTRY_CREATE_FIELD_FALLBACKS = _policy_maps.INDUSTRY_CREATE_FIELD_FALLBACKS",
            "register_legacy_standard_list_profile({",
        ]:
            if token not in core_text:
                errors.append(f"core_extension.py missing policy-map split token: {token}")

    if policy_text:
        for token in [
            "ROLE_SURFACE_OVERRIDES = {",
            "ROLE_GROUPS_EXPLICIT = {",
            "NAV_MENU_SCENE_MAP = {",
            "LEGACY_VISIBLE_BUSINESS_COLUMN_LABELS_BY_MODEL = {",
            "API_DATA_WRITE_ALLOWLIST = {",
            "DRAFT_DELETE_ALLOWED_STATES =",
            "def _state_unlink_policy(",
            "API_DATA_DRAFT_UNLINK_POLICIES = {",
            "API_DATA_UNLINK_POLICIES.update(API_DATA_DRAFT_UNLINK_POLICIES)",
            "API_DATA_UNLINK_ALLOWED_MODELS = list(API_DATA_UNLINK_POLICIES)",
            "INDUSTRY_CREATE_FIELD_FALLBACKS = {",
        ]:
            if token not in policy_text:
                errors.append(f"policy maps module missing token: {token}")
        for forbidden in ("env[", ".search(", ".write(", "requests.", "register_", "AccessError", "fields."):
            if forbidden in policy_text:
                errors.append(f"policy maps module must remain pure constants; forbidden token: {forbidden}")

    if "python3 scripts/verify/construction_core_extension_policy_maps_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run construction_core_extension_policy_maps_split_guard.py")

    if not errors:
        policy_maps = _load(POLICY_MAPS, "construction_core_extension_policy_maps_under_guard")
        if policy_maps.ROLE_PRECEDENCE != ("business_config_admin", "executive", "pm", "finance"):
            errors.append("policy maps must preserve role precedence")
        if policy_maps.NAV_MENU_SCENE_MAP.get("smart_construction_core.menu_payment_request") != "finance.payment_requests":
            errors.append("policy maps must preserve payment menu scene mapping")
        if "project.project" not in policy_maps.FILE_UPLOAD_ALLOWED_MODELS:
            errors.append("policy maps must preserve project upload model")
        if "payment.request" not in policy_maps.API_DATA_UNLINK_POLICIES:
            errors.append("policy maps must preserve payment request unlink policy")
        if policy_maps.API_DATA_UNLINK_POLICIES.get("sc.quality.rectification", {}).get("state_field") != "issue_state":
            errors.append("policy maps must preserve quality rectification state field")
        if policy_maps.CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES.get("my_work.workspace") != "/my-work":
            errors.append("policy maps must preserve critical route override")

    if errors:
        print("[construction_core_extension_policy_maps_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[construction_core_extension_policy_maps_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
