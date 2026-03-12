# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler

_logger = logging.getLogger(__name__)


class TelemetryTrackHandler(BaseIntentHandler):
    INTENT_TYPE = "telemetry.track"
    DESCRIPTION = "Track workspace telemetry events (non-product analytics)"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    ACL_MODE = "explicit_check"
    REQUIRED_GROUPS = ["base.group_user"]
    NON_IDEMPOTENT_ALLOWED = "telemetry stream is append-only and intentionally non-replayable"

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        if not isinstance(params, dict):
            params = {}
        event_type = str(
            params.get("event_type")
            or params.get("event")
            or params.get("event_name")
            or ""
        ).strip().lower()
        if not event_type:
            _logger.warning("[telemetry.track] ignored invalid payload: %s", params)
            return {
                "ok": True,
                "data": {"ignored": True, "reason": "invalid telemetry params"},
                "meta": {"intent": self.INTENT_TYPE},
            }

        user = self.env.user
        data = {
            "event_type": event_type,
            "user_id": int(user.id or 0) if user else 0,
            "company_id": int(user.company_id.id or 0) if user and user.company_id else 0,
            "payload": params,
        }
        _logger.info(
            "[telemetry.track] %s",
            json.dumps(data, ensure_ascii=False, sort_keys=True, default=str),
        )
        return {"ok": True, "data": {"event_type": event_type}, "meta": {"intent": self.INTENT_TYPE}}
