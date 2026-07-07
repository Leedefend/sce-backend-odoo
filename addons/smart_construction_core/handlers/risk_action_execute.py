# -*- coding: utf-8 -*-
from __future__ import annotations

from uuid import uuid4

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.core.project_context import (
    project_scope_denied_response,
    selected_project_id_from_context,
)
try:
    from odoo.addons.smart_core.core.project_context import record_in_business_scope
except ImportError:  # pragma: no cover - standalone boundary-test fallback
    from odoo.addons.smart_core.core.project_context import record_in_project_scope

    def record_in_business_scope(env_model, record_id, params=None, context=None):
        return record_in_project_scope(env_model, record_id, selected_project_id_from_context(params, context))
from odoo.addons.smart_core.handlers.reason_codes import (
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_OK,
    REASON_PERMISSION_DENIED,
    REASON_UNSUPPORTED_BUTTON_TYPE,
    failure_meta_for_reason,
)
from odoo.addons.smart_core.security.platform_admin import user_is_platform_admin


class RiskActionExecuteHandler(BaseIntentHandler):
    INTENT_TYPE = "risk.action.execute"
    DESCRIPTION = "Execute risk action mutation operations"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["smart_core.group_smart_core_data_operator"]
    ACL_MODE = "explicit_check"

    _SUPPORTED_ACTIONS = {"claim", "escalate", "close"}
    SOURCE_AUTHORITY = {
        "kind": "project_risk_action_odoo_model_method_proxy",
        "authorities": [
            "project.risk.action",
            "sc.evidence.exception",
            "project.project",
            "ir.model.access",
            "ir.rule",
            "odoo.orm",
        ],
        "projection_only": False,
        "runtime_authority": "project.risk.action model methods",
        "write_authority": "project.risk.action.create/write",
    }

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
            "meta": {"intent": self.INTENT_TYPE, "trace_id": trace_id, "source_authority": self.SOURCE_AUTHORITY},
        }

    def _assert_permission(self):
        user = self.env.user
        if not user:
            return False
        if user_is_platform_admin(user):
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
        exception_id = int((params or {}).get("exception_id") or 0)
        project_id = int((params or {}).get("project_id") or 0)
        name = str((params or {}).get("name") or "").strip()
        note = str((params or {}).get("note") or "").strip()
        owner_id = int((params or {}).get("owner_id") or 0)
        current_project_id = selected_project_id_from_context(params, self.context if isinstance(self.context, dict) else {})
        if current_project_id and project_id > 0 and project_id != current_project_id:
            return project_scope_denied_response(
                {
                    "enabled": True,
                    "project_id": current_project_id,
                    "applied": True,
                    "domain": [("project_id", "=", current_project_id)],
                    "model": "project.risk.action",
                }
            )

        RiskAction = self.env["project.risk.action"].sudo()
        registry = getattr(self.env, "registry", None)
        models = getattr(registry, "models", {}) if registry is not None else {}
        exception_model_available = "sc.evidence.exception" in models
        if exception_model_available:
            ExceptionModel = self.env["sc.evidence.exception"].sudo()
            exception = ExceptionModel.browse(exception_id) if exception_id > 0 else ExceptionModel.browse()
            if exception_id > 0 and not exception.exists():
                return self._error(
                    message="exception not found",
                    trace_id=trace_id,
                    code=404,
                    reason_code=REASON_NOT_FOUND,
                )
        else:
            exception = False
        record = RiskAction.browse(risk_action_id) if risk_action_id > 0 else RiskAction.browse()
        if not record and exception and exception.risk_action_id:
            record = exception.risk_action_id
        if risk_action_id > 0 and not record.exists():
            return self._error(
                message="risk action not found",
                trace_id=trace_id,
                code=404,
                reason_code=REASON_NOT_FOUND,
            )
        if record:
            in_scope, scope_meta = record_in_business_scope(
                RiskAction,
                int(record.id),
                params,
                self.context if isinstance(self.context, dict) else {},
            )
            if not in_scope:
                return project_scope_denied_response(scope_meta)

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
            if exception:
                exception.sudo().write({"risk_action_id": int(record.id)})

        if action == "claim":
            record.action_claim(owner_id=owner_id or self.env.user.id)
            if exception:
                exception.sudo().action_assign(user_id=owner_id or self.env.user.id)
        elif action == "escalate":
            record.action_escalate(note=note)
            if exception:
                exception.sudo().action_processing(user_id=owner_id or self.env.user.id, note=note)
        elif action == "close":
            record.action_close(note=note)
            if exception:
                exception.sudo().action_resolve(note=note)

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
                "exception": {
                    "id": int(exception.id or 0) if exception else 0,
                    "status": str(exception.status or "") if exception else "",
                    "assigned_to": int(exception.assigned_to.id or 0) if exception and exception.assigned_to else 0,
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
                "source_authority": self.SOURCE_AUTHORITY,
            },
        }
