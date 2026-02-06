# -*- coding: utf-8 -*-
import time
from datetime import datetime

from ..core.base_handler import BaseIntentHandler
from .system_init import SystemInitHandler, _build_scene_health_payload


class SceneHealthHandler(BaseIntentHandler):
    INTENT_TYPE = "scene.health"
    DESCRIPTION = "Scene health dashboard contract"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = []

    def _safe_int(self, value, default):
        try:
            return int(value)
        except Exception:
            return default

    def _parse_since(self, raw):
        if not raw:
            return None
        try:
            txt = str(raw).strip()
            if txt.endswith("Z"):
                txt = txt[:-1] + "+00:00"
            return datetime.fromisoformat(txt)
        except Exception:
            return None

    def _entry_ts(self, entry):
        if not isinstance(entry, dict):
            return None
        raw = entry.get("created_at") or entry.get("ts") or entry.get("timestamp")
        if not raw:
            return None
        try:
            txt = str(raw).strip()
            if txt.endswith("Z"):
                txt = txt[:-1] + "+00:00"
            return datetime.fromisoformat(txt)
        except Exception:
            return None

    def _apply_window_and_paging(self, items, since_dt, limit, offset):
        rows = list(items or [])
        if since_dt is not None:
            rows = [row for row in rows if (self._entry_ts(row) is None or self._entry_ts(row) >= since_dt)]
        start = max(0, offset)
        end = start + max(1, limit)
        return rows[start:end]

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
        mode = str(params.get("mode") or "summary").strip().lower()
        if mode not in {"summary", "full"}:
            mode = "summary"
        limit = self._safe_int(params.get("limit"), 50)
        offset = self._safe_int(params.get("offset"), 0)
        since_dt = self._parse_since(params.get("since"))

        details = data.get("details") if isinstance(data.get("details"), dict) else {}
        for key in ("resolve_errors", "drift", "debt"):
            if isinstance(details.get(key), list):
                details[key] = self._apply_window_and_paging(details.get(key), since_dt, limit, offset)
        data["details"] = details

        with_details = bool(params.get("with_details", True))
        if mode == "summary" or not with_details:
            data.pop("details", None)
        data["query"] = {
            "mode": mode,
            "limit": limit,
            "offset": offset,
            "since": params.get("since"),
        }

        return {
            "status": "success",
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
            },
        }
