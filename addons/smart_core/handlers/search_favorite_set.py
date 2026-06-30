# -*- coding: utf-8 -*-
import json
import logging

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler
from ..core.search_favorite_policy import client_requested_shared_favorite, resolve_search_favorite_shared

_logger = logging.getLogger(__name__)


class SearchFavoriteSetHandler(BaseIntentHandler):
    INTENT_TYPE = "search.favorite.set"
    DESCRIPTION = "保存当前搜索为用户收藏筛选"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = ["base.group_user"]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "odoo_filter_write_proxy"
    SOURCE_AUTHORITIES = ("ir.filters", "app.search.config", "ir.model.access")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls):
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def _err(self, code, message):
        return {
            "ok": False,
            "error": {"code": code, "message": message},
            "meta": self._source_meta(),
        }

    def _source_meta(self):
        return {
            "source_kind": self.SOURCE_KIND,
            "source_authorities": list(self.SOURCE_AUTHORITIES),
            "source_authority": self.source_authority_contract(),
        }

    def _params(self, payload):
        if isinstance(payload, dict) and isinstance(payload.get("params"), dict):
            return payload.get("params") or {}
        return payload or {}

    def _text_param(self, params: dict, key: str, *, required: bool = False):
        raw = params.get(key)
        if raw is None or raw == "":
            if required:
                return "", self._err(400, f"{key} 无效")
            return "", None
        if isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
            return "", self._err(400, f"{key} 无效")
        text = str(raw).strip()
        if required and not text:
            return "", self._err(400, f"{key} 无效")
        return text, None

    def _positive_int(self, value, field_name):
        if value in (None, False, ""):
            return 0, None
        try:
            result = int(value)
        except Exception:
            return 0, self._err(400, f"{field_name} 无效")
        if result < 0:
            return 0, self._err(400, f"{field_name} 无效")
        return result, None

    def handle(self, payload=None, ctx=None):
        params = self._params(payload or self.payload)
        if not isinstance(params, dict):
            return self._err(400, "params 无效")
        model, model_error = self._text_param(params, "model", required=True)
        if model_error:
            return model_error
        name, name_error = self._text_param(params, "name", required=True)
        if name_error:
            return name_error
        if not model or model not in self.env:
            return self._err(400, "模型不存在或未指定")
        if not name:
            return self._err(400, "收藏名称不能为空")
        if len(name) > 80:
            name = name[:80]

        Model = self.env[model]
        try:
            Model.check_access_rights("read")
        except AccessError:
            raise

        domain = params.get("domain")
        if not isinstance(domain, list):
            domain = []
        context = params.get("context")
        if not isinstance(context, dict):
            context = {}
        order_key = "sort" if params.get("sort") not in (None, "") else "order"
        order, order_error = self._text_param(params, order_key)
        if order_error:
            return order_error
        is_shared = resolve_search_favorite_shared(params)
        if client_requested_shared_favorite(params):
            _logger.warning("search.favorite.set ignored client shared favorite request model=%s", model)
        is_default = bool(params.get("is_default") is True)
        action_id, action_id_error = self._positive_int(params.get("action_id"), "action_id")
        if action_id_error:
            return action_id_error

        Filter = self.env["ir.filters"].sudo()
        vals = {
            "name": name,
            "model_id": model,
            "domain": json.dumps(domain, ensure_ascii=False, default=str),
            "context": json.dumps(context, ensure_ascii=False, default=str),
            "sort": order,
            "user_id": False if is_shared else self.env.uid,
            "is_default": is_default,
        }
        if action_id:
            vals["action_id"] = action_id
        existing = Filter.search([
            ("model_id", "=", model),
            ("name", "=", name),
            ("user_id", "=", False if is_shared else self.env.uid),
        ], limit=1)
        if is_default:
            default_domain = [
                ("model_id", "=", model),
                ("user_id", "=", False if is_shared else self.env.uid),
                ("is_default", "=", True),
            ]
            if action_id:
                default_domain.append(("action_id", "=", action_id))
            Filter.search(default_domain).write({"is_default": False})
        if existing:
            existing.write(vals)
            record = existing
        else:
            record = Filter.create(vals)

        cfg = None
        if "app.search.config" in self.env:
            cfg = self.env["app.search.config"].sudo()._generate_from_search(model)

        return {
            "ok": True,
            "data": {
                "id": record.id,
                "name": record.name,
                "model": model,
                "is_shared": is_shared,
                "is_default": is_default,
                "action_id": action_id or False,
                "search_version": getattr(cfg, "version", None),
            },
            "meta": {"intent": self.INTENT_TYPE, "version": self.VERSION, **self._source_meta()},
        }
