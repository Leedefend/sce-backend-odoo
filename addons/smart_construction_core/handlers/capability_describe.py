# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.handlers.system_init import CONTRACT_VERSION, API_VERSION


def _infer_schema(payload: dict) -> dict:
    schema = {}
    for key, value in (payload or {}).items():
        if isinstance(value, bool):
            schema[key] = "boolean"
        elif isinstance(value, int):
            schema[key] = "integer"
        elif isinstance(value, float):
            schema[key] = "number"
        elif isinstance(value, list):
            schema[key] = "array"
        elif isinstance(value, dict):
            schema[key] = "object"
        else:
            schema[key] = "string"
    return schema


class CapabilityDescribeHandler(BaseIntentHandler):
    INTENT_TYPE = "capability.describe"
    DESCRIPTION = "Describe capability payload/permissions/intent"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        key = params.get("key") or params.get("capability_key")
        cap_id = params.get("capability_id")

        Cap = self.env["sc.capability"].sudo()
        cap = None
        if key:
            cap = Cap.search([("key", "=", key)], limit=1)
        elif cap_id:
            try:
                cap = Cap.browse(int(cap_id))
            except Exception:
                cap = None
        if not cap or not cap.exists():
            return {"ok": False, "error": {"code": 404, "message": "Capability not found"}}

        if not cap._user_allowed(self.env.user):
            return {"ok": False, "error": {"code": 403, "message": "Permission denied"}}

        group_xmlids = cap.required_group_ids.get_external_id()
        required_groups = [
            group_xmlids.get(g.id) for g in cap.required_group_ids if group_xmlids.get(g.id)
        ]
        tags = [t.strip() for t in (cap.tags or "").split(",") if t.strip()]
        default_payload = cap._resolve_payload(cap.default_payload or {})

        data = {
            "key": cap.key,
            "name": cap.name,
            "ui_label": cap.ui_label or cap.name,
            "ui_hint": cap.ui_hint or "",
            "intent": cap.intent or "",
            "default_payload": default_payload,
            "payload_schema": _infer_schema(default_payload),
            "required_groups": required_groups,
            "tags": tags,
            "status": cap.status,
            "version": cap.version,
            "smoke_test": bool(cap.smoke_test),
            "contract_version": CONTRACT_VERSION,
            "api_version": API_VERSION,
        }
        meta = {"intent": self.INTENT_TYPE}
        return {"ok": True, "data": data, "meta": meta}
