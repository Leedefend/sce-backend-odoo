#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
FORM_RENDER = ROOT / "addons/smart_core/utils/contract_governance_form_render.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 3169


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
    form_render_text = _read(FORM_RENDER)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not form_render_text:
        errors.append(f"missing form render module: {FORM_RENDER.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_form_render_module()",
            "contract_governance_form_render.py",
            "return _form_render.to_bool(value, fallback=fallback)",
            "return _form_render.resolve_render_profile(data)",
            "_form_render.apply_form_view_capabilities(data)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing form render split token: {token}")

    if form_render_text:
        for token in [
            "def to_bool(",
            "def resolve_render_profile(",
            "def apply_form_view_capabilities(",
            "_RENDER_PROFILE_CREATE",
            "_RENDER_PROFILE_EDIT",
            "_RENDER_PROFILE_READONLY",
            'effective_rights["write"] = False',
            'head_permissions["create"] = False',
        ]:
            if token not in form_render_text:
                errors.append(f"form render module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in form_render_text:
                errors.append(f"form render module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_form_render_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_form_render_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_form_render_split_under_guard")
        if not governance._to_bool("yes") or governance._to_bool("off", fallback=True):
            errors.append("boolean coercion must preserve existing truthy/falsy tokens")
        if governance._resolve_render_profile({"head": {"view_type": "tree"}}) != governance._RENDER_PROFILE_EDIT:
            errors.append("non-form views must resolve to edit render profile")
        readonly = {
            "head": {"view_type": "form", "permissions": {"write": False, "create": False}},
            "permissions": {"effective": {"rights": {"write": False, "create": False}}},
        }
        if governance._resolve_render_profile(readonly) != governance._RENDER_PROFILE_READONLY:
            errors.append("no write/create rights must resolve readonly profile")
        create = {
            "head": {"view_type": "form", "permissions": {"write": True, "create": True}},
            "permissions": {"effective": {"rights": {"write": True, "create": True}}},
            "res_id": "new",
        }
        if governance._resolve_render_profile(create) != governance._RENDER_PROFILE_CREATE:
            errors.append("new record must resolve create profile")
        edit = dict(create)
        edit["res_id"] = "42"
        if governance._resolve_render_profile(edit) != governance._RENDER_PROFILE_EDIT:
            errors.append("persisted record id must resolve edit profile")

        data = {
            "views": {"form": {"capabilities": {"can_create": False, "can_write": False, "can_delete": False}}},
            "permissions": {"effective": {"rights": {"create": True, "write": True, "unlink": True}}},
            "head": {"permissions": {"create": True, "write": True, "unlink": True}},
        }
        governance._apply_form_view_capabilities(data)
        rights = data["permissions"]["effective"]["rights"]
        head_permissions = data["head"]["permissions"]
        if rights.get("create") or rights.get("write") or rights.get("unlink"):
            errors.append("form capabilities must disable effective rights")
        if head_permissions.get("create") or head_permissions.get("write"):
            errors.append("form capabilities must disable head create/write permissions")

    if errors:
        print("[contract_governance_form_render_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_form_render_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
