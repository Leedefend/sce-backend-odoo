# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/api_data_write.py
# v0.6: Minimal write intent (create/update) for project.project

import logging
from typing import Any, Dict, List

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler

_logger = logging.getLogger(__name__)


class ApiDataWriteHandler(BaseIntentHandler):
    """
    Intent: api.data.create / api.data.write
    - 限定 model=project.project
    - 字段白名单写入
    - 返回固定写入契约
    """

    INTENT_TYPE = "api.data.create"
    ALIASES = ["api.data.write"]
    DESCRIPTION = "Portal Shell v0.6 minimal write intent (create/update)"
    VERSION = "0.6.0"
    ETAG_ENABLED = False

    ALLOWED_MODELS = {
        "project.project": {"name", "description", "date_start"},
        "project.task": {"name", "description", "date_deadline", "project_id"},
    }

    def _err(self, code: int, message: str):
        return {"ok": False, "error": {"code": code, "message": message}, "code": code}

    def _collect_params(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        params = {}
        if isinstance(payload, dict):
            params.update(payload.get("params") or {})
            params.update(payload.get("payload") or {})
        if isinstance(self.params, dict):
            params.update(self.params)
        return params

    def _get_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = params.get("context")
        return ctx if isinstance(ctx, dict) else {}

    def _get_model(self, params: Dict[str, Any]) -> str:
        model = params.get("model") or params.get("res_model") or ""
        return str(model).strip()

    def _get_vals(self, params: Dict[str, Any]) -> Dict[str, Any]:
        vals = params.get("vals") or params.get("values") or {}
        return vals if isinstance(vals, dict) else {}

    def _get_id(self, params: Dict[str, Any]) -> int:
        for key in ("id", "record_id"):
            if key in params:
                try:
                    return int(params.get(key))
                except Exception:
                    return 0
        ids = params.get("ids")
        if isinstance(ids, list) and ids:
            try:
                return int(ids[0])
            except Exception:
                return 0
        return 0

    def _filter_vals(self, vals: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in vals.items() if k in self.ALLOWED_FIELDS}

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        params = self._collect_params(payload)
        intent = (payload.get("intent") or "").strip().lower()
        model = self._get_model(params)

        if not model:
            return self._err(400, "缺少参数 model")
        allowed_fields = self.ALLOWED_MODELS.get(model)
        if not allowed_fields:
            return self._err(403, f"模型不允许写入: {model}")
        if model not in self.env:
            return self._err(404, f"未知模型: {model}")

        vals = self._get_vals(params)
        if not vals:
            return self._err(400, "缺少参数 vals")

        illegal_fields = sorted(set(vals.keys()) - allowed_fields)
        if illegal_fields:
            return self._err(400, f"字段不允许写入: {', '.join(illegal_fields)}")

        safe_vals = {k: v for k, v in vals.items() if k in allowed_fields}
        if not safe_vals:
            return self._err(400, "vals 中无可写字段")

        context = self._get_context(params)
        env_model = self.env[model].with_context(context)

        trace_id = ""
        if isinstance(self.context, dict):
            trace_id = self.context.get("trace_id") or ""

        if intent == "api.data.write":
            record_id = self._get_id(params)
            if not record_id:
                return self._err(400, "缺少参数 id")

            rec = env_model.browse(record_id).exists()
            if not rec:
                return self._err(404, "记录不存在")

            try:
                env_model.check_access_rights("write")
                rec.check_access_rule("write")
                rec.write(safe_vals)
            except AccessError as ae:
                _logger.warning("api.data.write AccessError on %s: %s", model, ae)
                return self._err(403, "无写入权限")
            except Exception as e:
                _logger.exception("api.data.write failed on %s", model)
                return self._err(500, str(e))

            data = {
                "id": rec.id,
                "model": model,
                "written_fields": sorted(safe_vals.keys()),
                "values": safe_vals,
            }
            meta = {"trace_id": trace_id, "write_mode": "update", "source": "portal-shell"}
            return {"ok": True, "data": data, "meta": meta}

        if intent == "api.data.create":
            try:
                env_model.check_access_rights("create")
                rec = env_model.create(safe_vals)
            except AccessError as ae:
                _logger.warning("api.data.create AccessError on %s: %s", model, ae)
                return self._err(403, "无创建权限")
            except Exception as e:
                _logger.exception("api.data.create failed on %s", model)
                return self._err(500, str(e))

            data = {
                "id": rec.id,
                "model": model,
                "written_fields": sorted(safe_vals.keys()),
                "values": safe_vals,
            }
            meta = {"trace_id": trace_id, "write_mode": "create", "source": "portal-shell"}
            return {"ok": True, "data": data, "meta": meta}

        return self._err(400, f"未知写入意图: {intent}")
