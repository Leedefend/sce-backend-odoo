# -*- coding: utf-8 -*-
"""Guard project-level isolation selector contract.

Run inside Odoo shell. The selector is produced by smart_core but the
construction product must expose it as project context, not generic record
context, because users rely on it as the visible project isolation control.
"""

import json

from odoo.addons.smart_core.core.project_context import build_record_context_contract
from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first


payload = build_record_context_contract(env, {"scene": "web"}, search="", limit=5)
selector = payload.get("selector") if isinstance(payload, dict) else {}
selector = selector if isinstance(selector, dict) else {}
source_authority = payload.get("source_authority") if isinstance(payload, dict) else {}
source_authority = source_authority if isinstance(source_authority, dict) else {}
hook_payload = call_extension_hook_first(env, "smart_core_resolve_record_context_config", env, {"scene": "web"})

errors = []
if not payload.get("enabled"):
    errors.append("project context selector must be enabled")
if payload.get("model") != "project.project":
    errors.append("project context selector model must be project.project")
if selector.get("label") != "当前项目":
    errors.append("project context selector label must be 当前项目")
if selector.get("placeholder") != "搜索项目名称":
    errors.append("project context selector placeholder must be 搜索项目名称")
if not payload.get("legacy_project_context"):
    errors.append("legacy_project_context compatibility flag must be true")
if "project.project" not in (source_authority.get("registered_legacy_scope_models") or []):
    errors.append("project.project must be registered as legacy project scope model")
if not isinstance(hook_payload, dict) or hook_payload.get("label") != "当前项目":
    errors.append("smart_construction_core record context extension hook is not active")

result = {
    "guard": "project_context_selector_product_boundary_guard",
    "status": "FAIL" if errors else "PASS",
    "errors": errors,
    "selector": selector,
    "model": payload.get("model"),
    "enabled": payload.get("enabled"),
    "selected": payload.get("selected"),
    "operation_options": payload.get("operation_options"),
    "hook_payload": hook_payload,
}
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
if errors:
    raise SystemExit(1)
