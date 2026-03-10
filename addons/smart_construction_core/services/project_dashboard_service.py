# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from .project_dashboard_builders import BUILDERS


class ProjectDashboardService:
    """Assemble project.dashboard contract using block builders."""

    ZONE_BLOCKS = (
        ("header", "项目头部信息", "hero", "stack", "block.project.header"),
        ("metrics", "关键指标", "primary", "grid", "block.project.metrics"),
        ("progress", "项目进度", "primary", "stack", "block.project.progress"),
        ("contract", "合同执行", "secondary", "stack", "block.project.contract"),
        ("cost", "成本控制", "secondary", "stack", "block.project.cost"),
        ("finance", "资金情况", "secondary", "stack", "block.project.finance"),
        ("risk", "风险提醒", "supporting", "stack", "block.project.risk"),
    )

    def __init__(self, env):
        self.env = env
        self._builders = [builder_cls(env) for builder_cls in BUILDERS]
        self._builder_map = {builder.block_key: builder for builder in self._builders}

    def build(self, project_id=None, context=None):
        ctx = dict(context or {})
        project = self._resolve_project(project_id)
        project_payload = self._project_payload(project)

        zones = {}
        for key, title, zone_type, display_mode, block_key in self.ZONE_BLOCKS:
            builder = self._builder_map.get(block_key)
            block = (
                builder.build(project=project, context=ctx)
                if builder
                else self._error_block(block_key, "BLOCK_BUILDER_NOT_FOUND")
            )
            zones[key] = {
                "zone_key": "zone.%s" % key,
                "title": title,
                "zone_type": zone_type,
                "display_mode": display_mode,
                "blocks": [block],
            }

        return {
            "scene": {
                "key": "project.management",
                "page": "project.management.dashboard",
            },
            "page": {
                "key": "project.management.dashboard",
                "title": "项目管理控制台",
                "route": "/s/project.management",
            },
            "route_context": self._route_context(project),
            "project": project_payload,
            "zones": zones,
        }

    def _model(self, model_name):
        try:
            return self.env[model_name]
        except Exception:
            return None

    def _project_domain_for_user(self):
        model = self._model("project.project")
        if not model:
            return []
        f = getattr(model, "_fields", {})
        uid = int(self.env.user.id)
        ors = []
        for field in ("manager_id", "owner_id", "user_id"):
            if field in f:
                ors.append((field, "=", uid))
        if not ors:
            return []
        if len(ors) == 1:
            return [ors[0]]
        return (["|"] * (len(ors) - 1)) + ors

    def _resolve_project(self, project_id):
        Project = self._model("project.project")
        if not Project:
            return None
        if project_id:
            try:
                record = Project.browse(int(project_id)).exists()
                if record:
                    return record
            except Exception:
                pass
        try:
            return Project.search(self._project_domain_for_user(), order="write_date desc,id desc", limit=1)
        except Exception:
            return None

    def _project_payload(self, project):
        if not project:
            return {
                "id": 0,
                "name": "",
                "project_code": "",
                "partner_name": "",
                "manager_name": "",
                "stage_name": "",
                "state": "empty",
                "date": str(fields.Date.today()),
            }
        return {
            "id": int(project.id),
            "name": str(getattr(project, "name", "") or ""),
            "project_code": str(getattr(project, "project_code", "") or ""),
            "partner_name": str(getattr(getattr(project, "partner_id", None), "display_name", "") or ""),
            "manager_name": str(getattr(getattr(project, "user_id", None), "display_name", "") or ""),
            "stage_name": str(getattr(getattr(project, "stage_id", None), "display_name", "") or ""),
            "state": "ready",
            "date": str(fields.Date.today()),
        }

    @staticmethod
    def _route_context(project):
        route = "/s/project.management"
        query_key = "project_id"
        out = {
            "primary_protocol": "/s/project.management?project_id=<id>",
            "query_key": query_key,
            "scene_route": route,
            "project_route_template": "/s/project.management?project_id={project_id}",
            "project_route": route,
        }
        if project:
            out["project_route"] = "/s/project.management?project_id=%s" % int(project.id)
        return out

    @staticmethod
    def _error_block(block_key, code):
        return {
            "block_key": block_key,
            "block_type": "unknown",
            "title": block_key,
            "state": "error",
            "visibility": {"allowed": True, "reason_code": "OK", "reason": ""},
            "data": {},
            "error": {"code": code, "message": code},
        }
