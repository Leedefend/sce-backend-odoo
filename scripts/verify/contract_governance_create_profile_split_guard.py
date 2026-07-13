#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
CREATE_PROFILE = ROOT / "addons/smart_core/utils/contract_governance_create_profile.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 3528


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _field_node(layout: list, name: str) -> dict:
    return next(node for node in layout if isinstance(node, dict) and node.get("name") == name)


def main() -> int:
    errors: list[str] = []
    governance_text = _read(GOVERNANCE)
    create_profile_text = _read(CREATE_PROFILE)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not create_profile_text:
        errors.append(f"missing create profile module: {CREATE_PROFILE.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_create_profile_module()",
            "contract_governance_create_profile.py",
            "return _create_profile.is_create_render_profile(data)",
            "is_enterprise_user_form_contract=_is_enterprise_user_form_contract",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing create profile split token: {token}")

    if create_profile_text:
        for token in [
            "def is_create_render_profile(",
            "def mark_record_dependent_native_buttons_hidden_on_create(",
            "def is_create_profile_noise_field(",
            "def hide_create_profile_noise_fields(",
            "def hide_create_profile_state_ribbons(",
            "CREATE_PROFILE_REQUIRES_RECORD",
            "CREATE_PROFILE_TECHNICAL_FIELD",
            "CREATE_PROFILE_STATE_WIDGET",
        ]:
            if token not in create_profile_text:
                errors.append(f"create profile module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in create_profile_text:
                errors.append(f"create profile module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_create_profile_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_create_profile_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_create_profile_split_under_guard")
        if not governance._is_create_render_profile({"views": {"form": {}}, "record_id": "new"}):
            errors.append("new record id must be treated as create render profile")

        button_data = {
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "button",
                            "action": {"level": "smart", "visible_profiles": ["create", "edit"]},
                        }
                    ]
                }
            },
            "render_profile": "create",
        }
        governance._mark_record_dependent_native_buttons_hidden_on_create(button_data)
        button = button_data["views"]["form"]["layout"][0]
        action = button.get("action") or {}
        if button.get("invisible", {}).get("reason_code") != "CREATE_PROFILE_REQUIRES_RECORD":
            errors.append("record-dependent create button must be hidden")
        if "create" in action.get("visible_profiles", []):
            errors.append("record-dependent action must remove create visible profile")
        if not action.get("requires_record"):
            errors.append("record-dependent action must be marked requires_record")

        field_data = {
            "views": {
                "form": {
                    "layout": [
                        {"type": "field", "name": "same_vat_partner_id"},
                        {
                            "type": "widget",
                            "widget": "web_ribbon",
                            "title": "Archived",
                            "attributes": {},
                        },
                    ]
                }
            },
            "render_profile": "create",
            "fields": {
                "same_vat_partner_id": {"readonly": True, "compute": "_compute_same"},
                "name": {"type": "char"},
            },
        }
        governance._hide_create_profile_noise_fields(field_data)
        layout = field_data["views"]["form"]["layout"]
        hidden_field = _field_node(layout, "same_vat_partner_id")
        if hidden_field.get("invisible", {}).get("reason_code") != "CREATE_PROFILE_TECHNICAL_FIELD":
            errors.append("create-profile technical field must be hidden in layout")
        semantics = field_data.get("field_semantics", {}).get("same_vat_partner_id") or {}
        if semantics.get("surface_role") != "hidden":
            errors.append("create-profile technical field semantics must be hidden")
        governance._hide_create_profile_state_ribbons(field_data)
        ribbon = next(node for node in layout if isinstance(node, dict) and node.get("widget") == "web_ribbon")
        if ribbon.get("invisible", {}).get("reason_code") != "CREATE_PROFILE_STATE_WIDGET":
            errors.append("archive ribbon must be hidden in create profile")

    if errors:
        print("[contract_governance_create_profile_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_create_profile_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
