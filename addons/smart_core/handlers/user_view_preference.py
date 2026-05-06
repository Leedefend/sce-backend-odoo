# -*- coding: utf-8 -*-
from ..core.base_handler import BaseIntentHandler


class UserViewPreferenceGetHandler(BaseIntentHandler):
    INTENT_TYPE = "user.view.preference.get"
    DESCRIPTION = "读取当前用户视图偏好"
    VERSION = "1.0.0"
    SOURCE_KIND = "ui_only_user_preference"
    SOURCE_AUTHORITIES = ("sc.user.view.preference", "res.users", "ir.actions.actions")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls):
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": cls.INTENT_TYPE.endswith(".set"),
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def _params(self, payload):
        if isinstance(payload, dict) and isinstance(payload.get("params"), dict):
            return payload.get("params") or {}
        return payload or {}

    def _scope_key(self, params):
        Preference = self.env["sc.user.view.preference"]
        preference_key = Preference.normalize_preference_key(params.get("preference_key"))
        view_type = str(params.get("view_type") or "list").strip() or "list"
        action_id, action_error = self._read_positive_int(params.get("action_id"), "action_id")
        if action_error:
            return "", action_error
        model_name = str(params.get("model") or params.get("model_name") or "").strip()
        return Preference.build_scope_key(
            preference_key=preference_key,
            view_type=view_type,
            action_id=action_id,
            model_name=model_name,
        ), None

    def _legacy_scope_key(self, params):
        preference_key = self.env["sc.user.view.preference"].normalize_preference_key(params.get("preference_key"))
        view_type = str(params.get("view_type") or "list").strip() or "list"
        action_id, action_error = self._read_positive_int(params.get("action_id"), "action_id")
        if action_error:
            return "", action_error
        model_name = str(params.get("model") or params.get("model_name") or "").strip()
        target = f"action:{action_id}" if action_id else f"model:{model_name or 'unknown'}"
        return f"{preference_key}:{view_type}:{target}", None

    def _positive_int(self, value):
        result, _error = self._read_positive_int(value, "value")
        return result

    def _read_positive_int(self, value, field_name):
        if value in (None, False, ""):
            return 0, None
        try:
            result = int(value)
        except (TypeError, ValueError):
            return 0, self._err(400, f"{field_name} 无效")
        if result < 0:
            return 0, self._err(400, f"{field_name} 无效")
        return result, None

    def _err(self, code, message):
        return {"ok": False, "error": {"code": code, "message": message}, "code": code, "meta": self._source_meta()}

    def _source_meta(self):
        return {
            "source_kind": self.SOURCE_KIND,
            "source_authorities": list(self.SOURCE_AUTHORITIES),
            "source_authority": self.source_authority_contract(),
        }

    def handle(self, payload=None, ctx=None):
        params = self._params(payload or self.payload)
        scope_key, scope_error = self._scope_key(params)
        if scope_error:
            return scope_error
        legacy_scope_key, legacy_error = self._legacy_scope_key(params)
        if legacy_error:
            return legacy_error
        Preference = self.env["sc.user.view.preference"]
        record = Preference.search([
            ("user_id", "=", self.env.uid),
            ("scope_key", "=", scope_key),
        ], limit=1)
        if not record and legacy_scope_key != scope_key:
            record = Preference.search([
                ("user_id", "=", self.env.uid),
                ("scope_key", "=", legacy_scope_key),
            ], limit=1)
        value = record.value_json if record else {}
        return {
            "ok": True,
            "data": {
                "scope_key": scope_key,
                "preference": value if isinstance(value, dict) else {},
            },
            "meta": {"intent": self.INTENT_TYPE, "version": self.VERSION, **self._source_meta()},
        }


class UserViewPreferenceSetHandler(UserViewPreferenceGetHandler):
    INTENT_TYPE = "user.view.preference.set"
    DESCRIPTION = "保存当前用户视图偏好"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = ["base.group_user"]

    def handle(self, payload=None, ctx=None):
        params = self._params(payload or self.payload)
        scope_key, scope_error = self._scope_key(params)
        if scope_error:
            return scope_error
        preference_key = self.env["sc.user.view.preference"].normalize_preference_key(params.get("preference_key"))
        view_type = str(params.get("view_type") or "list").strip() or "list"
        action_id, action_error = self._read_positive_int(params.get("action_id"), "action_id")
        if action_error:
            return action_error
        model_name = str(params.get("model") or params.get("model_name") or "").strip()
        value = params.get("preference")
        if not isinstance(value, dict):
            value = {}
        Preference = self.env["sc.user.view.preference"]
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
            "meta": {"intent": self.INTENT_TYPE, "version": self.VERSION, **self._source_meta()},
        }
