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
