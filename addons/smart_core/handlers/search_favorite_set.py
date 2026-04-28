# -*- coding: utf-8 -*-
import json

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler


class SearchFavoriteSetHandler(BaseIntentHandler):
    INTENT_TYPE = "search.favorite.set"
    DESCRIPTION = "保存当前搜索为用户收藏筛选"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = ["base.group_user"]

    def _err(self, code, message):
        return {"ok": False, "error": {"code": code, "message": message}}

    def _params(self, payload):
        if isinstance(payload, dict) and isinstance(payload.get("params"), dict):
            return payload.get("params") or {}
        return payload or {}

    def handle(self, payload=None, ctx=None):
        params = self._params(payload or self.payload)
        model = str(params.get("model") or "").strip()
        name = str(params.get("name") or "").strip()
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
        order = str(params.get("sort") or params.get("order") or "").strip()
        is_shared = bool(params.get("is_shared") is True)

        Filter = self.env["ir.filters"].sudo()
        vals = {
            "name": name,
            "model_id": model,
            "domain": json.dumps(domain, ensure_ascii=False),
            "context": json.dumps(context, ensure_ascii=False),
            "sort": order,
            "user_id": False if is_shared else self.env.uid,
        }
        existing = Filter.search([
            ("model_id", "=", model),
            ("name", "=", name),
            ("user_id", "=", False if is_shared else self.env.uid),
        ], limit=1)
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
                "search_version": getattr(cfg, "version", None),
            },
            "meta": {"intent": self.INTENT_TYPE, "version": self.VERSION},
        }
