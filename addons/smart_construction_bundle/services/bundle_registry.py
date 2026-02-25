# -*- coding: utf-8 -*-
from __future__ import annotations


def list_bundle_scenes() -> list[dict]:
    return [
        {"code": "bundle.construction.startup", "name": "标准项目启动包"},
        {"code": "bundle.construction.payment", "name": "标准支付审批包"},
        {"code": "bundle.construction.exec", "name": "标准执行监控包"},
    ]


def list_bundle_capabilities() -> list[dict]:
    return [
        {"key": "bundle.construction.startup", "label": "项目启动包"},
        {"key": "bundle.construction.payment", "label": "支付审批包"},
        {"key": "bundle.construction.exec", "label": "执行监控包"},
    ]


def recommended_roles() -> list[str]:
    return ["pm", "finance", "executive"]


def default_dashboard() -> str:
    return "projects.dashboard"
