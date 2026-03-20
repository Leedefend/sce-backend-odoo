# -*- coding: utf-8 -*-
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
from typing import Any, Dict

def _load_semantics_registry() -> Dict[str, Any]:
    registry_path = Path(__file__).with_name("orchestration_semantics.py")
    try:
        spec = spec_from_file_location("smart_core_orchestration_semantics_page_contracts", registry_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec unavailable")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return {
            "STATE_TONES": tuple(getattr(module, "STATE_TONES", ()) or ()),
            "PROGRESS_STATES": tuple(getattr(module, "PROGRESS_STATES", ()) or ()),
        }
    except Exception:
        return {}


_SEM = _load_semantics_registry()
STATE_TONES = _SEM.get("STATE_TONES") or ("success", "warning", "danger", "info", "neutral")
PROGRESS_STATES = _SEM.get("PROGRESS_STATES") or ("overdue", "blocked", "pending", "running", "completed")
SUPPORTED_ROLE_CODES = {"pm", "finance", "owner"}
_ACTION_TARGET_RESOLVER = None
_DATA_PROVIDER_MODULE = None


def _shared_action_target(action_key: str, page_key: str) -> Dict[str, Any]:
    global _ACTION_TARGET_RESOLVER
    if callable(_ACTION_TARGET_RESOLVER):
        return _ACTION_TARGET_RESOLVER(action_key, page_key)
    helper_path = Path(__file__).with_name("action_target_schema.py")
    try:
        spec = spec_from_file_location("smart_core_action_target_schema_page_contracts", helper_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec unavailable")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        resolver = getattr(module, "resolve_action_target", None)
        if callable(resolver):
            _ACTION_TARGET_RESOLVER = resolver
            return resolver(action_key, page_key)
    except Exception:
        pass
    fallback_scene = str(page_key or "").strip().lower() or "portal.dashboard"
    return {"kind": "scene.key", "scene_key": fallback_scene}


def _load_data_provider():
    global _DATA_PROVIDER_MODULE
    if _DATA_PROVIDER_MODULE is not None:
        return _DATA_PROVIDER_MODULE
    provider_path = Path(__file__).with_name("page_orchestration_data_provider.py")
    try:
        spec = spec_from_file_location("smart_core_page_orchestration_data_provider", provider_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec unavailable")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        _DATA_PROVIDER_MODULE = module
        return module
    except Exception:
        _DATA_PROVIDER_MODULE = False
        return None


def _resolve_role_source_code(data: Dict[str, Any]) -> str:
    role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
    role_code = str(role_surface.get("role_code") or "").strip().lower()
    if role_code:
        return role_code
    return "owner"


def _normalize_role_code(data: Dict[str, Any]) -> str:
    role_code = _resolve_role_source_code(data)
    if role_code in SUPPORTED_ROLE_CODES:
        return role_code
    return "owner"


def _normalize_page_type(page_key: str) -> str:
    provider = _load_data_provider()
    if provider:
        fn = getattr(provider, "build_page_type", None)
        if callable(fn):
            value = str(fn(page_key) or "").strip()
            if value:
                return value
    key = str(page_key or "").strip().lower()
    if key in {"home", "workbench"}:
        return "workspace"
    if key in {"login", "menu", "placeholder"}:
        return "entry_hub"
    if key in {"my_work"}:
        return "approval"
    if key in {"scene_health", "usage_analytics"}:
        return "monitor"
    if key in {"action", "record", "scene"}:
        return "detail"
    return "list"


def _page_audience(page_key: str) -> list[str]:
    provider = _load_data_provider()
    if provider:
        fn = getattr(provider, "build_page_audience", None)
        if callable(fn):
            value = fn(page_key)
            if isinstance(value, list) and value:
                return value
    key = str(page_key or "").strip().lower()
    if key in {"usage_analytics", "scene_health"}:
        return ["executive", "owner", "project_manager"]
    if key in {"my_work", "action", "record"}:
        return ["project_manager", "finance_manager", "owner"]
    if key in {"home", "workbench"}:
        return ["project_manager", "finance_manager", "owner", "executive"]
    return ["generic_user"]


def _role_section_policy(role_code: str) -> Dict[str, Dict[str, list[str]]]:
    provider = _load_data_provider()
    if provider:
        fn = getattr(provider, "build_role_section_policy", None)
        if callable(fn):
            value = fn(role_code)
            if isinstance(value, dict):
                return value
    policies: Dict[str, Dict[str, Dict[str, list[str]]]] = {
        "pm": {
            "usage_analytics": {"disable": ["tables_role_user"]},
            "scene_health": {"disable": ["details_debt"]},
        },
        "finance": {
            "action": {"disable": ["group_view"]},
            "record": {"disable": ["dev_context"]},
        },
        "owner": {
            "workbench": {"disable": ["hud_details"]},
            "action": {"disable": ["advanced_view", "dev_context"]},
            "record": {"disable": ["dev_context"]},
            "scene_health": {"disable": ["details_drift", "details_debt"]},
        },
    }
    return policies.get(role_code, {})


def _apply_role_section_policy(payload: Dict[str, Any], role_code: str) -> None:
    pages = payload.get("pages") if isinstance(payload.get("pages"), dict) else {}
    if not isinstance(pages, dict):
        return
    policies = _role_section_policy(role_code)
    if not policies:
        return
    for page_key, cfg in policies.items():
        page = pages.get(page_key) if isinstance(pages.get(page_key), dict) else {}
        sections = page.get("sections") if isinstance(page.get("sections"), list) else []
        disable = {str(key).strip() for key in (cfg.get("disable") or []) if str(key).strip()}
        if not disable:
            continue
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_key = str(section.get("key") or "").strip()
            if section_key in disable:
                section["enabled"] = False


def _role_zone_order(role_code: str, page_type: str, page_key: str = "") -> list[str]:
    provider = _load_data_provider()
    if provider:
        fn = getattr(provider, "build_role_zone_order", None)
        if callable(fn):
            value = fn(role_code, page_type, page_key)
            if isinstance(value, list) and value:
                return value
    page = str(page_key or "").strip().lower()
    if page == "action":
        if role_code == "finance":
            return ["secondary", "primary", "hero", "supporting"]
        if role_code == "owner":
            return ["primary", "secondary", "hero", "supporting"]
        return ["primary", "secondary", "hero", "supporting"]
    if page_type == "monitor":
        return ["hero", "secondary", "primary", "supporting"] if role_code == "finance" else ["hero", "primary", "secondary", "supporting"]
    if page_type == "approval":
        return ["hero", "primary", "supporting", "secondary"] if role_code == "pm" else ["hero", "secondary", "primary", "supporting"]
    if page_type == "detail":
        return ["hero", "primary", "secondary", "supporting"] if role_code != "owner" else ["hero", "supporting", "primary", "secondary"]
    return ["hero", "primary", "secondary", "supporting"]


def _role_focus_sections(role_code: str, page_key: str) -> list[str]:
    provider = _load_data_provider()
    if provider:
        fn = getattr(provider, "build_role_focus_sections", None)
        if callable(fn):
            value = fn(role_code, page_key)
            if isinstance(value, list):
                return value
    page = str(page_key or "").strip().lower()
    mapping: Dict[str, Dict[str, list[str]]] = {
        "pm": {
            "workbench": ["status_panel", "tiles"],
            "action": ["quick_actions", "quick_filters"],
            "record": ["project_summary", "next_actions"],
            "my_work": ["todo_focus", "list_main"],
        },
        "finance": {
            "workbench": ["status_panel"],
            "action": ["quick_filters", "group_summary"],
            "record": ["project_summary"],
            "usage_analytics": ["summary_usage", "tables_daily"],
        },
        "owner": {
            "workbench": ["header", "status_panel"],
            "scene_health": ["cards", "governance"],
            "usage_analytics": ["summary_visibility", "tables_top"],
            "action": ["focus_strip"],
        },
    }
    return mapping.get(role_code, {}).get(page, [])


def _zone_from_tag(tag: str) -> Dict[str, str]:
    provider = _load_data_provider()
    if provider:
        fn = getattr(provider, "build_zone_from_tag", None)
        if callable(fn):
            payload = fn(tag)
            if isinstance(payload, dict) and payload:
                return payload
    normalized = str(tag or "").strip().lower()
    if normalized == "header":
        return {"key": "hero", "title": "页面头部", "zone_type": "hero", "display_mode": "stack"}
    if normalized == "details":
        return {"key": "supporting", "title": "辅助信息", "zone_type": "supporting", "display_mode": "accordion"}
    if normalized == "div":
        return {"key": "secondary", "title": "扩展信息", "zone_type": "secondary", "display_mode": "flow"}
    return {"key": "primary", "title": "主体内容", "zone_type": "primary", "display_mode": "stack"}


def _semantic_from_section(page_key: str, section_key: str, tag: str) -> Dict[str, Any]:
    provider = _load_data_provider()
    if provider:
        fn = getattr(provider, "build_semantic_from_section", None)
        if callable(fn):
            payload = fn(page_key, section_key, tag)
            if isinstance(payload, dict) and payload:
                return payload
    key = str(section_key or "").strip().lower()
    page = str(page_key or "").strip().lower()
    normalized_tag = str(tag or "").strip().lower()

    if normalized_tag == "header":
        return {"block_type": "record_summary", "tone": "info", "progress": "running", "importance": "high"}
    if normalized_tag == "details":
        return {"block_type": "accordion_group", "tone": "neutral", "progress": "completed", "importance": "medium"}
    if normalized_tag == "div":
        return {"block_type": "activity_feed", "tone": "neutral", "progress": "running", "importance": "medium"}

    if any(token in key for token in ("error", "forbidden", "risk", "warning", "blocked")):
        return {"block_type": "alert_panel", "tone": "danger", "progress": "blocked", "importance": "high"}
    if any(token in key for token in ("loading", "pending", "status_loading")):
        return {"block_type": "progress_summary", "tone": "info", "progress": "running", "importance": "medium"}
    if any(token in key for token in ("summary", "kpi", "metric", "cards", "hero", "project_summary")):
        return {"block_type": "metric_row", "tone": "info", "progress": "running", "importance": "high"}
    if any(token in key for token in ("todo", "approval", "quick_actions", "next_actions")):
        return {"block_type": "todo_list", "tone": "warning", "progress": "pending", "importance": "high"}
    if any(token in key for token in ("filter", "group", "slice", "preset", "tiles")):
        return {"block_type": "entry_grid", "tone": "neutral", "progress": "completed", "importance": "medium"}
    if any(token in key for token in ("table", "list", "daily", "top", "visibility")):
        return {"block_type": "activity_feed", "tone": "neutral", "progress": "running", "importance": "medium"}
    if page in {"login", "menu", "placeholder"}:
        return {"block_type": "record_summary", "tone": "neutral", "progress": "running", "importance": "medium"}
    return {"block_type": "record_summary", "tone": "neutral", "progress": "running", "importance": "medium"}


def _action_templates(section_key: str) -> list[Dict[str, Any]]:
    provider = _load_data_provider()
    if provider:
        fn = getattr(provider, "build_action_templates", None)
        if callable(fn):
            payload = fn(section_key)
            if isinstance(payload, list):
                return payload
    key = str(section_key or "").strip().lower()
    if "risk" in key:
        return [{"key": "open_risk_dashboard", "label": "进入风险驾驶舱", "intent": "ui.contract"}]
    if any(token in key for token in ("approval", "todo", "next_actions")):
        return [{"key": "open_my_work", "label": "进入我的工作", "intent": "ui.contract"}]
    if any(token in key for token in ("filter", "group", "slice")):
        return [{"key": "apply_filters", "label": "应用筛选", "intent": "ui.contract"}]
    if any(token in key for token in ("table", "list", "records")):
        return [{"key": "open_list", "label": "查看明细", "intent": "ui.contract"}]
    return []


def _action_target(action_key: str, page_key: str) -> Dict[str, Any]:
    return _shared_action_target(action_key, page_key)


def _data_source_key(section_key: str) -> str:
    provider = _load_data_provider()
    if provider:
        fn = getattr(provider, "build_section_data_source_key", None)
        if callable(fn):
            value = str(fn(section_key) or "").strip()
            if value:
                return value
    token = re.sub(r"[^a-z0-9_]+", "_", str(section_key or "").strip().lower())
    token = re.sub(r"_+", "_", token).strip("_")
    if not token:
        token = "section"
    return f"ds_section_{token}"


def _base_data_sources() -> Dict[str, Dict[str, Any]]:
    provider = _load_data_provider()
    if provider:
        fn = getattr(provider, "build_base_data_sources", None)
        if callable(fn):
            payload = fn()
            if isinstance(payload, dict) and payload:
                return payload
    return {
        "ds_sections": {"source_type": "static", "provider": "page_contract.sections", "section_keys": ["_all"]},
    }


def _section_data_source(page_key: str, section_key: str, section_tag: str) -> Dict[str, Any]:
    provider = _load_data_provider()
    if provider:
        fn = getattr(provider, "build_section_data_source", None)
        if callable(fn):
            payload = fn(page_key, section_key, section_tag)
            if isinstance(payload, dict) and payload:
                return payload
    return {
        "source_type": "scene_context",
        "provider": "page_contract.section",
        "page_key": page_key,
        "section_key": section_key,
        "section_tag": section_tag,
        "section_keys": [section_key],
    }


def _default_page_actions(page_key: str) -> list[Dict[str, Any]]:
    provider = _load_data_provider()
    if provider:
        fn = getattr(provider, "build_default_page_actions", None)
        if callable(fn):
            payload = fn(page_key)
            if isinstance(payload, list) and payload:
                return payload
    key = str(page_key or "").strip().lower()
    if key == "home":
        return [
            {"key": "open_my_work", "label": "我的工作", "intent": "ui.contract"},
            {"key": "open_usage_analytics", "label": "使用分析", "intent": "ui.contract"},
        ]
    if key == "my_work":
        return [
            {"key": "open_workbench", "label": "返回工作台", "intent": "ui.contract"},
            {"key": "open_risk_dashboard", "label": "进入风险驾驶舱", "intent": "ui.contract"},
            {"key": "refresh_page", "label": "刷新", "intent": "api.data"},
        ]
    if key == "workbench":
        return [
            {"key": "open_workbench", "label": "返回工作台", "intent": "ui.contract"},
            {"key": "open_menu", "label": "打开菜单", "intent": "ui.contract"},
            {"key": "refresh_page", "label": "刷新", "intent": "api.data"},
        ]
    if key in {"scene_health", "usage_analytics", "scene_packages"}:
        return [
            {"key": "open_workbench", "label": "返回工作台", "intent": "ui.contract"},
            {"key": "refresh_page", "label": "刷新", "intent": "api.data"},
        ]
    if key in {"action", "record", "scene"}:
        return [
            {"key": "open_my_work", "label": "进入我的工作", "intent": "ui.contract"},
            {"key": "open_risk_dashboard", "label": "进入风险驾驶舱", "intent": "ui.contract"},
            {"key": "refresh_page", "label": "刷新", "intent": "api.data"},
        ]
    return [{"key": "refresh_page", "label": "刷新", "intent": "api.data"}]


def _build_page_orchestration_v1(
    page_key: str,
    page: Dict[str, Any],
    role_code: str,
    role_source_code: str | None = None,
) -> Dict[str, Any]:
    source_role_code = str(role_source_code or "").strip().lower() or role_code
    sections = page.get("sections") if isinstance(page.get("sections"), list) else []
    title = ""
    texts = page.get("texts") if isinstance(page.get("texts"), dict) else {}
    if isinstance(texts, dict):
        title = str(texts.get("title") or "").strip()
    if not title:
        title = page_key.replace("_", " ").strip().title() or "Page"

    audience = _page_audience(page_key)
    page_type = _normalize_page_type(page_key)
    zone_buckets: Dict[str, Dict[str, Any]] = {}
    data_sources: Dict[str, Dict[str, Any]] = _base_data_sources()
    focus_sections = {key: idx + 1 for idx, key in enumerate(_role_focus_sections(role_code, page_key))}
    for idx, section in enumerate(sections):
        if not isinstance(section, dict):
            continue
        section_key = str(section.get("key") or "").strip()
        if not section_key:
            continue
        tag = str(section.get("tag") or "section").strip().lower()
        enabled = bool(section.get("enabled") is True)
        order_raw = section.get("order")
        order = int(order_raw) if isinstance(order_raw, int) and order_raw > 0 else idx + 1
        zone_cfg = _zone_from_tag(tag)
        zone_key = zone_cfg["key"]
        zone = zone_buckets.get(zone_key)
        if zone is None:
            zone = {
                "key": zone_key,
                "title": zone_cfg["title"],
                "description": f"{page_key}::{zone_key}",
                "zone_type": zone_cfg["zone_type"],
                "display_mode": zone_cfg["display_mode"],
                "priority": 100 - (len(zone_buckets) * 10),
                "visibility": {"roles": audience, "capabilities": [], "expr": None},
                "blocks": [],
            }
            zone_buckets[zone_key] = zone

        semantic = _semantic_from_section(page_key, section_key, tag)
        data_source = _data_source_key(section_key)
        data_sources[data_source] = _section_data_source(page_key, section_key, tag)
        zone["blocks"].append(
            {
                "key": f"{page_key}.{section_key}",
                "block_type": semantic["block_type"],
                "title": section_key,
                "priority": max(1, 100 - order),
                "importance": semantic["importance"],
                "tone": semantic["tone"],
                "progress": semantic["progress"] if enabled else "pending",
                "section_key": section_key,
                "data_source": data_source,
                "loading_strategy": "eager" if tag == "header" else "lazy",
                "refreshable": True,
                "collapsible": bool(tag == "details"),
                "visibility": {"roles": audience, "capabilities": [], "expr": None},
                "actions": _action_templates(section_key),
                "payload": {"tag": tag, "enabled": enabled, "open": bool(section.get("open") is True)},
            }
        )

        if section_key in focus_sections:
            zone["blocks"][-1]["priority"] = 200 - focus_sections[section_key]
            zone["blocks"][-1]["focus"] = True
        else:
            zone["blocks"][-1]["focus"] = False

    zones = list(zone_buckets.values())
    zone_rank = {key: idx + 1 for idx, key in enumerate(_role_zone_order(role_code, page_type, page_key))}
    for zone in zones:
        zone_key = str(zone.get("key") or "").strip()
        zone["priority"] = 100 - ((zone_rank.get(zone_key, 99) - 1) * 10)
    for zone in zones:
        zone["blocks"] = sorted(
            zone.get("blocks") if isinstance(zone.get("blocks"), list) else [],
            key=lambda item: int(item.get("priority") or 0),
            reverse=True,
        )

    action_schema_actions: Dict[str, Any] = {}
    page_actions = _default_page_actions(page_key)
    for action in page_actions:
        action_key = str(action.get("key") or "").strip()
        if not action_key:
            continue
        action_schema_actions[action_key] = {
            "label": str(action.get("label") or action_key),
            "intent": str(action.get("intent") or "ui.contract"),
            "target": _action_target(action_key, page_key),
            "visibility": {"roles": [role_code], "capabilities": [], "expr": None},
        }
    for zone in zones:
        blocks = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            actions = block.get("actions") if isinstance(block.get("actions"), list) else []
            for action in actions:
                if not isinstance(action, dict):
                    continue
                action_key = str(action.get("key") or "").strip()
                if not action_key:
                    continue
                if action_key in action_schema_actions:
                    continue
                action_schema_actions[action_key] = {
                    "label": str(action.get("label") or action_key),
                    "intent": str(action.get("intent") or "ui.contract"),
                    "target": _action_target(action_key, page_key),
                    "visibility": {"roles": [role_code], "capabilities": [], "expr": None},
                }

    return {
        "contract_version": "page_orchestration_v1",
        "scene_key": page_key,
        "page": {
            "key": page_key,
            "title": title,
            "subtitle": "",
            "page_type": page_type,
            "intent": "ui.contract",
            "scene_key": page_key,
            "layout_mode": "monitoring" if page_type == "monitor" else "single_flow",
            "audience": audience,
            "priority_model": "risk_first" if page_type == "monitor" else "task_first" if page_type == "approval" else "role_first",
            "status": "ready",
            "breadcrumbs": [],
            "header": {},
            "global_actions": page_actions,
            "filters": [],
            "context": {"role_code": source_role_code},
        },
        "zones": zones,
        "data_sources": data_sources,
        "state_schema": {
            "tones": {key: {"icon": key} for key in STATE_TONES},
            "business_states": {
                key: {"tone": ("danger" if key in {"blocked", "overdue"} else "success" if key == "completed" else "info"), "label": key}
                for key in PROGRESS_STATES
            },
        },
        "action_schema": {"actions": action_schema_actions},
        "render_hints": {
            "dense_mode": False,
            "preferred_columns": 2 if page_type in {"monitor", "dashboard"} else 1,
            "mobile_priority": [zone.get("key") for zone in zones if isinstance(zone, dict)],
            "sticky_header": True,
        },
        "meta": {
            "generated_by": "smart_core.page_contracts_builder",
            "schema_version": "1.0.0",
            "page_key": page_key,
            "role_variant": role_code,
            "role_source_code": source_role_code,
            "semantic_profile": page_type,
            "role_zone_order": _role_zone_order(role_code, page_type, page_key),
            "role_focus_sections": list(focus_sections.keys()),
        },
    }


def build_page_contracts(_data: Dict[str, Any]) -> Dict[str, Any]:
    safe_data = _data if isinstance(_data, dict) else {}
    role_source_code = _resolve_role_source_code(safe_data)
    role_code = _normalize_role_code(safe_data)
    payload = {
        "schema_version": "v1",
        "pages": {
            "home": {
                "schema_version": "v1",
                "texts": {
                    "title": "工作台",
                    "hero_lead": "围绕项目经营、风险与审批，优先处理今天最关键事项。",
                    "entry_error_title_prefix": "进入失败：",
                    "action_retry": "重试",
                    "action_acknowledge": "知道了",
                    "search_placeholder": "搜索功能名称或说明",
                    "search_clear": "清空搜索",
                    "ready_only_label": "仅显示可进入功能",
                    "state_all": "全部",
                    "state_ready": "可进入",
                    "state_locked": "暂不可用",
                    "state_preview": "即将开放",
                    "capability_state_all": "功能语义：全部",
                    "capability_state_allow": "可用",
                    "capability_state_readonly": "只读",
                    "capability_state_deny": "禁止",
                    "capability_state_pending": "待开放",
                    "capability_state_coming_soon": "建设中",
                    "filter_tip_ready_only": "已启用“仅显示可进入功能”，暂不可用与即将开放不会展示。",
                    "lock_reason_all": "锁定原因：全部",
                    "action_clear_all_filters": "清空全部筛选",
                    "action_expand_all_groups": "展开全部分组",
                    "action_collapse_all_groups": "折叠全部分组",
                    "action_clear_recent": "清空最近使用",
                    "empty_ready_only_no_result": "当前启用了“仅显示可进入功能”，暂时没有可进入功能。",
                    "empty_search_no_result_prefix": "未找到与“",
                    "empty_search_no_result_suffix": "”相关的功能，请调整筛选条件。",
                    "empty_filter_no_result": "未找到相关功能，请调整筛选条件。",
                    "action_clear_lock_reason": "清除锁定原因",
                    "action_show_all_capabilities": "显示全部功能",
                    "action_clear_search_filters": "清空搜索与筛选",
                    "empty_no_capability": "当前账号暂无可用功能，可能因为角色权限未开通或工作台尚未配置。",
                    "action_switch_role": "切换角色",
                    "action_back_home": "返回首页",
                    "action_expand_help": "查看帮助",
                    "action_collapse_help": "收起帮助",
                    "empty_help_detail": "建议先点击“切换角色”确认当前角色；若仍无功能，请联系管理员开通角色权限或配置工作台目录。",
                    "entry_subtitle_empty": "无说明",
                    "role_fallback_owner": "负责人",
                    "role_label_executive": "高管",
                    "role_label_owner": "负责人",
                    "role_landing_fallback": "工作台首页",
                    "tile_title_fallback_prefix": "功能 ",
                    "scene_title_uncategorized": "未分类模块",
                    "scene_title_uncategorized_with_key_prefix": "未分类模块（",
                    "scene_title_uncategorized_with_key_suffix": ")",
                    "metric_title_fallback_prefix": "指标 ",
                    "todo_title_fallback_prefix": "待办 ",
                    "todo_desc_fallback": "点击进入处理",
                    "today_actions.status_urgent": "紧急",
                    "today_actions.status_normal": "普通",
                    "risk_summary_fallback": "当前未出现严重风险，建议保持日常巡检节奏。",
                    "risk_action_title_fallback_prefix": "风险事项 ",
                    "risk_source_label_fallback_prefix": "来源 ",
                    "advice_title_fallback_prefix": "建议 ",
                    "risk_trend_label_prefix": "T-",
                    "level_red": "严重",
                    "level_amber": "关注",
                    "level_green": "正常",
                    "trend_up_prefix": "↑ ",
                    "trend_down_prefix": "↓ ",
                    "trend_flat": "→ 0%",
                    "todo_label_approval": "审核付款申请",
                    "todo_label_contract": "查看合同异常",
                    "todo_label_risk": "处理风险事项",
                    "todo_label_change": "确认变更事项",
                    "todo_label_overdue": "处理逾期任务",
                    "todo_label_default": "查看详情",
                    "todo_keywords_approval": "付款,支付,approval,审批",
                    "todo_keywords_contract": "合同,contract",
                    "todo_keywords_risk": "风险,risk",
                    "todo_keywords_change": "变更,change",
                    "todo_keywords_overdue": "逾期,任务,todo",
                    "result_summary_prefix": "当前显示 ",
                    "result_summary_middle": " / ",
                    "result_summary_suffix": " 项功能",
                    "result_summary_state_prefix": "状态：",
                    "result_summary_capability_state_prefix": "功能语义：",
                    "result_summary_reason_prefix": "原因：",
                    "chip_search_prefix": "搜索：",
                    "chip_ready_only": "仅显示可进入",
                    "chip_state_prefix": "状态：",
                    "chip_capability_state_prefix": "功能语义：",
                    "chip_reason_prefix": "锁定原因：",
                    "scene_summary_prefix": "覆盖场景：",
                    "scene_summary_more": "…",
                    "group_overview.aria_label": "辅助入口区",
                    "recent_group_title": "最近使用",
                    "lock_reason_permission_denied": "权限不足",
                    "lock_reason_feature_disabled": "订阅未开通",
                    "lock_reason_role_scope_mismatch": "角色范围不匹配",
                    "lock_reason_scope_missing": "缺少前置条件",
                    "lock_reason_scope_cycle": "功能依赖异常",
                    "lock_reason_coming_soon": "功能建设中",
                    "lock_reason_waiting_open": "待审批开放",
                    "lock_reason_default": "当前不可用",
                    "action_enter_disabled": "暂不可用",
                    "action_enter_preview": "即将开放",
                    "action_enter_readonly": "只读进入",
                    "action_enter_approval": "审核付款申请",
                    "action_enter_contract": "查看合同异常",
                    "action_enter_risk": "处理风险事项",
                    "action_enter_change": "确认变更事项",
                    "action_enter_task": "处理任务",
                    "action_enter_default": "进入处理",
                    "action_enter_keywords_approval": "payment,付款,支付,approval,审批",
                    "action_enter_keywords_contract": "contract,合同",
                    "action_enter_keywords_risk": "risk,风险,预警",
                    "action_enter_keywords_change": "change,变更",
                    "action_enter_keywords_task": "task,任务,todo,待办",
                    "enter_error_message_fallback": "功能入口暂时不可用",
                    "enter_error_hint_permission_denied": "请联系管理员开通对应权限后重试。",
                    "enter_error_hint_route_not_found": "入口配置异常，请稍后重试或联系管理员。",
                    "enter_error_hint_timeout": "网络连接超时，请检查网络后点击重试。",
                    "enter_error_hint_default": "请稍后重试；如果问题持续，请联系管理员。",
                },
            },
            "login": {
                "schema_version": "v1",
                "sections": [
                    {"key": "card", "enabled": True, "order": 1, "tag": "section"},
                    {"key": "form", "enabled": True, "order": 2, "tag": "section"},
                    {"key": "error", "enabled": True, "order": 3, "tag": "section"},
                ],
                "texts": {
                    "title": "登录",
                    "brand_name": "智能施工企业管理平台",
                    "brand_subtitle": "工程项目全生命周期管理系统",
                    "brand_slogan": "让项目透明 · 让合同可控 · 让资金协同 · 让风险可预警",
                    "username_label": "账号",
                    "username_placeholder": "请输入账号",
                    "password_label": "密码",
                    "password_placeholder": "请输入密码",
                    "submit_idle": "登录",
                    "submit_loading": "系统正在登录，请稍候…",
                    "error_login_failed": "登录失败，请稍后重试",
                    "error_invalid_credentials": "账号或密码错误，请重新输入",
                    "error_network": "网络异常，请稍后重试",
                    "capability_project": "项目全过程管理",
                    "capability_contract_cost": "合同成本联动",
                    "capability_fund": "资金支付协同",
                    "capability_risk": "风险预警驾驶舱",
                    "value_line_1": "让项目透明",
                    "value_line_2": "让合同可控",
                    "value_line_3": "让资金协同",
                    "value_line_4": "让风险可预警",
                },
            },
            "menu": {
                "schema_version": "v1",
                "sections": [
                    {"key": "status_loading", "enabled": True, "order": 1, "tag": "section"},
                    {"key": "status_info", "enabled": True, "order": 2, "tag": "section"},
                    {"key": "status_error", "enabled": True, "order": 3, "tag": "section"},
                ],
                "texts": {
                    "loading_title": "Resolving menu...",
                    "info_title": "Menu group",
                    "error_title": "Menu resolve failed",
                    "error_invalid_menu_id": "invalid menu id",
                    "error_resolve_failed": "resolve menu failed",
                },
            },
            "placeholder": {
                "schema_version": "v1",
                "sections": [
                    {"key": "card", "enabled": True, "order": 1, "tag": "section"},
                ],
                "texts": {
                    "title": "Dynamic View Placeholder",
                    "route_label": "Route",
                    "params_label": "Params",
                },
            },
            "workbench": {
                "schema_version": "v1",
                "sections": [
                    {"key": "header", "enabled": True, "order": 1, "tag": "header"},
                    {"key": "status_panel", "enabled": True, "order": 2, "tag": "section"},
                    {"key": "tiles", "enabled": True, "order": 3, "tag": "section"},
                    {"key": "hud_details", "enabled": True, "order": 4, "tag": "div"},
                ],
                "texts": {
                    "header_title": "页面暂时无法打开",
                    "header_subtitle": "我们已为你保留可继续操作的入口。",
                    "diagnostic_hint": "诊断页仅用于排查，不作为正式产品界面。",
                    "context_prefix": "推荐上下文：",
                    "action_clear_context": "清除",
                    "action_go_workbench": "返回工作台",
                    "action_open_menu": "打开菜单",
                    "action_refresh": "刷新",
                    "hud_label_reason": "原因",
                    "hud_label_menu": "菜单",
                    "hud_label_action": "动作",
                    "hud_label_route": "路由",
                    "hud_label_diag": "诊断",
                    "hud_label_action_type": "动作类型",
                    "hud_label_contract_type": "契约类型",
                    "hud_label_contract_url": "契约链接",
                    "hud_label_meta_url": "元信息链接",
                    "hud_label_last_intent": "最近意图",
                    "hud_label_trace_id": "追踪 ID",
                    "hud_label_data_source": "数据源协议",
                    "hud_value_ready": "就绪",
                    "hud_value_missing": "缺失",
                    "hud_value_na": "N/A",
                    "action_copy": "复制",
                    "panel_title": "页面暂时无法打开",
                    "reason_nav_menu_no_action": "菜单分组（无可执行动作）",
                    "reason_act_no_model": "动作未绑定模型",
                    "reason_act_unsupported_type": "动作类型暂不支持",
                    "reason_contract_context_missing": "契约上下文缺失",
                    "reason_capability_missing": "缺少能力权限",
                    "reason_unknown": "未知原因",
                    "message_nav_menu_no_action": "当前菜单是目录，暂时没有可进入的子菜单。",
                    "message_act_no_model": "当前动作对应的是自定义工作区，未绑定数据模型。",
                    "message_act_unsupported_type": "当前动作类型暂未在门户壳层支持。",
                    "message_contract_context_missing": "页面缺少契约必需上下文（例如 action_id）。",
                    "message_capability_missing": "当前账号尚未开通该能力。",
                    "message_default": "你可以返回工作台或打开菜单继续操作。",
                },
            },
            "my_work": {
                "schema_version": "v1",
                "sections": [
                    {"key": "hero", "enabled": True, "order": 1, "tag": "header"},
                    {"key": "todo_focus", "enabled": True, "order": 2, "tag": "section"},
                    {"key": "retry_panel", "enabled": True, "order": 3, "tag": "details", "open": False},
                    {"key": "list_main", "enabled": True, "order": 4, "tag": "section"},
                ],
                "texts": {
                    "title": "我的工作",
                    "loading_title": "加载我的工作中...",
                    "hero_subtitle": "聚合待办并直接处理，默认从“待我处理”开工。",
                    "action_refresh": "刷新",
                    "context_preset_prefix": "推荐视图：",
                    "action_clear_preset": "清除推荐",
                    "context_updated_at_prefix": "更新于 ",
                    "retry_failed_prefix": "失败待办 ",
                    "retry_failed_suffix": " 条",
                    "retry_mode_prefix": "模式: ",
                    "retry_replay": "重放结果",
                    "retry_expand_hint": "展开处理",
                    "retry_title": "失败明细",
                    "retry_action_select_failed": "选中失败项",
                    "retry_action_select_all_failed": "选中全部失败项",
                    "retry_action_select_retryable_only": "仅选可重试项",
                    "retry_action_select_non_retryable_only": "仅选不可重试项",
                    "retry_action_retry_failed": "重试失败项",
                    "retry_action_copy_summary": "复制失败摘要",
                    "retry_action_copy_current_view": "复制当前视图",
                    "retry_action_export_failed_csv": "导出失败 CSV",
                    "retry_action_copy_retry_request": "复制重试请求",
                    "retry_action_export_retry_json": "导出重试 JSON",
                    "retry_action_focus_in_main_list": "主列表定位失败",
                    "retry_action_copy_trace": "复制 Trace",
                    "retry_action_ignore": "忽略",
                    "retry_request_preview_title": "重试请求预览",
                    "retry_note_preset_network": "网络抖动",
                    "retry_note_preset_conflict": "并发冲突",
                    "retry_note_preset_dependency": "依赖满足",
                    "retry_note_template_network": "系统重试：网络抖动后重放",
                    "retry_note_template_conflict": "系统重试：并发冲突后重放",
                    "retry_note_template_dependency": "系统重试：依赖状态已满足",
                    "retry_note_label": "重试备注",
                    "retry_note_placeholder": "可选：补充本次重试说明",
                    "retry_capability_prefix": "重试能力：可重试 ",
                    "retry_capability_middle": " / 不可重试 ",
                    "retry_visible_prefix": "当前展示 ",
                    "retry_visible_middle": " / ",
                    "retry_visible_suffix": " 条",
                    "retry_action_expand_all": "展开全部",
                    "retry_action_collapse_all": "收起",
                    "retry_search_placeholder": "筛选失败明细：ID / 原因码 / 消息",
                    "retry_filter_all": "全部",
                    "retry_filter_retryable_only": "仅可重试",
                    "retry_filter_non_retryable_only": "仅不可重试",
                    "retry_group_mode_flat": "平铺显示",
                    "retry_group_mode_grouped": "按原因分组",
                    "retry_action_reset_panel": "重置面板",
                    "retry_reason_distribution_prefix": "失败原因分布：",
                    "retry_action_clear_failed_filter": "清除失败筛选",
                    "retry_group_summary_prefix": "分组摘要：",
                    "retry_group_retryable_prefix": "可重试 ",
                    "retry_action_select_group": "选中此组",
                    "retry_action_retry_group": "重试此组",
                    "retry_unknown_reason_code": "UNKNOWN",
                    "retry_action_copy_single": "复制单条",
                    "retry_action_open_record": "打开记录",
                    "filter_search_placeholder": "搜索事项 / 来源 / 动作",
                    "action_expand_filters": "展开筛选",
                    "action_collapse_filters": "收起筛选",
                    "action_apply_filters": "应用",
                    "action_reset_filters": "重置",
                    "filter_source_all": "全部来源",
                    "filter_reason_all": "全部原因码",
                    "sort_priority": "排序：优先级",
                    "sort_deadline": "排序：截止日",
                    "sort_title": "排序：事项标题",
                    "sort_reason_code": "排序：原因码",
                    "sort_source": "排序：来源",
                    "sort_id": "排序：ID",
                    "sort_desc": "降序",
                    "sort_asc": "升序",
                    "page_size_10": "每页 10",
                    "page_size_20": "每页 20",
                    "page_size_40": "每页 40",
                    "action_save_preset": "保存常用筛选",
                    "action_apply_preset": "应用常用筛选",
                    "action_clear_saved_preset": "清除预设",
                    "filter_empty_title": "当前筛选条件没有匹配结果",
                    "filter_empty_desc": "建议先恢复推荐视图，或一键清空筛选后重试。",
                    "action_restore_recommended_view": "恢复推荐视图",
                    "action_clear_filters": "清空筛选",
                    "batch_selected_prefix": "已选 ",
                    "batch_selected_suffix": " 条待办",
                    "action_batch_complete": "批量完成",
                    "action_clear_selection": "清空",
                    "empty_title_default": "当前无待处理事项",
                    "action_go_workbench": "去工作台",
                    "action_go_risk_cockpit": "去风险驾驶舱",
                    "table_col_item": "事项",
                    "table_col_action": "动作",
                    "table_col_deadline": "截止日",
                    "table_col_priority": "优先级",
                    "table_col_reason_code": "原因码",
                    "pager_prev": "上一页",
                    "pager_middle_prefix": "第 ",
                    "pager_middle_sep": " / ",
                    "pager_middle_suffix": " 页",
                    "pager_next": "下一页",
                    "empty_desc": "状态良好。你可以返回工作台查看整体态势，或进入风险驾驶舱继续巡检。",
                    "error_request_failed": "请求失败",
                    "feedback_save_preset_failed": "保存常用筛选失败",
                    "feedback_apply_preset_failed": "应用常用筛选失败",
                    "feedback_clear_preset_failed": "清除常用筛选失败",
                    "visibility_notice_suffix": "，请联系管理员开通对应权限。",
                    "partial_data_hidden": "部分数据未显示",
                    "model_label_sc_workflow_workitem": "流程待办",
                    "model_label_tier_review": "审批复核",
                    "model_label_mail_activity": "待办活动",
                    "model_label_project_task": "项目任务",
                    "model_label_project_project": "项目主数据",
                    "model_label_mail_message": "消息提醒",
                    "model_label_mail_followers": "关注记录",
                    "priority_high": "高",
                    "priority_medium": "中",
                    "priority_low": "低",
                    "feedback_restore_recommended": "已恢复推荐视图",
                    "feedback_save_preset_ok": "常用筛选已保存",
                    "feedback_apply_preset_ok": "已应用常用筛选",
                    "feedback_clear_preset_ok": "已清除常用筛选",
                    "feedback_filters_reset": "筛选条件已重置",
                    "feedback_suggest_action_ok_prefix": "已执行建议动作：",
                    "feedback_suggest_action_failed_prefix": "建议动作执行失败：",
                    "feedback_none_retryable": "当前没有可重试失败项",
                    "feedback_none_non_retryable": "当前没有不可重试失败项",
                    "feedback_none_failed_selectable": "当前没有失败项可选择",
                    "feedback_selected_failed_prefix": "已选中 ",
                    "feedback_selected_failed_suffix": " 条失败项",
                    "feedback_selected_retryable_suffix": " 条可重试失败项",
                    "feedback_selected_non_retryable_suffix": " 条不可重试失败项",
                    "feedback_filtered_by_reason_prefix": "已按失败原因筛选：",
                    "feedback_cleared_reason_filter": "已清除失败原因筛选",
                    "feedback_copy_summary_ok": "失败摘要已复制",
                    "feedback_copy_failed": "复制失败，请检查浏览器剪贴板权限",
                    "feedback_copy_item_ok_prefix": "失败项 #",
                    "feedback_copy_item_ok_suffix": " 已复制",
                    "feedback_copy_item_failed_prefix": "复制失败项 #",
                    "feedback_copy_item_failed_suffix": " 失败",
                    "feedback_copy_view_summary_ok": "当前视图摘要已复制",
                    "feedback_copy_view_summary_failed": "复制当前视图摘要失败，请检查浏览器剪贴板权限",
                    "feedback_focus_main_failed_view": "已定位到主列表失败待办视图",
                    "feedback_copy_retry_request_ok": "重试请求已复制",
                    "feedback_copy_retry_request_failed": "复制重试请求失败，请检查浏览器剪贴板权限",
                    "feedback_export_retry_json_ok": "重试请求 JSON 已导出",
                    "feedback_export_retry_json_failed": "导出重试请求 JSON 失败",
                    "feedback_copy_trace_ok": "trace_id 已复制",
                    "feedback_copy_trace_failed": "复制 trace_id 失败，请检查浏览器剪贴板权限",
                    "feedback_export_failed_csv_ok_prefix": "失败明细 CSV 已导出（",
                    "feedback_export_failed_csv_ok_suffix": " 条）",
                    "feedback_export_failed_csv_failed": "导出失败明细 CSV 失败",
                    "feedback_todo_done_ok": "待办已完成",
                    "feedback_todo_done_failed": "完成待办失败",
                    "confirm_batch_complete_prefix": "确认批量完成 ",
                    "confirm_batch_complete_suffix": " 条待办？",
                    "error_complete_todo_failed": "完成待办失败",
                    "error_batch_complete_failed": "批量完成待办失败",
                    "enter_error_message_fallback": "功能入口暂时不可用",
                    "feedback_reason_group_no_retry_prefix": "原因组 ",
                    "feedback_reason_group_no_retry_suffix": " 没有可重试项",
                    "feedback_selected_reason_retryable_prefix": "已选中 ",
                    "feedback_selected_reason_retryable_middle": " 条 ",
                    "feedback_selected_reason_retryable_suffix": " 可重试项",
                    "error_retry_failed_items_failed": "重试失败项失败",
                    "preset_label_prefix": "预设视图：",
                    "retry_tag_retryable": "可重试",
                    "retry_tag_non_retryable": "不可重试",
                    "retry_summary_group_count_sep": " x ",
                    "retry_summary_group_retryable_left": " (",
                    "retry_summary_group_retryable_right": ")",
                    "retry_summary_header_prefix": "失败待办 ",
                    "retry_summary_header_suffix": " 条",
                    "retry_summary_reason_dist_prefix": "原因分布: ",
                    "retry_summary_remaining_prefix": "剩余待办: ",
                    "retry_visible_mode_prefix": "筛选模式: ",
                    "retry_visible_display_prefix": "显示模式: ",
                    "retry_visible_display_grouped": "grouped",
                    "retry_visible_display_flat": "flat",
                    "retry_visible_items_prefix": "当前视图条目: ",
                    "batch_action_complete": "批量完成",
                    "batch_action_retry": "重试",
                    "batch_action_retry_group_left": "重试(",
                    "batch_action_retry_group_right": ")",
                    "batch_feedback_partial_suffix": "部分失败：",
                    "batch_feedback_success_count_suffix": " 成功，",
                    "batch_feedback_failed_count_suffix": " 失败",
                    "batch_feedback_preview_left": "（",
                    "batch_feedback_preview_right": "）",
                    "batch_feedback_remaining_prefix": "，剩余待办 ",
                    "batch_feedback_remaining_suffix": " 条",
                    "batch_feedback_replay_prefix": "，命中重放#",
                    "batch_feedback_success_suffix": "成功：",
                    "batch_feedback_done_suffix": " 条",
                },
            },
            "scene": {
                "schema_version": "v1",
                "sections": [
                    {"key": "status_loading", "enabled": True, "order": 1, "tag": "section"},
                    {"key": "status_error", "enabled": True, "order": 2, "tag": "section"},
                    {"key": "status_forbidden", "enabled": True, "order": 3, "tag": "section"},
                ],
                "texts": {
                    "loading_title": "正在加载场景...",
                    "validation_surface_title": "场景校验",
                    "error_fallback": "场景加载失败",
                    "forbidden_title": "能力未开通",
                    "forbidden_message": "当前角色无法进入该场景。",
                    "forbidden_title_permission": "权限不足",
                    "forbidden_message_scope_missing": "当前角色能力范围不包含该场景所需能力。",
                    "forbidden_message_missing_prefix": "缺少能力：",
                    "forbidden_message_missing_sep": "、",
                    "forbidden_detail_reason_left": "（",
                    "forbidden_detail_reason_right": "）",
                    "forbidden_hint_license_prefix": "当前 License：",
                    "forbidden_hint_license_suffix": "，可联系管理员评估升级或开通。",
                    "forbidden_hint_default": "可联系管理员开通对应能力。",
                    "error_scene_target_unsupported": "scene target unsupported",
                    "error_scene_resolve_failed": "scene resolve failed",
                },
            },
            "action": {
                "schema_version": "v1",
                "sections": [
                    {"key": "route_preset", "enabled": True, "order": 1, "tag": "section"},
                    {"key": "focus_strip", "enabled": True, "order": 2, "tag": "section"},
                    {"key": "quick_filters", "enabled": True, "order": 3, "tag": "section"},
                    {"key": "saved_filters", "enabled": True, "order": 4, "tag": "section"},
                    {"key": "group_view", "enabled": True, "order": 5, "tag": "section"},
                    {"key": "group_summary", "enabled": True, "order": 6, "tag": "section"},
                    {"key": "quick_actions", "enabled": True, "order": 7, "tag": "section"},
                    {"key": "advanced_view", "enabled": True, "order": 8, "tag": "section"},
                    {"key": "empty_next", "enabled": True, "order": 9, "tag": "section"},
                    {"key": "dev_context", "enabled": True, "order": 10, "tag": "div"},
                ],
                "texts": {
                    "error_fallback": "操作暂不可用",
                    "status_loading": "加载中",
                    "status_error": "加载失败",
                    "status_empty": "暂无数据",
                    "status_ready": "已就绪",
                    "label.quick_filters": "快速筛选",
                    "label.saved_filters": "已保存筛选",
                    "label.group_view": "分组查看",
                    "label.quick_actions": "快捷操作",
                    "label.contract_summary": "契约摘要",
                    "intent_title_risk": "风险驾驶舱：先处理严重与逾期风险",
                    "intent_summary_risk": "优先完成分派、关闭或发起审批，避免风险停留在“仅可见”状态。",
                    "intent_action_risk_todo": "待我处理风险",
                    "intent_action_risk_scene": "打开风险场景",
                    "empty_title_risk": "当前暂无风险记录",
                    "empty_hint_risk": "建议转到“我的工作”处理风险待办，或进入风险驾驶舱继续巡检。",
                    "primary_action_risk": "处理风险待办",
                    "secondary_action_risk": "进入风险驾驶舱",
                    "intent_title_contract": "合同执行：优先识别付款与变更风险",
                    "intent_summary_contract": "先看执行率与付款状态，再进入异常合同处理。",
                    "intent_action_contract_todo": "处理合同待办",
                    "intent_action_contract_dashboard": "查看风险驾驶舱",
                    "empty_title_contract": "当前暂无合同记录",
                    "empty_hint_contract": "可前往“我的工作”查看合同待办，或进入风险驾驶舱追踪履约风险。",
                    "primary_action_contract": "处理合同待办",
                    "secondary_action_contract": "查看风险驾驶舱",
                    "intent_title_cost": "成本执行：先回答是否超支",
                    "intent_summary_cost": "优先关注超支金额与超支项，再下钻到具体偏差来源。",
                    "intent_action_cost_todo": "处理成本待办",
                    "intent_action_cost_dashboard": "查看风险驾驶舱",
                    "empty_title_cost": "当前暂无成本记录",
                    "empty_hint_cost": "可前往“我的工作”处理成本待办，或进入风险驾驶舱继续巡检。",
                    "primary_action_cost": "处理超支待办",
                    "secondary_action_cost": "查看风险驾驶舱",
                    "intent_title_project": "项目视角：先判断是否可控",
                    "intent_summary_project": "优先查看风险、审批与经营指标，再决定下一步动作。",
                    "intent_action_project_todo": "查看项目待办",
                    "intent_action_project_dashboard": "进入风险驾驶舱",
                    "empty_title_project": "当前暂无项目记录",
                    "empty_hint_project": "建议进入“我的工作”处理项目待办，或去风险驾驶舱查看全局状态。",
                    "primary_action_project": "查看项目待办",
                    "secondary_action_project": "进入风险驾驶舱",
                    "intent_title_default": "业务列表：先看状态，再执行动作",
                    "intent_summary_default": "通过快速筛选与快捷操作，优先处理最关键事项。",
                    "intent_action_default_home": "工作台",
                    "intent_action_default_my_work": "我的工作",
                    "empty_title_default": "当前视图暂无数据",
                    "empty_hint_default": "建议切换到我的工作或风险驾驶舱继续处理。",
                    "primary_action_default": "去我的工作",
                    "secondary_action_default": "去风险驾驶舱",
                    "empty_reason_default": "可能因为暂无业务数据、当前角色权限受限，或数据尚未生成。",
                    "empty_reason_filter": "可能由当前筛选条件导致无数据，建议先清除筛选后重试。",
                    "empty_reason_wbs": "当前尚未生成执行结构数据，可先在项目立项或工程结构中创建后再查看。",
                    "route_preset_applied_prefix": "已应用推荐筛选：",
                    "route_preset_source_prefix": "来源：",
                    "route_preset_clear": "清除推荐",
                    "chip_action_clear": "清除",
                    "chip_more_filters_collapse": "收起更多筛选",
                    "chip_more_filters_expand": "更多筛选",
                    "chip_more_group_collapse": "收起更多分组",
                    "chip_more_group_expand": "更多分组",
                    "chip_more_actions_collapse": "收起更多操作",
                    "chip_more_actions_expand": "更多操作",
                    "sort_option_priority_deadline": "优先级↓ / 截止日↑",
                    "sort_option_deadline_updated": "截止日↑ / 更新时间↓",
                    "sort_option_updated_id": "更新时间↓ / ID↓",
                    "sort_option_updated_name_asc": "更新时间↓ / 名称↑",
                    "sort_option_updated_asc_name_asc": "更新时间↑ / 名称↑",
                    "sort_option_name_updated": "名称↑ / 更新时间↓",
                    "sort_option_name_desc_updated": "名称↓ / 更新时间↓",
                    "subtitle_records_suffix": " 条记录",
                    "subtitle_sort_prefix": "排序：",
                    "advanced_title_pivot": "数据透视视图",
                    "advanced_title_graph": "图表视图",
                    "advanced_title_calendar": "日历视图",
                    "advanced_title_gantt": "甘特视图",
                    "advanced_title_activity": "活动视图",
                    "advanced_title_dashboard": "仪表板视图",
                    "advanced_title_default": "高级视图",
                    "advanced_hint_pivot": "当前为可读降级视图，可查看核心统计记录并继续下钻到列表/表单。",
                    "advanced_hint_graph": "当前为可读降级视图，可查看核心指标记录并继续下钻到列表/表单。",
                    "advanced_hint_calendar": "当前为可读降级视图，可查看时间相关记录并继续下钻到列表/表单。",
                    "advanced_hint_gantt": "当前为可读降级视图，可查看进度相关记录并继续下钻到列表/表单。",
                    "advanced_hint_activity": "当前为可读降级视图，可查看活动记录并继续下钻到列表/表单。",
                    "advanced_hint_dashboard": "当前为可读降级视图，可查看关键记录并继续下钻到列表/表单。",
                    "advanced_hint_default": "当前视图使用可读降级渲染。",
                    "page_title_fallback": "工作台",
                    "hint_select_single_record": "请选择 1 条记录",
                    "hint_select_record_first": "请先选择记录",
                    "hint_permission_denied": "权限不足",
                    "group_label_basic": "基础操作",
                    "group_label_workflow": "流程推进",
                    "group_label_drilldown": "业务查看",
                    "group_label_other": "更多操作",
                    "group_label_unset": "未设置",
                    "preset_label_contract_filter_prefix": "契约筛选: ",
                    "preset_label_saved_filter_prefix": "保存筛选: ",
                    "retry_tag_retryable": "可重试",
                    "retry_tag_non_retryable": "不可重试",
                    "advanced_row_title_fallback": "记录",
                    "advanced_row_meta_empty": "无附加字段",
                    "batch_msg_contract_action_missing_action_id": "契约动作缺少 action_id，无法打开目标页面",
                    "batch_msg_select_single_before_run": "请选择 1 条记录后再执行",
                    "batch_msg_select_records_before_run": "请先选择记录后再执行",
                    "batch_msg_contract_action_missing_model": "契约动作缺少 model，无法执行",
                    "batch_msg_action_requires_record_context": "当前动作需要记录上下文，暂不支持无记录执行",
                    "batch_msg_contract_action_done_prefix": "契约动作执行完成：成功 ",
                    "batch_msg_contract_action_done_middle": "，失败 ",
                    "batch_msg_assignee_options_limited_prefix": "负责人候选加载受限（",
                    "batch_msg_assignee_options_limited_suffix": "）",
                    "batch_error_reason_prefix": "原因=",
                    "batch_error_scope_prefix": "范围=",
                    "batch_msg_model_no_active_field": "当前模型不支持 active 字段，无法批量归档/激活",
                    "batch_msg_idempotent_replay": "批量操作已幂等处理（重复请求被忽略）",
                    "batch_msg_activate_done_prefix": "批量激活完成：成功 ",
                    "batch_msg_archive_done_prefix": "批量归档完成：成功 ",
                    "batch_msg_done_middle": "，失败 ",
                    "batch_msg_activate_failed": "批量激活失败",
                    "batch_msg_archive_failed": "批量归档失败",
                    "batch_label_activate": "批量激活",
                    "batch_label_archive": "批量归档",
                    "batch_msg_model_no_assignee_field": "当前模型不支持负责人字段，无法批量指派",
                    "batch_msg_select_assignee_first": "请先选择负责人",
                    "batch_msg_assign_idempotent_prefix": "批量指派给 ",
                    "batch_msg_assign_idempotent_suffix": " 已幂等处理（重复请求被忽略）",
                    "batch_msg_assign_done_prefix": "批量指派给 ",
                    "batch_msg_assign_done_middle": "：成功 ",
                    "batch_msg_assign_failed": "批量指派失败",
                    "batch_label_assign": "批量指派",
                    "batch_msg_no_selected_records_export": "没有可导出的选中记录",
                    "batch_msg_no_records_export": "没有可导出的记录",
                    "batch_msg_export_done_prefix": "已导出 ",
                    "batch_msg_export_done_suffix": " 条记录",
                    "batch_msg_export_failed": "批量导出失败",
                    "batch_label_export": "批量导出",
                    "batch_label_load_more_failed": "加载更多失败",
                    "surface_kind_keywords_risk": "risk,风险",
                    "surface_kind_keywords_contract": "contract,合同",
                    "surface_kind_keywords_cost": "cost,成本",
                    "surface_kind_keywords_project": "project,项目",
                    "group_keywords_basic": "创建,保存,submit,create,save",
                    "group_keywords_workflow": "阶段,审批,workflow,transition",
                    "group_keywords_drilldown": "查看,列表,看板,open,view",
                    "columns_risk_bucket_identity": "title,name,风险,事项",
                    "columns_risk_bucket_priority": "priority,severity,优先级,严重",
                    "columns_risk_bucket_deadline": "deadline,date_deadline,截止,逾期",
                    "columns_risk_bucket_owner": "user_id,owner,assignee,负责人,分派",
                    "columns_risk_bucket_state": "state,stage,status,状态",
                    "columns_risk_bucket_reason": "reason,原因",
                    "columns_contract_bucket_amount": "amount_total,contract_amount,金额,合同额",
                    "columns_contract_bucket_execution": "execute,execution,progress,执行率",
                    "columns_contract_bucket_payment": "paid,payment,付款,支付",
                    "columns_contract_bucket_risk": "risk,风险,alert",
                    "columns_contract_bucket_change": "change,变更,write_date,最近",
                    "columns_contract_bucket_identity": "title,name,合同",
                    "columns_cost_bucket_execution": "cost,执行率,rate",
                    "columns_cost_bucket_overrun": "over,overrun,超支,偏差",
                    "columns_cost_bucket_count": "count,项数",
                    "columns_cost_bucket_deadline": "deadline,截止",
                    "columns_cost_bucket_priority": "priority,优先级",
                    "columns_cost_bucket_identity": "title,name,项目",
                    "columns_project_bucket_identity": "title,name,项目",
                    "columns_project_bucket_state": "state,stage,status,状态,阶段",
                    "columns_project_bucket_risk": "risk,风险",
                    "columns_project_bucket_payment": "payment,付款",
                    "columns_project_bucket_output": "output,产值",
                    "columns_project_bucket_cost": "cost,成本",
                },
            },
            "record": {
                "schema_version": "v1",
                "sections": [
                    {"key": "save_banner", "enabled": True, "order": 1, "tag": "div"},
                    {"key": "project_summary", "enabled": True, "order": 2, "tag": "section"},
                    {"key": "next_actions", "enabled": True, "order": 3, "tag": "section"},
                    {"key": "stat_buttons", "enabled": True, "order": 4, "tag": "div"},
                    {"key": "details_fallback", "enabled": True, "order": 5, "tag": "section"},
                    {"key": "chatter", "enabled": True, "order": 6, "tag": "section"},
                    {"key": "dev_context", "enabled": True, "order": 7, "tag": "div"},
                ],
                "texts": {
                    "loading_title": "Loading record...",
                    "saving_title": "Saving record...",
                    "error_fallback": "Record load failed",
                    "status_loading": "Loading",
                    "status_error": "Error",
                    "status_empty": "Empty",
                    "status_ready": "Ready",
                    "status_editing": "Editing",
                    "status_saving": "Saving",
                    "action_back": "Back",
                    "action_edit": "Edit",
                    "action_save": "Save",
                    "action_cancel": "Cancel",
                    "action_reload": "Reload",
                    "action_download": "Download",
                    "subtitle_editing": "Editing contract fields",
                    "subtitle_ready": "Record details",
                    "ribbon_fallback": "Ribbon",
                    "dev_context_title": "Record Context",
                    "error_load_record": "failed to load record",
                    "error_execute_button": "failed to execute button",
                    "error_save_record": "failed to save record",
                    "chatter_load_failed": "Failed to load chatter",
                    "chatter_post_failed": "Failed to post chatter message",
                    "chatter_upload_failed": "Failed to upload file",
                    "chatter_download_failed": "Failed to download file",
                    "view_node_unsupported_title": "View node unsupported",
                    "view_node_unsupported_message": "Layout nodes are present but renderer support is incomplete.",
                    "banner_saved": "Saved. Changes have been applied.",
                    "summary_status_stage": "项目状态与阶段",
                    "summary_risk": "关键风险摘要",
                    "summary_finance": "资金/产值指标",
                    "next_actions_title": "下一步动作",
                    "next_action_todo": "查看待办",
                    "next_action_risk": "查看风险",
                    "next_action_contract": "查看合同",
                    "next_action_cost": "查看成本",
                    "fallback_details_title": "项目详情",
                    "chatter_title": "协作时间线",
                    "chatter_input_placeholder": "输入评论，支持 @同事 ...",
                    "chatter_posting": "发布中...",
                    "chatter_post_action": "发布评论",
                    "chatter_uploading": "上传中…",
                    "chatter_empty": "暂无协作记录。",
                    "project_phase_unset": "未配置阶段",
                    "project_risk_ok": "正常，暂无高风险告警",
                    "project_risk_critical_prefix": "严重，当前高风险 ",
                    "project_risk_critical_suffix": " 项，需优先闭环",
                    "project_risk_attention_prefix": "关注，当前风险 ",
                    "project_risk_attention_suffix": " 项",
                    "project_output_prefix": "产值 ",
                    "project_output_unset": "产值未配置",
                    "project_pay_prefix": "付款比 ",
                    "project_pay_suffix": "%",
                    "project_pay_unset": "付款比未配置",
                    "readonly_hint_license_prefix": "当前为只读模式（License: ",
                    "readonly_hint_license_bundle_sep": ", Bundle: ",
                    "readonly_hint_license_suffix": "）。如需编辑权限请联系管理员。",
                    "readonly_hint_default": "当前记录处于只读模式，请联系管理员开通写权限。",
                    "missing_capability_prefix": "缺少能力：",
                    "missing_capability_sep": "、",
                    "missing_capability_license_prefix": "；当前 License: ",
                    "action_feedback_failed": "操作失败",
                },
            },
            "scene_health": {
                "schema_version": "v1",
                "sections": [
                    {"key": "header", "enabled": True, "order": 1, "tag": "header"},
                    {"key": "status_loading", "enabled": True, "order": 2, "tag": "section"},
                    {"key": "status_error", "enabled": True, "order": 3, "tag": "section"},
                    {"key": "content", "enabled": True, "order": 4, "tag": "div"},
                    {"key": "cards", "enabled": True, "order": 5, "tag": "section"},
                    {"key": "meta", "enabled": True, "order": 6, "tag": "section"},
                    {"key": "governance", "enabled": True, "order": 7, "tag": "section"},
                    {"key": "details_resolve_errors", "enabled": True, "order": 8, "tag": "details", "open": True},
                    {"key": "details_drift", "enabled": True, "order": 9, "tag": "details", "open": False},
                    {"key": "details_debt", "enabled": True, "order": 10, "tag": "details", "open": False},
                ],
                "texts": {
                    "title": "Scene Health Dashboard",
                    "subtitle": "可视化查看场景健康状态与自动降级结果。",
                    "loading_title": "Loading scene health...",
                    "error_fallback": "health request failed",
                    "error_reason_required": "reason is required for governance action",
                    "error_governance_failed": "governance action failed",
                },
            },
            "scene_packages": {
                "schema_version": "v1",
                "sections": [
                    {"key": "header", "enabled": True, "order": 1, "tag": "header"},
                    {"key": "status_loading", "enabled": True, "order": 2, "tag": "section"},
                    {"key": "status_error", "enabled": True, "order": 3, "tag": "section"},
                    {"key": "content", "enabled": True, "order": 4, "tag": "section"},
                    {"key": "installed_packages", "enabled": True, "order": 5, "tag": "section"},
                    {"key": "import_package", "enabled": True, "order": 6, "tag": "section"},
                    {"key": "export_package", "enabled": True, "order": 7, "tag": "section"},
                ],
                "texts": {
                    "title": "Scene Packages",
                    "subtitle": "导入、导出与审阅已安装的 Scene 能力包。",
                    "loading_title": "Loading packages...",
                    "error_title": "Package operation failed",
                    "error_load_failed": "load packages failed",
                    "error_dry_run_failed": "dry-run failed",
                    "error_import_failed": "import failed",
                    "error_export_failed": "export failed",
                    "error_reason_required": "reason is required for import",
                },
            },
            "usage_analytics": {
                "schema_version": "v1",
                "sections": [
                    {"key": "header", "enabled": True, "order": 1, "tag": "header"},
                    {"key": "status_loading", "enabled": True, "order": 2, "tag": "section"},
                    {"key": "status_error", "enabled": True, "order": 3, "tag": "section"},
                    {"key": "slice_bar", "enabled": True, "order": 4, "tag": "section"},
                    {"key": "summary_usage", "enabled": True, "order": 5, "tag": "section"},
                    {"key": "summary_visibility", "enabled": True, "order": 6, "tag": "section"},
                    {"key": "tables_top", "enabled": True, "order": 7, "tag": "section"},
                    {"key": "tables_daily", "enabled": True, "order": 8, "tag": "section"},
                    {"key": "tables_visibility", "enabled": True, "order": 9, "tag": "section"},
                    {"key": "tables_role_user", "enabled": True, "order": 10, "tag": "section"},
                ],
                "texts": {
                    "title": "Usage Analytics",
                    "subtitle": "Scene / Capability 使用统计（按公司累计）。",
                    "label_top": "Top",
                    "label_daily_range": "趋势范围",
                    "option_recent_3_days": "最近 3 天",
                    "option_recent_7_days": "最近 7 天",
                    "label_hidden_reason": "隐藏原因",
                    "option_all": "全部",
                    "label_role_slice": "角色切片",
                    "option_all_roles": "全部角色",
                    "label_user_slice": "用户切片",
                    "placeholder_user_slice": "0=全部",
                    "label_scene_prefix": "Scene 前缀",
                    "placeholder_scene_prefix": "如 projects.",
                    "label_capability_prefix": "Capability 前缀",
                    "placeholder_capability_prefix": "如 contract.",
                    "label_export_filtered_only": "仅导出当前筛选",
                    "action_copy_export_params": "复制导出参数",
                    "action_reset_filters": "重置筛选",
                    "action_export_csv": "导出 CSV",
                    "action_refresh": "刷新",
                    "slice_window_prefix": "窗口：",
                    "slice_role_prefix": "角色：",
                    "slice_user_prefix": "用户：",
                    "slice_scene_prefix_label": "Scene 前缀：",
                    "slice_capability_prefix_label": "Capability 前缀：",
                    "summary_scene_open_total": "Scene Open Total",
                    "summary_capability_open_total": "Capability Open Total",
                    "summary_generated_at": "Generated At",
                    "summary_capability_total": "Capability Total",
                    "summary_visible_hidden": "Visible / Hidden",
                    "summary_ready_preview_locked": "Ready / Preview / Locked",
                    "summary_role_codes": "Role Codes",
                    "table_top_scenes": "Top Scenes",
                    "table_scene_key": "Scene Key",
                    "table_count": "Count",
                    "table_top_capabilities": "Top Capabilities",
                    "table_capability_key": "Capability Key",
                    "table_scene_open_last_7_days": "Scene Open (Last 7 Days)",
                    "table_date": "Date",
                    "table_capability_open_last_7_days": "Capability Open (Last 7 Days)",
                    "table_visibility_reason_counts": "Visibility Reason Counts",
                    "table_reason_code": "Reason Code",
                    "table_hidden_capability_samples": "Hidden Capability Samples",
                    "table_key": "Key",
                    "table_reason": "Reason",
                    "table_role_top": "Role Top",
                    "table_role_code": "Role Code",
                    "table_scene": "Scene",
                    "table_capability": "Capability",
                    "table_total": "Total",
                    "table_user_top": "User Top",
                    "table_user_id": "User ID",
                    "loading_title": "Loading usage report...",
                    "error_fallback": "Failed to load usage report",
                    "empty_text": "暂无数据",
                    "error_export_failed": "导出失败",
                    "error_copy_export_params_failed": "复制导出参数失败",
                },
            },
        },
    }
    _apply_role_section_policy(payload, role_code)
    pages = payload.get("pages") if isinstance(payload.get("pages"), dict) else {}
    for key, page in pages.items():
        if not isinstance(page, dict):
            continue
        if isinstance(page.get("page_orchestration_v1"), dict):
            continue
        page["page_orchestration_v1"] = _build_page_orchestration_v1(
            str(key),
            page,
            role_code,
            role_source_code=role_source_code,
        )
    return payload
