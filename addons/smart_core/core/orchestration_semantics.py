# -*- coding: utf-8 -*-
from __future__ import annotations

BLOCK_TYPES = (
    "hero_metric",
    "metric_row",
    "todo_list",
    "alert_panel",
    "progress_summary",
    "entry_grid",
    "accordion_group",
    "record_summary",
    "activity_feed",
)

STATE_TONES = ("success", "warning", "danger", "info", "neutral")
PROGRESS_STATES = ("overdue", "blocked", "pending", "running", "completed")

PAGE_TYPES = ("workspace", "dashboard", "list", "detail", "approval", "monitor", "report", "entry_hub")
LAYOUT_MODES = ("dashboard", "two_column", "single_flow", "focus_task", "monitoring", "entry_grid")
PRIORITY_MODELS = ("role_first", "risk_first", "task_first", "metric_first")
ZONE_TYPES = ("hero", "primary", "secondary", "supporting", "sidebar", "footer")
ZONE_DISPLAY_MODES = ("stack", "grid", "carousel", "tabs", "accordion", "flow")

DATA_SOURCE_TYPES = ("static", "scene_context", "api.data", "computed", "capability_registry", "role_profile", "mixed")
ACTION_INTENTS = ("ui.contract", "api.data", "execute_button", "file.download")
ACTION_TARGET_KINDS = ("scene.key", "page.refresh", "menu.first_reachable", "route.path")

BLOCK_PAYLOAD_KEYS = {
    "hero_metric": {"main_value_field", "label_field", "trend_field", "status_field", "click_action"},
    "metric_row": {"items", "show_trend"},
    "todo_list": {"item_layout", "fields", "max_items", "sort_by"},
    "alert_panel": {"alert_level_field", "title_field", "desc_field", "group_by", "max_items", "show_counts"},
    "progress_summary": {"bars", "show_percentage", "show_target"},
    "entry_grid": {"entry_source", "group_key", "layout", "show_icon", "show_hint", "entry_action_intent"},
    "accordion_group": {"mode"},
    "record_summary": {"tag", "enabled", "open", "style_variant"},
    "activity_feed": {"stream"},
}

COMMON_PAYLOAD_KEYS = {"tag", "enabled", "open"}
FORBIDDEN_LAYOUT_KEYS = {"left", "top", "width", "height", "x", "y", "color", "background", "font_size"}

