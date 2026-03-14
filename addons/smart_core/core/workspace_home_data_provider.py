# -*- coding: utf-8 -*-
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Dict, Iterable, List

_PROVIDER = None


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def _load_industry_provider():
    global _PROVIDER
    if _PROVIDER is not None:
        return _PROVIDER
    provider_path = Path(__file__).resolve().parents[2] / "smart_construction_scene" / "profiles" / "workspace_home_scene_content.py"
    if not provider_path.exists():
        provider_path = Path(__file__).resolve().parents[2] / "smart_construction_scene" / "services" / "workspace_home_scene_content.py"
    try:
        spec = spec_from_file_location("smart_construction_workspace_home_scene_content", provider_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec unavailable")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        _PROVIDER = module
        return module
    except Exception:
        _PROVIDER = False
        return None


def _call_provider(name: str, fallback: Any, *args: Any) -> Any:
    provider = _load_industry_provider()
    if provider is None:
        return fallback
    fn = getattr(provider, name, None)
    if callable(fn):
        try:
            return fn(*args)
        except Exception:
            return fallback
    return fallback


def build_today_actions(ready_caps: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _call_provider("build_today_actions", [], ready_caps)


def build_advice_items(locked_caps: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    default = [{
        "id": "stable",
        "level": "green",
        "tone": "success",
        "progress": "completed",
        "title": "当前整体运行稳定",
        "description": "能力面运行正常，建议优先处理今日关键动作。",
        "action_label": "",
    }]
    return _call_provider("build_advice_items", default, locked_caps)


def build_role_focus_config(role_code: str) -> Dict[str, Any]:
    default = {
        "zone_order": ["primary", "support", "analysis"],
        "focus_blocks": ["record_overview", "risk_core", "todo_core", "entry_grid"],
    }
    return _call_provider("build_role_focus_config", default, role_code)


def build_v1_focus_map() -> Dict[str, List[str]]:
    default = {
        "pm": ["todo_list_today", "risk_alert_panel", "metric_row_core", "progress_summary_ops"],
        "finance": ["todo_list_today", "risk_alert_panel", "progress_summary_ops", "metric_row_core"],
        "owner": ["todo_list_today", "risk_alert_panel", "metric_row_core", "progress_summary_ops"],
    }
    return _call_provider("build_v1_focus_map", default)


def build_v1_page_profile(role_code: str) -> Dict[str, Any]:
    role = _to_text(role_code).lower()
    default = {
        "audience": ["project_manager", "construction_manager"] if role == "pm" else ["finance_manager", "construction_manager"] if role == "finance" else ["owner", "executive"],
        "priority_model": "task_first" if role == "pm" else "metric_first" if role == "finance" else "role_first",
        "mobile_priority": ["today_focus", "analysis", "quick_entries", "hero"],
    }
    return _call_provider("build_v1_page_profile", default, role_code)


def build_v1_data_sources() -> Dict[str, Dict[str, Any]]:
    default = {
        "ds_hero": {"source_type": "computed", "provider": "workspace.hero", "section_keys": ["hero"]},
        "ds_metrics": {"source_type": "computed", "provider": "workspace.metrics.summary", "section_keys": ["metrics"]},
        "ds_today_todos": {"source_type": "computed", "provider": "workspace.todo.today", "section_keys": ["today_actions"]},
        "ds_risk_alerts": {"source_type": "computed", "provider": "workspace.risk.alerts", "section_keys": ["risk"]},
        "ds_ops_progress": {"source_type": "computed", "provider": "workspace.progress.summary", "section_keys": ["ops"]},
        "ds_scene_groups": {"source_type": "scene_context", "provider": "workspace.scene.groups", "section_keys": ["scene_groups"]},
        "ds_capability_groups": {"source_type": "capability_registry", "provider": "workspace.capability.groups", "section_keys": ["group_overview"]},
        "ds_advice": {"source_type": "computed", "provider": "workspace.advice", "section_keys": ["advice"]},
        "ds_filters": {"source_type": "static", "provider": "workspace.filters", "section_keys": ["filters"]},
    }
    return _call_provider("build_v1_data_sources", default)


def build_legacy_blocks(role_code: str) -> List[Dict[str, Any]]:
    return _call_provider("build_legacy_blocks", [], role_code)


def build_v1_zones(role_code: str, audience: List[str], zone_rank: Dict[str, int]) -> List[Dict[str, Any]]:
    return _call_provider("build_v1_zones", [], role_code, audience, zone_rank)


def build_v1_state_schema() -> Dict[str, Dict[str, str]]:
    default = {
        "pending": {"tone": "warning", "label": "待处理"},
        "running": {"tone": "info", "label": "进行中"},
        "blocked": {"tone": "danger", "label": "已阻塞"},
        "completed": {"tone": "success", "label": "已完成"},
        "overdue": {"tone": "danger", "label": "已逾期"},
    }
    return _call_provider("build_v1_state_schema", default)
