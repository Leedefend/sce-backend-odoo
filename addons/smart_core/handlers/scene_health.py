# -*- coding: utf-8 -*-
import time

from ..core.base_handler import BaseIntentHandler
from .system_init import SystemInitHandler, _build_scene_health_payload


class SceneHealthHandler(BaseIntentHandler):
    INTENT_TYPE = "scene.health"
    DESCRIPTION = "Scene health dashboard contract"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = []

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        params = payload.get("params") if isinstance(payload, dict) else None
        if not isinstance(params, dict):
            params = payload if isinstance(payload, dict) else {}
        ts0 = time.time()

        init_handler = SystemInitHandler(
            self.env,
            self.su_env,
            self.request,
            context=self.context,
            payload={"params": params},
        )
        init_result = init_handler.handle(payload={"params": params}, ctx=ctx)
        init_data = init_result.get("data") if isinstance(init_result, dict) else {}
        if not isinstance(init_data, dict):
            init_data = {}

        company_id = params.get("company_id")
        if company_id in ("", None):
            company_id = None
        else:
            try:
                company_id = int(company_id)
            except Exception:
                company_id = None

        trace_id = ""
        try:
            trace_id = str((self.context or {}).get("trace_id") or "")
        except Exception:
            trace_id = ""
        data = _build_scene_health_payload(init_data, trace_id=trace_id, company_id=company_id)
        if not params.get("with_details", True):
            data["details"] = {"resolve_errors": [], "drift": [], "debt": []}

        return {
            "status": "success",
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
            },
        }
