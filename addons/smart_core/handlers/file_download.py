# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/file_download.py
# Minimal file download intent for portal attachments

import logging
from typing import Any, Dict

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler

_logger = logging.getLogger(__name__)


class FileDownloadHandler(BaseIntentHandler):
    """
    Intent: file.download
    - 允许 project.project / project.task 附件下载
    """

    INTENT_TYPE = "file.download"
    DESCRIPTION = "Portal Shell file download intent"
    VERSION = "0.1.0"
    ETAG_ENABLED = False

    ALLOWED_MODELS = {"project.project", "project.task"}

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

        attachment_id = params.get("id") or params.get("attachment_id")
        model = str(params.get("model") or params.get("res_model") or "").strip()
        res_id = params.get("res_id") or params.get("record_id")
        name = str(params.get("name") or "").strip()

        attachment = None

        if attachment_id:
            try:
                attachment_id = int(attachment_id)
            except Exception:
                return self._err(400, "id 无效")
        else:
            # Fallback locator for contract/export scenarios where attachment id
            # is created in a prior step and only model/res_id/name are known.
            if not model or not res_id:
                return self._err(400, "缺少参数 id")
            try:
                res_id = int(res_id)
            except Exception:
                return self._err(400, "res_id 无效")
            domain = [("res_model", "=", model), ("res_id", "=", res_id)]
            if name:
                domain.append(("name", "=", name))
            attachment = self.env["ir.attachment"].sudo().search(domain, order="id desc", limit=1)
            if not attachment:
                return self._err(404, "附件不存在")
            attachment_id = attachment.id

        trace_id = ""
        if isinstance(self.context, dict):
            trace_id = self.context.get("trace_id") or ""

        try:
            attachment = attachment or self.env["ir.attachment"].browse(attachment_id).exists()
            if not attachment:
                return self._err(404, "附件不存在")
            attachment_model = attachment.res_model
            if attachment_model not in self.ALLOWED_MODELS:
                return self._err(403, "附件不可访问")
            self.env[attachment_model].check_access_rights("read")
            self.env[attachment_model].browse(attachment.res_id).check_access_rule("read")
        except AccessError as ae:
            _logger.warning("file.download AccessError on %s: %s", attachment_id, ae)
            return self._err(403, "无下载权限")
        except Exception as e:
            _logger.exception("file.download failed on %s", attachment_id)
            return self._err(500, str(e))

        data = {
            "id": attachment.id,
            "name": attachment.name,
            "mimetype": attachment.mimetype or "application/octet-stream",
            "datas": attachment.datas or "",
            "res_model": attachment.res_model,
            "res_id": attachment.res_id,
        }
        meta = {"trace_id": trace_id, "source": "portal-shell"}
        return {"ok": True, "data": data, "meta": meta}
