# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def to_text(value: Any) -> str:
    return str(value or "").strip()


def build_default_role_focus_config() -> Dict[str, Any]:
    return {
        "zone_order": ["primary", "support", "analysis"],
        "focus_blocks": ["record_overview", "risk_core", "todo_core", "entry_grid"],
    }


def build_default_v1_focus_map() -> Dict[str, List[str]]:
    return {
        "pm": ["todo_list_today", "risk_alert_panel", "metric_row_core", "progress_summary_ops"],
        "finance": ["todo_list_today", "risk_alert_panel", "progress_summary_ops", "metric_row_core"],
        "owner": ["todo_list_today", "risk_alert_panel", "metric_row_core", "progress_summary_ops"],
    }


def build_default_v1_page_profile(role_code: str) -> Dict[str, Any]:
    role = to_text(role_code).lower()
    return {
        "audience": ["internal_user", "reviewer"] if role == "pm" else ["internal_user", "reviewer"] if role == "finance" else ["owner", "executive"],
        "priority_model": "task_first" if role == "pm" else "metric_first" if role == "finance" else "role_first",
        "mobile_priority": ["today_focus", "analysis", "quick_entries", "hero"],
    }


def build_default_v1_data_sources() -> Dict[str, Dict[str, Any]]:
    return {
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


def build_default_v1_state_schema() -> Dict[str, Dict[str, str]]:
    return {
        "pending": {"tone": "warning", "label": "待处理"},
        "running": {"tone": "info", "label": "进行中"},
        "blocked": {"tone": "danger", "label": "已阻塞"},
        "completed": {"tone": "success", "label": "已完成"},
        "overdue": {"tone": "danger", "label": "已逾期"},
    }
