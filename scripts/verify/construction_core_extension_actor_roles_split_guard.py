#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
ACTOR_ROLES = ROOT / "addons/smart_construction_core/core_extension_actor_roles.py"
CI = ROOT / "make/ci.mk"

MAX_CORE_EXTENSION_LINES = 1787
MAX_ACTOR_ROLES_LINES = 33


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Groups:
    def get_external_id(self):
        return {
            1: "smart_construction_core.group_sc_role_owner",
            2: "smart_construction_core.group_sc_role_finance",
            3: "base.group_user",
        }


class _User:
    groups_id = _Groups()

    def has_group(self, xmlid: str) -> bool:
        return xmlid in {
            "smart_construction_core.group_sc_cap_project_read",
            "smart_construction_core.group_sc_business_full",
        }


def main() -> int:
    errors: list[str] = []
    core_text = _read(CORE_EXTENSION)
    roles_text = _read(ACTOR_ROLES)
    ci_text = _read(CI)

    if not core_text:
        errors.append(f"missing core extension file: {CORE_EXTENSION.relative_to(ROOT)}")
    if not roles_text:
        errors.append(f"missing actor roles module: {ACTOR_ROLES.relative_to(ROOT)}")

    if core_text:
        line_count = len(core_text.splitlines())
        if line_count > MAX_CORE_EXTENSION_LINES:
            errors.append(f"core_extension.py line budget exceeded: {line_count} > {MAX_CORE_EXTENSION_LINES}")
        for token in [
            "core_extension_actor_roles as _actor_roles",
            "return _actor_roles.resolve_release_actor_role_codes(user)",
            "return smart_core_resolve_release_actor_role_codes(env, user)",
        ]:
            if token not in core_text:
                errors.append(f"core_extension.py missing actor role split token: {token}")

    if roles_text:
        line_count = len(roles_text.splitlines())
        if line_count > MAX_ACTOR_ROLES_LINES:
            errors.append(f"actor roles module line budget exceeded: {line_count} > {MAX_ACTOR_ROLES_LINES}")
        for token in [
            "def resolve_release_actor_role_codes(",
            "smart_construction_core.group_sc_role_",
            "smart_construction_core.group_sc_cap_project_read",
            "smart_construction_core.group_sc_business_full",
        ]:
            if token not in roles_text:
                errors.append(f"actor roles module missing token: {token}")
        for forbidden in ("env[", ".search(", ".write(", ".create(", ".unlink(", "registry[", "requests.", "commit("):
            if forbidden in roles_text:
                errors.append(f"actor roles module must not own ORM/registry side effects; forbidden token: {forbidden}")

    if "python3 scripts/verify/construction_core_extension_actor_roles_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run construction_core_extension_actor_roles_split_guard.py")

    if not errors:
        roles = _load(ACTOR_ROLES, "construction_core_extension_actor_roles_under_guard")
        resolved = roles.resolve_release_actor_role_codes(_User())
        if resolved != ["executive", "finance", "owner", "pm"]:
            errors.append(f"actor roles must preserve explicit and capability-derived roles: {resolved}")
        if roles.resolve_release_actor_role_codes(None) != []:
            errors.append("actor roles must return empty list for missing user")

    if errors:
        print("[construction_core_extension_actor_roles_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[construction_core_extension_actor_roles_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
