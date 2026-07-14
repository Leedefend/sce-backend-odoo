# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

SOURCE_KIND = "ui_contract_governance_projection"
SOURCE_AUTHORITIES = ("native_contract", "governance_rules", "legacy_industry_governance_profile")
NO_BUSINESS_FACT_AUTHORITY = True
LEGACY_INDUSTRY_GOVERNANCE_SOURCE_KIND = "legacy_industry_governance_profile"
LEGACY_USER_SURFACE_MODEL_POLICY_SOURCE_KIND = "legacy_user_surface_model_policy"
LEGACY_RECORD_CONTEXT_CLEAR_MODELS: set[str] = set()
LEGACY_DELETE_ONLY_MODELS = {"res.company", "hr.department", "res.users"}
_LEGACY_STANDARD_LIST_PROFILE_REGISTRY: list[dict[str, Any]] = []
_LEGACY_FIELD_PRESENTATION_REGISTRY: dict[tuple[str, str], dict[str, Any]] = {}
_LEGACY_PROJECT_FORM_GOVERNANCE_MODELS: set[str] = set()
_LEGACY_PROJECT_FORM_PROFILE_REGISTRY: dict[str, dict[str, Any]] = {}
_LEGACY_PROJECT_TASK_FORM_GOVERNANCE_MODELS: set[str] = set()
_LEGACY_PROJECT_KANBAN_GOVERNANCE_MODELS: set[str] = set()
_LEGACY_PROJECT_TASK_FORM_PROFILE_REGISTRY: dict[str, dict[str, Any]] = {}
_LEGACY_PROJECT_KANBAN_PROFILE_REGISTRY: dict[str, dict[str, Any]] = {}
_LEGACY_KANBAN_ROW_ACTION_REGISTRY: dict[str, list[dict[str, Any]]] = {}
_CAPABILITY_GROUP_PROFILE_REGISTRY: dict[str, dict[str, Any]] = {}
_SCENE_SEMANTIC_PROFILE_REGISTRY: list[dict[str, Any]] = []


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _safe_lower(value: Any) -> str:
    return _safe_text(value).lower()


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def _deep_clone_json_like(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _deep_clone_json_like(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deep_clone_json_like(v) for v in obj]
    return obj


def register_legacy_standard_list_profile(profile: dict[str, Any]) -> None:
    if not isinstance(profile, dict):
        return
    model_name = _safe_text(profile.get("model_name"))
    if not model_name:
        return
    normalized = {
        "model_name": model_name,
        "columns_order": [
            _safe_text(name)
            for name in (profile.get("columns_order") if isinstance(profile.get("columns_order"), list) else [])
            if _safe_text(name)
        ],
        "column_labels": {
            _safe_text(key): _safe_text(value)
            for key, value in (profile.get("column_labels") if isinstance(profile.get("column_labels"), dict) else {}).items()
            if _safe_text(key)
        },
        "row_primary": _safe_text(profile.get("row_primary")),
        "row_secondary": _safe_text(profile.get("row_secondary")),
        "status_field": _safe_text(profile.get("status_field")),
        "strict_columns": bool(profile.get("strict_columns")),
        "profile_key": _safe_text(profile.get("profile_key")),
        "signature_any": [
            _safe_text(item)
            for item in (profile.get("signature_any") if isinstance(profile.get("signature_any"), list) else [])
            if _safe_text(item)
        ],
    }
    if not normalized["columns_order"]:
        return
    dedupe_key = normalized["profile_key"] or normalized["model_name"]
    for index, existing in enumerate(_LEGACY_STANDARD_LIST_PROFILE_REGISTRY):
        existing_key = _safe_text(existing.get("profile_key")) or _safe_text(existing.get("model_name"))
        if existing_key == dedupe_key:
            _LEGACY_STANDARD_LIST_PROFILE_REGISTRY[index] = normalized
            return
    _LEGACY_STANDARD_LIST_PROFILE_REGISTRY.append(normalized)


def register_legacy_record_context_clear_model(model_name: str) -> None:
    model = _safe_text(model_name)
    if model:
        LEGACY_RECORD_CONTEXT_CLEAR_MODELS.add(model)


def register_legacy_delete_only_model(model_name: str) -> None:
    model = _safe_text(model_name)
    if model:
        LEGACY_DELETE_ONLY_MODELS.add(model)


def register_legacy_project_form_governance_model(model_name: str) -> None:
    model = _safe_text(model_name)
    if model:
        _LEGACY_PROJECT_FORM_GOVERNANCE_MODELS.add(model)


def register_legacy_project_form_profile(model_name: str, profile: dict[str, Any], *, default_max_fields: int) -> None:
    model = _safe_text(model_name)
    if not model or not isinstance(profile, dict):
        return
    primary_fields = [_safe_text(name) for name in (profile.get("primary_fields") or []) if _safe_text(name)]
    create_hidden_fields = [
        _safe_text(name)
        for name in (profile.get("create_hidden_fields") or [])
        if _safe_text(name)
    ]
    action_priorities = [
        _safe_text(name)
        for name in (profile.get("action_priorities") or [])
        if _safe_text(name)
    ]
    action_noise_markers = [
        _safe_lower(name)
        for name in (profile.get("action_noise_markers") or [])
        if _safe_text(name)
    ]
    search_noise_markers = [
        _safe_lower(name)
        for name in (profile.get("search_noise_markers") or [])
        if _safe_text(name)
    ]
    action_group_labels = {
        _safe_text(key): _safe_text(value)
        for key, value in _as_dict(profile.get("action_group_labels")).items()
        if _safe_text(key) and _safe_text(value)
    }
    _LEGACY_PROJECT_FORM_PROFILE_REGISTRY[model] = {
        "primary_fields": primary_fields,
        "create_hidden_fields": create_hidden_fields,
        "action_priorities": action_priorities,
        "action_noise_markers": action_noise_markers,
        "search_noise_markers": search_noise_markers,
        "action_group_labels": action_group_labels,
        "max_fields": int(profile.get("max_fields") or default_max_fields),
    }


def register_legacy_project_task_form_governance_model(model_name: str) -> None:
    model = _safe_text(model_name)
    if model:
        _LEGACY_PROJECT_TASK_FORM_GOVERNANCE_MODELS.add(model)


def register_legacy_project_task_form_profile(model_name: str, profile: dict[str, Any]) -> None:
    model = _safe_text(model_name)
    if not model or not isinstance(profile, dict):
        return
    fields = [_safe_text(name) for name in (profile.get("fields") or []) if _safe_text(name)]
    if not fields:
        return
    labels = {
        _safe_text(key): _safe_text(value)
        for key, value in _as_dict(profile.get("field_labels")).items()
        if _safe_text(key) and _safe_text(value)
    }
    description_fields = [
        _safe_text(name)
        for name in (profile.get("description_fields") or [])
        if _safe_text(name)
    ]
    _LEGACY_PROJECT_TASK_FORM_PROFILE_REGISTRY[model] = {
        "fields": fields,
        "field_labels": labels,
        "core_group_label": _safe_text(profile.get("core_group_label")) or "基础信息",
        "description_group_label": _safe_text(profile.get("description_group_label")) or "说明",
        "description_fields": description_fields,
    }


def register_legacy_project_kanban_governance_model(model_name: str) -> None:
    model = _safe_text(model_name)
    if model:
        _LEGACY_PROJECT_KANBAN_GOVERNANCE_MODELS.add(model)


def register_legacy_project_kanban_profile(model_name: str, profile: dict[str, Any]) -> None:
    model = _safe_text(model_name)
    if not model or not isinstance(profile, dict):
        return

    def _field_list(key: str) -> list[str]:
        return [_safe_text(name) for name in (profile.get(key) or []) if _safe_text(name)]

    _LEGACY_PROJECT_KANBAN_PROFILE_REGISTRY[model] = {
        "primary_fields": _field_list("primary_fields"),
        "secondary_fields": _field_list("secondary_fields"),
        "status_fields": _field_list("status_fields"),
        "title_field": _safe_text(profile.get("title_field")),
        "max_meta": int(profile.get("max_meta") or 4),
    }


def register_legacy_kanban_row_action(model_name: str, action: dict[str, Any]) -> None:
    model = _safe_text(model_name)
    if not model or not isinstance(action, dict):
        return
    key = _safe_text(action.get("key") or action.get("name"))
    if not key:
        return
    row = _deep_clone_json_like(action)
    row["key"] = key
    row.setdefault("name", key)
    _LEGACY_KANBAN_ROW_ACTION_REGISTRY.setdefault(model, [])
    existing = _LEGACY_KANBAN_ROW_ACTION_REGISTRY[model]
    existing[:] = [item for item in existing if _safe_text(item.get("key") or item.get("name")) != key]
    existing.append(row)


def register_legacy_field_presentation(model_name: str, field_name: str, profile: dict[str, Any]) -> None:
    model = _safe_text(model_name)
    field = _safe_text(field_name)
    if not model or not field or not isinstance(profile, dict):
        return
    normalized = {
        "label": _safe_text(profile.get("label")),
        "widget": _safe_text(profile.get("widget")),
        "cell_role": _safe_text(profile.get("cell_role")),
        "mutation": _deep_clone_json_like(profile.get("mutation")) if isinstance(profile.get("mutation"), dict) else {},
    }
    _LEGACY_FIELD_PRESENTATION_REGISTRY[(model, field)] = normalized


def register_capability_group_profile(group_key: str, profile: dict[str, Any]) -> None:
    key = _safe_text(group_key)
    if not key or not isinstance(profile, dict):
        return
    _CAPABILITY_GROUP_PROFILE_REGISTRY[key] = {
        "label": _safe_text(profile.get("label"), key),
        "icon": _safe_text(profile.get("icon")),
        "key_prefixes": tuple(
            _safe_lower(item)
            for item in (profile.get("key_prefixes") if isinstance(profile.get("key_prefixes"), list) else [])
            if _safe_text(item)
        ),
    }


def register_scene_semantic_profile(profile: dict[str, Any]) -> None:
    if not isinstance(profile, dict):
        return
    purpose = _safe_text(profile.get("purpose"))
    if not purpose:
        return
    normalized = {
        "purpose": purpose,
        "code_prefixes": tuple(
            _safe_lower(item)
            for item in (profile.get("code_prefixes") if isinstance(profile.get("code_prefixes"), list) else [])
            if _safe_text(item)
        ),
        "code_contains": tuple(
            _safe_lower(item)
            for item in (profile.get("code_contains") if isinstance(profile.get("code_contains"), list) else [])
            if _safe_text(item)
        ),
    }
    if not normalized["code_prefixes"] and not normalized["code_contains"]:
        return
    _SCENE_SEMANTIC_PROFILE_REGISTRY.append(normalized)

CONTRACT_MODES = {"user", "hud"}
CONTRACT_SURFACES = {"user", "native", "hud"}
_NON_HUD_STRIP_KEYS = {
    "diagnostic",
    "scene_diagnostics",
    "scene_channel_selector",
    "scene_channel_source_ref",
}
_USER_MODE_STRIP_KEYS = {
    "action_xmlid",
    "menu_xmlid",
    "scene_key",
    "res_id",
    "id",
}
_USER_CAPABILITY_KEYS = (
    "key",
    "name",
    "group_key",
    "group_label",
    "group_icon",
    "group_sequence",
    "ui_label",
    "ui_hint",
    "intent",
    "status",
    "state",
    "capability_state",
    "capability_state_reason",
    "reason",
    "reason_code",
    "delivery_level",
    "target_scene_key",
    "entry_kind",
    "version",
    "tags",
    "default_payload",
)
_USER_SCENE_KEYS = (
    "code",
    "key",
    "name",
    "title",
    "label",
    "icon",
    "route",
    "target",
    "layout",
    "tiles",
    "capabilities",
    "required_capabilities",
    "breadcrumbs",
    "list_profile",
    "scene_meta",
    "filters",
    "default_sort",
    "access",
    "status",
    "state",
    "version",
    "tags",
)
_USER_SCENE_TARGET_KEYS = (
    "route",
    "action_id",
    "menu_id",
    "model",
    "view_mode",
    "view_type",
    "record_id",
)
_USER_SCENE_TILE_KEYS = (
    "key",
    "title",
    "subtitle",
    "icon",
    "status",
    "state",
    "capability_state",
    "capability_state_reason",
    "reason",
    "reason_code",
    "route",
    "intent",
    "payload",
    "capabilities",
    "required_capabilities",
    "requiredCapabilities",
    "allowed",
    "tags",
)
_USER_SCENE_ACCESS_KEYS = (
    "allowed",
    "state",
    "reason_code",
    "reason",
    "required_capabilities",
    "suggested_action",
)

_PROJECT_FORM_PAGE_PRESERVE_FIELDS = {
    "access_instruction_message",
    "alias_id",
    "alias_email",
    "alias_name",
    "alias_domain_id",
    "alias_contact",
    "task_ids",
    "collaborator_ids",
}
_BUSINESS_DETAIL_RELATION_FIELDS = {
    "line_ids",
    "boq_line_ids",
    "ledger_line_ids",
    "outflow_line_ids",
    "receipt_invoice_line_ids",
}
_TECHNICAL_RELATION_FIELD_PREFIXES = (
    "message_",
    "activity_",
    "rating_",
    "website_",
    "review",
    "rejected",
    "validated",
)
_PROJECT_FORM_FIELD_MAX = 25
_PROJECT_FORM_HEADER_ACTION_MAX = 3
_PROJECT_FORM_SMART_ACTION_MAX = 4
_ENTERPRISE_COMPANY_FORM_FIELDS = [
    "name",
    "sc_short_name",
    "sc_credit_code",
    "sc_contact_phone",
    "sc_address",
    "sc_is_active",
]
_ENTERPRISE_COMPANY_FIELD_LABELS = {
    "name": "公司名称",
    "sc_short_name": "公司简称",
    "sc_credit_code": "统一社会信用代码",
    "sc_contact_phone": "联系电话",
    "sc_address": "地址",
    "sc_is_active": "启用",
}
_ENTERPRISE_DEPARTMENT_FORM_FIELDS = [
    "name",
    "parent_id",
    "sc_manager_user_id",
    "company_id",
    "sc_is_active",
]
_ENTERPRISE_DEPARTMENT_FIELD_LABELS = {
    "name": "部门名称",
    "parent_id": "上级部门",
    "sc_manager_user_id": "部门负责人",
    "company_id": "所属公司",
    "sc_is_active": "启用",
}
_ENTERPRISE_USER_FORM_FIELDS = [
    "name",
    "login",
    "password",
    "phone",
    "email",
    "active",
    "company_id",
    "sc_department_id",
    "sc_manager_user_id",
    "sc_role_profile",
    "sc_role_effective",
    "sc_role_landing_label",
    "sc_user_role_group_ids",
]
_ENTERPRISE_USER_FIELD_LABELS = {
    "name": "姓名",
    "login": "用户名",
    "password": "重置密码",
    "phone": "手机号",
    "email": "邮箱",
    "active": "启用",
    "company_id": "所属公司",
    "sc_department_id": "所属部门",
    "sc_manager_user_id": "直属上级",
    "sc_role_profile": "产品角色",
    "sc_role_effective": "当前生效角色",
    "sc_role_landing_label": "默认首页",
    "sc_user_role_group_ids": "业务角色组",
}
_PROJECT_FORM_ACTION_GROUP_LIMIT = 5
_PROJECT_FORM_DEFAULT_ACTION_GROUP_LABELS = {
    "basic": "Primary",
    "workflow": "Workflow",
    "drilldown": "Open",
    "other": "More",
}
_FORM_CORE_FIELD_MAX = 8
_FORM_ACTION_PRIMARY_KEYWORDS = (
    "提交",
    "保存",
    "创建",
    "确认",
    "进入下一阶段",
    "approve",
    "submit",
    "save",
    "create",
    "confirm",
)
_FORM_ACTION_READONLY_KEYWORDS = (
    "查看",
    "打开",
    "open",
    "view",
)
_FORM_PRIMARY_DISABLED_REASON = "请先完成必填字段后再执行主操作"
_FORM_DISABLED_REASON_CAPABILITY = "缺少执行该操作所需能力"
_FORM_DISABLED_REASON_LIFECYCLE = "当前生命周期状态不允许该操作"
_FORM_DISABLED_REASON_GROUP = "当前角色组不满足执行条件"
_FORM_DISABLED_REASON_ROLE = "当前角色不满足执行条件"
_FORM_SCENE_PROFILE_DEFAULT = "generic.form"
_FORM_SCENE_PROFILE_PROJECT = "project.form"
_CAPABILITY_GROUP_DEFAULTS = {
    "governance": {"label": "Governance", "icon": "shield"},
    "analytics": {"label": "Analytics", "icon": "chart"},
    "others": {"label": "Other", "icon": "grid"},
}
_CONTRACT_KEY_CANONICAL_MAP = {
    "requiredCapabilities": "required_capabilities",
    "groupsXmlids": "groups_xmlids",
    "actionId": "action_id",
    "menuId": "menu_id",
    "viewType": "view_type",
    "recordId": "record_id",
    "reasonCode": "reason_code",
    "deliveryLevel": "delivery_level",
    "targetSceneKey": "target_scene_key",
    "entryKind": "entry_kind",
    "capabilityState": "capability_state",
    "capabilityStateReason": "capability_state_reason",
    "defaultPayload": "default_payload",
    "groupKey": "group_key",
    "groupLabel": "group_label",
    "groupIcon": "group_icon",
    "groupSequence": "group_sequence",
}
_TIER_REVIEW_LIST_NAV_ACTION_PREFIXES = ()
_BUSINESS_FIELD_LABEL_OVERRIDES = {
    "display_name": "名称",
}
_USER_SURFACE_ACTION_GROUP_LABELS = {
    "basic": "Primary",
    "workflow": "Workflow",
    "drilldown": "Open",
    "other": "More",
}
_USER_SURFACE_NOISE_MARKERS = (
    "demo",
    "showcase",
    "smoke",
    "internal",
    "ir_cron",
    "project_update_all_action",
)
_USER_SURFACE_FILTER_MAX = 8
_USER_SURFACE_ACTION_MAX = 8
_USER_SURFACE_PRIMARY_FILTER_MAX = 5
_USER_SURFACE_PRIMARY_ACTION_MAX = 4
_RENDER_PROFILE_CREATE = "create"
_RENDER_PROFILE_EDIT = "edit"
_RENDER_PROFILE_READONLY = "readonly"
_RENDER_PROFILES = {
    _RENDER_PROFILE_CREATE,
    _RENDER_PROFILE_EDIT,
    _RENDER_PROFILE_READONLY,
}
