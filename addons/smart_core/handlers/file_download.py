# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/file_download.py
# Minimal file download intent for portal attachments

import logging
from typing import Any, Dict

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler
from ..core.project_context import (
    project_scope_denied_response,
)
try:
    from ..core.project_context import record_in_business_scope
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import record_in_project_scope, selected_project_id_from_context

    def record_in_business_scope(env_model, record_id, params=None, context=None):
        return record_in_project_scope(env_model, record_id, selected_project_id_from_context(params, context))
from ..core.request_params import parse_positive_int
from ..utils.extension_hooks import call_extension_hook_first

_logger = logging.getLogger(__name__)


class FileDownloadHandler(BaseIntentHandler):
    """
    Intent: file.download
    - 按 allowlist 限定可下载附件 model
    """

    INTENT_TYPE = "file.download"
    DESCRIPTION = "Portal Shell file download intent"
    VERSION = "0.1.0"
    ETAG_ENABLED = False

    ALLOWED_MODELS = {"res.partner"}
    SOURCE_AUTHORITY = "ir.attachment"
    SOURCE_KIND = "odoo_attachment_download_projection"
    SOURCE_AUTHORITIES = ("ir.attachment", "odoo.orm", "ir.rule", "ir.model.access", "record_context_model")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authority": cls.SOURCE_AUTHORITY,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def _allowed_models(self):
        payload = call_extension_hook_first(self.env, "smart_core_file_download_allowed_models", self.env)
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

        attachment_id = params.get("id") if "id" in params else params.get("attachment_id")
        model = str(params.get("model") or params.get("res_model") or "").strip()
        res_id = params.get("res_id") if "res_id" in params else params.get("record_id")
        name = str(params.get("name") or "").strip()

        attachment = None

        if not _is_empty_param(attachment_id):
            attachment_id, attachment_id_error = parse_positive_int(attachment_id)
            if attachment_id_error:
                return self._err(400, "id 无效")
        else:
            # Fallback locator for contract/export scenarios where attachment id
            # is created in a prior step and only model/res_id/name are known.
            if not model or _is_empty_param(res_id):
                return self._err(400, "缺少参数 id")
            if model not in self._allowed_models():
                return self._err(403, "附件不可访问")
            if model not in self.env:
                return self._err(404, "附件业务模型不存在")
            res_id, res_id_error = parse_positive_int(res_id)
            if res_id_error:
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
            attachment = attachment or self.env["ir.attachment"].sudo().browse(attachment_id).exists()
            if not attachment:
                return self._err(404, "附件不存在")
            auth_model = attachment.res_model
            auth_res_id = attachment.res_id
            if "payment.request" in self.env:
                parent_request = self.env["payment.request"].sudo().search(
                    [("attachment_ids", "in", attachment.id)],
                    limit=1,
                )
                if parent_request:
                    auth_model = "payment.request"
                    auth_res_id = parent_request.id
            if auth_model not in self._allowed_models():
                return self._err(403, "附件不可访问")
            if auth_model not in self.env:
                return self._err(404, "附件业务模型不存在")
            self.env[auth_model].check_access_rights("read")
            record = self.env[auth_model].browse(auth_res_id).exists()
            if not record:
                return self._err(404, "附件业务记录不存在")
            in_scope, scope_meta = record_in_business_scope(
                self.env[auth_model],
                int(record.id),
                params,
                self.context if isinstance(self.context, dict) else {},
            )
            if not in_scope:
                return project_scope_denied_response(scope_meta)
            record.check_access_rule("read")
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
            "type": attachment.type or "binary",
            "url": attachment.url or "",
            "res_model": attachment.res_model,
            "res_id": attachment.res_id,
        }
        meta = {
            "trace_id": trace_id,
            "source": "portal-shell",
            "source_authority": self.source_authority_contract(),
            "legacy_source_authority": self.SOURCE_AUTHORITY,
            "project_scope": scope_meta,
            "record_scope": scope_meta,
        }
        return {"ok": True, "data": data, "meta": meta}


def _is_empty_param(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())
