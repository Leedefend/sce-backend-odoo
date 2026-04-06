# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Set

from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first


SERVER_ACTION_WINDOW_MAP: Dict[str, str] = {
    "smart_construction_core.action_exec_structure_entry": "smart_construction_core.action_exec_structure_wbs",
}

FILE_UPLOAD_ALLOWED_MODELS: Set[str] = {
    "project.project",
    "project.task",
}

FILE_DOWNLOAD_ALLOWED_MODELS: Set[str] = {
    "project.project",
    "project.task",
}

API_DATA_WRITE_ALLOWLIST: Dict[str, Set[str]] = {
    "project.project": {"name", "description", "date_start"},
    "project.task": {"name", "description", "date_deadline", "project_id"},
}

API_DATA_UNLINK_ALLOWED_MODELS: Set[str] = {
    "project.task",
    "res.company",
    "hr.department",
    "res.users",
}

MODEL_CODE_MAPPING: Dict[str, str] = {
    "project": "project.project",
    "task": "project.task",
}

CREATE_FIELD_FALLBACKS: Dict[str, Dict[str, Any]] = {
    "project.project": {
        "selection_defaults": {
            "privacy_visibility": "followers",
            "rating_status": "stage",
            "last_update_status": "to_define",
            "rating_status_period": "monthly",
        }
    }
}


def get_server_action_window_map(env) -> Dict[str, str]:
    mapping = dict(SERVER_ACTION_WINDOW_MAP)
    payload = call_extension_hook_first(env, "get_server_action_window_map_contributions", env)
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_text = str(key or "").strip()
            value_text = str(value or "").strip()
            if key_text and value_text:
                mapping[key_text] = value_text
    return mapping


def get_file_upload_allowed_models(env) -> Set[str]:
    models = set(FILE_UPLOAD_ALLOWED_MODELS)
    payload = call_extension_hook_first(env, "get_file_upload_allowed_model_contributions", env)
    if isinstance(payload, (list, tuple, set)):
        values = {str(item).strip() for item in payload if str(item).strip()}
        if values:
            models = values
    return models


def get_file_download_allowed_models(env) -> Set[str]:
    models = set(FILE_DOWNLOAD_ALLOWED_MODELS)
    payload = call_extension_hook_first(env, "get_file_download_allowed_model_contributions", env)
    if isinstance(payload, (list, tuple, set)):
        values = {str(item).strip() for item in payload if str(item).strip()}
        if values:
            models = values
    return models


def get_api_data_write_allowlist(env) -> Dict[str, Set[str]]:
    mapping: Dict[str, Set[str]] = {
        str(model_name): set(field_names)
        for model_name, field_names in API_DATA_WRITE_ALLOWLIST.items()
    }
    payload = call_extension_hook_first(env, "get_api_data_write_allowlist_contributions", env)
    if isinstance(payload, dict):
        override: Dict[str, Set[str]] = {}
        for model_name, fields in payload.items():
            model = str(model_name or "").strip()
            if not model:
                continue
            normalized = {str(item).strip() for item in (fields or []) if str(item).strip()}
            if normalized:
                override[model] = normalized
        if override:
            mapping = override
    return mapping


def get_api_data_unlink_allowed_models(env) -> Set[str]:
    models = set(API_DATA_UNLINK_ALLOWED_MODELS)
    payload = call_extension_hook_first(env, "get_api_data_unlink_allowed_model_contributions", env)
    if isinstance(payload, (list, tuple, set)):
        values = {str(item).strip() for item in payload if str(item).strip()}
        if values:
            models = values
    return models


def get_model_code_mapping(env) -> Dict[str, str]:
    mapping = dict(MODEL_CODE_MAPPING)
    payload = call_extension_hook_first(env, "get_model_code_mapping_contributions", env)
    if isinstance(payload, dict):
        for key, value in payload.items():
            k = str(key or "").strip()
            v = str(value or "").strip()
            if k and v:
                mapping[k] = v
    return mapping


def get_create_field_fallbacks(env, model_name: str) -> Dict[str, Any]:
    model = str(model_name or "").strip()
    fallback = dict(CREATE_FIELD_FALLBACKS.get(model, {}))
    payload = call_extension_hook_first(env, "get_create_field_fallback_contributions", env, model)
    if isinstance(payload, dict):
        fallback.update(payload)
    return fallback
