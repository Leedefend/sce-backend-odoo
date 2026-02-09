# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/api_data_unlink.py
# Minimal unlink intent for portal relational MVP

import logging
from typing import Any, Dict, List

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler
from ..utils.reason_codes import (
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_PERMISSION_DENIED,
    REASON_SYSTEM_ERROR,
    REASON_UNSUPPORTED_SOURCE,
    failure_meta_for_reason,
)

_logger = logging.getLogger(__name__)


class ApiDataUnlinkHandler(BaseIntentHandler):
    """
    Intent: api.data.unlink
    - 限定 model=project.task
    - 返回删除 ids
    """

    INTENT_TYPE = "api.data.unlink"
    DESCRIPTION = "Portal Shell minimal unlink intent"
    VERSION = "0.1.0"
    ETAG_ENABLED = False

    ALLOWED_MODELS = {"project.task"}

    def _err(self, code: int, message: str, reason_code: str):
        return {
            "ok": False,
            "error": {
                "code": reason_code,
                "message": message,
                "reason_code": reason_code,
                **failure_meta_for_reason(reason_code),
            },
            "code": code,
        }

    def _collect_params(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        params = {}
        if isinstance(payload, dict):
            params.update(payload.get("params") or {})
            params.update(payload.get("payload") or {})
        if isinstance(self.params, dict):
            params.update(self.params)
        return params

    def _get_model(self, params: Dict[str, Any]) -> str:
        model = params.get("model") or params.get("res_model") or ""
        return str(model).strip()

    def _get_ids(self, params: Dict[str, Any]) -> List[int]:
        ids = params.get("ids") or params.get("record_ids") or []
        if isinstance(ids, list):
            return [int(v) for v in ids if v is not None]
        try:
            return [int(ids)]
        except Exception:
            return []

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        params = self._collect_params(payload)
        model = self._get_model(params)
        if not model:
            return self._err(400, "缺少参数 model", REASON_MISSING_PARAMS)
        if model not in self.ALLOWED_MODELS:
            return self._err(403, f"模型不允许删除: {model}", REASON_UNSUPPORTED_SOURCE)
        if model not in self.env:
            return self._err(404, f"未知模型: {model}", REASON_NOT_FOUND)

        ids = self._get_ids(params)
        dry_run = bool(params.get("dry_run"))
        if not ids:
            return self._err(400, "缺少参数 ids", REASON_MISSING_PARAMS)

        env_model = self.env[model]
        trace_id = ""
        if isinstance(self.context, dict):
            trace_id = self.context.get("trace_id") or ""

        recs = env_model.browse(ids).exists()
        if not recs:
            return self._err(404, "记录不存在", REASON_NOT_FOUND)

        try:
            env_model.check_access_rights("unlink")
            recs.check_access_rule("unlink")
            if not dry_run:
                recs.unlink()
        except AccessError as ae:
            _logger.warning("api.data.unlink AccessError on %s: %s", model, ae)
            return self._err(403, "无删除权限", REASON_PERMISSION_DENIED)
        except Exception as e:
            _logger.exception("api.data.unlink failed on %s", model)
            return self._err(500, str(e), REASON_SYSTEM_ERROR)

        data = {"ids": ids, "model": model, "dry_run": dry_run}
        meta = {"trace_id": trace_id, "write_mode": "unlink", "source": "portal-shell"}
        return {"ok": True, "data": data, "meta": meta}
