# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_context_contract import (
    build_project_context,
)
from odoo.addons.smart_construction_core.services.project_dashboard_service import (
    ProjectDashboardService,
)


class ProjectEntryContextService:
    ENTRY_ROUTE = "/s/project.management"

    def __init__(self, env):
        self.env = env
        self._dashboard_service = ProjectDashboardService(env)

    @staticmethod
    def _source_from_reason(resolution_path):
        normalized = str(resolution_path or "").strip().lower()
        if normalized == "explicit_project_id":
            return "current", "high"
        if normalized == "creator_domain":
            return "recent", "high"
        if normalized == "user_domain":
            return "current", "medium"
        if normalized in {"global_search", "active_search_read"}:
            return "fallback", "low"
        return "fallback", "low"

    def resolve(self, project_id=0):
        project, diagnostics = self._dashboard_service.resolve_project_with_diagnostics(project_id)
        project_context = build_project_context(project)
        source, confidence = self._source_from_reason((diagnostics or {}).get("resolution_path"))
        available = int(project_context.get("project_id") or 0) > 0
        return {
            "available": available,
            "project_context": project_context,
            "source": source if available else "none",
            "confidence": confidence if available else "low",
            "route": self.ENTRY_ROUTE if available else "/my-work",
            "diagnostics": diagnostics or {},
        }
