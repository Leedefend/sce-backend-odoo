# -*- coding: utf-8 -*-
import time

from ..core.base_handler import BaseIntentHandler
from ..utils.extension_hooks import call_extension_hook_first

ALLOWED_SCENE_CHANNELS = {"stable", "beta", "dev"}


def _trace_id_from_context(ctx) -> str:
    try:
        return str((ctx or {}).get("trace_id") or "")
    except Exception:
        return ""


def _service(env, user):
    service_cls = call_extension_hook_first(env, "smart_core_scene_governance_service_class", env)
    if service_cls is None:
        raise RuntimeError("scene governance service provider is not configured")
    return service_cls(env, user)


class _BaseSceneGovernanceHandler(BaseIntentHandler):
    REQUIRED_GROUPS = ["smart_core.group_smart_core_scene_admin"]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "scene_delivery_governance"
    SOURCE_AUTHORITIES = ("sc.scene", "sc.scene.version", "ir.ui.menu", "ir.actions", "res.groups")
    NO_BUSINESS_FACT_AUTHORITY = True

    def _params(self, payload):
        params = (payload or {}).get("params") if isinstance(payload, dict) else payload
        if isinstance(params, dict):
            return params
        if isinstance(payload, dict):
            return payload
        return {}

    def _text_param(self, params: dict, field_name: str, *, default=None):
        raw = (params or {}).get(field_name, default)
        if raw is None or isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
            return "", self._err(400, f"{field_name} 无效")
        text = str(raw).strip()
        if not text:
            return "", self._err(400, f"{field_name} 无效")
        return text, None

    def _require_reason(self, params: dict):
        reason, error = self._text_param(params, "reason")
        if error:
            return "", error
        if not reason:
            return "", self._err(400, "reason 无效")
        return reason, None

    def _scene_channel(self, params: dict, *, default=None):
        channel, error = self._text_param(params, "channel", default=default)
        if error:
            return "", error
        channel = channel.lower()
        if channel not in ALLOWED_SCENE_CHANNELS:
            return "", self._err(400, "channel 无效")
        return channel, None

    def _err(self, code: int, message: str):
        return {
            "ok": False,
            "error": {"code": code, "message": message},
            "code": code,
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract()},
        }

    def _positive_int(self, value, field_name: str):
        if value in (None, False, ""):
            return 0, None
        try:
            parsed = int(value)
        except Exception:
            return 0, self._err(400, f"{field_name} 无效")
        if parsed <= 0:
            return 0, self._err(400, f"{field_name} 无效")
        return parsed, None

    def _response(self, ts0: float, data: dict):
        return {
            "status": "success",
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "source_authority": self._source_authority_contract(),
            },
        }

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "delivery_only": True,
            "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
        }


class SceneGovernanceSetChannelHandler(_BaseSceneGovernanceHandler):
    INTENT_TYPE = "scene.governance.set_channel"
    DESCRIPTION = "Set scene channel for company"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "admin policy change mutates governance state and needs operator intent per request"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        reason, reason_error = self._require_reason(params)
        if reason_error:
            return reason_error
        channel, channel_error = self._scene_channel(params)
        if channel_error:
            return channel_error
        company_id = params.get("company_id") or self.env.user.company_id.id
        company_id, company_error = self._positive_int(company_id, "company_id")
        if company_error:
            return company_error
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
        reason, reason_error = self._require_reason(params)
        if reason_error:
            return reason_error
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
        reason, reason_error = self._require_reason(params)
        if reason_error:
            return reason_error
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
        reason, reason_error = self._require_reason(params)
        if reason_error:
            return reason_error
        channel, channel_error = self._scene_channel(params, default="stable")
        if channel_error:
            return channel_error
        result = _service(self.env, self.env.user).export_contract(
            channel, reason, trace_id=_trace_id_from_context(self.context)
        )
        return self._response(ts0, result)
