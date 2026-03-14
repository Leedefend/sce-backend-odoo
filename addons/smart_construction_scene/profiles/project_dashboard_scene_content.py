# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def build_project_dashboard_scene_content() -> Dict[str, Any]:
    zone_blocks: List[Dict[str, str]] = [
        {
            "key": "header",
            "title": "项目头部信息",
            "zone_type": "hero",
            "display_mode": "stack",
            "block_key": "block.project.header",
        },
        {
            "key": "metrics",
            "title": "关键指标",
            "zone_type": "primary",
            "display_mode": "grid",
            "block_key": "block.project.metrics",
        },
        {
            "key": "progress",
            "title": "项目进度",
            "zone_type": "primary",
            "display_mode": "stack",
            "block_key": "block.project.progress",
        },
        {
            "key": "contract",
            "title": "合同执行",
            "zone_type": "secondary",
            "display_mode": "stack",
            "block_key": "block.project.contract",
        },
        {
            "key": "cost",
            "title": "成本控制",
            "zone_type": "secondary",
            "display_mode": "stack",
            "block_key": "block.project.cost",
        },
        {
            "key": "finance",
            "title": "资金情况",
            "zone_type": "secondary",
            "display_mode": "stack",
            "block_key": "block.project.finance",
        },
        {
            "key": "risk",
            "title": "风险提醒",
            "zone_type": "supporting",
            "display_mode": "stack",
            "block_key": "block.project.risk",
        },
    ]
    return {
        "scene": {
            "key": "project.management",
            "page": "project.management.dashboard",
        },
        "page": {
            "key": "project.management.dashboard",
            "title": "项目驾驶舱",
            "route": "/s/project.management",
        },
        "zone_blocks": zone_blocks,
    }

