# -*- coding: utf-8 -*-
from __future__ import annotations

import time

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.handlers.project_dashboard_enter import ProjectDashboardEnterHandler
from odoo.addons.smart_construction_core.handlers.project_context_resolver import (
    ProjectContextResolverMixin,
)


class ProjectDashboardOpenHandler(ProjectContextResolverMixin, BaseIntentHandler):
    INTENT_TYPE = "project.dashboard.open"
    DESCRIPTION = "历史入口转发到 project.dashboard.enter"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]
    SOURCE_AUTHORITY = {
        "kind": "project_dashboard_legacy_alias_proxy",
        "authorities": ["project.dashboard.enter"],
        "projection_only": True,
        "compatibility_only": True,
        "no_business_fact_authority": True,
    }

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        ctx = ctx or {}
        project_id = self._resolve_project_id(params, ctx)
        delegate = ProjectDashboardEnterHandler(self.env, payload={"project_id": project_id}, context=self.context)
        delegated = delegate.handle(payload={"project_id": project_id}, ctx=ctx)
        meta = delegated.get("meta") if isinstance(delegated.get("meta"), dict) else {}
        meta.update(
            {
                "intent": self.INTENT_TYPE,
                "deprecated": True,
                "deprecated_replacement_intent": "project.dashboard.enter",
                "deprecated_removal_phase": "Phase 12-G",
                "source_authority": meta.get("source_authority") or self.SOURCE_AUTHORITY,
            }
        )
        if delegated.get("ok") is not True:
            delegated["meta"] = meta
            return delegated
        data = delegated.get("data") if isinstance(delegated.get("data"), dict) else {}
        return {
            "ok": True,
            "data": {
                "alias_intent": self.INTENT_TYPE,
                "target_intent": "project.dashboard.enter",
                "project_id": int(data.get("project_id") or 0),
                "entry": data,
            },
            "meta": meta,
        }
