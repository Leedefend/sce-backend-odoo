# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

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

_PROJECT_FORM_PRIMARY_FIELDS = [
    "name",
    "project_type_id",
    "project_category_id",
    "lifecycle_state",
    "stage_id",
    "manager_id",
    "user_id",
    "owner_id",
    "company_id",
    "start_date",
    "end_date",
    "contract_no",
    "budget_total",
    "location",
]
_PROJECT_FORM_CREATE_HIDDEN_FIELDS = {
    "project_code",
    "code",
    "company_id",
    "analytic_account_id",
    "lifecycle_state",
    "stage_id",
    "last_update_status",
    "privacy_visibility",
    "rating_status",
    "rating_status_period",
}
_PROJECT_FORM_FIELD_MAX = 25
_PROJECT_FORM_HEADER_ACTION_MAX = 3
_PROJECT_FORM_SMART_ACTION_MAX = 4
_PROJECT_FORM_ACTION_DEMOTE_KEYWORDS = {
    "设置阶段",
    "评分",
    "cron",
    "ir_cron",
    "演示",
    "showcase",
}
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
    "active",
    "company_id",
    "sc_department_id",
    "sc_manager_user_id",
    "sc_role_profile",
    "sc_role_effective",
    "sc_role_landing_label",
]
_ENTERPRISE_USER_FIELD_LABELS = {
    "name": "姓名",
    "login": "登录账号",
    "password": "初始密码",
    "phone": "手机号",
    "active": "启用",
    "company_id": "所属公司",
    "sc_department_id": "所属部门",
    "sc_manager_user_id": "直属上级",
    "sc_role_profile": "产品角色",
    "sc_role_effective": "当前生效角色",
    "sc_role_landing_label": "默认首页",
}
_PROJECT_FORM_ACTION_PRIORITIES = (
    "提交",
    "进入下一阶段",
    "创建项目",
    "保存",
    "查看任务",
)
_PROJECT_FORM_ACTION_GROUP_LIMIT = 5
_PROJECT_FORM_ACTION_GROUP_LABELS = {
    "basic": "基础操作",
    "workflow": "流程推进",
    "drilldown": "业务查看",
    "other": "更多操作",
}
_PROJECT_KANBAN_PRIMARY_FIELDS = [
    "name",
    "project_code",
    "manager_id",
]
_PROJECT_KANBAN_SECONDARY_FIELDS = [
    "stage_id",
    "lifecycle_state",
    "end_date",
    "budget_total",
]
_PROJECT_KANBAN_STATUS_FIELDS = [
    "lifecycle_state",
    "stage_id",
]
_PROJECT_TASK_FORM_FIELDS = [
    "name",
    "project_id",
    "stage_id",
    "sc_state",
    "user_ids",
    "date_deadline",
    "priority",
    "description",
]
_PROJECT_TASK_FIELD_LABELS = {
    "name": "任务名称",
    "project_id": "所属项目",
    "stage_id": "当前阶段",
    "sc_state": "执行状态",
    "user_ids": "执行人",
    "date_deadline": "截止日期",
    "priority": "优先级",
    "description": "执行说明",
}
_PROJECT_LIST_COLUMNS = [
    "name",
    "user_id",
    "partner_id",
    "stage_id",
    "lifecycle_state",
    "date_start",
    "date",
]
_PROJECT_LIST_COLUMN_LABELS = {
    "name": "项目名称",
    "user_id": "项目经理",
    "partner_id": "业主单位",
    "stage_id": "当前阶段",
    "lifecycle_state": "项目状态",
    "date_start": "开始日期",
    "date": "结束日期",
}
_PROJECT_TASK_LIST_COLUMNS = [
    "name",
    "project_id",
    "user_ids",
    "stage_id",
    "sc_state",
    "date_deadline",
    "priority",
]
_PROJECT_TASK_LIST_COLUMN_LABELS = {
    "name": "任务名称",
    "project_id": "所属项目",
    "user_ids": "执行人",
    "stage_id": "当前阶段",
    "sc_state": "执行状态",
    "date_deadline": "截止日期",
    "priority": "优先级",
}
_USER_SURFACE_ACTION_GROUP_LABELS = {
    "basic": "基础操作",
    "workflow": "流程推进",
    "drilldown": "业务查看",
    "other": "更多操作",
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


def _inject_enterprise_form_governance(data: dict, *, next_action_key: str = "", next_action_label: str = "") -> None:
    governance = _as_dict(data.get("form_governance"))
    governance.update(
        {
            "surface": "enterprise_enablement",
            "hide_workflow": True,
            "hide_search_filters": True,
            "hide_body_actions": True,
            "suppress_contract_header_actions": True,
        }
    )
    if _safe_text(next_action_key) and _safe_text(next_action_label):
        governance["next_action"] = {
            "step_key": _safe_text(next_action_key),
            "label": _safe_text(next_action_label),
        }
    else:
        governance.pop("next_action", None)
    data["form_governance"] = governance
_FORM_PRIMARY_DISABLED_REASON = "请先完成必填字段后再执行主操作"
_FORM_DISABLED_REASON_CAPABILITY = "缺少执行该操作所需能力"


def _governance_primary_model(data: dict) -> str:
    governance = _as_dict(data.get("governance"))
    head = _as_dict(data.get("head"))
    permissions = _as_dict(data.get("permissions"))
    return _safe_text(
        governance.get("primary_model")
        or data.get("governance_primary_model")
        or head.get("model")
        or data.get("model")
        or permissions.get("model")
    )
_FORM_DISABLED_REASON_LIFECYCLE = "当前生命周期状态不允许该操作"
_FORM_DISABLED_REASON_GROUP = "当前角色组不满足执行条件"
_FORM_DISABLED_REASON_ROLE = "当前角色不满足执行条件"
_FORM_SCENE_PROFILE_DEFAULT = "generic.form"
_FORM_SCENE_PROFILE_PROJECT = "project.form"

_CAPABILITY_GROUP_DEFAULTS = {
    "project_management": {"label": "项目管理", "icon": "briefcase"},
    "contract_management": {"label": "合同管理", "icon": "file-text"},
    "cost_management": {"label": "成本管理", "icon": "calculator"},
    "finance_management": {"label": "财务管理", "icon": "wallet"},
    "material_management": {"label": "物资管理", "icon": "boxes"},
    "governance": {"label": "治理配置", "icon": "shield"},
    "analytics": {"label": "经营分析", "icon": "chart"},
    "others": {"label": "其他能力", "icon": "grid"},
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

_DOMAIN_OVERRIDE_REGISTRY: list[dict[str, Any]] = []


def is_truthy(value: Any) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def resolve_contract_mode(params: dict | None) -> str:
    params = params if isinstance(params, dict) else {}
    raw_mode = str(params.get("contract_mode") or "").strip().lower()
    if raw_mode in CONTRACT_MODES:
        return raw_mode
    if is_truthy(params.get("hud")) or is_truthy(params.get("debug_hud")):
        return "hud"
    return "user"


def resolve_contract_surface(params: dict | None, contract_mode: str | None = None) -> str:
    params = params if isinstance(params, dict) else {}
    raw_surface = str(params.get("contract_surface") or params.get("surface") or "").strip().lower()
    if raw_surface in CONTRACT_SURFACES:
        return raw_surface
    mode = str(contract_mode or "").strip().lower()
    if mode == "hud":
        return "hud"
    return "user"


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _parse_tags(raw: Any) -> set[str]:
    if isinstance(raw, list):
        items = raw
    else:
        items = str(raw or "").split(",")
    out: set[str] = set()
    for item in items:
        val = _safe_text(item).lower()
        if val:
            out.add(val)
    return out


def _contains_demo_marker(value: Any) -> bool:
    text = _safe_text(value).lower()
    if not text:
        return False
    return any(marker in text for marker in ("demo", "showcase", "domain_demo"))


def _has_demo_semantics(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    if item.get("is_demo") is True:
        return True
    tags = _parse_tags(item.get("tags"))
    return "demo" in tags or "showcase" in tags


def _normalized_tags_for_item(item: dict) -> list[str]:
    tags = _parse_tags(item.get("tags"))
    key = _safe_text(item.get("key")).lower()
    code = _safe_text(item.get("code")).lower()
    name = _safe_text(item.get("name")).lower()
    target = item.get("target") if isinstance(item.get("target"), dict) else {}
    target_text = " ".join(
        [
            _safe_text(target.get("menu_xmlid")).lower(),
            _safe_text(target.get("action_xmlid")).lower(),
            _safe_text(target.get("route")).lower(),
        ]
    ).strip()
    if item.get("is_test") or item.get("smoke_test"):
        tags.update({"internal", "smoke"})
    if "smoke" in key or "smoke" in code or "smoke" in name:
        tags.update({"internal", "smoke"})
    if "internal" in key or "internal" in code or "internal" in name:
        tags.add("internal")
    combined = f"{key} {code} {name} {target_text}"
    if "showcase" in combined or "demo" in combined or "domain_demo" in combined:
        tags.add("demo")
    return sorted(tags)


def is_internal_or_smoke(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    if item.get("is_internal") is True or item.get("is_smoke") is True:
        return True
    tags = _parse_tags(item.get("tags"))
    if "internal" in tags or "smoke" in tags or "demo" in tags or "showcase" in tags:
        return True
    return bool(item.get("is_test") or item.get("smoke_test"))


def normalize_capabilities(capabilities: list) -> list[dict]:
    def _normalize_capability_status(value: Any) -> str:
        status = _safe_text(value).lower()
        if status in {"ga", "beta", "alpha"}:
            return status
        if status in {"active", "enabled", "ready"}:
            return "ga"
        if status in {"preview", "pilot", "pending"}:
            return "beta"
        if status in {"disabled", "inactive", "blocked"}:
            return "alpha"
        return "ga"

    def _infer_capability_group_key(capability_key: str) -> str:
        key = _safe_text(capability_key).lower()
        if not key:
            return "others"
        if key.startswith(("project.", "scene.project", "wbs.", "progress.", "tender.")):
            return "project_management"
        if key.startswith(("contract.", "settlement.")):
            return "contract_management"
        if key.startswith(("cost.", "budget.", "boq.")):
            return "cost_management"
        if key.startswith(("finance.", "payment.", "treasury.")):
            return "finance_management"
        if key.startswith(("material.", "purchase.", "stock.")):
            return "material_management"
        if key.startswith(("usage.", "report.", "dashboard.", "analytics.")):
            return "analytics"
        if key.startswith(("scene.", "portal.", "config.", "permission.", "subscription.", "pack.")):
            return "governance"
        return "others"

    def _normalize_capability_state(value: Any) -> str:
        state = _safe_text(value).lower()
        if state in {"allow", "readonly", "deny", "pending", "coming_soon"}:
            return state
        return ""

    def _derive_capability_state(status: str, state: str, tags: list[str], reason_code: str) -> str:
        if state:
            return state
        tag_set = {str(tag or "").strip().lower() for tag in tags if str(tag or "").strip()}
        if "readonly" in tag_set or "read_only" in tag_set:
            return "readonly"
        if reason_code in {"PERMISSION_DENIED", "ACCESS_DENIED", "FORBIDDEN"}:
            return "deny"
        if status == "alpha":
            return "coming_soon"
        if status == "beta":
            return "pending"
        return "allow"

    def _extract_scene_key_from_route(route: Any) -> str:
        route_text = _safe_text(route)
        if not route_text:
            return ""
        marker = "scene="
        idx = route_text.find(marker)
        if idx < 0:
            return ""
        tail = route_text[idx + len(marker):]
        scene = tail.split("&", 1)[0].strip()
        return scene

    def _derive_target_scene_key(item: dict) -> str:
        direct = _safe_text(item.get("target_scene_key"))
        if direct:
            return direct
        payload = item.get("default_payload")
        if isinstance(payload, dict):
            payload_scene = _safe_text(payload.get("scene_key"))
            if payload_scene:
                return payload_scene
            route_scene = _extract_scene_key_from_route(payload.get("route"))
            if route_scene:
                return route_scene
        return ""

    def _derive_entry_kind(item: dict, target_scene_key: str) -> str:
        explicit = _safe_text(item.get("entry_kind")).lower()
        if explicit in {"exclusive", "alias"}:
            return explicit
        payload = item.get("default_payload") if isinstance(item.get("default_payload"), dict) else {}
        has_direct_entry = bool(payload.get("action_id") or payload.get("menu_id") or payload.get("route"))
        if target_scene_key and has_direct_entry:
            return "exclusive"
        return "alias"

    def _derive_delivery_level(item: dict, target_scene_key: str, entry_kind: str) -> str:
        explicit = _safe_text(item.get("delivery_level")).lower()
        if explicit in {"exclusive", "shared", "placeholder"}:
            return explicit
        payload = item.get("default_payload") if isinstance(item.get("default_payload"), dict) else {}
        has_entry = bool(target_scene_key or payload.get("route") or payload.get("action_id") or payload.get("menu_id"))
        if not has_entry:
            return "placeholder"
        if entry_kind == "exclusive":
            return "exclusive"
        return "shared"

    out: list[dict] = []
    for cap in capabilities or []:
        if not isinstance(cap, dict):
            continue
        item = dict(cap)
        item["key"] = _safe_text(item.get("key"))
        item["name"] = _safe_text(item.get("name"), item.get("key") or "未命名能力")
        item["ui_label"] = _safe_text(item.get("ui_label"), item.get("name") or item.get("key") or "未命名能力")
        item["status"] = _normalize_capability_status(item.get("status"))
        item["group_key"] = _safe_text(item.get("group_key"), _infer_capability_group_key(item.get("key")))
        group_meta = _CAPABILITY_GROUP_DEFAULTS.get(item["group_key"], _CAPABILITY_GROUP_DEFAULTS["others"])
        item["group_label"] = _safe_text(item.get("group_label"), group_meta.get("label") or item["group_key"])
        item["group_icon"] = _safe_text(item.get("group_icon"), group_meta.get("icon") or "")
        try:
            item["group_sequence"] = int(item.get("group_sequence") or 0)
        except Exception:
            item["group_sequence"] = 0
        item["tags"] = _normalized_tags_for_item(item)
        state = _normalize_capability_state(item.get("capability_state"))
        reason_code = _safe_text(item.get("reason_code")).upper()
        item["capability_state"] = _derive_capability_state(
            status=item["status"],
            state=state,
            tags=item["tags"],
            reason_code=reason_code,
        )
        item["state"] = _safe_text(item.get("state")).upper()
        if item["state"] not in {"READY", "LOCKED", "PREVIEW"}:
            if item["capability_state"] in {"deny"}:
                item["state"] = "LOCKED"
            elif item["capability_state"] in {"pending", "coming_soon"}:
                item["state"] = "PREVIEW"
            else:
                item["state"] = "READY"
        reason = _safe_text(item.get("capability_state_reason"))
        if not reason:
            if item["capability_state"] == "readonly":
                reason = "当前能力为只读模式"
            elif item["capability_state"] == "pending":
                reason = "能力处于试运行阶段"
            elif item["capability_state"] == "coming_soon":
                reason = "能力尚在建设中，即将开放"
        item["capability_state_reason"] = reason
        target_scene_key = _derive_target_scene_key(item)
        item["target_scene_key"] = target_scene_key
        item["entry_kind"] = _derive_entry_kind(item, target_scene_key)
        item["delivery_level"] = _derive_delivery_level(item, target_scene_key, item["entry_kind"])
        out.append(item)
    return out


def _strip_user_mode_fields(obj: Any) -> Any:
    if isinstance(obj, list):
        return [_strip_user_mode_fields(item) for item in obj]
    if not isinstance(obj, dict):
        return obj
    out: dict[str, Any] = {}
    for key, value in obj.items():
        if str(key or "").strip() in _USER_MODE_STRIP_KEYS:
            continue
        out[key] = _strip_user_mode_fields(value)
    return out


def _pick_fields(raw: dict, allowed_keys: tuple[str, ...] | list[str]) -> dict:
    out: dict[str, Any] = {}
    for key in allowed_keys:
        if key in raw:
            out[key] = raw.get(key)
    return out


def _sanitize_capability_for_user(item: dict) -> dict:
    cap = _pick_fields(dict(item), _USER_CAPABILITY_KEYS)
    payload = cap.get("default_payload")
    if isinstance(payload, dict):
        cap["default_payload"] = _strip_user_mode_fields(payload)
    return cap


def _sanitize_scene_for_user(item: dict) -> dict:
    scene = _pick_fields(dict(item), _USER_SCENE_KEYS)
    scene = _strip_user_mode_fields(scene)
    scene["code"] = _safe_text(scene.get("code") or scene.get("key"))
    scene["key"] = _safe_text(scene.get("key"), scene.get("code"))
    scene["name"] = _safe_text(scene.get("name"), scene.get("code") or "未命名场景")
    target = scene.get("target")
    if isinstance(target, dict):
        scene["target"] = _strip_user_mode_fields(_pick_fields(target, _USER_SCENE_TARGET_KEYS))
    access = scene.get("access")
    if isinstance(access, dict):
        scene["access"] = _strip_user_mode_fields(_pick_fields(access, _USER_SCENE_ACCESS_KEYS))
    tiles = scene.get("tiles")
    if isinstance(tiles, list):
        cleaned_tiles = []
        for tile in tiles:
            if not isinstance(tile, dict):
                continue
            cleaned_tiles.append(_strip_user_mode_fields(_pick_fields(tile, _USER_SCENE_TILE_KEYS)))
        scene["tiles"] = cleaned_tiles
    scene["tags"] = _normalized_tags_for_item(scene)
    return scene


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def _safe_lower(value: Any) -> str:
    return _safe_text(value).lower()


def _is_numeric_token(value: Any) -> bool:
    text = _safe_text(value)
    return bool(text) and text.isdigit()


def _contains_noise_marker(*values: Any) -> bool:
    merged = " ".join(_safe_lower(item) for item in values if _safe_text(item))
    if not merged:
        return False
    return any(marker in merged for marker in _USER_SURFACE_NOISE_MARKERS)


def _is_noisy_filter_row(row: dict) -> bool:
    key = _safe_text(row.get("key"))
    label = _safe_text(row.get("label") or key)
    if not key or not label:
        return True
    if _is_numeric_token(key) or _is_numeric_token(label):
        return True
    return _contains_noise_marker(key, label, row.get("domain_raw"), row.get("context_raw"))


def _sanitize_user_search_filters(data: dict) -> None:
    search = _as_dict(data.get("search"))
    rows = search.get("filters")
    if not isinstance(rows, list):
        return
    out: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        if _is_noisy_filter_row(row):
            continue
        key = _safe_text(row.get("key"))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(row)
        if len(out) >= _USER_SURFACE_FILTER_MAX:
            break
    search["filters"] = out
    data["search"] = search


def _is_noisy_action_row(row: dict) -> bool:
    key = _safe_text(row.get("key"))
    label = _safe_text(row.get("label") or key)
    if not key or not label:
        return True
    if _is_numeric_token(key) or _is_numeric_token(label):
        return True
    return _contains_noise_marker(key, label, row.get("name"), row.get("xml_id"))


def _classify_user_surface_action_group(action: dict) -> str:
    key = _safe_lower(action.get("key"))
    label = _safe_lower(action.get("label"))
    merged = f"{key} {label}"
    if any(marker in merged for marker in ("提交", "审批", "transition", "workflow", "lifecycle", "阶段")):
        return "workflow"
    if any(marker in merged for marker in ("查看", "open", "dashboard", "看板", "列表", "台账")):
        return "drilldown"
    if any(marker in merged for marker in ("创建", "保存", "新增", "submit", "create", "save")):
        return "basic"
    return "other"


def _build_user_surface_action_groups(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {"basic": [], "workflow": [], "drilldown": [], "other": []}
    for row in rows:
        if not isinstance(row, dict):
            continue
        grouped.setdefault(_classify_user_surface_action_group(row), []).append(row)
    result: list[dict] = []
    for key in ("basic", "workflow", "drilldown", "other"):
        actions = grouped.get(key) or []
        if not actions:
            continue
        primary = actions[:_PROJECT_FORM_ACTION_GROUP_LIMIT]
        overflow = actions[_PROJECT_FORM_ACTION_GROUP_LIMIT:]
        result.append(
            {
                "key": key,
                "label": _USER_SURFACE_ACTION_GROUP_LABELS.get(key, key),
                "actions": primary,
                "overflow_actions": overflow,
                "overflow_count": len(overflow),
            }
        )
    return result


def _sanitize_user_action_rows(rows: Any, max_count: int = _USER_SURFACE_ACTION_MAX) -> list[dict]:
    if not isinstance(rows, list):
        return []
    out: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        if _is_noisy_action_row(row):
            continue
        key = _safe_text(row.get("key"))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(row)
        if len(out) >= max_count:
            break
    return out


def _apply_user_surface_noise_reduction(data: dict) -> None:
    _sanitize_user_search_filters(data)
    action_rows: list[dict] = []
    if isinstance(data.get("buttons"), list):
        data["buttons"] = _sanitize_user_action_rows(data.get("buttons"))
        action_rows.extend(data["buttons"])
    toolbar = _as_dict(data.get("toolbar"))
    if toolbar:
        for section in ("header", "sidebar", "footer"):
            if isinstance(toolbar.get(section), list):
                toolbar[section] = _sanitize_user_action_rows(toolbar.get(section), max_count=4)
                action_rows.extend(toolbar[section])
        data["toolbar"] = toolbar
    if action_rows and not isinstance(data.get("action_groups"), list):
        data["action_groups"] = _build_user_surface_action_groups(action_rows)


def _apply_user_surface_policies(data: dict) -> None:
    head = _as_dict(data.get("head"))
    view_type = _safe_lower(head.get("view_type") or data.get("view_type"))
    model = _safe_text(head.get("model") or data.get("model"))
    filters_primary_max = _USER_SURFACE_PRIMARY_FILTER_MAX
    actions_primary_max = _USER_SURFACE_PRIMARY_ACTION_MAX
    if view_type in {"form"}:
        filters_primary_max = 0
        actions_primary_max = 3
    primary_model = _governance_primary_model(data)
    if model and primary_model and model == primary_model:
        filters_primary_max = min(filters_primary_max, 4)
        actions_primary_max = min(actions_primary_max, 3)
    data["surface_policies"] = {
        "filters_primary_max": filters_primary_max,
        "actions_primary_max": actions_primary_max,
        "filters_max": _USER_SURFACE_FILTER_MAX,
        "actions_max": _USER_SURFACE_ACTION_MAX,
    }


def _normalize_scene_list_profile(item: dict) -> dict:
    raw = item.get("list_profile")
    profile = dict(raw) if isinstance(raw, dict) else {}
    columns = profile.get("columns") if isinstance(profile.get("columns"), list) else []
    hidden = profile.get("hidden_columns") if isinstance(profile.get("hidden_columns"), list) else []
    row_primary = _safe_text(profile.get("row_primary"))
    row_secondary = _safe_text(profile.get("row_secondary"))
    primary_field = _safe_text(profile.get("primary_field"), row_primary or (columns[0] if columns else "name"))
    status_field = _safe_text(profile.get("status_field"), "lifecycle_state")
    urgency_score = int(profile.get("urgency_score") or 0)
    highlight_rule = profile.get("highlight_rule") if isinstance(profile.get("highlight_rule"), dict) else {}
    if not highlight_rule:
        highlight_rule = {
            "overdue": {"field": "end_date", "operator": "lt_today", "level": "danger"},
            "at_risk": {"field": status_field, "operator": "in", "value": ["paused", "closing"], "level": "warning"},
        }
    profile["columns"] = columns
    profile["hidden_columns"] = sorted({str(col).strip() for col in hidden if str(col).strip()})
    profile["row_primary"] = row_primary
    profile["row_secondary"] = row_secondary
    profile["primary_field"] = primary_field
    profile["status_field"] = status_field
    profile["urgency_score"] = urgency_score
    profile["highlight_rule"] = highlight_rule
    return profile


def _derive_scene_meta(item: dict) -> dict:
    code = _safe_text(item.get("code") or item.get("key")).lower()
    purpose = "业务工作"
    if code.startswith("projects.") or "project" in code:
        purpose = "项目推进"
    elif code.startswith("finance.") or "payment" in code:
        purpose = "资金与审批"
    elif code.startswith("contracts.") or "contract" in code:
        purpose = "合同履约"

    access = item.get("access") if isinstance(item.get("access"), dict) else {}
    required_caps = access.get("required_capabilities") if isinstance(access.get("required_capabilities"), list) else []
    is_allowed = bool(access.get("allowed", True))
    is_default = bool(item.get("is_default"))
    base_score = 80
    if is_default:
        base_score += 10
    if not is_allowed:
        base_score -= 30
    base_score -= min(30, len(required_caps) * 5)
    role_relevance_score = max(0, min(100, base_score))

    tiles = item.get("tiles") if isinstance(item.get("tiles"), list) else []
    action_labels: list[str] = []
    for tile in tiles:
        if not isinstance(tile, dict):
            continue
        label = _safe_text(tile.get("title") or tile.get("subtitle") or tile.get("key"))
        if label and label not in action_labels:
            action_labels.append(label)
    core_action = action_labels[0] if action_labels else "进入场景"
    priority_actions = action_labels[:3]
    return {
        "purpose": purpose,
        "core_action": core_action,
        "priority_actions": priority_actions,
        "role_relevance_score": role_relevance_score,
    }


def _is_project_form_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    form_view = _as_dict(views.get("form"))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or form_view.get("model")
        or permissions.get("model")
    )
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    has_form_view = isinstance(views.get("form"), dict)
    if not view_type and has_form_view:
        view_type = "form"
    primary_model = _governance_primary_model(data)
    if primary_model != "project.project":
        return False
    if not primary_model or model != primary_model:
        return False
    if has_form_view:
        return "form" in view_type if view_type else True
    return view_type == "form"


def _is_enterprise_company_form_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    form_view = _as_dict(views.get("form"))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or form_view.get("model")
        or permissions.get("model")
    )
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if not view_type and isinstance(views.get("form"), dict):
        view_type = "form"
    primary_model = _governance_primary_model(data)
    return bool(primary_model == "res.company" and model == "res.company" and "form" in view_type)


def _is_enterprise_user_form_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    form_view = _as_dict(views.get("form"))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or form_view.get("model")
        or permissions.get("model")
    )
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if not view_type and isinstance(views.get("form"), dict):
        view_type = "form"
    primary_model = _governance_primary_model(data)
    return bool(primary_model == "res.users" and model == "res.users" and "form" in view_type)


def _is_project_kanban_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    kanban_view = _as_dict(views.get("kanban"))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or kanban_view.get("model")
        or permissions.get("model")
    )
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if not view_type and isinstance(views.get("kanban"), dict):
        view_type = "kanban"
    primary_model = _governance_primary_model(data)
    return bool(primary_model and model == primary_model and "kanban" in view_type)


def _is_project_task_form_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    form_view = _as_dict(views.get("form"))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or form_view.get("model")
        or permissions.get("model")
    )
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if not view_type and isinstance(views.get("form"), dict):
        view_type = "form"
    primary_model = _governance_primary_model(data)
    return bool(primary_model == "project.task" and model == "project.task" and "form" in view_type)


def _is_model_tree_contract(data: dict, model_name: str) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    tree_view = _as_dict(views.get("tree") or views.get("list"))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or tree_view.get("model")
        or permissions.get("model")
    )
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if not view_type and isinstance(views.get("tree"), dict):
        view_type = "tree"
    primary_model = _governance_primary_model(data)
    return bool(primary_model == model_name and model == model_name and "tree" in view_type)


def _is_form_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if view_type == "form":
        return True
    return isinstance(views.get("form"), dict)


def _is_technical_field(name: str, descriptor: dict) -> bool:
    low = _safe_lower(name)
    if not low:
        return True
    if low in {"id", "__last_update", "display_name"}:
        return True
    if low.startswith(("create_", "write_", "message_", "activity_", "access_", "alias_", "website_")):
        return True
    if low.endswith(("_ids", "_id_count")) and low not in {
        "project_type_id",
        "project_category_id",
        "stage_id",
        "manager_id",
        "user_id",
        "owner_id",
        "company_id",
    }:
        return True
    ttype = _safe_lower(descriptor.get("type") or descriptor.get("ttype"))
    if ttype in {"one2many", "many2many", "properties_definition"}:
        return True
    return False


def _pick_project_form_fields(data: dict) -> list[str]:
    fields_map = _as_dict(data.get("fields"))
    if not fields_map:
        return []
    ordered_fields = _iter_field_order(data)

    selected: list[str] = []
    for name in _PROJECT_FORM_PRIMARY_FIELDS:
        descriptor = _as_dict(fields_map.get(name))
        if descriptor and not _is_technical_field(name, descriptor) and name not in selected:
            selected.append(name)

    for name in ordered_fields:
        if len(selected) >= _PROJECT_FORM_FIELD_MAX:
            break
        descriptor = _as_dict(fields_map.get(name))
        if not descriptor or _is_technical_field(name, descriptor):
            continue
        if name not in selected:
            selected.append(name)

    for name, descriptor_raw in fields_map.items():
        if len(selected) >= _PROJECT_FORM_FIELD_MAX:
            break
        descriptor = _as_dict(descriptor_raw)
        if _is_technical_field(name, descriptor):
            continue
        required = bool(descriptor.get("required"))
        readonly = bool(descriptor.get("readonly"))
        if required and not readonly and name not in selected:
            selected.append(name)

    if "name" in fields_map and "name" not in selected:
        selected.insert(0, "name")
    return selected[:_PROJECT_FORM_FIELD_MAX]


def _govern_project_kanban_contract_for_user(data: dict) -> None:
    fields_map = _as_dict(data.get("fields"))
    if not fields_map:
        return

    available = [name for name in fields_map.keys() if not _is_technical_field(name, _as_dict(fields_map.get(name)))]
    primary: list[str] = []
    secondary: list[str] = []
    status: list[str] = []

    def _pick(target: list[str], name: str) -> None:
        if name in available and name not in target:
            target.append(name)

    for name in _PROJECT_KANBAN_PRIMARY_FIELDS:
        _pick(primary, name)
    for name in _PROJECT_KANBAN_SECONDARY_FIELDS:
        _pick(secondary, name)
    for name in _PROJECT_KANBAN_STATUS_FIELDS:
        _pick(status, name)

    if not primary:
        for fallback in ("name", "display_name"):
            _pick(primary, fallback)
            if primary:
                break
    if len(primary) < 3:
        for name in available:
            _pick(primary, name)
            if len(primary) >= 3:
                break
    if len(secondary) < 4:
        for name in available:
            if name in primary:
                continue
            _pick(secondary, name)
            if len(secondary) >= 4:
                break
    if not status:
        for name in ("lifecycle_state", "stage_id", "state"):
            _pick(status, name)
            if status:
                break

    selected = [name for name in primary + secondary if name]
    selected = selected[:8]
    data["visible_fields"] = selected
    data["kanban_profile"] = {
        "title_field": primary[0] if primary else "name",
        "primary_fields": primary[:3],
        "secondary_fields": secondary[:4],
        "status_fields": status[:2],
        "max_meta": 4,
    }

    views = _as_dict(data.get("views"))
    kanban = _as_dict(views.get("kanban"))
    existing = kanban.get("fields") if isinstance(kanban.get("fields"), list) else []
    merged_fields: list[str] = []
    for name in existing + selected:
        normalized = _safe_text(name)
        if normalized and normalized in fields_map and normalized not in merged_fields:
            merged_fields.append(normalized)
    kanban["fields"] = merged_fields or ["id", "name"]
    kanban["kanban_profile"] = _as_dict(data.get("kanban_profile"))
    views["kanban"] = kanban
    data["views"] = views


def _restructure_project_form_layout(data: dict) -> None:
    if not _is_project_form_contract(data):
        return
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    if not isinstance(layout, list):
        return

    fields_map = _as_dict(data.get("fields"))
    field_names = [name for name in fields_map.keys() if _safe_text(name)]
    visible_fields = data.get("visible_fields") if isinstance(data.get("visible_fields"), list) else []
    ordered = [str(name).strip() for name in visible_fields if str(name).strip() in fields_map]
    if not ordered:
        ordered = field_names

    profile = _as_dict(data.get("form_profile"))
    core_raw = profile.get("core_fields") if isinstance(profile.get("core_fields"), list) else []
    advanced_raw = profile.get("advanced_fields") if isinstance(profile.get("advanced_fields"), list) else []
    core_fields = [str(name).strip() for name in core_raw if str(name).strip() in ordered]
    advanced_fields = [str(name).strip() for name in advanced_raw if str(name).strip() in ordered]
    if not core_fields:
        core_fields = ordered[: min(8, len(ordered))]
    if not advanced_fields:
        advanced_fields = [name for name in ordered if name not in set(core_fields)]

    header_nodes = [
        node
        for node in layout
        if isinstance(node, dict) and _safe_lower(node.get("type")) == "header"
    ]
    groups = []
    if core_fields:
        groups.append(
            {
                "type": "group",
                "name": "core_group",
                "string": "核心信息",
                "children": [{"type": "field", "name": name} for name in core_fields],
            }
        )
    if advanced_fields:
        groups.append(
            {
                "type": "group",
                "name": "advanced_group",
                "string": "高级信息",
                "children": [{"type": "field", "name": name} for name in advanced_fields],
            }
        )
    if not groups:
        return

    form["layout"] = header_nodes + [
        {
            "type": "sheet",
            "name": "project_form_sheet",
            "children": groups,
        }
    ]
    views["form"] = form
    data["views"] = views


def _filter_project_form_layout(data: dict, selected_fields: list[str]) -> None:
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    if not isinstance(layout, list):
        return

    def _iter_children(node: dict) -> list[list]:
        rows: list[list] = []
        for key in ("children", "tabs", "pages", "nodes", "items"):
            candidate = node.get(key)
            if isinstance(candidate, list):
                rows.append(candidate)
        return rows

    def _collect_layout_field_names(nodes: list, out: list[str]) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_type = _safe_lower(node.get("type"))
            if node_type == "field":
                name = _safe_text(node.get("name"))
                if name and name not in out:
                    out.append(name)
            for children in _iter_children(node):
                _collect_layout_field_names(children, out)

    def _prune_layout(nodes: list, allowed: set[str]) -> list[dict]:
        cleaned: list[dict] = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_type = _safe_lower(node.get("type"))
            if node_type == "field":
                name = _safe_text(node.get("name"))
                if name and name in allowed:
                    cleaned.append(node)
                continue
            copied = dict(node)
            keep_node = True
            for key in ("children", "tabs", "pages", "nodes", "items"):
                raw_children = node.get(key)
                if not isinstance(raw_children, list):
                    continue
                pruned_children = _prune_layout(raw_children, allowed)
                copied[key] = pruned_children
                if node_type in {"group", "page", "notebook", "sheet", "header"} and not pruned_children and key in {"children", "tabs", "pages"}:
                    keep_node = False
            if keep_node:
                cleaned.append(copied)
        return cleaned

    selected_order = [name for name in selected_fields if _safe_text(name)]
    selected_set = set(selected_order)
    filtered_layout = _prune_layout(layout, selected_set)

    existing_field_names: list[str] = []
    _collect_layout_field_names(filtered_layout, existing_field_names)
    if not existing_field_names:
        for name in _PROJECT_FORM_PRIMARY_FIELDS:
            if name in selected_fields:
                filtered_layout.append({"type": "field", "name": name})
        _collect_layout_field_names(filtered_layout, existing_field_names)

    # Ensure filtered layout covers selected user-surface fields, so frontend can render
    # a coherent contract-driven form without falling back to unordered field maps.
    existing_set = set(existing_field_names)
    missing_selected = [name for name in selected_order if name and name not in existing_set]
    for name in missing_selected:
        filtered_layout.append({"type": "field", "name": name})
    form_profile = _as_dict(data.get("form_profile"))
    core_raw = form_profile.get("core_fields")
    advanced_raw = form_profile.get("advanced_fields")
    core_fields = [
        _safe_text(name)
        for name in (core_raw if isinstance(core_raw, list) else [])
        if _safe_text(name) in selected_set
    ]
    advanced_fields = [
        _safe_text(name)
        for name in (advanced_raw if isinstance(advanced_raw, list) else [])
        if _safe_text(name) in selected_set
    ]
    field_order = [name for name in selected_order if name in selected_set]
    if not core_fields and field_order:
        core_fields = field_order[: min(8, len(field_order))]
    if not advanced_fields:
        advanced_fields = [name for name in field_order if name not in set(core_fields)]

    header_nodes: list[dict] = []
    for node in filtered_layout:
        if isinstance(node, dict) and _safe_lower(node.get("type")) == "header":
            header_nodes.append(node)

    grouped_children: list[dict] = []
    if core_fields:
        grouped_children.append(
            {
                "type": "group",
                "name": "core_group",
                "string": "核心信息",
                "children": [{"type": "field", "name": name} for name in core_fields],
            }
        )
    if advanced_fields:
        grouped_children.append(
            {
                "type": "group",
                "name": "advanced_group",
                "string": "高级信息",
                "children": [{"type": "field", "name": name} for name in advanced_fields],
            }
        )

    if grouped_children:
        sheet_node = {
            "type": "sheet",
            "name": "project_form_sheet",
            "children": grouped_children,
        }
        form["layout"] = header_nodes + [sheet_node]
    else:
        form["layout"] = filtered_layout
    views["form"] = form
    data["views"] = views


def _govern_project_form_search(data: dict) -> None:
    search = _as_dict(data.get("search"))
    filters = search.get("filters")
    if not isinstance(filters, list):
        return
    cleaned = []
    seen: set[str] = set()
    for row in filters:
        if not isinstance(row, dict):
            continue
        key = _safe_text(row.get("key"))
        label = _safe_text(row.get("label"))
        if not key or key in seen:
            continue
        if not label:
            continue
        if any(marker in _safe_lower(label) for marker in ("活动", "评分", "status_period")):
            continue
        cleaned.append(row)
        seen.add(key)
        if len(cleaned) >= 8:
            break
    search["filters"] = cleaned
    data["search"] = search


def _action_priority(action: dict) -> int:
    label = _safe_text(action.get("label"))
    for idx, key in enumerate(_PROJECT_FORM_ACTION_PRIORITIES):
        if key and key in label:
            return idx
    return len(_PROJECT_FORM_ACTION_PRIORITIES) + 1


def _is_noisy_project_action(action: dict) -> bool:
    key = _safe_lower(action.get("key"))
    label = _safe_lower(action.get("label"))
    if not label and not key:
        return True
    if label.isdigit():
        return True
    for marker in _PROJECT_FORM_ACTION_DEMOTE_KEYWORDS:
        if marker in key or marker in label:
            return True
    return False


def _classify_project_action_group(action: dict) -> str:
    key = _safe_lower(action.get("key"))
    label = _safe_lower(action.get("label"))
    merged = f"{key} {label}"
    if any(marker in merged for marker in ("阶段", "提交", "审批", "transition", "workflow", "lifecycle")):
        return "workflow"
    if any(marker in merged for marker in ("查看", "open", "dashboard", "看板", "列表")):
        return "drilldown"
    if any(marker in merged for marker in ("创建", "保存", "提交")):
        return "basic"
    return "other"


def _build_project_action_groups(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {"basic": [], "workflow": [], "drilldown": [], "other": []}
    for row in rows:
        if not isinstance(row, dict):
            continue
        group_key = _classify_project_action_group(row)
        grouped.setdefault(group_key, []).append(row)

    result: list[dict] = []
    for key in ("basic", "workflow", "drilldown", "other"):
        actions = grouped.get(key) or []
        if not actions:
            continue
        primary = actions[:_PROJECT_FORM_ACTION_GROUP_LIMIT]
        overflow = actions[_PROJECT_FORM_ACTION_GROUP_LIMIT:]
        result.append({
            "key": key,
            "label": _PROJECT_FORM_ACTION_GROUP_LABELS.get(key, key),
            "actions": primary,
            "overflow_actions": overflow,
            "overflow_count": len(overflow),
        })
    return result


def _govern_project_form_actions(data: dict) -> None:
    toolbar = _as_dict(data.get("toolbar"))
    if isinstance(toolbar.get("header"), list):
        toolbar["header"] = []
    data["toolbar"] = toolbar

    rows = data.get("buttons")
    if not isinstance(rows, list):
        return
    header_rows: list[dict] = []
    smart_rows: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if _is_noisy_project_action(row):
            continue
        level = _safe_lower(row.get("level"))
        if level == "header":
            header_rows.append(row)
        elif level in {"smart", "row"}:
            smart_rows.append(row)

    header_rows = sorted(header_rows, key=lambda item: (_action_priority(item), _safe_text(item.get("label"))))
    smart_rows = sorted(smart_rows, key=lambda item: (_action_priority(item), _safe_text(item.get("label"))))
    curated = header_rows[:_PROJECT_FORM_HEADER_ACTION_MAX] + smart_rows[:_PROJECT_FORM_SMART_ACTION_MAX]
    data["buttons"] = curated
    data["action_groups"] = _build_project_action_groups(curated)


def _build_project_lifecycle_summary(data: dict) -> None:
    workflow = _as_dict(data.get("workflow"))
    states = workflow.get("states")
    transitions = workflow.get("transitions")
    if not isinstance(states, list):
        states = []
    if not isinstance(transitions, list):
        transitions = []

    state_keys = []
    for row in states:
        if not isinstance(row, dict):
            continue
        key = _safe_text(row.get("key"))
        label = _safe_text(row.get("label"), key)
        if not key:
            continue
        state_keys.append({"key": key, "label": label})

    transition_rows = []
    for row in transitions:
        if not isinstance(row, dict):
            continue
        trigger = _as_dict(row.get("trigger"))
        label = _safe_text(trigger.get("label") or trigger.get("name"))
        if not label:
            continue
        transition_rows.append({
            "label": label,
            "kind": _safe_text(trigger.get("kind")),
        })

    data["lifecycle"] = {
        "state_field": _safe_text(workflow.get("state_field"), "stage_id"),
        "current_state": "",
        "steps": state_keys,
        "allowed_transitions": transition_rows[:8],
        "blockers": [],
        "progress_percent": 0 if state_keys else None,
    }


def _govern_project_form_contract_for_user(data: dict) -> None:
    selected = _pick_project_form_fields(data)
    selected_set = set(selected)
    fields_map = _as_dict(data.get("fields"))
    data["fields"] = {name: fields_map.get(name) for name in selected if name in fields_map}
    data["visible_fields"] = selected
    data["form_profile"] = {
        "core_fields": selected[:8],
        "advanced_fields": selected[8:],
        "max_fields": _PROJECT_FORM_FIELD_MAX,
    }
    _filter_project_form_layout(data, selected)
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    form["form_profile"] = _as_dict(data.get("form_profile"))
    views["form"] = form
    data["views"] = views

    permissions = _as_dict(data.get("permissions"))
    field_groups = _as_dict(permissions.get("field_groups"))
    if field_groups:
        permissions["field_groups"] = {name: val for name, val in field_groups.items() if name in selected_set}
    data["permissions"] = permissions

    _govern_project_form_actions(data)
    _govern_project_form_search(data)
    _build_project_lifecycle_summary(data)
    _realign_access_policy_with_visible_fields(data)


def _govern_project_task_form_for_user(data: dict) -> None:
    if not _is_project_task_form_contract(data):
        return
    fields_map = _as_dict(data.get("fields"))
    selected = [name for name in _PROJECT_TASK_FORM_FIELDS if name in fields_map]
    if not selected:
        return

    data["visible_fields"] = selected
    data["field_groups"] = [
        {
            "name": "core",
            "label": "任务基础信息",
            "priority": 1,
            "collapsible": False,
            "fields": [name for name in selected if name != "description"],
        },
        {
            "name": "advanced",
            "label": "任务说明",
            "priority": 2,
            "collapsible": True,
            "fields": [name for name in selected if name == "description"],
        },
    ]

    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    form["layout"] = [
        {
            "type": "sheet",
            "name": "project_task_form_sheet",
            "children": [
                {
                    "type": "group",
                    "name": "project_task_core_group",
                    "string": "任务基础信息",
                    "children": [
                        _make_labeled_field_node(name, fields_map, _PROJECT_TASK_FIELD_LABELS)
                        for name in selected
                        if name != "description"
                    ],
                },
                {
                    "type": "group",
                    "name": "project_task_description_group",
                    "string": "任务说明",
                    "children": [
                        _make_labeled_field_node(name, fields_map, _PROJECT_TASK_FIELD_LABELS)
                        for name in selected
                        if name == "description"
                    ],
                },
            ],
        }
    ]
    views["form"] = form
    data["views"] = views


def _govern_standard_list_for_user(
    data: dict,
    *,
    model_name: str,
    columns_order: list[str],
    column_labels: dict[str, str],
    row_primary: str,
    row_secondary: str,
    status_field: str,
) -> None:
    if not _is_model_tree_contract(data, model_name):
        return
    fields_map = _as_dict(data.get("fields"))
    selected = [name for name in columns_order if name in fields_map]
    if not selected:
        return

    views = _as_dict(data.get("views"))
    tree = _as_dict(views.get("tree") or views.get("list"))
    tree["columns"] = selected
    views["tree"] = tree
    data["views"] = views

    list_profile = _as_dict(data.get("list_profile"))
    list_profile.update(
        {
            "columns": selected,
            "hidden_columns": [],
            "column_labels": {name: column_labels.get(name, name) for name in selected},
            "row_primary": row_primary,
            "row_secondary": row_secondary,
            "primary_field": row_primary,
            "status_field": status_field,
        }
    )
    data["list_profile"] = list_profile

    semantic_page = _as_dict(data.get("semantic_page"))
    list_semantics = _as_dict(semantic_page.get("list_semantics"))
    list_semantics["columns"] = [
        {"name": name, "label": column_labels.get(name, name)}
        for name in selected
    ]
    semantic_page["list_semantics"] = list_semantics
    data["semantic_page"] = semantic_page


def _realign_access_policy_with_visible_fields(data: dict) -> None:
    fields_map = _as_dict(data.get("fields"))
    policy = _as_dict(data.get("access_policy"))
    if not policy:
        return

    visible = set()
    for name in (data.get("visible_fields") or []):
        field_name = _safe_text(name)
        if field_name and field_name in fields_map:
            visible.add(field_name)
    if not visible:
        visible = set(fields_map.keys())

    def _normalize_rows(rows: Any) -> list[dict]:
        out: list[dict] = []
        if not isinstance(rows, list):
            return out
        for row in rows:
            if not isinstance(row, dict):
                continue
            field_name = _safe_text(row.get("field"))
            if not field_name:
                continue
            if field_name != "__model__" and field_name not in visible:
                continue
            out.append(
                {
                    "field": field_name,
                    "model": _safe_text(row.get("model")),
                    "reason_code": _safe_text(row.get("reason_code")),
                }
            )
        return out

    blocked_rows = _normalize_rows(policy.get("blocked_fields"))
    degraded_rows = _normalize_rows(policy.get("degraded_fields"))
    mode = "allow"
    reason_code = ""
    message = ""
    if blocked_rows:
        mode = "block"
        first = blocked_rows[0]
        reason_code = _safe_text(first.get("reason_code"), "RELATION_READ_FORBIDDEN_CORE")
        if reason_code == "RELATION_READ_FORBIDDEN":
            reason_code = "RELATION_READ_FORBIDDEN_CORE"
        label = _safe_text(first.get("field") or first.get("model"), "unknown")
        message = f"core field access blocked: {label}"
    elif degraded_rows:
        mode = "degrade"
        first = degraded_rows[0]
        reason_code = _safe_text(first.get("reason_code"), "RELATION_READ_FORBIDDEN")
        label = _safe_text(first.get("field") or first.get("model"), "unknown")
        message = f"relation access degraded: {label}"

    policy["mode"] = mode
    policy["reason_code"] = reason_code
    policy["message"] = message
    policy["blocked_fields"] = blocked_rows
    policy["degraded_fields"] = degraded_rows
    data["access_policy"] = policy

    warnings = data.get("warnings") if isinstance(data.get("warnings"), list) else []
    warnings = [item for item in warnings if not (_safe_text(item).startswith("access_policy:"))]
    if mode in {"block", "degrade"}:
        marker = f"access_policy:{mode}:{reason_code or 'UNKNOWN'}"
        if marker not in warnings:
            warnings.append(marker)
    if warnings:
        data["warnings"] = warnings
    else:
        data.pop("warnings", None)


def _normalize_native_view_contract_surface(data: dict) -> None:
    parser_contract = _as_dict(data.get("parser_contract"))
    if parser_contract:
        parser_contract.setdefault("layout", _as_dict(parser_contract.get("layout")))
        contract_version = _safe_text(data.get("contract_version")) or "native_view.v1"
        parser_contract.setdefault("contract_version", contract_version)
        data["parser_contract"] = parser_contract

    view_semantics = _as_dict(data.get("view_semantics"))
    if view_semantics:
        view_semantics.setdefault("kind", "view_semantics")
        view_semantics["capability_flags"] = _as_dict(view_semantics.get("capability_flags"))
        view_semantics["semantic_meta"] = _as_dict(view_semantics.get("semantic_meta"))
        data["view_semantics"] = view_semantics

    native_view = _as_dict(data.get("native_view"))
    if native_view:
        native_view["views"] = _as_dict(native_view.get("views"))
        native_view["search"] = _as_dict(native_view.get("search"))
        native_view["toolbar"] = _as_dict(native_view.get("toolbar"))
        data["native_view"] = native_view


def _normalize_scene_semantic_surface(data: dict) -> None:
    def _normalize_page_surface(page_payload: dict) -> dict:
        page = _as_dict(page_payload)
        surface = _as_dict(page.get("surface"))
        if surface:
            surface["semantic_view"] = _as_dict(surface.get("semantic_view"))
            surface["semantic_page"] = _as_dict(surface.get("semantic_page"))
            page["surface"] = surface
        return page

    def _normalize_parser_semantic_surface(surface_payload: dict) -> dict:
        surface = _as_dict(surface_payload)
        if not surface:
            return {}
        parser_contract = _as_dict(surface.get("parser_contract"))
        if parser_contract:
            parser_contract.setdefault("layout", _as_dict(parser_contract.get("layout")))
            parser_contract.setdefault(
                "contract_version",
                _safe_text(data.get("contract_version")) or "native_view.v1",
            )
            surface["parser_contract"] = parser_contract
        view_semantics = _as_dict(surface.get("view_semantics"))
        if view_semantics:
            view_semantics.setdefault("kind", "view_semantics")
            view_semantics["capability_flags"] = _as_dict(view_semantics.get("capability_flags"))
            view_semantics["semantic_meta"] = _as_dict(view_semantics.get("semantic_meta"))
            surface["view_semantics"] = view_semantics
        native_view = _as_dict(surface.get("native_view"))
        if native_view:
            native_view["views"] = _as_dict(native_view.get("views"))
            native_view["search"] = _as_dict(native_view.get("search"))
            native_view["toolbar"] = _as_dict(native_view.get("toolbar"))
            surface["native_view"] = native_view
        semantic_page = _as_dict(surface.get("semantic_page"))
        if semantic_page:
            surface["semantic_page"] = semantic_page
        return surface

    scene_contract_standard = _as_dict(data.get("scene_contract_standard_v1"))
    if scene_contract_standard:
        scene_contract_standard["page"] = _normalize_page_surface(scene_contract_standard.get("page"))
        governance = _as_dict(scene_contract_standard.get("governance"))
        parser_surface = _normalize_parser_semantic_surface(governance.get("parser_semantic_surface"))
        if parser_surface:
            governance["parser_semantic_surface"] = parser_surface
        scene_contract_standard["governance"] = governance
        data["scene_contract_standard_v1"] = scene_contract_standard

    scene_contract_v1 = _as_dict(data.get("scene_contract_v1"))
    if scene_contract_v1:
        scene_contract_v1["page"] = _normalize_page_surface(scene_contract_v1.get("page"))
        diagnostics = _as_dict(scene_contract_v1.get("diagnostics"))
        parser_surface = _normalize_parser_semantic_surface(diagnostics.get("parser_semantic_surface"))
        if parser_surface:
            diagnostics["parser_semantic_surface"] = parser_surface
        scene_contract_v1["diagnostics"] = diagnostics
        data["scene_contract_v1"] = scene_contract_v1

    semantic_runtime = _as_dict(data.get("semantic_runtime"))
    if semantic_runtime:
        semantic_runtime["semantic_view"] = _as_dict(semantic_runtime.get("semantic_view"))
        semantic_runtime["semantic_page"] = _as_dict(semantic_runtime.get("semantic_page"))
        parser_surface = _normalize_parser_semantic_surface(semantic_runtime.get("parser_semantic_surface"))
        if parser_surface:
            semantic_runtime["parser_semantic_surface"] = parser_surface
        data["semantic_runtime"] = semantic_runtime

    released_scene_surface = _as_dict(data.get("released_scene_semantic_surface"))
    if released_scene_surface:
        released_scene_surface["page_surface"] = _normalize_page_surface({"surface": released_scene_surface.get("page_surface")}).get("surface") or {}
        parser_surface = _normalize_parser_semantic_surface(released_scene_surface.get("parser_semantic_surface"))
        if parser_surface:
            released_scene_surface["parser_semantic_surface"] = parser_surface
        data["released_scene_semantic_surface"] = released_scene_surface


def _to_bool(value: Any, fallback: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return fallback
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    return fallback


def _resolve_render_profile(data: dict) -> str:
    explicit = _safe_text(data.get("render_profile")).lower()
    if explicit in _RENDER_PROFILES:
        return explicit
    head = _as_dict(data.get("head"))
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if view_type and "form" not in view_type:
        return _RENDER_PROFILE_EDIT
    effective = _as_dict(_as_dict(data.get("permissions")).get("effective")).get("rights")
    effective_rights = _as_dict(effective)
    head_permissions = _as_dict(head.get("permissions"))
    can_write = _to_bool(
        effective_rights.get("write", head_permissions.get("write")),
        fallback=False,
    )
    can_create = _to_bool(
        effective_rights.get("create", head_permissions.get("create")),
        fallback=False,
    )
    if not can_write and not can_create:
        return _RENDER_PROFILE_READONLY
    has_record = False
    for raw in (data.get("res_id"), head.get("res_id"), data.get("id")):
        if raw in (None, "", False):
            continue
        token = str(raw).strip().lower()
        if token in {"", "0", "new", "false", "null", "none"}:
            continue
        try:
            if int(token) > 0:
                has_record = True
                break
        except Exception:
            # 非数字主键在当前项目契约中不作为“已有记录”判定依据
            continue
    return _RENDER_PROFILE_EDIT if has_record else _RENDER_PROFILE_CREATE


def _iter_field_order(data: dict) -> list[str]:
    def _iter_children(node: dict) -> list[list]:
        rows: list[list] = []
        for key in ("children", "tabs", "pages", "nodes", "items"):
            candidate = node.get(key)
            if isinstance(candidate, list):
                rows.append(candidate)
        return rows

    def _collect_fields(nodes: list, out: list[str]) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if _safe_lower(node.get("type")) == "field":
                name = _safe_text(node.get("name"))
                if name and name not in out:
                    out.append(name)
            for children in _iter_children(node):
                _collect_fields(children, out)

    ordered: list[str] = []
    form = _as_dict(_as_dict(data.get("views")).get("form"))
    layout = form.get("layout")
    _collect_fields(layout if isinstance(layout, list) else [], ordered)
    for name in (_as_dict(data.get("fields")) or {}).keys():
        if name not in ordered:
            ordered.append(name)
    return ordered


def _derive_form_core_fields(data: dict) -> list[str]:
    fields_map = _as_dict(data.get("fields"))
    ordered = _iter_field_order(data)
    core: list[str] = []
    is_project_form = _is_project_form_contract(data)

    def _push(name: str) -> None:
        if not name or name in core:
            return
        descriptor = _as_dict(fields_map.get(name))
        if not descriptor:
            return
        if _is_technical_field(name, descriptor):
            return
        if is_project_form and name in _PROJECT_FORM_CREATE_HIDDEN_FIELDS:
            return
        core.append(name)

    # For project create forms, prioritize stable business fields first.
    if is_project_form:
        for name in _PROJECT_FORM_PRIMARY_FIELDS:
            _push(name)
            if len(core) >= _FORM_CORE_FIELD_MAX:
                break

    for name in ordered:
        descriptor = _as_dict(fields_map.get(name))
        if not descriptor:
            continue
        required = _to_bool(descriptor.get("required"), fallback=False)
        readonly = _to_bool(descriptor.get("readonly"), fallback=False)
        if is_project_form and name in _PROJECT_FORM_CREATE_HIDDEN_FIELDS:
            continue
        if required and not readonly:
            _push(name)
        if len(core) >= _FORM_CORE_FIELD_MAX:
            break

    if len(core) < _FORM_CORE_FIELD_MAX:
        for preferred in ("name", "display_name"):
            _push(preferred)
            if len(core) >= _FORM_CORE_FIELD_MAX:
                break

    if len(core) < _FORM_CORE_FIELD_MAX:
        for name in ordered:
            _push(name)
            if len(core) >= _FORM_CORE_FIELD_MAX:
                break
    return core[:_FORM_CORE_FIELD_MAX]


def _apply_form_field_groups(data: dict) -> None:
    if not _is_form_contract(data):
        return
    existing_groups = data.get("field_groups") if isinstance(data.get("field_groups"), list) else []
    if existing_groups and (
        _is_enterprise_company_form_contract(data)
        or _is_enterprise_user_form_contract(data)
    ):
        return
    fields_map = _as_dict(data.get("fields"))
    if not fields_map:
        return
    core_fields = _derive_form_core_fields(data)
    core_set = set(core_fields)
    advanced_fields = [
        name
        for name in _iter_field_order(data)
        if name in fields_map and name not in core_set
    ]
    data["field_groups"] = [
        {
            "name": "core",
            "label": "核心信息",
            "priority": 1,
            "collapsible": False,
            "fields": core_fields,
        },
        {
            "name": "advanced",
            "label": "高级信息",
            "priority": 2,
            "collapsible": True,
            "collapsed_by_default": True,
            "fields": advanced_fields,
        },
    ]


def _make_labeled_field_node(
    name: str,
    fields_map: dict[str, Any],
    preferred_labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    descriptor = _as_dict(fields_map.get(name))
    label = _safe_text((preferred_labels or {}).get(name), "")
    if not label:
        label = _safe_text(_ENTERPRISE_USER_FIELD_LABELS.get(name) or _ENTERPRISE_COMPANY_FIELD_LABELS.get(name), "")
    if not label:
        label = _safe_text(descriptor.get("string") if descriptor else "", name)
    node = {"type": "field", "name": name}
    if label:
        node["string"] = label
    return node


def _infer_action_semantic(action: dict) -> str:
    label = _safe_lower(action.get("label"))
    key = _safe_lower(action.get("key"))
    merged = f"{label} {key}"
    if any(keyword in merged for keyword in _FORM_ACTION_PRIMARY_KEYWORDS):
        return "primary_action"
    if any(keyword in merged for keyword in ("删除", "停用", "archive", "unlink", "删除")):
        return "danger"
    return "secondary"


def _infer_visible_profiles(action: dict) -> list[str]:
    label = _safe_lower(action.get("label"))
    key = _safe_lower(action.get("key"))
    merged = f"{label} {key}"
    if any(keyword in merged for keyword in ("创建", "提交", "create", "submit")):
        return [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT]
    if any(keyword in merged for keyword in ("编辑", "修改", "edit", "write")):
        return [_RENDER_PROFILE_EDIT]
    if any(keyword in merged for keyword in _FORM_ACTION_READONLY_KEYWORDS):
        return [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
    return [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT]


def _annotate_form_actions(data: dict) -> None:
    if not _is_form_contract(data):
        return
    buttons = data.get("buttons")
    if not isinstance(buttons, list):
        return
    primary_assigned = False
    for row in buttons:
        if not isinstance(row, dict):
            continue
        semantic = _safe_text(row.get("semantic")).lower() or _infer_action_semantic(row)
        if semantic == "primary_action":
            if primary_assigned:
                semantic = "secondary"
            else:
                primary_assigned = True
        row["semantic"] = semantic
        raw_profiles = row.get("visible_profiles")
        if isinstance(raw_profiles, list) and raw_profiles:
            profiles = [
                _safe_text(item).lower()
                for item in raw_profiles
                if _safe_text(item).lower() in _RENDER_PROFILES
            ]
        else:
            profiles = _infer_visible_profiles(row)
        row["visible_profiles"] = profiles or [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT]


def _apply_form_render_semantics(data: dict, contract_mode: str) -> None:
    if not _is_form_contract(data):
        return
    data["render_profile"] = _resolve_render_profile(data)
    data["hide_filters_on_create"] = True
    _apply_form_field_groups(data)
    _annotate_form_actions(data)
    _apply_form_policy_contract(data, contract_mode)


def _resolve_contract_required_fields(data: dict, fields_map: dict[str, Any]) -> list[str]:
    if _is_project_form_contract(data):
        descriptor = _as_dict(fields_map.get("name"))
        if descriptor and not _to_bool(descriptor.get("readonly"), fallback=False):
            return ["name"]
        return []
    required_fields: list[str] = []
    for name, descriptor_raw in fields_map.items():
        descriptor = _as_dict(descriptor_raw)
        if not descriptor:
            continue
        required = _to_bool(descriptor.get("required"), fallback=False)
        readonly = _to_bool(descriptor.get("readonly"), fallback=False)
        if required and not readonly:
            required_fields.append(name)
    return required_fields


def _build_form_field_policies(data: dict) -> dict[str, dict[str, Any]]:
    fields_map = _as_dict(data.get("fields"))
    core_group = {}
    advanced_group = {}
    for item in data.get("field_groups") if isinstance(data.get("field_groups"), list) else []:
        if not isinstance(item, dict):
            continue
        key = _safe_lower(item.get("name"))
        rows = item.get("fields")
        if not isinstance(rows, list):
            continue
        normalized = [str(name).strip() for name in rows if str(name).strip()]
        if key == "core":
            core_group = {name: True for name in normalized}
        if key == "advanced":
            advanced_group = {name: True for name in normalized}

    policies: dict[str, dict[str, Any]] = {}
    contract_required_fields = set(_resolve_contract_required_fields(data, fields_map))
    is_project_form = _is_project_form_contract(data)
    for name, descriptor_raw in fields_map.items():
        descriptor = _as_dict(descriptor_raw)
        if not descriptor:
            continue
        required = name in contract_required_fields
        readonly = _to_bool(descriptor.get("readonly"), fallback=False)
        visible_profiles = [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
        if name in advanced_group:
            visible_profiles = [_RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
            if is_project_form and name not in _PROJECT_FORM_CREATE_HIDDEN_FIELDS:
                visible_profiles = [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
        required_profiles = [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT] if required and not readonly else []
        readonly_profiles = [_RENDER_PROFILE_READONLY]
        if readonly:
            readonly_profiles = [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
        policies[name] = {
            "visible_profiles": visible_profiles,
            "required_profiles": required_profiles,
            "readonly_profiles": readonly_profiles,
            "source_required": required,
            "source_readonly": readonly,
            "group": "core" if name in core_group else ("advanced" if name in advanced_group else "secondary"),
        }
        # Project create page should not expose system-derived/status fields to end users.
        if is_project_form and name in _PROJECT_FORM_CREATE_HIDDEN_FIELDS:
            policies[name]["visible_profiles"] = [_RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
            policies[name]["required_profiles"] = []
            policies[name]["readonly_profiles"] = [
                _RENDER_PROFILE_CREATE,
                _RENDER_PROFILE_EDIT,
                _RENDER_PROFILE_READONLY,
            ]
            policies[name]["source_required"] = False
            policies[name]["source_readonly"] = True
            policies[name]["group"] = "advanced"
    return policies


def _default_action_policy(semantic: str, visible_profiles: list[str], required_fields: list[str]) -> dict[str, Any]:
    policy = {
        "visible_profiles": visible_profiles or [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT],
        "enabled_when": {},
        "disabled_reason": "",
        "semantic": semantic,
    }
    if semantic == "primary_action":
        policy["enabled_when"] = {
            "required_fields": required_fields[:12],
            "profiles": [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT],
            "conditions": [],
        }
        policy["disabled_reason"] = _FORM_PRIMARY_DISABLED_REASON
    return policy


def _resolve_form_scene_profile(data: dict) -> str:
    return _FORM_SCENE_PROFILE_PROJECT if _is_project_form_contract(data) else _FORM_SCENE_PROFILE_DEFAULT


def _resolve_action_policy_template_keys(
    *,
    scene_profile: str,
    semantic: str,
    required_capabilities: list[str],
    required_groups: list[str],
    required_roles: list[str],
    lifecycle_field: str,
    lifecycle_blocked_states: list[str],
) -> list[str]:
    keys: list[str] = []
    if semantic == "primary_action":
        keys.append("base.primary")
    else:
        keys.append("base.secondary")
    if required_capabilities or required_groups or required_roles or (lifecycle_field and lifecycle_blocked_states):
        keys.append("constraint.access")
    if scene_profile == _FORM_SCENE_PROFILE_PROJECT and semantic == "primary_action":
        keys.append("scene.project.form.primary")
    return keys


def _apply_action_policy_templates(
    policy: dict[str, Any],
    template_keys: list[str],
    *,
    required_fields: list[str],
    required_capabilities: list[str],
    lifecycle_field: str,
    lifecycle_blocked_states: list[str],
    required_groups: list[str],
    required_roles: list[str],
    fields_map: dict[str, Any],
) -> None:
    def _apply_base_primary() -> None:
        base = _default_action_policy("primary_action", policy.get("visible_profiles") or [], required_fields)
        policy["enabled_when"] = base.get("enabled_when") or {}
        policy["disabled_reason"] = base.get("disabled_reason") or policy.get("disabled_reason") or ""
        policy["semantic"] = "primary_action"

    def _apply_base_secondary() -> None:
        base = _default_action_policy(
            _safe_text(policy.get("semantic"), "secondary"),
            policy.get("visible_profiles") or [],
            required_fields,
        )
        policy["enabled_when"] = base.get("enabled_when") or {}
        policy["disabled_reason"] = base.get("disabled_reason") or policy.get("disabled_reason") or ""

    def _apply_constraint_access() -> None:
        _merge_policy_constraints(
            policy,
            required_capabilities=required_capabilities,
            lifecycle_field=lifecycle_field,
            lifecycle_blocked_states=lifecycle_blocked_states,
            required_groups=required_groups,
            required_roles=required_roles,
        )

    def _apply_scene_project_primary() -> None:
        _append_primary_action_conditions(policy, fields_map)

    template_registry = {
        "base.primary": _apply_base_primary,
        "base.secondary": _apply_base_secondary,
        "constraint.access": _apply_constraint_access,
        "scene.project.form.primary": _apply_scene_project_primary,
    }
    for key in template_keys:
        runner = template_registry.get(key)
        if callable(runner):
            runner()


def _merge_policy_constraints(
    policy: dict[str, Any],
    *,
    required_capabilities: list[str],
    lifecycle_field: str,
    lifecycle_blocked_states: list[str],
    required_groups: list[str],
    required_roles: list[str],
) -> None:
    enabled_when = policy.get("enabled_when")
    if not isinstance(enabled_when, dict):
        enabled_when = {}

    if required_capabilities:
        enabled_when["required_capabilities"] = required_capabilities
        if not policy.get("disabled_reason"):
            policy["disabled_reason"] = _FORM_DISABLED_REASON_CAPABILITY
    if lifecycle_field and lifecycle_blocked_states:
        enabled_when["lifecycle"] = {"field": lifecycle_field, "disallow_states": lifecycle_blocked_states}
        if not policy.get("disabled_reason"):
            policy["disabled_reason"] = _FORM_DISABLED_REASON_LIFECYCLE
    if required_groups:
        enabled_when["required_groups"] = required_groups
        if not policy.get("disabled_reason"):
            policy["disabled_reason"] = _FORM_DISABLED_REASON_GROUP
    if required_roles:
        enabled_when["required_roles"] = required_roles
        if not policy.get("disabled_reason"):
            policy["disabled_reason"] = _FORM_DISABLED_REASON_ROLE
    policy["enabled_when"] = enabled_when


def _append_primary_action_conditions(policy: dict[str, Any], fields_map: dict[str, Any]) -> None:
    if _safe_text(policy.get("semantic")) != "primary_action":
        return
    enabled_when = policy.get("enabled_when")
    if not isinstance(enabled_when, dict):
        enabled_when = {"conditions": []}
    conditions = enabled_when.get("conditions")
    if not isinstance(conditions, list):
        conditions = []
    if "phase_key" in fields_map:
        conditions.append({"source": "record", "field": "phase_key", "op": "not_in", "value": ["archive"]})
    if "stage_id" in fields_map:
        conditions.append({"source": "record", "field": "stage_id", "op": "truthy"})
    enabled_when["conditions"] = conditions
    if conditions:
        enabled_when["condition_expr"] = {"op": "and", "items": [item for item in conditions if isinstance(item, dict)]}
    policy["enabled_when"] = enabled_when


def _build_form_action_policies(data: dict) -> dict[str, dict[str, Any]]:
    required_fields = _resolve_contract_required_fields(data, _as_dict(data.get("fields")))
    policies: dict[str, dict[str, Any]] = {}
    buttons = data.get("buttons")
    if not isinstance(buttons, list):
        return policies
    lifecycle_field = ""
    lifecycle_blocked_states: list[str] = []
    fields_map = _as_dict(data.get("fields"))
    scene_profile = _resolve_form_scene_profile(data)
    lifecycle_desc = _as_dict(fields_map.get("lifecycle_state"))
    if lifecycle_desc:
        lifecycle_field = "lifecycle_state"
        selection = lifecycle_desc.get("selection")
        rows = selection if isinstance(selection, list) else []
        for row in rows:
            if not isinstance(row, (list, tuple)) or len(row) < 2:
                continue
            key = _safe_text(row[0]).lower()
            label = _safe_text(row[1]).lower()
            merged = f"{key} {label}"
            if any(token in merged for token in ("close", "closed", "done", "archive", "竣工", "关闭", "归档")):
                lifecycle_blocked_states.append(_safe_text(row[0]))
    for row in buttons:
        if not isinstance(row, dict):
            continue
        key = _safe_text(row.get("key"))
        if not key:
            continue
        semantic = _safe_text(row.get("semantic"), "secondary")
        visible_profiles = row.get("visible_profiles") if isinstance(row.get("visible_profiles"), list) else []
        normalized_visible = [
            _safe_text(item).lower()
            for item in visible_profiles
            if _safe_text(item).lower() in _RENDER_PROFILES
        ]
        policy = _default_action_policy(semantic, normalized_visible, required_fields)
        row_groups = row.get("groups_xmlids") if isinstance(row.get("groups_xmlids"), list) else []
        required_groups = [
            _safe_text(item)
            for item in row_groups
            if _safe_text(item)
        ]
        required_roles_raw = row.get("required_roles") if isinstance(row.get("required_roles"), list) else []
        required_roles = [
            _safe_text(item).lower()
            for item in required_roles_raw
            if _safe_text(item)
        ]
        required_capabilities = row.get("required_capabilities")
        if not isinstance(required_capabilities, list):
            required_capabilities = row.get("capabilities")
        required_capabilities = [
            _safe_text(item)
            for item in (required_capabilities if isinstance(required_capabilities, list) else [])
            if _safe_text(item)
        ]
        template_keys = _resolve_action_policy_template_keys(
            scene_profile=scene_profile,
            semantic=semantic,
            required_capabilities=required_capabilities,
            required_groups=required_groups,
            required_roles=required_roles,
            lifecycle_field=lifecycle_field,
            lifecycle_blocked_states=lifecycle_blocked_states,
        )
        _apply_action_policy_templates(
            policy,
            template_keys,
            required_fields=required_fields,
            required_capabilities=required_capabilities,
            lifecycle_field=lifecycle_field,
            lifecycle_blocked_states=lifecycle_blocked_states,
            required_groups=required_groups,
            required_roles=required_roles,
            fields_map=fields_map,
        )
        policies[key] = policy
    return policies


def _govern_enterprise_company_form_for_user(data: dict) -> None:
    if not _is_enterprise_company_form_contract(data):
        return
    fields_map = _as_dict(data.get("fields"))
    selected = [name for name in _ENTERPRISE_COMPANY_FORM_FIELDS if name in fields_map]
    if not selected:
        return
    data["visible_fields"] = selected
    data["field_groups"] = [
        {
            "name": "core",
            "label": "企业基础信息",
            "priority": 1,
            "collapsible": False,
            "fields": selected,
        },
    ]
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    form["layout"] = [
        {
            "type": "sheet",
            "name": "enterprise_company_form_sheet",
            "children": [
                {
                    "type": "group",
                    "name": "enterprise_company_core_group",
                    "string": "企业基础信息",
                    "children": [
                        _make_labeled_field_node(name, fields_map, _ENTERPRISE_COMPANY_FIELD_LABELS)
                        for name in selected
                    ],
                }
            ],
        }
    ]
    views["form"] = form
    data["views"] = views

    if _resolve_render_profile(data) == _RENDER_PROFILE_CREATE:
        toolbar = _as_dict(data.get("toolbar"))
        if isinstance(toolbar.get("header"), list):
            toolbar["header"] = []
        data["toolbar"] = toolbar
        data["buttons"] = []
        data["action_groups"] = []
    _inject_enterprise_form_governance(
        data,
        next_action_key="department",
        next_action_label="进入组织架构",
    )


def _govern_enterprise_department_form_for_user(data: dict) -> None:
    if _governance_primary_model(data) != "hr.department":
        return
    if not _is_form_contract(data):
        return
    fields_map = _as_dict(data.get("fields"))
    selected = [name for name in _ENTERPRISE_DEPARTMENT_FORM_FIELDS if name in fields_map]
    if not selected:
        return
    data["visible_fields"] = selected
    data["field_groups"] = [
        {
            "name": "core",
            "label": "组织基础信息",
            "priority": 1,
            "collapsible": False,
            "fields": selected,
        },
    ]
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    form["layout"] = [
        {
            "type": "sheet",
            "name": "enterprise_department_form_sheet",
            "children": [
                {
                    "type": "group",
                    "name": "enterprise_department_core_group",
                    "string": "组织基础信息",
                    "children": [
                        _make_labeled_field_node(name, fields_map, _ENTERPRISE_DEPARTMENT_FIELD_LABELS)
                        for name in selected
                    ],
                }
            ],
        }
    ]
    views["form"] = form
    data["views"] = views

    if _resolve_render_profile(data) == _RENDER_PROFILE_CREATE:
        toolbar = _as_dict(data.get("toolbar"))
        if isinstance(toolbar.get("header"), list):
            toolbar["header"] = []
        data["toolbar"] = toolbar
        data["buttons"] = []
        data["action_groups"] = []
    _inject_enterprise_form_governance(
        data,
        next_action_key="user",
        next_action_label="进入用户设置",
    )


def _govern_enterprise_user_form_for_user(data: dict) -> None:
    if not _is_enterprise_user_form_contract(data):
        return
    fields_map = _as_dict(data.get("fields"))
    selected = [name for name in _ENTERPRISE_USER_FORM_FIELDS if name in fields_map]
    if not selected:
        return
    data["visible_fields"] = selected
    data["field_groups"] = [
        {
            "name": "basic",
            "label": "用户基础信息",
            "priority": 1,
            "collapsible": False,
            "fields": [name for name in selected if name in {"name", "login", "password", "phone", "active"}],
        },
        {
            "name": "assignment",
            "label": "组织与角色",
            "priority": 2,
            "collapsible": False,
            "fields": [
                name
                for name in selected
                if name in {"company_id", "sc_department_id", "sc_manager_user_id", "sc_role_profile", "sc_role_effective", "sc_role_landing_label"}
            ],
        },
    ]
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    form["layout"] = [
        {
            "type": "sheet",
            "name": "enterprise_user_form_sheet",
            "children": [
                {
                    "type": "group",
                    "name": "enterprise_user_basic_group",
                    "string": "用户基础信息",
                    "children": [
                        _make_labeled_field_node(name, fields_map, _ENTERPRISE_USER_FIELD_LABELS)
                        for name in selected
                        if name in {"name", "login", "password", "phone", "active"}
                    ],
                },
                {
                    "type": "group",
                    "name": "enterprise_user_assignment_group",
                    "string": "组织与角色",
                    "children": [
                        _make_labeled_field_node(name, fields_map, _ENTERPRISE_USER_FIELD_LABELS)
                        for name in selected
                        if name in {"company_id", "sc_department_id", "sc_manager_user_id", "sc_role_profile", "sc_role_effective", "sc_role_landing_label"}
                    ],
                },
            ],
        }
    ]
    views["form"] = form
    data["views"] = views

    field_policies = _as_dict(data.get("field_policies"))
    basic_fields = {"name", "login", "password", "phone", "active"}
    readonly_fields = {"sc_role_effective", "sc_role_landing_label"}
    contract_required_fields = set(_resolve_contract_required_fields(data, fields_map))
    for name in selected:
        descriptor = _as_dict(fields_map.get(name))
        readonly = name in readonly_fields or _to_bool(descriptor.get("readonly"), fallback=False)
        field_policies[name] = {
            "visible_profiles": [
                _RENDER_PROFILE_CREATE,
                _RENDER_PROFILE_EDIT,
                _RENDER_PROFILE_READONLY,
            ],
            "required_profiles": (
                [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT]
                if name in contract_required_fields and not readonly
                else []
            ),
            "readonly_profiles": (
                [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
                if readonly
                else [_RENDER_PROFILE_READONLY]
            ),
            "source_required": name in contract_required_fields and not readonly,
            "source_readonly": readonly,
            "group": "core" if name in basic_fields else "secondary",
        }
    data["field_policies"] = field_policies

    if _resolve_render_profile(data) == _RENDER_PROFILE_CREATE:
        toolbar = _as_dict(data.get("toolbar"))
        if isinstance(toolbar.get("header"), list):
            toolbar["header"] = []
        data["toolbar"] = toolbar
        data["buttons"] = []
        data["action_groups"] = []
    _inject_enterprise_form_governance(data)


def _build_form_validation_rules(data: dict, contract_mode: str) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    fields_map = _as_dict(data.get("fields"))
    required_fields = _resolve_contract_required_fields(data, fields_map)
    for name in required_fields:
        descriptor = _as_dict(fields_map.get(name))
        if not descriptor:
            continue
        readonly = _to_bool(descriptor.get("readonly"), fallback=False)
        if not readonly:
            rules.append(
                {
                    "code": "REQUIRED",
                    "field": name,
                    "when_profiles": [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT],
                    "message": f"{_safe_text(descriptor.get('string'), name)} 为必填字段",
                }
            )
    record_rules = _as_dict(_as_dict(data.get("validator")).get("record_rules"))
    for row in record_rules.get("sql_checks") if isinstance(record_rules.get("sql_checks"), list) else []:
        if not isinstance(row, dict):
            continue
        message = _safe_text(row.get("message"))
        definition = _safe_text(row.get("definition"))
        if not message and not definition:
            continue
        item = {
            "code": "SQL_CHECK",
            "name": _safe_text(row.get("name")),
            "message": message or definition,
        }
        if contract_mode == "hud":
            item["expr"] = definition
        rules.append(item)
    return rules


def _apply_form_policy_contract(data: dict, contract_mode: str) -> None:
    data["field_policies"] = _build_form_field_policies(data)
    data["action_policies"] = _build_form_action_policies(data)
    data["validation_rules"] = _build_form_validation_rules(data, contract_mode)


def _classify_field_semantic_type(name: str, descriptor: dict) -> str:
    low = _safe_lower(name)
    ttype = _safe_lower(descriptor.get("type") or descriptor.get("ttype"))
    if _is_technical_field(name, descriptor):
        return "technical"
    if ttype in {"many2one", "one2many", "many2many"}:
        return "relation"
    if descriptor.get("compute") or descriptor.get("related"):
        return "computed"
    if low in {"active", "company_id", "create_uid", "create_date", "write_uid", "write_date"}:
        return "system"
    return "business"


def _annotate_field_semantics(data: dict) -> None:
    fields_map = _as_dict(data.get("fields"))
    if not fields_map:
        return
    field_groups = data.get("field_groups") if isinstance(data.get("field_groups"), list) else []
    core_set: set[str] = set()
    advanced_set: set[str] = set()
    for item in field_groups:
        if not isinstance(item, dict):
            continue
        key = _safe_lower(item.get("name"))
        names = item.get("fields") if isinstance(item.get("fields"), list) else []
        normalized = {_safe_text(name) for name in names if _safe_text(name)}
        if key == "core":
            core_set.update(normalized)
        elif key == "advanced":
            advanced_set.update(normalized)

    field_policies = _as_dict(data.get("field_policies"))
    semantics_map: dict[str, dict[str, Any]] = {}
    for field_name, raw_descriptor in list(fields_map.items()):
        descriptor = _as_dict(raw_descriptor)
        if not descriptor:
            continue
        semantic_type = _classify_field_semantic_type(field_name, descriptor)
        policy = _as_dict(field_policies.get(field_name))
        policy_group = _safe_lower(policy.get("group"))
        visible_profiles = policy.get("visible_profiles") if isinstance(policy.get("visible_profiles"), list) else []
        normalized_profiles = {_safe_lower(item) for item in visible_profiles if _safe_text(item)}
        has_surface_visibility = bool(normalized_profiles & {_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY})

        if policy_group in {"core", "advanced"}:
            surface_role = policy_group
        elif field_name in core_set:
            surface_role = "core"
        elif field_name in advanced_set:
            surface_role = "advanced"
        elif semantic_type == "technical" or not has_surface_visibility:
            surface_role = "hidden"
        else:
            surface_role = "advanced"

        descriptor["semantic_type"] = semantic_type
        descriptor["surface_role"] = surface_role
        descriptor["technical"] = semantic_type == "technical"
        fields_map[field_name] = descriptor
        semantics_map[field_name] = {
            "semantic_type": semantic_type,
            "surface_role": surface_role,
            "technical": semantic_type == "technical",
        }

    data["fields"] = fields_map
    data["field_semantics"] = semantics_map


def _canonicalize_contract_keys(
    obj: Any,
    *,
    path: str = "$",
    conflicts: list[dict[str, Any]] | None = None,
) -> Any:
    conflicts = conflicts if isinstance(conflicts, list) else []
    if isinstance(obj, list):
        return [
            _canonicalize_contract_keys(item, path=f"{path}[{idx}]", conflicts=conflicts)
            for idx, item in enumerate(obj)
        ]
    if not isinstance(obj, dict):
        return obj
    out: dict[str, Any] = {}
    source_keys: dict[str, str] = {}
    for raw_key, raw_val in obj.items():
        key = str(raw_key)
        canonical = _CONTRACT_KEY_CANONICAL_MAP.get(key, key)
        normalized_val = _canonicalize_contract_keys(raw_val, path=f"{path}.{canonical}", conflicts=conflicts)
        if canonical not in out:
            out[canonical] = normalized_val
            source_keys[canonical] = key
            continue
        previous = source_keys.get(canonical, canonical)
        snake_preferred = canonical
        should_replace = key == snake_preferred and previous != snake_preferred
        conflicts.append(
            {
                "path": f"{path}.{canonical}",
                "canonical": canonical,
                "kept_from": key if should_replace else previous,
                "dropped_from": previous if should_replace else key,
            }
        )
        if should_replace:
            out[canonical] = normalized_val
            source_keys[canonical] = key
    return out


def register_contract_domain_override(
    name: str,
    handler: Any,
    *,
    priority: int = 100,
) -> None:
    if not callable(handler):
        return
    normalized_name = _safe_text(name, "unnamed_override")
    for row in _DOMAIN_OVERRIDE_REGISTRY:
        if _safe_text(row.get("name")) == normalized_name:
            row["handler"] = handler
            row["priority"] = int(priority)
            return
    _DOMAIN_OVERRIDE_REGISTRY.append(
        {
            "name": normalized_name,
            "priority": int(priority),
            "handler": handler,
        }
    )
    _DOMAIN_OVERRIDE_REGISTRY.sort(key=lambda item: int(item.get("priority") or 100))


def _append_governance_diagnostic(data: dict, key: str, value: Any) -> None:
    diagnostic = data.get("diagnostic")
    if not isinstance(diagnostic, dict):
        diagnostic = {}
    diagnostic[key] = value
    data["diagnostic"] = diagnostic


def _apply_domain_overrides(data: dict, contract_mode: str) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for row in _DOMAIN_OVERRIDE_REGISTRY:
        handler = row.get("handler")
        if not callable(handler):
            continue
        try:
            handler(data, contract_mode)
        except Exception as exc:
            failures.append(
                {
                    "name": _safe_text(row.get("name")),
                    "error_type": exc.__class__.__name__,
                    "message": _safe_text(str(exc))[:240],
                }
            )
            continue
    return failures


def apply_project_form_domain_override(data: dict, contract_mode: str) -> None:
    if contract_mode in {"user", "hud"} and _is_project_form_contract(data):
        _restructure_project_form_layout(data)
    if contract_mode == "user" and _is_project_form_contract(data):
        _govern_project_form_contract_for_user(data)
    if contract_mode == "user" and _is_project_task_form_contract(data):
        _govern_project_task_form_for_user(data)
    if contract_mode == "user":
        _govern_standard_list_for_user(
            data,
            model_name="project.project",
            columns_order=_PROJECT_LIST_COLUMNS,
            column_labels=_PROJECT_LIST_COLUMN_LABELS,
            row_primary="name",
            row_secondary="stage_id",
            status_field="lifecycle_state",
        )
        _govern_standard_list_for_user(
            data,
            model_name="project.task",
            columns_order=_PROJECT_TASK_LIST_COLUMNS,
            column_labels=_PROJECT_TASK_LIST_COLUMN_LABELS,
            row_primary="name",
            row_secondary="project_id",
            status_field="sc_state",
        )
    if contract_mode == "user" and _is_enterprise_company_form_contract(data):
        _govern_enterprise_company_form_for_user(data)
    if contract_mode == "user":
        _govern_enterprise_department_form_for_user(data)
    if contract_mode == "user" and _is_enterprise_user_form_contract(data):
        _govern_enterprise_user_form_for_user(data)
    if contract_mode == "user" and _is_project_kanban_contract(data):
        _govern_project_kanban_contract_for_user(data)


def _apply_sanitize_governance(data: dict, contract_mode: str) -> None:
    if isinstance(data.get("capabilities"), list):
        capabilities = normalize_capabilities(data.get("capabilities") or [])
        if contract_mode == "user":
            capabilities = [item for item in capabilities if not is_internal_or_smoke(item)]
            capabilities = [item for item in capabilities if not _has_demo_semantics(item)]
            capabilities = [_sanitize_capability_for_user(item) for item in capabilities]
        data["capabilities"] = capabilities

    if isinstance(data.get("scenes"), list):
        scenes = normalize_scenes(data.get("scenes") or [])
        if contract_mode == "user":
            scenes = [item for item in scenes if not is_internal_or_smoke(item)]
            scenes = [item for item in scenes if not _has_demo_semantics(item)]
            scenes = [_sanitize_scene_for_user(item) for item in scenes]
            scenes = [item for item in scenes if not _has_demo_semantics(item)]
        data["scenes"] = scenes

    if contract_mode != "hud":
        for key in _NON_HUD_STRIP_KEYS:
            data.pop(key, None)
    if contract_mode == "user":
        _apply_user_surface_noise_reduction(data)
        _apply_user_surface_policies(data)


def _apply_semantic_governance(data: dict, contract_mode: str) -> None:
    if _is_form_contract(data):
        _apply_form_render_semantics(data, contract_mode)


def normalize_scenes(scenes: list) -> list[dict]:
    out: list[dict] = []
    for scene in scenes or []:
        if not isinstance(scene, dict):
            continue
        item = dict(scene)
        code = _safe_text(item.get("code") or item.get("key"))
        item["code"] = code or item.get("code")
        item["key"] = _safe_text(item.get("key"), code)
        item["name"] = _safe_text(item.get("name"), code or "未命名场景")
        item["list_profile"] = _normalize_scene_list_profile(item)
        item["scene_meta"] = _derive_scene_meta(item)
        item["tags"] = _normalized_tags_for_item(item)
        out.append(item)
    return out


def _deep_clone_json_like(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _deep_clone_json_like(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deep_clone_json_like(v) for v in obj]
    return obj


def _collect_layout_snapshot(layout: Any) -> dict[str, Any]:
    field_order: list[str] = []
    node_signatures: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        node_type = _safe_lower(node.get("type"))
        node_name = _safe_text(node.get("name"))
        node_label = _safe_text(node.get("string") or node.get("label"))
        node_signatures.append(f"{node_type}:{node_name or node_label}")
        if node_type == "field":
            if node_name and node_name not in field_order:
                field_order.append(node_name)
        for key in ("children", "tabs", "pages", "nodes", "items"):
            walk(node.get(key))

    walk(layout)
    return {
        "field_order": field_order,
        "node_signatures": node_signatures,
    }


def _collect_action_snapshot(rows: Any) -> list[str]:
    out: list[str] = []
    if not isinstance(rows, list):
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = _safe_text(row.get("key"))
        name = _safe_text(row.get("name"))
        method = _safe_text(_as_dict(row.get("payload")).get("method"))
        label = _safe_text(row.get("label"))
        signature = key or name or method or label
        if signature and signature not in out:
            out.append(signature)
    return out


def _collect_surface_snapshot(data: dict) -> dict[str, Any]:
    fields_map = _as_dict(data.get("fields"))
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    layout_info = _collect_layout_snapshot(layout if isinstance(layout, list) else [])
    field_modifiers = _as_dict(form.get("field_modifiers"))
    buttons = _collect_action_snapshot(data.get("buttons"))
    header_buttons = _collect_action_snapshot(form.get("header_buttons"))
    stat_buttons = _collect_action_snapshot(form.get("stat_buttons"))

    return {
        "fields": list(fields_map.keys()),
        "layout_field_order": layout_info.get("field_order") or [],
        "layout_nodes": layout_info.get("node_signatures") or [],
        "buttons": buttons,
        "header_buttons": header_buttons,
        "stat_buttons": stat_buttons,
        "field_modifiers": list(field_modifiers.keys()),
    }


def _build_surface_mapping(native_snapshot: dict[str, Any], governed_snapshot: dict[str, Any]) -> dict[str, Any]:
    native_fields = [x for x in native_snapshot.get("fields", []) if _safe_text(x)]
    governed_fields = [x for x in governed_snapshot.get("fields", []) if _safe_text(x)]
    native_layout_fields = [x for x in native_snapshot.get("layout_field_order", []) if _safe_text(x)]
    governed_layout_fields = [x for x in governed_snapshot.get("layout_field_order", []) if _safe_text(x)]

    def diff(native_rows: list[str], governed_rows: list[str]) -> dict[str, Any]:
        native_set = set(native_rows)
        governed_set = set(governed_rows)
        removed = sorted([x for x in native_rows if x not in governed_set])
        added = sorted([x for x in governed_rows if x not in native_set])
        reordered = bool(native_rows and governed_rows and native_rows != governed_rows and not removed and not added)
        return {
            "native_count": len(native_rows),
            "governed_count": len(governed_rows),
            "removed": removed,
            "added": added,
            "reordered": reordered,
        }

    return {
        "native_to_governed": {
            "fields": diff(native_fields, governed_fields),
            "layout_fields": diff(native_layout_fields, governed_layout_fields),
            "layout_nodes": diff(
                [x for x in native_snapshot.get("layout_nodes", []) if _safe_text(x)],
                [x for x in governed_snapshot.get("layout_nodes", []) if _safe_text(x)],
            ),
            "buttons": diff(
                [x for x in native_snapshot.get("buttons", []) if _safe_text(x)],
                [x for x in governed_snapshot.get("buttons", []) if _safe_text(x)],
            ),
            "header_buttons": diff(
                [x for x in native_snapshot.get("header_buttons", []) if _safe_text(x)],
                [x for x in governed_snapshot.get("header_buttons", []) if _safe_text(x)],
            ),
            "stat_buttons": diff(
                [x for x in native_snapshot.get("stat_buttons", []) if _safe_text(x)],
                [x for x in governed_snapshot.get("stat_buttons", []) if _safe_text(x)],
            ),
            "field_modifiers": diff(
                [x for x in native_snapshot.get("field_modifiers", []) if _safe_text(x)],
                [x for x in governed_snapshot.get("field_modifiers", []) if _safe_text(x)],
            ),
        }
    }


def apply_contract_governance(
    data: dict | Any,
    contract_mode: str,
    *,
    contract_surface: str = "user",
    source_mode: str = "",
    inject_contract_mode: bool = True,
) -> dict | Any:
    if not isinstance(data, dict):
        return data

    pipeline = ["canonicalize", "sanitize", "semantic", "domain_overrides", "inject_mode"]
    key_conflicts: list[dict[str, Any]] = []
    data = _canonicalize_contract_keys(data, conflicts=key_conflicts)

    normalized_surface = str(contract_surface or "").strip().lower()
    if normalized_surface not in CONTRACT_SURFACES:
        normalized_surface = "hud" if contract_mode == "hud" else "user"

    native_snapshot = _collect_surface_snapshot(_deep_clone_json_like(data))

    nested_payload = data.get("data")
    if isinstance(nested_payload, dict):
        data["data"] = apply_contract_governance(
            nested_payload,
            contract_mode,
            contract_surface=normalized_surface,
            source_mode=source_mode,
            inject_contract_mode=False,
        )

    _normalize_native_view_contract_surface(data)
    _normalize_scene_semantic_surface(data)

    effective_mode = contract_mode
    if normalized_surface == "native":
        # Native surface keeps parser-origin structure and skips user/hud policy transforms.
        effective_mode = "hud"

    if normalized_surface != "native":
        _apply_sanitize_governance(data, effective_mode)
        _apply_semantic_governance(data, effective_mode)
        override_failures = _apply_domain_overrides(data, effective_mode)
    else:
        override_failures = []
    _annotate_field_semantics(data)

    governed_snapshot = _collect_surface_snapshot(data)
    surface_mapping = _build_surface_mapping(native_snapshot, governed_snapshot)

    if inject_contract_mode:
        data["contract_mode"] = contract_mode
    data["contract_surface"] = normalized_surface
    data["render_mode"] = "native" if normalized_surface == "native" else "governed"
    data["source_mode"] = _safe_text(
        source_mode,
        "native_parser" if normalized_surface == "native" else "governance_pipeline",
    )
    data["governed_from_native"] = normalized_surface != "native"
    data["surface_mapping"] = surface_mapping
    if contract_mode == "hud":
        if key_conflicts:
            _append_governance_diagnostic(data, "contract_key_conflicts", key_conflicts)
        if override_failures:
            _append_governance_diagnostic(data, "domain_override_failures", override_failures)
        _append_governance_diagnostic(data, "governance_pipeline", pipeline)
    return data
