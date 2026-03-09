# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def build_page_contracts(_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": "v1",
        "pages": {
            "home": {"schema_version": "v1", "texts": {}},
            "login": {
                "schema_version": "v1",
                "texts": {
                    "title": "Login",
                    "username_label": "Username",
                    "password_label": "Password",
                    "submit_idle": "Sign in",
                    "submit_loading": "Signing in...",
                    "error_login_failed": "Login failed",
                },
            },
            "menu": {
                "schema_version": "v1",
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
                "texts": {
                    "title": "Dynamic View Placeholder",
                    "route_label": "Route",
                    "params_label": "Params",
                },
            },
            "workbench": {
                "schema_version": "v1",
                "texts": {
                    "header_title": "页面暂时无法打开",
                    "header_subtitle": "我们已为你保留可继续操作的入口。",
                    "action_go_workbench": "返回工作台",
                    "action_open_menu": "打开菜单",
                    "action_refresh": "刷新",
                    "panel_title": "页面暂时无法打开",
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
                "texts": {
                    "title": "我的工作",
                    "loading_title": "加载我的工作中...",
                    "empty_desc": "状态良好。你可以返回工作台查看整体态势，或进入风险驾驶舱继续巡检。",
                    "error_request_failed": "请求失败",
                    "feedback_save_preset_failed": "保存常用筛选失败",
                    "feedback_apply_preset_failed": "应用常用筛选失败",
                    "feedback_clear_preset_failed": "清除常用筛选失败",
                },
            },
            "scene": {
                "schema_version": "v1",
                "texts": {
                    "loading_title": "正在加载场景...",
                    "error_fallback": "场景加载失败",
                    "forbidden_title": "能力未开通",
                    "forbidden_message": "当前角色无法进入该场景。",
                    "forbidden_title_permission": "权限不足",
                    "forbidden_message_scope_missing": "当前角色能力范围不包含该场景所需能力。",
                    "error_scene_target_unsupported": "scene target unsupported",
                    "error_scene_resolve_failed": "scene resolve failed",
                },
            },
            "action": {
                "schema_version": "v1",
                "texts": {
                    "status_loading": "加载中",
                    "status_error": "加载失败",
                    "status_empty": "暂无数据",
                    "status_ready": "已就绪",
                    "intent_title_risk": "风险驾驶舱：先处理严重与逾期风险",
                    "intent_title_contract": "合同执行：优先识别付款与变更风险",
                    "intent_title_cost": "成本执行：先回答是否超支",
                    "intent_title_project": "项目视角：先判断是否可控",
                    "intent_title_default": "业务列表：先看状态，再执行动作",
                    "empty_title_default": "当前视图暂无数据",
                    "empty_hint_default": "建议切换到我的工作或风险驾驶舱继续处理。",
                    "empty_reason_default": "可能因为暂无业务数据、当前角色权限受限，或数据尚未生成。",
                    "empty_reason_filter": "可能由当前筛选条件导致无数据，建议先清除筛选后重试。",
                },
            },
            "record": {
                "schema_version": "v1",
                "texts": {
                    "loading_title": "Loading record...",
                    "saving_title": "Saving record...",
                    "error_fallback": "Record load failed",
                },
            },
            "scene_health": {
                "schema_version": "v1",
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
                "texts": {
                    "title": "Usage Analytics",
                    "loading_title": "Loading usage report...",
                    "error_fallback": "Failed to load usage report",
                    "empty_text": "暂无数据",
                },
            },
        },
    }
