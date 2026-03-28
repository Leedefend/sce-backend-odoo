# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List


DEFAULT_CAPABILITY_GROUPS = [
    {"key": "workspace", "label": "工作台", "icon": "layout-grid"},
    {"key": "governance", "label": "治理配置", "icon": "shield"},
    {"key": "analytics", "label": "经营分析", "icon": "chart"},
    {"key": "others", "label": "其他能力", "icon": "grid"},
]


def default_group_meta(group_key: str) -> dict:
    for item in DEFAULT_CAPABILITY_GROUPS:
        if item["key"] == group_key:
            return dict(item)
    return {"key": group_key, "label": group_key, "icon": ""}


def infer_group_key(capability_key: str) -> str:
    key = str(capability_key or "").strip().lower()
    if not key:
        return "others"
    if key.startswith(("workspace.", "my.", "app.")):
        return "workspace"
    if key.startswith(("usage.", "report.", "dashboard.", "analytics.")):
        return "analytics"
    if key.startswith(("scene.", "portal.", "config.", "permission.", "subscription.", "pack.")):
        return "governance"
    return "others"


def default_group_order_map(groups: List[dict] | None = None) -> dict[str, int]:
    source = groups if isinstance(groups, list) and groups else DEFAULT_CAPABILITY_GROUPS
    return {item["key"]: index for index, item in enumerate(source, start=1) if isinstance(item, dict) and item.get("key")}
