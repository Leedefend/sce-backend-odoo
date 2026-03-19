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
            "contracts": "合同履约",
            "payments": "收付款",
            "my_work": "我的工作",
            "portfolio": "项目组合",
            "quality": "质量管理",
            "safety": "安全管理",
            "resource": "资源调配",
            "delivery": "交付管理",
            "operation": "经营总览",
            "workspace": "工作空间",
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
            "contracts": 100,
            "payments": 110,
            "my_work": 120,
            "portfolio": 130,
            "quality": 140,
            "safety": 150,
            "resource": 160,
            "delivery": 170,
            "operation": 180,
            "workspace": 190,
            "others": 999,
        },
        "group_aliases": {
            "project": "projects",
        },
    }
