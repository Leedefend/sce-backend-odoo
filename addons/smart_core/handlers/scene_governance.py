# -*- coding: utf-8 -*-
import time

from ..core.base_handler import BaseIntentHandler


def _trace_id_from_context(ctx) -> str:
    try:
        return str((ctx or {}).get("trace_id") or "")
    except Exception:
        return ""


def _service(env, user):
    from odoo.addons.smart_construction_scene.services.scene_governance_service import SceneGovernanceService
    return SceneGovernanceService(env, user)


class _BaseSceneGovernanceHandler(BaseIntentHandler):
    REQUIRED_GROUPS = ["smart_construction_core.group_sc_cap_config_admin"]

    def _params(self, payload):
        params = (payload or {}).get("params") if isinstance(payload, dict) else payload
        if isinstance(params, dict):
            return params
        if isinstance(payload, dict):
            return payload
        return {}

    def _require_reason(self, params: dict) -> str:
        reason = str((params or {}).get("reason") or "").strip()
        if not reason:
            raise ValueError("reason is required")
        return reason

    def _response(self, ts0: float, data: dict):
        return {
            "status": "success",
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
            },
        }


class SceneGovernanceSetChannelHandler(_BaseSceneGovernanceHandler):
    INTENT_TYPE = "scene.governance.set_channel"
    DESCRIPTION = "Set scene channel for company"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "admin policy change mutates governance state and needs operator intent per request"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        reason = self._require_reason(params)
        channel = (params.get("channel") or "").strip().lower()
        company_id = params.get("company_id") or self.env.user.company_id.id
        company_id = int(company_id)
        result = _service(self.env, self.env.user).set_company_channel(
            company_id, channel, reason, trace_id=_trace_id_from_context(self.context)
        )
        return self._response(ts0, result)


class SceneGovernanceRollbackHandler(_BaseSceneGovernanceHandler):
    INTENT_TYPE = "scene.governance.rollback"
    DESCRIPTION = "Rollback scene to stable pinned"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "rollback is an operator action and should not be auto-replayed"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        reason = self._require_reason(params)
        result = _service(self.env, self.env.user).rollback_stable(
            reason, trace_id=_trace_id_from_context(self.context)
        )
        return self._response(ts0, result)


class SceneGovernancePinStableHandler(_BaseSceneGovernanceHandler):
    INTENT_TYPE = "scene.governance.pin_stable"
    DESCRIPTION = "Pin stable contract and enable rollback mode"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "pin stable writes governance baseline and must remain explicit"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        reason = self._require_reason(params)
        result = _service(self.env, self.env.user).pin_stable(
            reason, trace_id=_trace_id_from_context(self.context)
        )
        return self._response(ts0, result)


class SceneGovernanceExportContractHandler(_BaseSceneGovernanceHandler):
    INTENT_TYPE = "scene.governance.export_contract"
    DESCRIPTION = "Export scene contract for channel"
    VERSION = "1.0.0"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        reason = self._require_reason(params)
        channel = (params.get("channel") or "stable").strip().lower()
        result = _service(self.env, self.env.user).export_contract(
            channel, reason, trace_id=_trace_id_from_context(self.context)
        )
        return self._response(ts0, result)
