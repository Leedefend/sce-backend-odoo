# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.services.project_dashboard_service import (
    ProjectDashboardService,
)


def _extract_zone_block(zones, *keys):
    if not isinstance(zones, dict):
        return {}
    for key in keys:
        zone = zones.get(key) if isinstance(zones.get(key), dict) else {}
        blocks = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
        if blocks and isinstance(blocks[0], dict):
            return blocks[0]
    return {}


def build_dashboard_contract_v1(raw_data, *, project_id: int = 0):
    payload = raw_data if isinstance(raw_data, dict) else {}
    zones = payload.get("zones") if isinstance(payload.get("zones"), dict) else {}
    summary_block = _extract_zone_block(zones, "metrics", "header", "dashboard_summary")
    progress_block = _extract_zone_block(zones, "progress", "dashboard_progress")
    next_actions_block = _extract_zone_block(zones, "risk", "dashboard_risk")

    if not summary_block:
        summary_block = {
            "key": "block.project.dashboard.summary.placeholder",
            "state": "empty",
            "data": {"summary": {}},
        }
    if not progress_block:
        progress_block = {
            "key": "block.project.dashboard.progress.placeholder",
            "state": "empty",
            "data": {"progress": {}},
        }
    if not next_actions_block:
        next_actions_block = {
            "key": "block.project.dashboard.next_actions.placeholder",
            "state": "empty",
            "data": {
                "actions": [
                    {
                        "key": "open_workspace_overview",
                        "label": "返回工作区",
                        "intent": "ui.contract",
                    }
                ]
            },
        }

    return {
        "kind": "project_dashboard_contract_v1",
        "scene_key": "project.dashboard",
        "project_context": {"project_id": int(project_id or 0)},
        "blocks": [
            {"key": "summary", "block": summary_block},
            {"key": "progress", "block": progress_block},
            {"key": "next_actions", "block": next_actions_block},
        ],
    }


class ProjectDashboardHandler(BaseIntentHandler):
    INTENT_TYPE = "project.dashboard"
    DESCRIPTION = "Project management dashboard contract"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    @staticmethod
    def _coerce_project_id(raw):
        try:
            value = int(raw or 0)
        except Exception:
            return 0
        return value if value > 0 else 0

    def _resolve_project_id(self, params, ctx):
        payload = self.payload if isinstance(self.payload, dict) else {}
        candidates = [
            (params or {}).get("project_id"),
            payload.get("project_id"),
            (ctx or {}).get("project_id"),
        ]
        model = str((ctx or {}).get("model") or "").strip()
        if model == "project.project":
            candidates.append((ctx or {}).get("record_id"))
        for item in candidates:
            project_id = self._coerce_project_id(item)
            if project_id > 0:
                return project_id
        return 0

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        ctx = ctx or {}
        project_id = self._resolve_project_id(params, ctx)
        service = ProjectDashboardService(self.env)
        data = service.build(project_id=project_id, context=ctx)
        dashboard_contract = build_dashboard_contract_v1(data, project_id=project_id)
        data["dashboard_contract"] = dashboard_contract
        data["project_context"] = {"project_id": int(project_id or 0)}
        trace_id = str((ctx or {}).get("trace_id") or (params or {}).get("trace_id") or "")
        return {
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "trace_id": trace_id,
                "contract_version": "v1",
            },
        }
