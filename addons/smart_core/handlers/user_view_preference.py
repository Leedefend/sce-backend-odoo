# -*- coding: utf-8 -*-
from ..core.base_handler import BaseIntentHandler


USER_CONFIRMED_FORMAL_LIST_ACTION_IDS = {
    506, 525, 529, 530, 531, 545, 549, 565, 566, 615,
    642, 644, 645, 646, 647, 669, 701, 751, 752, 753,
    754, 756, 757, 758, 759, 761, 762, 764, 768, 769,
    770, 771, 772, 773, 776, 777, 778, 779, 780, 781,
    782, 783, 784, 786, 787, 805, 814, 841, 859, 862,
    868, 869, 871, 901, 902, 906, 907, 935, 936, 949,
    963, 964,
}


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

    def _text_param(self, params, keys, *, default=""):
        if isinstance(keys, str):
            keys = (keys,)
        raw = None
        for key in keys:
            if key in params:
                raw = params.get(key)
                break
        if raw is None or raw == "":
            return default, None
        if isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
            return "", self._err(400, f"{keys[0]} 无效")
        text = str(raw).strip()
        return text or default, None

    def _scope_key(self, params):
        Preference = self.env["sc.user.view.preference"]
        preference_key = Preference.normalize_preference_key(params.get("preference_key"))
        view_type, view_type_error = self._text_param(params, "view_type", default="list")
        if view_type_error:
            return "", view_type_error
        action_id, action_error = self._read_positive_int(params.get("action_id"), "action_id")
        if action_error:
            return "", action_error
        model_name, model_error = self._text_param(params, ("model", "model_name"))
        if model_error:
            return "", model_error
        return Preference.build_scope_key(
            preference_key=preference_key,
            view_type=view_type,
            action_id=action_id,
            model_name=model_name,
        ), None

    def _legacy_scope_key(self, params):
        preference_key = self.env["sc.user.view.preference"].normalize_preference_key(params.get("preference_key"))
        view_type, view_type_error = self._text_param(params, "view_type", default="list")
        if view_type_error:
            return "", view_type_error
        action_id, action_error = self._read_positive_int(params.get("action_id"), "action_id")
        if action_error:
            return "", action_error
        model_name, model_error = self._text_param(params, ("model", "model_name"))
        if model_error:
            return "", model_error
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

    def _sanitize_list(self, value, *, max_size=80):
        if not isinstance(value, list):
            return []
        rows = []
        seen = set()
        for item in value:
            name = str(item or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            rows.append(name)
            if len(rows) >= max_size:
                break
        return rows

    def _sanitize_widths(self, value, *, names=None):
        if not isinstance(value, dict):
            return {}
        allowed = set(names or [])
        rows = {}
        for key, raw in value.items():
            name = str(key or "").strip()
            if not name:
                continue
            if allowed and name not in allowed:
                continue
            try:
                width = int(raw)
            except (TypeError, ValueError):
                continue
            if width <= 0:
                continue
            rows[name] = min(max(width, 80), 640)
        return rows

    def _sanitize_preference(self, preference_key, value):
        data = value if isinstance(value, dict) else {}
        if preference_key == "list_columns":
            visible = self._sanitize_list(data.get("visible_columns"))
            hidden = [name for name in self._sanitize_list(data.get("hidden_columns")) if name not in set(visible)]
            order = self._sanitize_list(data.get("column_order"))
            known = set(visible) | set(hidden)
            if known:
                order = [name for name in order if name in known]
            widths = self._sanitize_widths(data.get("column_widths"), names=known)
            return {
                "visible_columns": visible,
                "hidden_columns": hidden,
                "column_order": order,
                "column_widths": widths,
            }
        return {}

    def _resolve_list_profile_contract(self, *, action_id=0, model_name="", view_type="list"):
        try:
            from .ui_contract import UiContractHandler
            from ..core.intent_execution_result import adapt_handler_result

            ui_payload = {
                "params": {
                    "op": "action_open" if int(action_id or 0) > 0 else "model",
                    "action_id": int(action_id or 0),
                    "model": str(model_name or "").strip(),
                    "view_type": str(view_type or "list").strip() or "list",
                    "source_mode": "backend_internal",
                    "contract_surface": "user",
                }
            }
            result = adapt_handler_result(UiContractHandler(env=self.env).handle(ui_payload))
            data = result.get("data") if isinstance(result, dict) else {}
            if isinstance(data, dict):
                list_profile = data.get("list_profile")
                if isinstance(list_profile, dict):
                    return list_profile
        except Exception:
            pass

        svc = self.env.get("app.contract.service") if hasattr(self.env, "get") else None
        if not svc:
            return {}
        try:
            scoped = svc.with_context(dict(self.env.context or {}))
            result = scoped.generate_contract(
                model_name=str(model_name or "").strip(),
                view_type=str(view_type or "list").strip() or "list",
                include_parts={"view", "action", "permission", "model"},
                force_refresh=False,
                client_version="",
                menu_id=0,
                action_id=int(action_id or 0),
            ) or {}
            data = result.get("data") if isinstance(result, dict) else {}
            if not isinstance(data, dict):
                return {}
            list_profile = data.get("list_profile")
            return list_profile if isinstance(list_profile, dict) else {}
        except Exception:
            return {}

    def _apply_list_preference_policy(self, payload, *, list_profile, action_id=0, model_name=""):
        value = payload if isinstance(payload, dict) else {}
        profile = list_profile if isinstance(list_profile, dict) else {}
        columns = self._sanitize_list(profile.get("columns"), max_size=200)
        column_set = set(columns)
        fact_columns = self._sanitize_list(profile.get("fact_columns"), max_size=200)
        policy = profile.get("preference_policy") if isinstance(profile.get("preference_policy"), dict) else {}
        allow_visibility = policy.get("allow_visibility") is not False
        allow_order = policy.get("allow_order") is not False
        allow_width = policy.get("allow_width") is not False
        locked = set(self._sanitize_list(policy.get("locked_columns"), max_size=200))
        must_request = set(self._sanitize_list(policy.get("must_request_columns"), max_size=200))
        formal_locked = int(action_id or 0) in USER_CONFIRMED_FORMAL_LIST_ACTION_IDS
        if formal_locked:
            must_request.update(columns or fact_columns)
        # Scope boundary:
        # - fact_columns / must_request_columns: data request contract only
        # - locked_columns: UI visibility constraint
        pinned = set(locked)

        visible = self._sanitize_list(value.get("visible_columns"))
        hidden = self._sanitize_list(value.get("hidden_columns"))
        order = self._sanitize_list(value.get("column_order"))
        widths = self._sanitize_widths(value.get("column_widths"), names=(column_set or None))

        model_fields = set()
        model_name = str(model_name or "").strip()
        if model_name and model_name in self.env:
            model_fields = set(getattr(self.env[model_name], "_fields", {}) or {})
        if column_set:
            allowed = column_set | model_fields
            visible = [name for name in visible if name in allowed]
            hidden = [name for name in hidden if name in allowed]
            order = [name for name in order if name in allowed]
            widths = {name: width for name, width in widths.items() if name in column_set}

        if allow_visibility:
            visible_set = set(visible)
            hidden = [name for name in hidden if name not in visible_set and name not in pinned]
            if visible or hidden:
                visible = [name for name in visible if name not in hidden]
        else:
            visible = []
            hidden = []

        if not allow_order:
            order = []
        if not allow_width:
            widths = {}

        return {
            "visible_columns": visible,
            "hidden_columns": hidden,
            "column_order": order,
            "column_widths": widths,
        }

    def _build_preference_contract_meta(self, *, list_profile, action_id=0):
        profile = list_profile if isinstance(list_profile, dict) else {}
        policy = profile.get("preference_policy") if isinstance(profile.get("preference_policy"), dict) else {}
        try:
            action_id = int(action_id or 0)
        except Exception:
            action_id = 0
        locked_columns = self._sanitize_list(policy.get("locked_columns"), max_size=200)
        return {
            "columns": self._sanitize_list(profile.get("columns"), max_size=200),
            "fact_columns": self._sanitize_list(profile.get("fact_columns"), max_size=200),
            "preference_policy": {
                "scope": str(policy.get("scope") or "ui_only"),
                "allow_visibility": policy.get("allow_visibility") is not False,
                "allow_order": policy.get("allow_order") is not False,
                "allow_width": policy.get("allow_width") is not False,
                "locked_columns": locked_columns,
                "must_request_columns": self._sanitize_list(policy.get("must_request_columns"), max_size=200),
            },
        }

    def _source_meta(self):
        return {
            "source_kind": self.SOURCE_KIND,
            "source_authorities": list(self.SOURCE_AUTHORITIES),
            "source_authority": self.source_authority_contract(),
        }

    def handle(self, payload=None, ctx=None):
        params = self._params(payload or self.payload)
        if not isinstance(params, dict):
            return self._err(400, "params 无效")
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
        preference_key = Preference.normalize_preference_key(params.get("preference_key"))
        list_profile = {}
        if preference_key == "list_columns":
            action_id, _ = self._read_positive_int(params.get("action_id"), "action_id")
            model_name, _ = self._text_param(params, ("model", "model_name"))
            view_type, _ = self._text_param(params, "view_type", default="list")
            list_profile = self._resolve_list_profile_contract(
                action_id=action_id,
                model_name=model_name,
                view_type=view_type,
            )
        value = self._sanitize_preference(preference_key, record.value_json if record else {})
        if preference_key == "list_columns":
            value = self._apply_list_preference_policy(value, list_profile=list_profile, action_id=action_id, model_name=model_name)
        return {
            "ok": True,
            "data": {
                "scope_key": scope_key,
                "preference": value,
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "version": self.VERSION,
                "preference_contract": self._build_preference_contract_meta(
                    list_profile=list_profile,
                    action_id=action_id,
                ),
                **self._source_meta(),
            },
        }


class UserViewPreferenceSetHandler(UserViewPreferenceGetHandler):
    INTENT_TYPE = "user.view.preference.set"
    DESCRIPTION = "保存当前用户视图偏好"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = ["base.group_user"]
    ACL_MODE = "explicit_check"

    def handle(self, payload=None, ctx=None):
        params = self._params(payload or self.payload)
        if not isinstance(params, dict):
            return self._err(400, "params 无效")
        scope_key, scope_error = self._scope_key(params)
        if scope_error:
            return scope_error
        preference_key = self.env["sc.user.view.preference"].normalize_preference_key(params.get("preference_key"))
        view_type, view_type_error = self._text_param(params, "view_type", default="list")
        if view_type_error:
            return view_type_error
        action_id, action_error = self._read_positive_int(params.get("action_id"), "action_id")
        if action_error:
            return action_error
        model_name, model_error = self._text_param(params, ("model", "model_name"))
        if model_error:
            return model_error
        value = self._sanitize_preference(preference_key, params.get("preference"))
        list_profile = {}
        if preference_key == "list_columns":
            list_profile = self._resolve_list_profile_contract(
                action_id=action_id,
                model_name=model_name,
                view_type=view_type,
            )
            value = self._apply_list_preference_policy(value, list_profile=list_profile, action_id=action_id, model_name=model_name)
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
            "meta": {
                "intent": self.INTENT_TYPE,
                "version": self.VERSION,
                "preference_contract": self._build_preference_contract_meta(
                    list_profile=list_profile,
                    action_id=action_id,
                ),
                **self._source_meta(),
            },
        }
