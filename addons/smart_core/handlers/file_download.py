# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/file_download.py
# Minimal file download intent for portal attachments

import base64
import logging
import mimetypes
import os
from pathlib import Path
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

LEGACY_FILE_URL_PREFIX = "legacy-file://"
LEGACY_FILE_ID_URL_PREFIX = "legacy-file-id://"
DEFAULT_LEGACY_FILE_ROOTS = (
    "/mnt/legacy-files",
    "/mnt/legacy_files",
    "/opt/sce-legacy-files",
    "/opt/sce/legacy-files",
)


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
        base_values = set(self.ALLOWED_MODELS)
        payload = call_extension_hook_first(self.env, "smart_core_file_download_allowed_models", self.env)
        if isinstance(payload, (list, tuple, set)):
            values = {str(item).strip() for item in payload if str(item).strip()}
            if values:
                return base_values | values
        return base_values

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
        attachment_url = str(params.get("url") or "").strip()
        model = str(params.get("model") or params.get("res_model") or "").strip()
        res_id = params.get("res_id") if "res_id" in params else params.get("record_id")
        name = str(params.get("name") or "").strip()

        attachment = None

        if not _is_empty_param(attachment_id):
            attachment_id, attachment_id_error = parse_positive_int(attachment_id)
            if attachment_id_error:
                return self._err(400, "id 无效")
        else:
            if attachment_url.startswith((LEGACY_FILE_URL_PREFIX, LEGACY_FILE_ID_URL_PREFIX)):
                domain = [("type", "=", "url"), ("url", "=", attachment_url)]
                if model:
                    domain.append(("res_model", "=", model))
                if not _is_empty_param(res_id):
                    res_id, res_id_error = parse_positive_int(res_id)
                    if res_id_error:
                        return self._err(400, "res_id 无效")
                    domain.append(("res_id", "=", res_id))
                attachment = self.env["ir.attachment"].sudo().search(domain, order="id desc", limit=1)
                if not attachment and (model or not _is_empty_param(res_id)):
                    attachment = self.env["ir.attachment"].sudo().search(
                        [("type", "=", "url"), ("url", "=", attachment_url)],
                        order="id desc",
                        limit=1,
                    )
                if not attachment:
                    return self._err(404, "附件不存在")
                attachment_id = attachment.id
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

        legacy_file = self._read_legacy_file(attachment)
        if legacy_file.get("error"):
            return self._err(legacy_file["code"], legacy_file["message"])

        data = {
            "id": attachment.id,
            "name": legacy_file.get("name") or attachment.name,
            "mimetype": legacy_file.get("mimetype") or attachment.mimetype or "application/octet-stream",
            "datas": legacy_file.get("datas") or attachment.datas or "",
            "type": "binary" if legacy_file.get("datas") else attachment.type or "binary",
            "url": attachment.url or "",
            "res_model": attachment.res_model,
            "res_id": attachment.res_id,
            "legacy_url": attachment.url or "",
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

    def _read_legacy_file(self, attachment):
        url = str(attachment.url or "").strip()
        if attachment.type != "url" or not url.startswith((LEGACY_FILE_URL_PREFIX, LEGACY_FILE_ID_URL_PREFIX)):
            return {}
        relative_path = self._legacy_relative_path(url)
        if not relative_path:
            return {"error": True, "code": 404, "message": "历史附件索引不存在"}
        path = _resolve_legacy_file_path(relative_path)
        if not path:
            _logger.warning("legacy attachment file missing: attachment=%s url=%s path=%s", attachment.id, url, relative_path)
            return {"error": True, "code": 404, "message": "历史附件文件不存在"}
        try:
            raw = path.read_bytes()
        except OSError:
            _logger.exception("legacy attachment file unreadable: attachment=%s path=%s", attachment.id, path)
            return {"error": True, "code": 500, "message": "历史附件读取失败"}
        mimetype = attachment.mimetype or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        return {
            "datas": base64.b64encode(raw).decode("ascii"),
            "name": attachment.name or path.name,
            "mimetype": mimetype,
        }

    def _legacy_relative_path(self, url: str) -> str:
        if url.startswith(LEGACY_FILE_URL_PREFIX):
            return url[len(LEGACY_FILE_URL_PREFIX):]
        legacy_file_id = url[len(LEGACY_FILE_ID_URL_PREFIX):].strip()
        if not legacy_file_id or "sc.legacy.file.index" not in self.env:
            return ""
        file_index = self.env["sc.legacy.file.index"].sudo().search(
            ["|", ("legacy_file_id", "=", legacy_file_id), ("legacy_file_key", "=", legacy_file_id)],
            limit=1,
        )
        if not file_index:
            return ""
        return file_index.preview_path or file_index.file_path or ""


def _is_empty_param(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _legacy_file_roots():
    raw = os.environ.get("SC_LEGACY_FILE_ROOTS") or os.environ.get("LEGACY_FILE_ROOTS") or ""
    roots = []
    for item in raw.replace(",", os.pathsep).split(os.pathsep):
        item = item.strip()
        if item:
            roots.append(Path(item))
    roots.extend(Path(item) for item in DEFAULT_LEGACY_FILE_ROOTS)
    deduped = []
    seen = set()
    for root in roots:
        marker = str(root)
        if marker not in seen:
            seen.add(marker)
            deduped.append(root)
    return deduped


def _resolve_legacy_file_path(relative_path: str):
    clean = relative_path.replace("\\", "/").lstrip("/")
    if not clean or ".." in Path(clean).parts:
        return None
    candidates = [clean]
    if clean.startswith("UploadFile/UserFile/"):
        candidates.append(clean[len("UploadFile/"):])
    for root in _legacy_file_roots():
        root_resolved = root.resolve()
        for candidate in candidates:
            full_path = (root_resolved / candidate).resolve()
            try:
                full_path.relative_to(root_resolved)
            except ValueError:
                continue
            if full_path.is_file():
                return full_path
    return None
