# -*- coding: utf-8 -*-
from __future__ import annotations


class ProjectInitializationService:
    """Initialize lightweight project skeleton after intake creation."""

    def __init__(self, env):
        self.env = env

    def bootstrap(self, project):
        project.ensure_one()
        result = {
            "project_task_root": False,
            "project_cost_ledger": "deferred",
            "project_finance_ledger": "deferred",
            "project_risk_profile": "derived",
        }

        task_model = self.env["project.task"].sudo() if "project.task" in self.env else None
        if task_model is not None:
            has_task = bool(task_model.search_count([("project_id", "=", project.id)]))
            if not has_task:
                vals = {
                    "name": "项目根任务（Project Root Task）",
                    "project_id": project.id,
                }
                if getattr(project, "manager_id", False):
                    vals["user_ids"] = [(6, 0, [int(project.manager_id.id)])]
                    if "user_id" in getattr(task_model, "_fields", {}):
                        vals["user_id"] = int(project.manager_id.id)
                task_model.create(vals)
            result["project_task_root"] = True

        if hasattr(project, "message_post"):
            project.sudo().message_post(
                body=(
                    "项目初始化已完成：已建立项目管理对象；"
                    "任务根节点已就绪；成本/资金/风险承载采用按业务事件驱动补充。"
                )
            )

        return result


class ProjectCreationService:
    """Domain service for intake-style project creation semantics."""

    def __init__(self, env):
        self.env = env
        self.initializer = ProjectInitializationService(env)

    def normalize_create_vals(self, vals):
        normalized = dict(vals or {})
        if not normalized.get("manager_id"):
            fallback_uid = normalized.get("user_id") or self.env.user.id
            normalized["manager_id"] = int(fallback_uid)
        if not normalized.get("phase_key"):
            normalized["phase_key"] = "initiation"
        if not normalized.get("lifecycle_state"):
            normalized["lifecycle_state"] = "draft"
        return normalized

    def post_create_bootstrap(self, projects):
        for project in projects:
            self.initializer.bootstrap(project)
