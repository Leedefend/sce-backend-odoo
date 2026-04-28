# -*- coding: utf-8 -*-
from ..core.base_handler import BaseIntentHandler


class UserViewPreferenceGetHandler(BaseIntentHandler):
    INTENT_TYPE = "user.view.preference.get"
    DESCRIPTION = "读取当前用户视图偏好"
    VERSION = "1.0.0"

    def _params(self, payload):
        if isinstance(payload, dict) and isinstance(payload.get("params"), dict):
            return payload.get("params") or {}
        return payload or {}

    def _scope_key(self, params):
        preference_key = str(params.get("preference_key") or "list_columns").strip() or "list_columns"
        view_type = str(params.get("view_type") or "list").strip() or "list"
        action_id = self._positive_int(params.get("action_id"))
        model_name = str(params.get("model") or params.get("model_name") or "").strip()
        target = f"action:{action_id}" if action_id else f"model:{model_name or 'unknown'}"
        return f"{preference_key}:{view_type}:{target}"

    def _positive_int(self, value):
        try:
            result = int(value or 0)
        except (TypeError, ValueError):
            result = 0
        return result if result > 0 else 0

    def handle(self, payload=None, ctx=None):
        params = self._params(payload or self.payload)
        scope_key = self._scope_key(params)
        record = self.env["sc.user.view.preference"].sudo().search([
            ("user_id", "=", self.env.uid),
            ("scope_key", "=", scope_key),
        ], limit=1)
        value = record.value_json if record else {}
        return {
            "ok": True,
            "data": {
                "scope_key": scope_key,
                "preference": value if isinstance(value, dict) else {},
            },
            "meta": {"intent": self.INTENT_TYPE, "version": self.VERSION},
        }


class UserViewPreferenceSetHandler(UserViewPreferenceGetHandler):
    INTENT_TYPE = "user.view.preference.set"
    DESCRIPTION = "保存当前用户视图偏好"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = ["base.group_user"]

    def handle(self, payload=None, ctx=None):
        params = self._params(payload or self.payload)
        scope_key = self._scope_key(params)
        preference_key = str(params.get("preference_key") or "list_columns").strip() or "list_columns"
        view_type = str(params.get("view_type") or "list").strip() or "list"
        action_id = self._positive_int(params.get("action_id"))
        model_name = str(params.get("model") or params.get("model_name") or "").strip()
        value = params.get("preference")
        if not isinstance(value, dict):
            value = {}
        Preference = self.env["sc.user.view.preference"].sudo()
        record = Preference.search([
            ("user_id", "=", self.env.uid),
            ("scope_key", "=", scope_key),
        ], limit=1)
        vals = {
            "user_id": self.env.uid,
            "scope_key": scope_key,
            "action_id": action_id or False,
            "model_name": model_name,
            "view_type": view_type,
            "preference_key": preference_key,
            "value_json": value,
        }
        if record:
            record.write(vals)
        else:
            record = Preference.create(vals)
        return {
            "ok": True,
            "data": {
                "id": record.id,
                "scope_key": scope_key,
                "preference": record.value_json if isinstance(record.value_json, dict) else {},
            },
            "meta": {"intent": self.INTENT_TYPE, "version": self.VERSION},
        }
