# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/file_download.py
# Minimal file download intent for portal attachments

import base64
import json
import logging
import mimetypes
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import quote, urljoin

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

LEGACY_FILE_URL_PREFIX = "legacy-file://"
LEGACY_FILE_ID_URL_PREFIX = "legacy-file-id://"
LEGACY_ATTACHMENT_LABEL_RE = re.compile(r"^附件\([1-9]\d*\)$")
DEFAULT_ONLINE_LEGACY_BASE_URL = "https://www.builderp.cn/SCBSLY_V2"
DEFAULT_LEGACY_FILE_HTTP_BASE_URLS = (
    "https://www.builderp.cn/SCBS",
    "https://www.builderp.cn/SCBSLY_V2",
)
DEFAULT_LEGACY_FILE_ROOTS = (
    "/mnt/artifacts/legacy-online-mirror",
    "/mnt/legacy-online-mirror",
    "/mnt/legacy-files",
    "/mnt/legacy_files",
    "/opt/sce-legacy-files",
    "/opt/sce/legacy-files",
)
LEGACY_ONLINE_ATTACHMENT_FALLBACK_ENV = "SC_LEGACY_ONLINE_ATTACHMENT_FALLBACK"


@dataclass(frozen=True)
class _LegacyAttachmentRefs:
    primary: list[str]
    secondary: list[str]


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
                if not attachment and model and not _is_empty_param(res_id):
                    if model not in self._allowed_models():
                        return self._err(403, "附件不可访问")
                    if model not in self.env:
                        return self._err(404, "附件业务模型不存在")
                    attachment = self.env["ir.attachment"].sudo().create(
                        {
                            "name": name or Path(attachment_url.split("?", 1)[0]).name or "历史附件",
                            "res_model": model,
                            "res_id": res_id,
                            "type": "url",
                            "url": attachment_url,
                            "mimetype": mimetypes.guess_type(name or attachment_url)[0] or "application/octet-stream",
                        }
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
                attachment = None
                if not name and self._should_prefer_legacy_attachment_resolution(model):
                    attachment = self._legacy_attachment_for_record(model, res_id)
                domain = [("res_model", "=", model), ("res_id", "=", res_id)]
                if name:
                    domain.append(("name", "=", name))
                if not attachment:
                    attachment = self.env["ir.attachment"].sudo().search(domain, order="id desc", limit=1)
                if not attachment and not name:
                    attachment = self._legacy_attachment_for_record(model, res_id)
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
            auth_override = call_extension_hook_first(
                self.env,
                "smart_core_file_download_auth_subject",
                self.env,
                attachment,
                {"model": auth_model, "res_id": auth_res_id},
            )
            if isinstance(auth_override, dict):
                override_model = str(auth_override.get("model") or "").strip()
                override_res_id = auth_override.get("res_id")
                if override_model and override_res_id:
                    auth_model = override_model
                    auth_res_id = override_res_id
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
                return record_scope_denied_response(scope_meta)
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
        if attachment.type != "url":
            return {}
        if url and _is_online_legacy_file_url(url):
            return _read_online_legacy_file_url(url, attachment.name, attachment.mimetype)
        if not url.startswith((LEGACY_FILE_URL_PREFIX, LEGACY_FILE_ID_URL_PREFIX)):
            return {}
        relative_path = self._legacy_relative_path(url)
        if not relative_path:
            if url.startswith(LEGACY_FILE_ID_URL_PREFIX):
                legacy_file_id = url[len(LEGACY_FILE_ID_URL_PREFIX):].strip()
                file_info = _fetch_online_legacy_file_by_bill_id(
                    legacy_file_id,
                    _online_legacy_base_url_for_attachment(attachment),
                )
                online_url = str((file_info or {}).get("ATTR_PATH") or "").strip()
                if online_url:
                    online_name = str((file_info or {}).get("ATTR_NAME") or "").strip()
                    return _read_online_legacy_file_url(online_url, online_name or attachment.name, "")
            return {"error": True, "code": 404, "message": "旧系统未返回该历史附件文件"}
        path = _resolve_legacy_file_path(relative_path)
        if not path:
            remote_file = _read_remote_legacy_file_path(
                relative_path,
                attachment.name,
                attachment.mimetype,
                preferred_base_url=_online_legacy_base_url_for_attachment(attachment),
            )
            if not remote_file.get("error"):
                return remote_file
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
        return _legacy_file_index_relative_path(file_index)

    def _legacy_attachment_for_record(self, model: str, res_id: int):
        if "sc.legacy.file.index" not in self.env:
            return None
        record = self.env[model].sudo().browse(res_id).exists()
        if not record:
            return None
        path_attachment = self._legacy_path_attachment_for_record(record, model, res_id)
        if path_attachment:
            return path_attachment
        legacy_refs = self._legacy_attachment_refs(record)
        if not legacy_refs.primary and not legacy_refs.secondary:
            return None
        file_index = self._legacy_file_index_for_refs(legacy_refs)
        if not file_index:
            return self._online_legacy_attachment_for_refs(model, res_id, legacy_refs.primary)
        path = _legacy_file_index_relative_path(file_index)
        if not path:
            return self._online_legacy_attachment_for_refs(model, res_id, legacy_refs.primary)
        url = LEGACY_FILE_URL_PREFIX + path.lstrip("/")
        attachment = self.env["ir.attachment"].sudo().search(
            [
                ("res_model", "=", model),
                ("res_id", "=", res_id),
                ("type", "=", "url"),
                ("url", "=", url),
            ],
            order="id desc",
            limit=1,
        )
        if attachment:
            return attachment
        return self.env["ir.attachment"].sudo().create(
            {
                "name": file_index.file_name or file_index.legacy_file_id or "历史附件",
                "res_model": model,
                "res_id": res_id,
                "type": "url",
                "url": url,
                "mimetype": mimetypes.guess_type(path)[0] or "application/octet-stream",
            }
        )

    def _legacy_path_attachment_for_record(self, record, model: str, res_id: int):
        fields = getattr(record, "_fields", {}) or {}
        if "legacy_attachment_path" not in fields:
            return None
        path = str(getattr(record, "legacy_attachment_path", "") or "").strip()
        if not path:
            return None
        name = ""
        if "legacy_attachment_name" in fields:
            name = str(getattr(record, "legacy_attachment_name", "") or "").strip()
        url = LEGACY_FILE_URL_PREFIX + path.lstrip("/")
        attachment = self.env["ir.attachment"].sudo().search(
            [
                ("res_model", "=", model),
                ("res_id", "=", res_id),
                ("type", "=", "url"),
                ("url", "=", url),
            ],
            order="id desc",
            limit=1,
        )
        if attachment:
            return attachment
        return self.env["ir.attachment"].sudo().create(
            {
                "name": name or Path(path).name or "历史附件",
                "res_model": model,
                "res_id": res_id,
                "type": "url",
                "url": url,
                "mimetype": mimetypes.guess_type(name or path)[0] or "application/octet-stream",
            }
        )

    def _legacy_file_index_for_refs(self, legacy_refs):
        FileIndex = self.env["sc.legacy.file.index"].sudo()
        if legacy_refs.primary:
            file_index = FileIndex.search(
                [
                    ("active", "=", True),
                    "|",
                    "|",
                    ("bill_id", "in", legacy_refs.primary),
                    ("legacy_file_id", "in", legacy_refs.primary),
                    ("legacy_file_key", "in", legacy_refs.primary),
                ],
                order="upload_time desc, id desc",
                limit=1,
            )
            if file_index:
                return file_index
        if legacy_refs.secondary:
            return FileIndex.search(
                [
                    ("active", "=", True),
                    "|",
                    ("business_id", "in", legacy_refs.secondary),
                    ("legacy_pid", "in", legacy_refs.secondary),
                ],
                order="upload_time desc, id desc",
                limit=1,
            )
        return None

    def _online_legacy_attachment_for_refs(self, model: str, res_id: int, legacy_refs: list[str]):
        if not _online_legacy_attachment_fallback_enabled():
            return None
        record = self.env[model].sudo().browse(res_id).exists() if model in self.env else None
        base_url = _online_legacy_base_url_for_record(record)
        for ref in legacy_refs:
            file_info = _fetch_online_legacy_file_by_bill_id(ref, base_url)
            if not file_info:
                continue
            url = str(file_info.get("ATTR_PATH") or "").strip()
            if not url:
                continue
            name = str(file_info.get("ATTR_NAME") or file_info.get("ID") or "历史附件").strip()
            attachment = self.env["ir.attachment"].sudo().search(
                [
                    ("res_model", "=", model),
                    ("res_id", "=", res_id),
                    ("type", "=", "url"),
                    ("url", "=", url),
                ],
                order="id desc",
                limit=1,
            )
            if attachment:
                return attachment
            return self.env["ir.attachment"].sudo().create(
                {
                    "name": name,
                    "res_model": model,
                    "res_id": res_id,
                    "type": "url",
                    "url": url,
                    "mimetype": mimetypes.guess_type(name or url)[0] or "application/octet-stream",
                }
            )
        return None

    def _should_prefer_legacy_attachment_resolution(self, model: str) -> bool:
        if model.startswith("sc.legacy."):
            return True
        if model not in self.env:
            return False
        env_model = self.env[model]
        fields = getattr(env_model, "_fields", {}) or {}
        return bool({"attachment_ref", "legacy_attachment_ref", "raw_payload", "legacy_record_id"} & set(fields))

    def _legacy_attachment_refs(self, record):
        primary_refs: list[str] = []
        secondary_refs: list[str] = []
        fields = getattr(record, "_fields", {}) or {}
        for field in (
            "attachment_ref",
            "attachment_links",
            "legacy_attachment_ref",
            "legacy_line_attachment_ref",
            "line_attachment_ref",
        ):
            if field not in fields:
                continue
            value = getattr(record, field, "")
            if isinstance(value, str):
                primary_refs.extend(_split_legacy_refs(value))
        primary_refs.extend(_legacy_inline_attachment_refs(getattr(record, "raw_payload", "")))
        for field in (
            "legacy_pid",
            "legacy_header_id",
            "legacy_contract_id",
            "legacy_record_id",
            "legacy_source_id",
            "legacy_file_id",
            "contract_no",
            "document_no",
        ):
            if field not in fields:
                continue
            value = getattr(record, field, "")
            if isinstance(value, str):
                secondary_refs.extend(_split_legacy_refs(value))
        primary = list(dict.fromkeys(primary_refs))
        secondary = [ref for ref in dict.fromkeys(secondary_refs) if ref not in set(primary)]
        return _LegacyAttachmentRefs(primary=primary, secondary=secondary)


def _is_empty_param(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _split_legacy_refs(value: str) -> list[str]:
    refs = []
    for part in value.replace("\n", " ").replace("\r", " ").split():
        clean = part.strip().strip(",;|")
        if clean.startswith(LEGACY_FILE_ID_URL_PREFIX):
            clean = clean[len(LEGACY_FILE_ID_URL_PREFIX):].strip()
        if clean and "://" not in clean:
            refs.append(clean)
    return refs


def _legacy_inline_attachment_refs(raw_payload: Any) -> list[str]:
    if not raw_payload:
        return []
    if isinstance(raw_payload, str):
        try:
            payload = json.loads(raw_payload)
        except (TypeError, ValueError, json.JSONDecodeError):
            return []
    elif isinstance(raw_payload, dict):
        payload = raw_payload
    else:
        return []
    refs: list[str] = []
    for key, label_value in payload.items():
        key_text = str(key or "").strip()
        if not key_text.endswith("_FJ"):
            continue
        label_text = str(label_value or "").strip()
        if not LEGACY_ATTACHMENT_LABEL_RE.match(label_text):
            continue
        source_key = key_text[:-3]
        ref = str(payload.get(source_key) or "").strip()
        if ref and "://" not in ref:
            refs.append(ref)
    return list(dict.fromkeys(refs))


def _online_legacy_base_url_for_attachment(attachment) -> str:
    if not attachment or not getattr(attachment, "res_model", "") or not getattr(attachment, "res_id", 0):
        return os.environ.get("SC_ONLINE_LEGACY_BASE_URL", DEFAULT_ONLINE_LEGACY_BASE_URL).rstrip("/")
    try:
        record = attachment.env[attachment.res_model].sudo().browse(attachment.res_id).exists()
    except Exception:
        record = None
    return _online_legacy_base_url_for_record(record)


def _online_legacy_base_url_for_record(record) -> str:
    source_table = ""
    if record:
        try:
            source_table = str(getattr(record, "legacy_source_table", "") or "")
        except Exception:
            source_table = ""
    if source_table.startswith("online_old_scbs:"):
        return os.environ.get("SC_ONLINE_LEGACY_SCBS_BASE_URL", "https://www.builderp.cn/SCBS").rstrip("/")
    if source_table.startswith("online_old_scbsly"):
        return os.environ.get("SC_ONLINE_LEGACY_SCBSLY_BASE_URL", "https://www.builderp.cn/SCBSLY_V2").rstrip("/")
    return os.environ.get("SC_ONLINE_LEGACY_BASE_URL", DEFAULT_ONLINE_LEGACY_BASE_URL).rstrip("/")


def _prefer_online_legacy_attachment_lookup(record) -> bool:
    if not record:
        return False
    try:
        source_table = str(getattr(record, "legacy_source_table", "") or "")
        source_system = str(getattr(record, "source_system", "") or "")
    except Exception:
        return False
    return source_table.startswith(("online_old_scbs:", "online_old_scbsly")) or source_system.startswith(
        ("online_old_scbs", "online_old_scbsly")
    )


def _online_legacy_attachment_fallback_enabled() -> bool:
    value = os.environ.get(LEGACY_ONLINE_ATTACHMENT_FALLBACK_ENV, "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _fetch_online_legacy_file_by_bill_id(bill_id: str, base_url: str | None = None) -> dict[str, Any] | None:
    clean = str(bill_id or "").strip()
    if not clean:
        return None
    base_url = (base_url or os.environ.get("SC_ONLINE_LEGACY_BASE_URL", DEFAULT_ONLINE_LEGACY_BASE_URL)).rstrip("/")
    url = f"{base_url}/api/System/FileApi/GetFileByBillId?BillId={clean}"
    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, ValueError, json.JSONDecodeError):
        _logger.exception("online legacy file lookup failed: bill_id=%s", clean)
        return None
    rows = payload.get("Data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("DEL") or "0") not in ("0", "False", "false", ""):
            continue
        if str(row.get("ATTR_PATH") or "").strip():
            return row
    return None


def _is_online_legacy_file_url(url: str) -> bool:
    clean = str(url or "").strip()
    if not clean:
        return False
    base_url = os.environ.get("SC_ONLINE_LEGACY_BASE_URL", DEFAULT_ONLINE_LEGACY_BASE_URL).rstrip("/")
    return clean.startswith(f"{base_url}/Api/System/FileApi/ShowFileById/")


def _legacy_file_index_relative_path(file_index) -> str:
    values = [
        str(getattr(file_index, "preview_path", "") or "").strip(),
        str(getattr(file_index, "file_path", "") or "").strip(),
    ]
    values = [value for value in values if value]
    for value in values:
        if _resolve_legacy_file_path(value):
            return value
    return values[0] if values else ""


def _read_online_legacy_file_url(url: str, fallback_name: str = "", fallback_mimetype: str = "") -> dict[str, Any]:
    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            content_type = response.headers.get_content_type() if response.headers else ""
    except (OSError, URLError):
        _logger.exception("online legacy file read failed: url=%s", url)
        return {"error": True, "code": 502, "message": "历史附件在线读取失败"}
    name = fallback_name or Path(url.split("?", 1)[0]).name or "历史附件"
    mimetype = fallback_mimetype or content_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
    return {
        "datas": base64.b64encode(raw).decode("ascii"),
        "name": name,
        "mimetype": mimetype,
    }


def _read_remote_legacy_file_path(
    relative_path: str,
    fallback_name: str = "",
    fallback_mimetype: str = "",
    preferred_base_url: str = "",
) -> dict[str, Any]:
    base_urls = _legacy_file_http_base_urls(preferred_base_url)
    if not base_urls:
        return {"error": True}
    clean = str(relative_path or "").strip().replace("\\", "/").lstrip("/")
    path_candidates = [clean]
    if clean.startswith("UploadFile/"):
        path_candidates.append(clean[len("UploadFile/"):])
    elif clean and not clean.startswith(("http://", "https://")):
        path_candidates.append("UploadFile/" + clean)
    if clean.startswith("~/"):
        without_home = clean[2:]
        path_candidates.append(without_home)
        if without_home.startswith("File_New/"):
            path_candidates.append("OldSystem/" + without_home)
            path_candidates.append("UploadFile/OldSystem/" + without_home)
    if clean.startswith("File_New/"):
        path_candidates.append("OldSystem/" + clean)
        path_candidates.append("UploadFile/OldSystem/" + clean)
    path_candidates = [item for item in dict.fromkeys(path_candidates) if item]
    last_url = ""
    for base_url in base_urls:
        for candidate in path_candidates:
            quoted = "/".join(quote(part) for part in candidate.split("/") if part)
            url = urljoin(base_url.rstrip("/") + "/", quoted)
            last_url = url
            try:
                request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(request, timeout=30) as response:
                    raw = response.read()
                    content_type = response.headers.get_content_type() if response.headers else ""
            except (OSError, URLError):
                continue
            name = fallback_name or Path(candidate).name or "历史附件"
            mimetype = fallback_mimetype or content_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
            return {
                "datas": base64.b64encode(raw).decode("ascii"),
                "name": name,
                "mimetype": mimetype,
            }
    _logger.warning("remote legacy file read failed: last_url=%s", last_url)
    return {"error": True, "code": 404, "message": "历史附件文件不存在"}


def _legacy_file_http_base_urls(preferred_base_url: str = "") -> list[str]:
    raw = str(os.environ.get("SC_LEGACY_FILE_HTTP_BASE") or "").strip()
    values: list[str] = []
    for item in raw.replace("\n", ",").replace("\r", ",").split(","):
        clean = item.strip().rstrip("/")
        if clean:
            values.append(clean)
    preferred = str(preferred_base_url or "").strip().rstrip("/")
    if preferred:
        values.append(preferred)
    values.extend(DEFAULT_LEGACY_FILE_HTTP_BASE_URLS)
    return list(dict.fromkeys(values))


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
    if clean.startswith("~/"):
        without_home = clean[2:]
        candidates.append(without_home)
        if without_home.startswith("File_New/"):
            candidates.append("OldSystem/" + without_home)
            candidates.append("UploadFile/OldSystem/" + without_home)
    if clean.startswith("File_New/"):
        candidates.append("OldSystem/" + clean)
        candidates.append("UploadFile/OldSystem/" + clean)
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
