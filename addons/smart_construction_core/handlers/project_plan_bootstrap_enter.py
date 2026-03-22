# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler


class ProjectPlanBootstrapEnterHandler(BaseIntentHandler):
    INTENT_TYPE = "project.plan_bootstrap.enter"
    DESCRIPTION = "预留项目计划编排场景入口"
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

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        project_id = self._coerce_project_id((params or {}).get("project_id"))
        if project_id <= 0:
            return {
                "ok": False,
                "error": {
                    "code": "MISSING_PARAMS",
                    "message": "缺少参数：project_id",
                    "suggested_action": "fix_input",
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": str((self.context or {}).get("trace_id") or ""),
                },
            }

        return {
            "ok": True,
            "data": {
                "state": "planned",
                "project_id": project_id,
                "scene_key": "project.plan_bootstrap",
                "reason_code": "PLAN_BOOTSTRAP_RESERVED",
                "message": "Phase 12-E 仅预留 plan bootstrap 入口，本轮不展开场景实现。",
                "suggested_action": {
                    "key": "return_project_dashboard",
                    "intent": "project.dashboard.enter",
                    "params": {"project_id": project_id},
                    "reason_code": "PLAN_BOOTSTRAP_NOT_DELIVERED_YET",
                },
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "trace_id": str((self.context or {}).get("trace_id") or ""),
            },
        }
