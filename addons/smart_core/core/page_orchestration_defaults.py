# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def to_text(value: Any) -> str:
    return str(value or "").strip()


def build_default_page_type(page_key: str) -> str:
    key = to_text(page_key).lower()
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


def build_default_page_audience(page_key: str) -> List[str]:
    key = to_text(page_key).lower()
    if key in {"usage_analytics", "scene_health"}:
        return ["executive", "owner", "internal_user"]
    if key in {"my_work", "action", "record"}:
        return ["internal_user", "owner", "reviewer"]
    if key in {"home", "workbench"}:
        return ["internal_user", "owner", "executive"]
    return ["generic_user"]


def build_default_page_actions(page_key: str) -> List[Dict[str, Any]]:
    key = to_text(page_key).lower()
    if key == "home":
        return [
            {"key": "open_my_work", "label": "我的工作", "intent": "ui.contract"},
            {"key": "open_usage_analytics", "label": "使用分析", "intent": "ui.contract"},
        ]
    if key == "my_work":
        return [{"key": "refresh_page", "label": "刷新", "intent": "api.data"}]
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
            {"key": "open_my_work", "label": "进入工作区", "intent": "ui.contract"},
            {"key": "open_workspace_overview", "label": "查看工作概览", "intent": "ui.contract"},
            {"key": "refresh_page", "label": "刷新", "intent": "api.data"},
        ]
    return [{"key": "refresh_page", "label": "刷新", "intent": "api.data"}]
