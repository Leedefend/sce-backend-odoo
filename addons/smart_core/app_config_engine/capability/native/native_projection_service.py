# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .menu_adapter import project_menu_capabilities
from .action_adapter import project_window_action_capabilities
from .model_adapter import project_model_access_capabilities
from .server_action_adapter import project_server_action_capabilities
from .report_adapter import project_report_action_capabilities
from .view_binding_adapter import project_view_binding_capabilities


def load_native_capability_rows(env, user=None) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    rows: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    try:
        rows.extend(project_menu_capabilities(env, user=user))
    except Exception as exc:
        errors.append({"module": "smart_core.native.menu", "stage": "projection", "error": str(exc)})

    try:
        rows.extend(project_window_action_capabilities(env, user=user))
    except Exception as exc:
        errors.append({"module": "smart_core.native.action", "stage": "projection", "error": str(exc)})

    try:
        rows.extend(project_model_access_capabilities(env, user=user))
    except Exception as exc:
        errors.append({"module": "smart_core.native.model", "stage": "projection", "error": str(exc)})

    try:
        rows.extend(project_server_action_capabilities(env, user=user))
    except Exception as exc:
        errors.append({"module": "smart_core.native.server_action", "stage": "projection", "error": str(exc)})

    try:
        rows.extend(project_report_action_capabilities(env, user=user))
    except Exception as exc:
        errors.append({"module": "smart_core.native.report", "stage": "projection", "error": str(exc)})

    try:
        rows.extend(project_view_binding_capabilities(env, user=user))
    except Exception as exc:
        errors.append({"module": "smart_core.native.view_binding", "stage": "projection", "error": str(exc)})

    return rows, errors
