# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.extension_loader import call_extension_hook_first


def _require_extension_result(hook_name: str, value):
    if value is None:
        raise RuntimeError(f"missing extension hook result: {hook_name}")
    return value


def describe_project_capabilities(env, project):
    result = call_extension_hook_first(
        env,
        "smart_core_describe_project_capabilities",
        env,
        project,
    )
    return _require_extension_result("smart_core_describe_project_capabilities", result)


def build_portal_dashboard(env):
    result = call_extension_hook_first(
        env,
        "smart_core_build_portal_dashboard",
        env,
    )
    return _require_extension_result("smart_core_build_portal_dashboard", result)


def build_capability_matrix(env):
    result = call_extension_hook_first(
        env,
        "smart_core_build_capability_matrix",
        env,
    )
    return _require_extension_result("smart_core_build_capability_matrix", result)


def get_project_insight(env, record, scene):
    result = call_extension_hook_first(
        env,
        "smart_core_get_project_insight",
        env,
        record,
        scene,
    )
    return _require_extension_result("smart_core_get_project_insight", result)


def build_portal_execute_button_contract(env, model, res_id, method):
    result = call_extension_hook_first(
        env,
        "smart_core_build_portal_execute_button_contract",
        env,
        model,
        res_id,
        method,
    )
    return _require_extension_result(
        "smart_core_build_portal_execute_button_contract",
        result,
    )
