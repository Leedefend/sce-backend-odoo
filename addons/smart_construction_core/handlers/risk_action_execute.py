# -*- coding: utf-8 -*-
from __future__ import annotations

from uuid import uuid4

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.handlers.reason_codes import (
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_OK,
    REASON_PERMISSION_DENIED,
    REASON_UNSUPPORTED_BUTTON_TYPE,
    failure_meta_for_reason,
)


class RiskActionExecuteHandler(BaseIntentHandler):
    INTENT_TYPE = "risk.action.execute"
    DESCRIPTION = "Execute risk action mutation operations"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    _SUPPORTED_ACTIONS = {"claim", "escalate", "close"}

    def _trace_id(self) -> str:
        if isinstance(self.context, dict):
            value = str(self.context.get("trace_id") or "").strip()
            if value:
                return value
        return f"risk_exec_{uuid4().hex[:12]}"

    def _error(self, *, message: str, trace_id: str, code: int = 400, reason_code: str = REASON_MISSING_PARAMS):
        return {
            "ok": False,
            "data": {
                "success": False,
                "reason_code": reason_code,
                "message": str(message or ""),
            },
            "error": {
                "code": reason_code,
                "reason_code": reason_code,
                "message": str(message or ""),
                **failure_meta_for_reason(reason_code),
            },
            "code": int(code),
            "meta": {"intent": self.INTENT_TYPE, "trace_id": trace_id},
        }

    def _assert_permission(self):
        user = self.env.user
        if not user:
            return False
        if user.has_group("base.group_system"):
            return True
        for xmlid in (
            "smart_construction_core.group_sc_cap_project_user",
            "smart_construction_core.group_sc_cap_project_manager",
            "smart_construction_core.group_sc_cap_project_read",
        ):
            try:
                if user.has_group(xmlid):
                    return True
            except Exception:
                continue
        return False

    def handle(self, payload=None, ctx=None):
        trace_id = self._trace_id()
        if not self._assert_permission():
            return self._error(
                message="permission denied",
                trace_id=trace_id,
                code=403,
                reason_code=REASON_PERMISSION_DENIED,
            )

        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}

        action = str((params or {}).get("action") or "").strip().lower()
        if action not in self._SUPPORTED_ACTIONS:
            return self._error(
                message="unsupported action",
                trace_id=trace_id,
                code=400,
                reason_code=REASON_UNSUPPORTED_BUTTON_TYPE,
            )

        risk_action_id = int((params or {}).get("risk_action_id") or 0)
        project_id = int((params or {}).get("project_id") or 0)
        name = str((params or {}).get("name") or "").strip()
        note = str((params or {}).get("note") or "").strip()
        owner_id = int((params or {}).get("owner_id") or 0)

        RiskAction = self.env["project.risk.action"]
        record = RiskAction.browse(risk_action_id) if risk_action_id > 0 else RiskAction.browse()
        if risk_action_id > 0 and not record.exists():
            return self._error(
                message="risk action not found",
                trace_id=trace_id,
                code=404,
                reason_code=REASON_NOT_FOUND,
            )

        if not record:
            if project_id <= 0 or not name:
                return self._error(
                    message="missing project_id or name",
                    trace_id=trace_id,
                    code=400,
                    reason_code=REASON_MISSING_PARAMS,
                )
            record = RiskAction.create(
                {
                    "project_id": project_id,
                    "name": name,
                    "state": "open",
                    "risk_level": str((params or {}).get("risk_level") or "medium"),
                    "note": note,
                }
            )

        if action == "claim":
            record.action_claim(owner_id=owner_id or self.env.user.id)
        elif action == "escalate":
            record.action_escalate(note=note)
        elif action == "close":
            record.action_close(note=note)

        return {
            "ok": True,
            "code": 200,
            "data": {
                "success": True,
                "reason_code": REASON_OK,
                "intent_action": action,
                "risk_action": {
                    "id": int(record.id),
                    "name": str(record.name or ""),
                    "project_id": int(record.project_id.id or 0),
                    "state": str(record.state or ""),
                    "risk_level": str(record.risk_level or ""),
                    "owner_id": int(record.owner_id.id or 0),
                },
                "mutation": {
                    "type": "transition",
                    "model": "project.risk.action",
                    "operation": action,
                },
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "trace_id": trace_id,
            },
        }
