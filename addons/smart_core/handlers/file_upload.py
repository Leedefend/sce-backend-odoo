# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/file_upload.py
# Minimal file upload intent for portal chatter attachments

import base64
import logging
from typing import Any, Dict

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler
from ..utils.extension_hooks import call_extension_hook_first

_logger = logging.getLogger(__name__)


class FileUploadHandler(BaseIntentHandler):
    """
    Intent: file.upload
    - 允许 project.project / project.task 附件上传
    - 传入 base64 数据
    """

    INTENT_TYPE = "file.upload"
    DESCRIPTION = "Portal Shell file upload intent"
    VERSION = "0.1.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["smart_core.group_smart_core_data_operator"]
    ACL_MODE = "explicit_check"

    ALLOWED_MODELS = {"res.partner"}
    MAX_BYTES = 5 * 1024 * 1024

    def _allowed_models(self):
        payload = call_extension_hook_first(self.env, "smart_core_file_upload_allowed_models", self.env)
        if isinstance(payload, (list, tuple, set)):
            values = {str(item).strip() for item in payload if str(item).strip()}
            if values:
                return values
        return set(self.ALLOWED_MODELS)

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

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        params = self._collect_params(payload)

        model = str(params.get("model") or params.get("res_model") or "").strip()
        res_id = params.get("res_id") or params.get("record_id")
        name = params.get("name") or "upload.bin"
        mimetype = params.get("mimetype") or "application/octet-stream"
        data = params.get("data") or ""

        if not model:
            return self._err(400, "缺少参数 model")
        if model not in self._allowed_models():
            return self._err(403, f"模型不允许上传: {model}")
        if not res_id:
            return self._err(400, "缺少参数 res_id")

        try:
            res_id = int(res_id)
        except Exception:
            return self._err(400, "res_id 无效")

        if not data or not isinstance(data, str):
            return self._err(400, "缺少参数 data")

        try:
            raw = base64.b64decode(data, validate=True)
        except Exception:
            return self._err(400, "data 不是合法 base64")

        if len(raw) > self.MAX_BYTES:
            return self._err(413, "文件过大")

        trace_id = ""
        if isinstance(self.context, dict):
            trace_id = self.context.get("trace_id") or ""

        try:
            self.env[model].check_access_rights("write")
            self.env[model].browse(res_id).check_access_rule("write")
            attachment = self.env["ir.attachment"].create(
                {
                    "name": name,
                    "datas": data,
                    "mimetype": mimetype,
                    "res_model": model,
                    "res_id": res_id,
                }
            )
        except AccessError as ae:
            _logger.warning("file.upload AccessError on %s: %s", model, ae)
            return self._err(403, "无上传权限")
        except Exception as e:
            _logger.exception("file.upload failed on %s", model)
            return self._err(500, str(e))

        data = {"id": attachment.id, "name": attachment.name, "model": model, "res_id": res_id}
        meta = {"trace_id": trace_id, "write_mode": "upload", "source": "portal-shell"}
        return {"ok": True, "data": data, "meta": meta}
