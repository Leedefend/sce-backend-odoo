#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard form-view fact scope rules.

Odoo view structure is not a single global form.  The stable identities are:
generic model view, explicit native view, and action-bound native view.  User
preferences must not become structure facts.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_VIEW_CONFIG = ROOT / "addons/smart_core/app_config_engine/models/app_view_config.py"
FIELD_POLICY = ROOT / "addons/smart_core/model/ui_form_field_policy.py"
CUSTOM_FIELD_HANDLER = ROOT / "addons/smart_core/handlers/form_field_configuration.py"
DYNAMIC_CONFIG = ROOT / "addons/smart_core/model/ui_dynamic_config.py"
SCOPE_DOC = ROOT / "docs/audit/native/form_view_scope_rules_20260515.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _class_body(text: str, class_name: str) -> str:
    match = re.search(rf"^class {re.escape(class_name)}\b[\s\S]*?(?=^class |\Z)", text, re.MULTILINE)
    return match.group(0) if match else ""


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    app_view_config = _read(APP_VIEW_CONFIG)
    field_policy = _read(FIELD_POLICY)
    custom_field_handler = _read(CUSTOM_FIELD_HANDLER)
    dynamic_config = _read(DYNAMIC_CONFIG)
    scope_doc = _read(SCOPE_DOC)

    app_view_body = _class_body(app_view_config, "AppViewConfig")
    policy_body = _class_body(field_policy, "UIFormFieldPolicy")

    _assert(
        "user_id = fields." not in app_view_body and "fields.Many2one('res.users'" not in app_view_body,
        "app.view.config must not add user_id to structural projection identity",
        errors,
    )
    projection_identity = re.search(
        r"def _projection_identity\b[\s\S]*?(?=\n    def |\n    #|\Z)",
        app_view_config,
    )
    projection_identity_body = projection_identity.group(0) if projection_identity else ""
    _assert(
        "user_id" not in projection_identity_body,
        "app.view.config projection identity must not include user_id",
        errors,
    )
    _assert(
        '"projection_scope": "generic:%s:%s"' in app_view_config,
        "app.view.config must keep generic model/view projection scope",
        errors,
    )
    _assert(
        '"projection_scope": "view:%s:%s:%s"' in app_view_config,
        "app.view.config must keep explicit ir.ui.view projection scope",
        errors,
    )
    _assert(
        '"projection_scope": "action:%s:%s:%s:view:%s"' in app_view_config,
        "app.view.config must keep action-bound projection scope including source view",
        errors,
    )
    _assert(
        "contract_action_id" in app_view_config and "contract_view_id" in app_view_config,
        "app.view.config must read action/view context before composing native view",
        errors,
    )
    _assert(
        "Model.with_context(load_all_views=True).get_view(view_id=view_id, view_type=view_type)" in app_view_config,
        "app.view.config must load explicit source_view_id through Odoo get_view",
        errors,
    )

    _assert(
        "user_id" not in policy_body,
        "ui.form.field.policy must not support per-user structural field policy",
        errors,
    )
    _assert(
        'SOURCE_AUTHORITIES = ("ui.form.field.policy", "ir.model.fields", "app.view.config")' in field_policy,
        "ui.form.field.policy source authority must exclude res.users",
        errors,
    )
    for token in ('"action_id"', '"view_id"', '"company_id"'):
        _assert(token in field_policy, f"ui.form.field.policy must preserve {token} scope", errors)
    _assert(
        "def scope_weight(policy) -> tuple[int, int, int]:" in field_policy
        and "1 if policy.action_id else 0" in field_policy
        and "1 if policy.view_id else 0" in field_policy
        and "1 if policy.company_id else 0" in field_policy,
        "ui.form.field.policy must keep deterministic action/view/company merge priority",
        errors,
    )

    handler_class = re.search(
        r"class FormCustomFieldCreateHandler\b[\s\S]*?(?=^class |\Z)",
        custom_field_handler,
        re.MULTILINE,
    )
    handler_body = handler_class.group(0) if handler_class else ""
    _assert(handler_body, "FormCustomFieldCreateHandler not found", errors)
    _assert("user_id" not in handler_body, "custom field creation must not write user scope", errors)
    for token in ('"action_id": action_id or False', '"view_id": view_id or False', '"company_id": self.env.company.id'):
        _assert(token in handler_body, f"custom field creation must preserve scope assignment `{token}`", errors)

    _assert(
        "user_id = fields.Many2one('res.users'" in dynamic_config,
        "ui.dynamic.config may keep user_id only as legacy preference overlay",
        errors,
    )
    _assert(
        "ui_overlay_only" in dynamic_config,
        "ui.dynamic.config must declare overlay-only authority",
        errors,
    )
    _assert(
        "用户个性化不属于结构事实" in scope_doc
        and "projection_scope" in scope_doc
        and "ui.form.field.policy" in scope_doc,
        "scope rules document must define user/model/action/view policy boundaries",
        errors,
    )

    if errors:
        print("[form_view_scope_boundary_guard] FAIL")
        for error in errors:
            print(f" - {error}")
        return 1

    print("[form_view_scope_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
