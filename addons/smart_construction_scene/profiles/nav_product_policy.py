# -*- coding: utf-8 -*-
from __future__ import annotations


def build_nav_group_policy() -> dict:
    """Construction-industry nav product policy for scene-nav v1."""

    return {
        "group_labels": {
            "portal": "工作台",
            "projects": "项目管理",
            "task": "任务管理",
            "risk": "风险管理",
            "cost": "成本管理",
            "contract": "合同管理",
            "finance": "资金财务",
            "data": "数据与字典",
            "config": "配置中心",
            "others": "其他场景",
        },
        "group_order": {
            "portal": 10,
            "projects": 20,
            "task": 30,
            "risk": 40,
            "cost": 50,
            "contract": 60,
            "finance": 70,
            "data": 80,
            "config": 90,
            "others": 999,
        },
        "group_aliases": {
            "project": "projects",
        },
    }
