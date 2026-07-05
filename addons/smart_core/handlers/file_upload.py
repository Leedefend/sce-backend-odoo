# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/file_upload.py
# Minimal file upload intent for portal chatter attachments

import base64
import logging
from typing import Any, Dict

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler
try:
    from ..core.project_context import record_scope_denied_response
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import project_scope_denied_response as record_scope_denied_response
try:
    from ..core.project_context import record_in_business_scope
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import record_in_project_scope
    try:
        from ..core.project_context import selected_record_context_id_from_context
    except ImportError:  # pragma: no cover - compatibility for older lightweight boundary tests
        from ..core.project_context import selected_project_id_from_context as selected_record_context_id_from_context

    def record_in_business_scope(env_model, record_id, params=None, context=None):
        return record_in_project_scope(env_model, record_id, selected_record_context_id_from_context(params, context))
from ..core.request_params import parse_positive_int
from ..utils.extension_hooks import call_extension_hook_first

_logger = logging.getLogger(__name__)


class FileUploadHandler(BaseIntentHandler):
    """
    Intent: file.upload
    - 按 allowlist 限定可上传附件 model
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
    SOURCE_AUTHORITY = "ir.attachment"
    SOURCE_KIND = "odoo_attachment_upload_proxy"
    SOURCE_AUTHORITIES = ("ir.attachment", "odoo.orm", "ir.rule", "ir.model.access", "record_context_model")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authority": cls.SOURCE_AUTHORITY,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

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
        res_id = params.get("res_id") if "res_id" in params else params.get("record_id")
        name = params.get("name") or "upload.bin"
        mimetype = params.get("mimetype") or "application/octet-stream"
        data = params.get("data") or ""

        if not model:
            return self._err(400, "缺少参数 model")
        if model not in self._allowed_models():
            return self._err(403, f"模型不允许上传: {model}")
        if model not in self.env:
            return self._err(404, f"未知模型: {model}")
        if _is_empty_param(res_id):
            return self._err(400, "缺少参数 res_id")

        res_id, res_id_error = parse_positive_int(res_id)
        if res_id_error:
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
            record = self.env[model].browse(res_id).exists()
            if not record:
                return self._err(404, "记录不存在")
            in_scope, scope_meta = record_in_business_scope(
                self.env[model],
                int(record.id),
                params,
                self.context if isinstance(self.context, dict) else {},
            )
            if not in_scope:
                return record_scope_denied_response(scope_meta)
            record.check_access_rule("write")
            attachment = self.env["ir.attachment"].create(
                {
                    "name": name,
                    "datas": data,
                    "mimetype": mimetype,
                    "res_model": model,
                    "res_id": res_id,
                }
            )
            attachment_field = getattr(record, "_fields", {}).get("attachment_ids")
            if (
                attachment_field
                and attachment_field.type == "many2many"
                and attachment_field.comodel_name == "ir.attachment"
            ):
                record.write({"attachment_ids": [(4, attachment.id)]})
        except AccessError as ae:
            _logger.warning("file.upload AccessError on %s: %s", model, ae)
            return self._err(403, "无上传权限")
        except Exception as e:
            _logger.exception("file.upload failed on %s", model)
            return self._err(500, str(e))

        data = {"id": attachment.id, "name": attachment.name, "model": model, "res_id": res_id}
        meta = {
            "trace_id": trace_id,
            "write_mode": "upload",
            "source": "portal-shell",
            "source_authority": self.source_authority_contract(),
            "legacy_source_authority": self.SOURCE_AUTHORITY,
            "project_scope": scope_meta,
            "record_scope": scope_meta,
        }
        return {"ok": True, "data": data, "meta": meta}


def _is_empty_param(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())
