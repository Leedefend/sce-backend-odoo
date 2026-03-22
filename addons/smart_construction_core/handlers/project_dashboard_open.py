# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict

from odoo.exceptions import AccessError

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.handlers.project_dashboard import build_dashboard_contract_v1
from odoo.addons.smart_construction_core.services.project_dashboard_service import ProjectDashboardService


class ProjectDashboardOpenHandler(BaseIntentHandler):
    INTENT_TYPE = "project.dashboard.open"
    DESCRIPTION = "打开项目驾驶舱场景并返回最小 contract 入口"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]

    @staticmethod
    def _coerce_project_id(raw: Any) -> int:
        try:
            value = int(raw or 0)
        except Exception:
            return 0
        return value if value > 0 else 0

    def _resolve_project_id(self, params: Dict[str, Any], ctx: Dict[str, Any]) -> int:
        candidates = [
            (params or {}).get("project_id"),
            (params or {}).get("record_id"),
            ((params or {}).get("project_context") or {}).get("project_id")
            if isinstance((params or {}).get("project_context"), dict)
            else None,
            (ctx or {}).get("project_id"),
            (ctx or {}).get("record_id"),
        ]
        for item in candidates:
            project_id = self._coerce_project_id(item)
            if project_id > 0:
                return project_id
        return 0

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        ctx = ctx or {}

        project_id = self._resolve_project_id(params, ctx)
        menu_xmlid = "smart_construction_core.menu_sc_project_dashboard"
        menu = self.env.ref(menu_xmlid, raise_if_not_found=False)

        if project_id <= 0:
            data = {
                "subject": "ui.contract",
                "scene_key": "workspace.home",
                "route": "/s/workspace.home",
                "reason_code": "PROJECT_CONTEXT_MISSING",
                "project_context": {"project_id": 0},
                "contract_ref": {
                    "intent": "ui.contract",
                    "params": {"op": "menu", "menu_xmlid": "smart_core.menu_sc_workspace_home"},
                },
            }
            return {
                "ok": True,
                "data": data,
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": str((self.context or {}).get("trace_id") or ""),
                },
            }

        dashboard_reason = "PROJECT_DASHBOARD_OPEN"
        try:
            service = ProjectDashboardService(self.env)
            raw_contract = service.build(project_id=project_id, context=ctx)
            dashboard_contract = build_dashboard_contract_v1(raw_contract, project_id=project_id)
        except AccessError:
            dashboard_reason = "PROJECT_DASHBOARD_PERMISSION_DENIED"
            dashboard_contract = {
                "kind": "project_dashboard_contract_v1",
                "scene_key": "project.dashboard",
                "project_context": {"project_id": int(project_id)},
                "blocks": [
                    {
                        "key": "summary",
                        "block": {
                            "key": "block.project.dashboard.summary.forbidden",
                            "state": "forbidden",
                            "data": {"summary": {}},
                        },
                    },
                    {
                        "key": "progress",
                        "block": {
                            "key": "block.project.dashboard.progress.forbidden",
                            "state": "forbidden",
                            "data": {"progress": {}},
                        },
                    },
                    {
                        "key": "next_actions",
                        "block": {
                            "key": "block.project.dashboard.next_actions.forbidden",
                            "state": "ready",
                            "data": {
                                "actions": [
                                    {
                                        "key": "request_access",
                                        "label": "申请项目驾驶舱权限",
                                        "intent": "permission.check",
                                    }
                                ]
                            },
                        },
                    },
                ],
            }
        except Exception:
            dashboard_reason = "PROJECT_DASHBOARD_FALLBACK"
            dashboard_contract = {
                "kind": "project_dashboard_contract_v1",
                "scene_key": "project.dashboard",
                "project_context": {"project_id": int(project_id)},
                "blocks": [
                    {
                        "key": "summary",
                        "block": {
                            "key": "block.project.dashboard.summary.empty",
                            "state": "empty",
                            "data": {"summary": {}},
                        },
                    },
                    {
                        "key": "progress",
                        "block": {
                            "key": "block.project.dashboard.progress.empty",
                            "state": "empty",
                            "data": {"progress": {}},
                        },
                    },
                    {
                        "key": "next_actions",
                        "block": {
                            "key": "block.project.dashboard.next_actions.empty",
                            "state": "ready",
                            "data": {
                                "actions": [
                                    {
                                        "key": "open_workspace_overview",
                                        "label": "返回工作区",
                                        "intent": "ui.contract",
                                    }
                                ]
                            },
                        },
                    },
                ],
            }

        contract_params = {
            "op": "menu",
            "menu_id": int(menu.id) if menu else 0,
            "menu_xmlid": menu_xmlid,
            "project_id": int(project_id),
            "scene_key": "project.dashboard",
        }
        if int(contract_params.get("menu_id") or 0) <= 0:
            contract_params = {
                "op": "model",
                "model": "project.project",
                "project_id": int(project_id),
                "scene_key": "project.dashboard",
            }

        data = {
            "subject": "ui.contract",
            "scene_key": "project.dashboard",
            "route": f"/s/project.dashboard?project_id={int(project_id)}",
            "reason_code": dashboard_reason,
            "project_context": {"project_id": int(project_id)},
            "contract_ref": {
                "intent": "ui.contract",
                "params": dict(contract_params),
            },
            "dashboard_contract": dashboard_contract,
        }
        return {
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "trace_id": str((self.context or {}).get("trace_id") or ""),
            },
        }
