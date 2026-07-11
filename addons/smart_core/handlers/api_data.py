# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/api_data.py
# 统一数据读取意图（P0）：list / read / count
# - list:  search + read（支持分页/排序/fields="*"）
# - read:  read(ids)
# - count: search_count

import logging
import re
from typing import Any, Dict, Tuple, List, Optional
from ast import literal_eval
import base64
import csv
import io
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import unquote

from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import AccessError
from odoo.http import request

from ..core.base_handler import BaseIntentHandler
from ..core.api_data_execution_policy import client_requested_sudo, resolve_api_data_sudo
try:
    from ..core.project_context import selected_record_context_id_from_context
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import selected_project_id_from_context as selected_record_context_id_from_context
try:
    from ..core.project_context import apply_business_scope_domain
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import apply_project_scope_domain

    def apply_business_scope_domain(env_model, domain, params=None, context=None):
        return apply_project_scope_domain(env_model, domain, selected_record_context_id_from_context(params, context))
from ..core.request_params import parse_non_negative_int, parse_positive_int
from ..utils.extension_hooks import call_extension_hook_first
from ..utils.reason_codes import (
    REASON_OK,
    REASON_PROJECT_SCOPE_DENIED,
    REASON_READONLY_PROJECTION_MUTATION_DENIED,
    REASON_RECORD_VERSION_CONFLICT,
    failure_meta_for_reason,
)

_logger = logging.getLogger(__name__)
_NOT_NULL_COLUMN_RE = re.compile(r'null value in column "([^"]+)"', re.IGNORECASE)
_UNIQUE_VIOLATION_RE = re.compile(r"(duplicate key value|unique constraint|already exists)", re.IGNORECASE)


def _json(o):
    return json.dumps(o, ensure_ascii=False, default=str, separators=(",", ":"))


class ApiDataHandler(BaseIntentHandler):
    INTENT_TYPE = "api.data"
    DESCRIPTION = "通用数据读取：list/read/count（P0 可用版）"
    VERSION = "2.1.1"
    REQUIRED_GROUPS = ["base.group_user"]
    ETAG_ENABLED = False  # 列表不缓存，避免错判
    GROUP_WINDOW_IDENTITY_VERSION = "v1"
    GROUP_WINDOW_IDENTITY_ALGO = "sha1"
    SOURCE_KIND = "odoo_orm_proxy"
    SOURCE_AUTHORITIES = ("odoo.orm", "ir.model.access", "ir.rule", "ir.model.fields")

    # ----------------- 通用取参 -----------------

    def _err(self, code: int, message: str, reason_code: str = ""):
        error = {"code": code, "message": message}
        if reason_code:
            error["reason_code"] = reason_code
        return {"ok": False, "error": error}

    def _source_authority_contract(self, model: str, op: str) -> Dict[str, Any]:
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "model": str(model or ""),
            "op": str(op or ""),
            "proxy_only": True,
            "no_business_fact_authority": True,
            "field_value_passthrough_only": True,
        }

    def _read_if_none_match(self, p: Dict[str, Any]) -> str:
        if_none_match = str(self._dig(p, "if_none_match", "") or "").strip().strip('"')
        if if_none_match:
            return if_none_match
        try:
            return str((request.httprequest.headers.get("If-None-Match") or "")).strip().strip('"')
        except Exception:
            return ""

    def _read_if_match(self, p: Dict[str, Any]) -> str:
        return str(
            self._dig(p, "if_match", "")
            or self._dig(p, "ifMatch", "")
            or self._dig(p, "record_version", "")
            or self._dig(p, "recordVersion", "")
            or ""
        ).strip().strip('"')

    @staticmethod
    def _format_write_date(value) -> str:
        if not value:
            return ""
        try:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(value or "").strip()

    def _build_etag(self, *, model: str, op: str, ctx: Dict[str, Any], data: Dict[str, Any], meta: Dict[str, Any]) -> str:
        src = {
            "model": model,
            "op": op,
            "uid": int(getattr(self.env, "uid", 0) or 0),
            "lang": str(ctx.get("lang") or ""),
            "allowed_company_ids": list(ctx.get("allowed_company_ids") or []),
            "meta": meta,
            "data": data,
        }
        return hashlib.sha1(_json(src).encode("utf-8")).hexdigest()

    def _collect_params(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}

        def _merge(d: Any):
            if isinstance(d, dict):
                merged.update(d)

        # 1) 顶层（kwargs）
        _merge(kwargs)
        # 2) BaseIntentHandler 注入
        for attr in ("params", "payload", "_params", "_payload"):
            _merge(getattr(self, attr, None))
        # 3) 外层打包
        for key in ("payload", "params", "data", "args"):
            inner = merged.get(key)
            if isinstance(inner, dict):
                for k, v in inner.items():
                    if k not in merged:
                        merged[k] = v
        return merged

    def _request_context(self, p: Dict[str, Any]) -> Dict[str, Any]:
        """Merge client context over the authenticated Odoo context.

        ``with_context(dict)`` replaces the existing context in Odoo.  Keeping
        the server context preserves lang/tz/company defaults for translated
        fields while still allowing request-level overrides.
        """
        context = dict(getattr(self.env, "context", {}) or {})
        payload_context = self._dig(p, "context") or {}
        if not isinstance(payload_context, dict):
            payload_context = {}
        envelope_context = p.get("context") if isinstance(p.get("context"), dict) else {}
        if envelope_context:
            context.update(envelope_context)
        if payload_context:
            context.update(payload_context)
        if "active_test" not in context:
            context["active_test"] = self._get_bool(p, "active_test", True)
        company_id, company_error = parse_positive_int(self._dig(p, "company_id", None), allow_empty=True)
        if company_error:
            return context
        if company_id:
            context["allowed_company_ids"] = [company_id]
            context["company_id"] = company_id
        op = (self._get_str(p, "op", "list") or "list").strip().lower()
        project_scope_candidate = self._dig(p, "current_project_id", None)
        if op not in {"create", "write"}:
            project_scope_candidate = project_scope_candidate or self._dig(p, "project_id", None)
        project_id, project_error = parse_positive_int(project_scope_candidate, allow_empty=True)
        if not project_error and project_id:
            context["current_project_id"] = project_id
            context.setdefault("default_project_id", project_id)
        operation_strategy = str(
            self._dig(p, "operation_strategy", None)
            or self._dig(p, "operationStrategy", None)
            or ""
        ).strip()
        if operation_strategy:
            context["operation_strategy"] = operation_strategy
        return context

    def _dig(self, p: Dict[str, Any], key: str, default=None):
        if not isinstance(p, dict):
            return default
        if key in p:
            return p.get(key, default)
        for nest in ("payload", "params", "data", "args"):
            v = p.get(nest) or {}
            if isinstance(v, dict) and key in v:
                return v.get(key, default)
        return default

    def _dig_in(self, obj: Any, path: str, default=None):
        try:
            cur = obj
            for seg in path.split("."):
                if not isinstance(cur, dict) or seg not in cur:
                    return default
                cur = cur[seg]
            return cur
        except Exception:
            return default

    def _get_str(self, p: Dict[str, Any], key: str, default: str = "") -> str:
        v = self._dig(p, key, None)
        if v is None:
            return default
        try:
            return str(v)
        except Exception:
            return default

    def _get_bool(self, p: Dict[str, Any], key: str, default=False) -> bool:
        v = self._dig(p, key, None)
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        if isinstance(v, str):
            return v.strip().lower() in ("1", "true", "yes", "y", "on")
        return default

    def _get_int(self, p: Dict[str, Any], key: str, default: int = 0) -> int:
        v = self._dig(p, key, None)
        try:
            return int(v)
        except Exception:
            return default

    def _read_positive_param(self, p: Dict[str, Any], key: str, default: int):
        value, error = parse_positive_int(self._dig(p, key, None), allow_empty=True)
        if error:
            return 0, self._err(400, f"{key} 无效")
        return value or default, None

    def _read_non_negative_param(self, p: Dict[str, Any], key: str, default: int):
        value, error = parse_non_negative_int(self._dig(p, key, None), allow_empty=True)
        if error:
            return 0, self._err(400, f"{key} 无效")
        return default if value is None else value, None

    def _get_list(self, p: Dict[str, Any], key: str, default: Optional[List] = None) -> List:
        v = self._dig(p, key, None)
        if v is None:
            return list(default or [])
        # 特判 fields="*"
        if key == "fields" and v == "*":
            return ["*"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if key == "fields" and (s == "*" or ("," in s and not s.startswith("["))):
                if s == "*":
                    return ["*"]
                return [x.strip() for x in s.split(",") if x.strip()]
            if s.startswith("["):
                try:
                    arr = literal_eval(s)
                    return arr if isinstance(arr, list) else list(default or [])
                except Exception:
                    return list(default or [])
        return list(default or [])

    def _read_fields_param(self, p: Dict[str, Any], default: Optional[List] = None):
        raw = self._dig(p, "fields", None)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return list(default or []), None
        if raw == "*":
            return ["*"], None
        if isinstance(raw, list):
            fields = [str(item).strip() for item in raw if str(item).strip()]
            return fields, None
        if isinstance(raw, str):
            text = raw.strip()
            if text == "*":
                return ["*"], None
            if "," in text and not text.startswith("["):
                return [item.strip() for item in text.split(",") if item.strip()], None
            if text.startswith("["):
                try:
                    parsed = literal_eval(text)
                except Exception:
                    return [], self._err(400, "fields 无效")
                if not isinstance(parsed, list):
                    return [], self._err(400, "fields 无效")
                return [str(item).strip() for item in parsed if str(item).strip()], None
        return [], self._err(400, "fields 无效")

    def _read_domain_param(self, p: Dict[str, Any]):
        raw = self._dig(p, "domain", None)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return [], None
        if isinstance(raw, list):
            return raw, None
        if isinstance(raw, str):
            text = raw.strip()
            if not text.startswith("["):
                return [], self._err(400, "domain 无效")
            try:
                parsed = literal_eval(text)
            except Exception:
                try:
                    parsed = safe_eval(text, {})
                except Exception:
                    return [], self._err(400, "domain 无效")
            if not isinstance(parsed, list):
                return [], self._err(400, "domain 无效")
            return parsed, None
        return [], self._err(400, "domain 无效")

    def _read_group_by_param(self, p: Dict[str, Any], key: str = "group_by"):
        raw = self._dig(p, key, None)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return None, None
        if isinstance(raw, str):
            text = raw.strip()
            if "," in text:
                items = [part.strip() for part in text.split(",") if part.strip()]
                return (items or None), None
            return text, None
        if isinstance(raw, (tuple, list)):
            items = [str(part).strip() for part in raw if str(part).strip()]
            if not items:
                return None, None
            return (items if len(items) > 1 else items[0]), None
        return None, self._err(400, f"{key} 无效")

    def _read_search_term_param(self, p: Dict[str, Any]) -> str:
        for key in ("search_term", "searchTerm", "search", "keyword", "q"):
            value = self._dig(p, key, None)
            if value is None:
                continue
            try:
                term = str(value).strip()
            except Exception:
                term = ""
            if term:
                return term
        return ""

    def _read_ids_param(self, p: Dict[str, Any], key: str = "ids"):
        raw = self._dig(p, key, None)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return [], self._err(400, f"缺少参数 {key}")
        if isinstance(raw, list):
            values = raw
        elif isinstance(raw, str):
            text = raw.strip()
            if text.startswith("["):
                try:
                    parsed = literal_eval(text)
                except Exception:
                    return [], self._err(400, f"{key} 无效")
                if not isinstance(parsed, list):
                    return [], self._err(400, f"{key} 无效")
                values = parsed
            elif "," in text:
                values = [part.strip() for part in text.split(",")]
            else:
                values = [text]
        else:
            values = [raw]
        out: List[int] = []
        for value in values:
            parsed, error = parse_positive_int(value)
            if error:
                return [], self._err(400, f"{key} 无效")
            out.append(parsed)
        if not out:
            return [], self._err(400, f"缺少参数 {key}")
        return out, None

    def _normalize_domain(self, val) -> List:
        if val is None:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            s = val.strip()
            if not s:
                return []
            if s.startswith("["):
                try:
                    return literal_eval(s)
                except Exception:
                    try:
                        res = safe_eval(s, {})
                        return res if isinstance(res, list) else []
                    except Exception:
                        return []
        return []

    def _normalize_group_by(self, val):
        if val is None:
            return None
        if isinstance(val, str):
            text = val.strip()
            if not text:
                return None
            if "," in text:
                items = [part.strip() for part in text.split(",") if part.strip()]
                return items or None
            return text
        if isinstance(val, (tuple, list)):
            items = [str(part).strip() for part in val if str(part).strip()]
            if not items:
                return None
            return items if len(items) > 1 else items[0]
        return None

    def _build_group_key(self, field_name: str, value: Any) -> str:
        field_part = str(field_name or "group").strip() or "group"
        if isinstance(value, (str, int, float, bool)):
            value_part = str(value)
        else:
            try:
                value_part = json.dumps(value, ensure_ascii=False, default=str)
            except Exception:
                value_part = str(value)
        return f"{field_part}:{value_part}"

    def _normalize_group_page_offsets(self, val):
        out: Dict[str, int] = {}
        if val in (None, ""):
            return out, None
        if isinstance(val, dict):
            for raw_key, raw_offset in val.items():
                key = str(raw_key or "").strip()
                if not key:
                    return {}, self._err(400, "group_page_offsets 无效")
                offset, offset_error = parse_non_negative_int(raw_offset)
                if offset_error:
                    return {}, self._err(400, "group_page_offsets 无效")
                out[key] = offset
            return out, None
        if isinstance(val, str):
            text = val.strip()
            if not text:
                return out, None
            # 兼容 route 风格: k1:0;k2:3（key 可能经过 encodeURIComponent）
            for pair in text.split(";"):
                if ":" not in pair:
                    return {}, self._err(400, "group_page_offsets 无效")
                raw_key, raw_offset = pair.split(":", 1)
                key = unquote(str(raw_key or "").strip())
                if not key:
                    return {}, self._err(400, "group_page_offsets 无效")
                offset, offset_error = parse_non_negative_int(raw_offset)
                if offset_error:
                    return {}, self._err(400, "group_page_offsets 无效")
                out[key] = offset
            return out, None
        return {}, self._err(400, "group_page_offsets 无效")

    def _primary_group_by_field(self, group_by) -> str:
        if isinstance(group_by, str):
            return group_by.strip()
        if isinstance(group_by, (tuple, list)) and group_by:
            return str(group_by[0] or "").strip()
        return ""

    def _selection_label(self, env_model, field_name: str, value):
        field = env_model._fields.get(field_name)
        if not field:
            return str(value)
        try:
            selection = field.selection
            if callable(selection):
                selection = selection(env_model)
            pairs = selection or []
            mapping = {str(key): str(label) for key, label in pairs if key is not None}
            return mapping.get(str(value), str(value))
        except Exception:
            return str(value)

    def _normalize_group_item(self, env_model, field_name: str, value):
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            return {"value": value[0], "label": str(value[1])}
        if value in (False, None):
            return {"value": None, "label": "未设置"}
        field = env_model._fields.get(field_name)
        ftype = str(getattr(field, "type", "") or "").strip().lower() if field else ""
        if ftype == "selection":
            return {"value": value, "label": self._selection_label(env_model, field_name, value)}
        return {"value": value, "label": str(value)}

    def _build_group_summary(self, env_model, domain, group_by, limit: int = 20):
        return self._build_group_summary_with_offset(env_model, domain, group_by, limit=limit, offset=0)

    def _build_group_summary_with_offset(self, env_model, domain, group_by, limit: int = 20, offset: int = 0):
        field_name = self._primary_group_by_field(group_by)
        if not field_name:
            return []
        if field_name not in env_model._fields:
            return []
        limit = max(1, min(int(limit or 20), 50))
        offset = max(0, int(offset or 0))
        try:
            rows = env_model.read_group(domain or [], [field_name], [field_name], offset=offset, limit=limit, lazy=False)
        except Exception:
            _logger.exception("read_group failed model=%s group_by=%s", env_model._name, field_name)
            return []
        out = []
        count_key = f"{field_name}_count"
        for row in rows or []:
            normalized = self._normalize_group_item(env_model, field_name, row.get(field_name))
            group_key = self._build_group_key(field_name, normalized.get("value"))
            out.append(
                {
                    "group_key": group_key,
                    "field": field_name,
                    "value": normalized.get("value"),
                    "label": normalized.get("label"),
                    "count": int(row.get(count_key) or row.get("__count") or 0),
                    "domain": row.get("__domain") if isinstance(row.get("__domain"), list) else [],
                }
            )
        return out

    def _count_group_total(self, env_model, domain, group_by) -> Optional[int]:
        field_name = self._primary_group_by_field(group_by)
        if not field_name:
            return None
        if field_name not in env_model._fields:
            return None
        try:
            rows = env_model.read_group(domain or [], [field_name], [field_name], lazy=False)
        except Exception:
            _logger.exception("read_group total failed model=%s group_by=%s", env_model._name, field_name)
            return None
        return len(rows or [])

    def _build_numeric_aggregates(self, env_model, domain, fields_safe: List[str]) -> Dict[str, Dict[str, Any]]:
        if bool(getattr(env_model, "_sc_skip_default_list_aggregates", False)):
            return {}
        numeric_types = {"integer", "float", "monetary"}
        aggregate_fields = []
        for field_name in fields_safe or []:
            field = env_model._fields.get(field_name)
            field_type = str(getattr(field, "type", "") or "").strip().lower() if field else ""
            if (
                field_name != "id"
                and field_type in numeric_types
                and bool(getattr(field, "store", False))
                and bool(getattr(field, "column_type", None))
            ):
                aggregate_fields.append(field_name)
        if not aggregate_fields:
            return {}
        if getattr(env_model, "_auto", True) is False:
            try:
                rows = env_model.read_group(
                    domain or [],
                    [f"{field_name}:sum" for field_name in aggregate_fields],
                    [],
                    lazy=False,
                )
            except Exception:
                _logger.exception("numeric aggregate read_group fallback failed model=%s", env_model._name)
            else:
                row = (rows or [{}])[0] or {}
                out: Dict[str, Dict[str, Any]] = {}
                for field_name in aggregate_fields:
                    value = row.get(f"{field_name}_sum")
                    if not isinstance(value, (int, float)):
                        value = row.get(field_name)
                    if isinstance(value, (int, float)):
                        out[field_name] = {"sum": value}
                if out:
                    return out
            try:
                total = env_model.search_count(domain or [])
            except Exception:
                total = None
            if total is not None and total <= 20000:
                try:
                    rows = env_model.search(domain or [], order=None, limit=None).read(aggregate_fields)
                except Exception:
                    _logger.exception("numeric aggregate read fallback failed model=%s", env_model._name)
                else:
                    out: Dict[str, Dict[str, Any]] = {}
                    for field_name in aggregate_fields:
                        total_value = 0.0
                        has_value = False
                        for row in rows or []:
                            value = row.get(field_name)
                            if isinstance(value, (int, float)):
                                total_value += value
                                has_value = True
                        if has_value:
                            out[field_name] = {"sum": total_value}
                    return out
        out: Dict[str, Dict[str, Any]] = {}
        for field_name in aggregate_fields:
            try:
                rows = env_model.read_group(domain or [], [f"{field_name}:sum"], [], lazy=False)
            except Exception:
                _logger.exception("numeric aggregate failed model=%s field=%s", env_model._name, field_name)
                continue
            row = (rows or [{}])[0] or {}
            value = row.get(f"{field_name}_sum")
            if not isinstance(value, (int, float)):
                value = row.get(field_name)
            if isinstance(value, (int, float)):
                out[field_name] = {"sum": value}
        return out

    def _build_group_query_fingerprint(self, model: str, domain, group_by, order: str, search_term: str, ctx: Dict[str, Any]) -> str:
        group_by_norm = self._normalize_group_by(group_by)
        stable_ctx_keys = {
            "active_test",
            "lang",
            "tz",
            "uid",
            "allowed_company_ids",
            "company_id",
        }
        stable_ctx = {
            key: value
            for key, value in (ctx if isinstance(ctx, dict) else {}).items()
            if key in stable_ctx_keys
        }
        payload = {
            "model": str(model or ""),
            "domain": domain if isinstance(domain, list) else [],
            "group_by": group_by_norm,
            "order": str(order or "").strip(),
            "search_term": str(search_term or "").strip(),
            "ctx": stable_ctx,
        }
        return hashlib.sha1(_json(payload).encode("utf-8")).hexdigest()

    def _build_group_window_id(self, group_field: str, group_offset: int, group_limit: int, fingerprint: str) -> str:
        field_part = str(group_field or "group").strip() or "group"
        offset_part = max(0, int(group_offset or 0))
        limit_part = max(1, int(group_limit or 1))
        fp_part = str(fingerprint or "").strip()[:12] or "nofp"
        return f"{field_part}:{offset_part}:{limit_part}:{fp_part}"

    def _build_group_window_digest(self, window_id: str, group_summary: List[Dict[str, Any]]) -> str:
        normalized = []
        for item in group_summary or []:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "group_key": str(item.get("group_key") or "").strip(),
                    "count": int(item.get("count") or 0),
                }
            )
        payload = {
            "window_id": str(window_id or "").strip(),
            "groups": normalized,
        }
        return hashlib.sha1(_json(payload).encode("utf-8")).hexdigest()

    def _build_group_window_identity_key(self, window_id: str, window_digest: str) -> str:
        version = str(self.GROUP_WINDOW_IDENTITY_VERSION or "").strip() or "v1"
        algo = str(self.GROUP_WINDOW_IDENTITY_ALGO or "").strip().lower() or "sha1"
        wid = str(window_id or "").strip() or "-"
        wdg = str(window_digest or "").strip() or "-"
        return f"{version}:{algo}:{wid}:{wdg}"

    def _build_grouped_rows(
        self,
        env_model,
        domain,
        group_by,
        fields_safe: List[str],
        limit: int = 20,
        sample_limit: int = 3,
        group_page_size: Optional[int] = None,
        group_page_offsets: Optional[Dict[str, int]] = None,
        group_summary: Optional[List[Dict[str, Any]]] = None,
        order: str = "",
    ):
        summary = group_summary if isinstance(group_summary, list) else self._build_group_summary(env_model, domain, group_by, limit=limit)
        if not summary:
            return []
        row_fields = list(fields_safe or ["id", "name"])
        if "id" not in row_fields:
            row_fields.insert(0, "id")
        page_offsets = group_page_offsets if isinstance(group_page_offsets, dict) else {}
        out = []
        for item in summary:
            group_domain = item.get("domain") if isinstance(item.get("domain"), list) else []
            if not group_domain:
                continue
            count = int(item.get("count") or 0)
            requested_page_size = int(group_page_size or sample_limit or 3)
            page_limit = max(1, requested_page_size)
            group_key = self._build_group_key(str(item.get("field") or ""), item.get("value"))
            req_offset = int(page_offsets.get(group_key) or 0)
            max_offset = max(0, count - page_limit)
            page_offset = max(0, min(req_offset, max_offset))
            page_offset = (page_offset // page_limit) * page_limit
            page_total = max(1, ((count + page_limit - 1) // page_limit))
            page_current = (page_offset // page_limit) + 1
            page_range_start = page_offset + 1 if count > 0 else 0
            page_range_end = min(count, page_offset + page_limit) if count > 0 else 0
            try:
                sample_rows, order_error, _python_order_applied = self._search_read_with_order(
                    env_model,
                    group_domain,
                    row_fields,
                    order,
                    page_limit,
                    page_offset,
                )
                if order_error:
                    sample_rows = []
            except Exception:
                _logger.exception("group sample query failed model=%s group=%s", env_model._name, item.get("label"))
                sample_rows = []
            sample_count = len(sample_rows)
            out.append(
                {
                    "group_key": group_key,
                    "field": item.get("field"),
                    "value": item.get("value"),
                    "label": item.get("label"),
                    "count": item.get("count"),
                    "total_count": count,
                    "domain": group_domain,
                    "sample_rows": sample_rows,
                    "sample_count": sample_count,
                    "is_sampled": sample_count < count,
                    "page_requested_size": requested_page_size,
                    "page_applied_size": page_limit,
                    "page_requested_offset": req_offset,
                    "page_applied_offset": page_offset,
                    "page_max_offset": max_offset,
                    "page_clamped": page_offset != req_offset,
                    "page_offset": page_offset,
                    "page_limit": page_limit,
                    "page_size": page_limit,
                    "page_current": page_current,
                    "page_total": page_total,
                    "page_range_start": page_range_start,
                    "page_range_end": page_range_end,
                    "page_window": {
                        "start": page_range_start,
                        "end": page_range_end,
                    },
                    "page_has_prev": page_offset > 0,
                    "page_has_next": (page_offset + page_limit) < count,
                }
            )
        return out

    def _safe_eval_with_runtime(self, raw: str):
        if not isinstance(raw, str):
            return None
        text = raw.strip()
        if not text:
            return None
        context = getattr(self.env, "context", {}) or {}
        if not isinstance(context, dict):
            context = {}
        allowed_company_ids = self._runtime_allowed_company_ids(context)
        runtime_env = {
            "uid": int(getattr(self.env, "uid", 0) or 0),
            "user": getattr(self.env, "user", None),
            "allowed_company_ids": allowed_company_ids,
            "company_id": allowed_company_ids[0] if allowed_company_ids else False,
            "active_id": context.get("active_id"),
            "active_ids": context.get("active_ids") or [],
            "active_model": context.get("active_model"),
            "context": context,
            "context_today": lambda: datetime.now().date(),
            "datetime": datetime,
        }
        try:
            return safe_eval(text, runtime_env)
        except Exception:
            return None

    def _runtime_allowed_company_ids(self, context: Dict[str, Any]) -> List[int]:
        raw = context.get("allowed_company_ids") if isinstance(context, dict) else None
        ids = self._normalize_runtime_ids(raw)
        if ids:
            return ids

        companies = getattr(getattr(self.env, "user", None), "company_ids", None)
        ids = self._normalize_runtime_ids(getattr(companies, "ids", None))
        if ids:
            return ids

        env_companies = getattr(self.env, "companies", None)
        ids = self._normalize_runtime_ids(getattr(env_companies, "ids", None))
        if ids:
            return ids

        company = getattr(self.env, "company", None) or getattr(getattr(self.env, "user", None), "company_id", None)
        company_id = int(getattr(company, "id", 0) or 0)
        return [company_id] if company_id > 0 else []

    @staticmethod
    def _normalize_runtime_ids(raw) -> List[int]:
        if raw is None:
            return []
        if isinstance(raw, int):
            return [raw] if raw > 0 else []
        if not isinstance(raw, (list, tuple, set)):
            return []
        ids = []
        for item in raw:
            try:
                value = int(item or 0)
            except (TypeError, ValueError):
                continue
            if value > 0 and value not in ids:
                ids.append(value)
        return ids

    def _pick_model(self, p: Dict[str, Any]) -> str:
        model = self._get_str(p, "model", "").strip()
        if model:
            return model
        res_model = self._get_str(p, "res_model", "").strip()
        if res_model:
            return res_model
        for container_key in ("payload", "params", "data", "args"):
            container = p.get(container_key, {})
            if isinstance(container, dict):
                entry_model = self._dig_in(container, "entry.model", "")
                if isinstance(entry_model, str) and entry_model.strip():
                    return entry_model.strip()
                action_res_model = self._dig_in(container, "action.res_model", "")
                if isinstance(action_res_model, str) and action_res_model.strip():
                    return action_res_model.strip()
        return ""

    # ----------------- 字段访问过滤 -----------------

    def _filter_readable_fields(self, env_model, fields: List[str]) -> List[str]:
        """按 field.groups 过滤当前用户无权访问的字段；确保含 id。"""
        safe: List[str] = []
        user = env_model.env.user

        for f in (fields or []):
            if f == "id":
                safe.append("id")
                continue
            fld = env_model._fields.get(f)
            if not fld:
                continue
            groups_spec = getattr(fld, "groups", "") or ""
            if not groups_spec:
                safe.append(f)
                continue
            # groups 是逗号分隔的 xmlid 列表；满足其一即可
            allowed = False
            for g in groups_spec.split(","):
                g = g.strip()
                if not g:
                    continue
                try:
                    if user.has_group(g):
                        allowed = True
                        break
                except Exception:
                    # has_group 解析失败就当未授权
                    allowed = False
            if allowed:
                safe.append(f)

        if "id" not in safe:
            safe.insert(0, "id")
        return safe

    def _parse_order_clauses(self, env_model, order: str):
        clauses = []
        for raw_clause in str(order or "").split(","):
            text = raw_clause.strip()
            if not text:
                continue
            parts = text.split()
            field_name = parts[0].strip()
            if not field_name or field_name not in env_model._fields:
                return [], self._err(400, "order 无效")
            direction = parts[1].strip().lower() if len(parts) > 1 else "asc"
            if direction not in {"asc", "desc"}:
                return [], self._err(400, "order 无效")
            clauses.append((field_name, direction))
        return clauses, None

    def _requires_python_order(self, env_model, clauses: List[Tuple[str, str]]) -> bool:
        for field_name, _direction in clauses or []:
            field = env_model._fields.get(field_name)
            if not field:
                return False
            if field_name == "id":
                continue
            if not bool(getattr(field, "store", False)) or not bool(getattr(field, "column_type", None)):
                return True
        return False

    def _sort_key_value(self, value):
        if value in (None, False):
            return (1, 9, "")
        if isinstance(value, (list, tuple)):
            if len(value) >= 2:
                return self._sort_key_value(value[1])
            if value:
                return self._sort_key_value(value[0])
            return (1, 9, "")
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return (1, 9, "")
            date_key = self._sort_key_date_text(text)
            if date_key is not None:
                return (0, 0, date_key)
            return (0, 2, text.casefold())
        if isinstance(value, (int, float)):
            return (0, 1, value)
        if isinstance(value, datetime):
            return (0, 0, (value.year, value.month, value.day, value.hour, value.minute, value.second))
        try:
            return (0, 2, str(value).casefold())
        except Exception:
            return (1, 9, "")

    def _sort_key_date_text(self, text: str):
        normalized = text.strip().replace("T", " ")
        normalized = re.sub(r"[年月/.]", "-", normalized)
        normalized = normalized.replace("日", "")
        match = re.match(
            r"^(\d{4})-(\d{1,2})-(\d{1,2})(?:\s+(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?",
            normalized,
        )
        if not match:
            return None
        try:
            year, month, day = (int(match.group(i) or 0) for i in range(1, 4))
            hour = int(match.group(4) or 0)
            minute = int(match.group(5) or 0)
            second = int(match.group(6) or 0)
            datetime(year, month, day, hour, minute, second)
        except Exception:
            return None
        return (year, month, day, hour, minute, second)

    def _sort_rows_by_python_clause(self, rows: List[Dict[str, Any]], field_name: str, direction: str):
        blanks = []
        values = []
        for row in rows:
            key = self._sort_key_value(row.get(field_name))
            if key[0]:
                blanks.append(row)
            else:
                values.append(row)
        values.sort(
            key=lambda row, name=field_name: self._sort_key_value(row.get(name))[1:],
            reverse=direction == "desc",
        )
        return values + blanks

    def _search_read_with_order(
        self,
        env_model,
        domain,
        fields_safe: List[str],
        order: str,
        limit: int,
        offset: int = 0,
    ):
        clauses, order_error = self._parse_order_clauses(env_model, order)
        if order_error:
            return [], order_error, False
        if not clauses or not self._requires_python_order(env_model, clauses):
            recs = env_model.search(domain or [], order=order or None, limit=limit or None, offset=offset or 0)
            return recs.read(fields_safe or ["id", "name"]), None, False

        row_fields = list(dict.fromkeys(list(fields_safe or ["id", "name"]) + [field for field, _direction in clauses]))
        recs = env_model.search(domain or [], order="id asc")
        rows = recs.read(row_fields)
        for field_name, direction in reversed(clauses):
            rows = self._sort_rows_by_python_clause(rows, field_name, direction)
        start = max(0, int(offset or 0))
        end = start + int(limit or 0) if int(limit or 0) > 0 else None
        return rows[start:end], None, True

    def _current_project_id(self, p: Dict[str, Any], ctx: Dict[str, Any]) -> int:
        return selected_record_context_id_from_context(p, ctx)

    def _current_record_context_id(self, p: Dict[str, Any], ctx: Dict[str, Any]) -> int:
        return self._current_project_id(p, ctx)

    def _apply_record_scope(self, env_model, domain: List[Any], p: Dict[str, Any], ctx: Dict[str, Any]):
        return apply_business_scope_domain(env_model, domain, p, ctx)

    def _apply_project_scope(self, env_model, domain: List[Any], p: Dict[str, Any], ctx: Dict[str, Any]):
        return self._apply_record_scope(env_model, domain, p, ctx)

    def _record_scope_denied(self, message: str, scope_meta: Dict[str, Any]):
        return {
            "ok": False,
            "error": {
                "code": REASON_PROJECT_SCOPE_DENIED,
                "message": message,
                "reason_code": REASON_PROJECT_SCOPE_DENIED,
                "kind": "permission",
                "project_scope": scope_meta,
                "record_scope": scope_meta,
            },
            "code": 403,
        }

    def _project_scope_denied(self, message: str, scope_meta: Dict[str, Any]):
        return self._record_scope_denied(message, scope_meta)

    def _normalize_ids(self, ids: List[Any]) -> List[int]:
        out: List[int] = []
        for value in ids or []:
            try:
                parsed = int(value or 0)
            except Exception:
                parsed = 0
            if parsed > 0:
                out.append(parsed)
        return out

    def _ensure_records_in_record_scope(self, env_model, ids: List[Any], p: Dict[str, Any], ctx: Dict[str, Any]):
        normalized_ids = self._normalize_ids(ids)
        if not normalized_ids:
            return None
        scoped_domain, scope_meta = self._apply_record_scope(env_model, [("id", "in", normalized_ids)], p, ctx)
        if not scope_meta.get("applied"):
            return None
        allowed_count = env_model.search_count(scoped_domain)
        if int(allowed_count or 0) == len(set(normalized_ids)):
            return None
        return self._record_scope_denied("当前记录上下文不允许访问或修改其他记录的数据", scope_meta)

    def _ensure_records_in_project_scope(self, env_model, ids: List[Any], p: Dict[str, Any], ctx: Dict[str, Any]):
        return self._ensure_records_in_record_scope(env_model, ids, p, ctx)

    def _search_view_field_names(self, env_model) -> List[str]:
        model_name = str(getattr(env_model, "_name", "") or "").strip()
        if not model_name:
            return []
        cache = getattr(self, "_search_view_field_cache", None)
        if cache is None:
            cache = {}
            setattr(self, "_search_view_field_cache", cache)
        if model_name in cache:
            return list(cache.get(model_name) or [])

        names: List[str] = []
        try:
            views = env_model.env["ir.ui.view"].sudo().search([
                ("model", "=", model_name),
                ("type", "=", "search"),
            ])
        except Exception:
            cache[model_name] = []
            return []

        for view in views:
            arch = str(getattr(view, "arch_db", "") or "").strip()
            if not arch:
                continue
            try:
                root = ET.fromstring(arch.encode("utf-8"))
            except Exception:
                continue
            for node in root.iter("field"):
                field_name = str(node.attrib.get("name") or "").strip()
                if field_name and field_name not in names:
                    names.append(field_name)

        cache[model_name] = names
        return list(names)

    def _extension_search_field_names(self, env_model) -> List[str]:
        model_name = str(getattr(env_model, "_name", "") or "").strip()
        if not model_name:
            return []
        cache = getattr(self, "_extension_search_field_cache", None)
        if cache is None:
            cache = {}
            setattr(self, "_extension_search_field_cache", cache)
        if model_name in cache:
            return list(cache.get(model_name) or [])

        names: List[str] = []
        try:
            payload = call_extension_hook_first(
                env_model.env,
                "smart_core_api_data_search_fields",
                env_model.env,
                model_name,
            )
        except Exception:
            payload = None
        if isinstance(payload, dict):
            raw_fields = payload.get(model_name) or payload.get("fields") or []
        else:
            raw_fields = payload or []
        if isinstance(raw_fields, str):
            raw_fields = [raw_fields]
        if isinstance(raw_fields, (list, tuple, set)):
            for field_name in raw_fields:
                value = str(field_name or "").strip()
                if value and value not in names:
                    names.append(value)

        cache[model_name] = names
        return list(names)

    def _fallback_search_field_names(self, env_model, limit: int = 16) -> List[str]:
        fields = getattr(env_model, "_fields", {}) or {}
        preferred_names = [
            str(getattr(env_model, "_rec_name", "") or "").strip(),
            "name",
            "display_name",
            "title",
            "document_no",
            "contract_no",
            "project_name",
            "partner_name",
            "remark",
            "notes",
            "description",
        ]
        ordered_names = []
        for name in preferred_names + list(fields.keys()):
            name = str(name or "").strip()
            if name and name != "id" and name not in ordered_names:
                ordered_names.append(name)

        readable_names = self._filter_readable_fields(env_model, ordered_names)
        out: List[str] = []
        for field_name in readable_names:
            field = fields.get(field_name)
            if not field:
                continue
            field_type = str(getattr(field, "type", "") or "")
            if field_type not in ("char", "text", "html", "many2one"):
                continue
            if not bool(getattr(field, "store", False)) and not getattr(field, "search", None):
                continue
            if field_name not in out:
                out.append(field_name)
            if len(out) >= max(1, int(limit or 16)):
                break
        return out

    def _build_search_term_domain(self, env_model, search_term: str, fields_safe: List[str]) -> List[Any]:
        term = str(search_term or "").strip()
        if not term:
            return []
        try:
            search_id = int(term)
        except Exception:
            search_id = None

        candidates: List[str] = []
        related_candidates: List[str] = []
        rec_name = str(getattr(env_model, "_rec_name", "") or "").strip()
        search_view_fields_raw = self._search_view_field_names(env_model)
        search_view_fields = self._filter_readable_fields(env_model, search_view_fields_raw) if search_view_fields_raw else []
        extension_fields_raw = self._extension_search_field_names(env_model)
        extension_fields = self._filter_readable_fields(env_model, extension_fields_raw) if extension_fields_raw else []
        for field_name in [rec_name, "name"] + list(fields_safe or []) + list(search_view_fields or []) + list(extension_fields or []):
            if not field_name or field_name == "id" or field_name in candidates:
                continue
            field = env_model._fields.get(field_name)
            if not field:
                continue
            field_type = str(getattr(field, "type", "") or "")
            if not bool(getattr(field, "store", False)) and not getattr(field, "search", None):
                continue
            if field_type in ("char", "text", "html", "many2one"):
                candidates.append(field_name)
            if field_type == "many2one":
                relation_model_name = str(getattr(field, "comodel_name", "") or "").strip()
                relation_model = None
                if relation_model_name:
                    try:
                        relation_model = env_model.env[relation_model_name]
                    except Exception:
                        relation_model = None
                relation_fields = getattr(relation_model, "_fields", {}) if relation_model is not None else {}
                relation_rec_name = str(getattr(relation_model, "_rec_name", "") or "").strip() if relation_model is not None else ""
                relation_probe_fields = [
                    relation_rec_name,
                    "name",
                    "display_name",
                    "title",
                    "document_no",
                    "contract_no",
                    "project_name",
                    "partner_name",
                    "legacy_visible_title",
                    "legacy_visible_project_name",
                    "legacy_visible_counterparty",
                    "legacy_visible_contract_no",
                    "legacy_visible_document_no",
                ]
                for relation_field_name in relation_probe_fields:
                    relation_field_name = str(relation_field_name or "").strip()
                    if not relation_field_name:
                        continue
                    relation_field = relation_fields.get(relation_field_name)
                    relation_field_type = str(getattr(relation_field, "type", "") or "") if relation_field else ""
                    if relation_field_type not in ("char", "text", "html"):
                        continue
                    if not bool(getattr(relation_field, "store", False)) and not getattr(relation_field, "search", None):
                        continue
                    dotted = "%s.%s" % (field_name, relation_field_name)
                    if dotted not in related_candidates:
                        related_candidates.append(dotted)

        if not candidates and not related_candidates:
            for field_name in self._fallback_search_field_names(env_model):
                if field_name and field_name not in candidates:
                    candidates.append(field_name)

        search_candidates = candidates + related_candidates
        leaves: List[Any] = [(field_name, "ilike", term) for field_name in search_candidates]
        token_domain: List[Any] = []
        tokens: List[str] = []
        for token in re.split(r"[\s/|,，;；()（）]+", term):
            value = token.strip()
            if len(value) >= 2 and value not in tokens:
                tokens.append(value)
            if len(tokens) >= 5:
                break
        if len(tokens) >= 2 and search_candidates:
            token_groups: List[Any] = []
            for token in tokens:
                token_leaves = [(field_name, "ilike", token) for field_name in search_candidates]
                if len(token_leaves) == 1:
                    token_groups.append(token_leaves)
                else:
                    token_groups.append(["|"] * (len(token_leaves) - 1) + token_leaves)
            token_domain = token_groups[0]
            for group in token_groups[1:]:
                token_domain = ["&"] + token_domain + group
        if search_id is not None:
            leaves.append(("id", "=", search_id))
        exact_domain: List[Any] = []
        if len(leaves) == 1:
            exact_domain = leaves
        elif len(leaves) > 1:
            exact_domain = ["|"] * (len(leaves) - 1) + leaves
        if exact_domain and token_domain:
            return ["|"] + exact_domain + token_domain
        if token_domain:
            return token_domain
        if not exact_domain:
            return [("id", "=", 0)]
        return exact_domain

    def _apply_search_term_domain(self, env_model, domain: List[Any], p: Dict[str, Any], fields_safe: List[str]) -> Tuple[List[Any], str]:
        search_term = self._read_search_term_param(p)
        if not search_term:
            return list(domain or []), ""
        return list(domain or []) + self._build_search_term_domain(env_model, search_term, fields_safe), search_term

    def _prepare_create_vals(self, env_model, vals: Dict[str, Any]) -> Dict[str, Any]:
        safe_vals = {k: v for k, v in (vals or {}).items() if k in env_model._fields}
        if not safe_vals:
            return {}

        missing_for_default = [
            name
            for name in (env_model._fields or {}).keys()
            if name not in safe_vals and not str(name or "").startswith("__")
        ]
        if missing_for_default:
            try:
                defaults = env_model.default_get(missing_for_default) or {}
            except Exception:
                defaults = {}
            if isinstance(defaults, dict):
                for name in missing_for_default:
                    if name in safe_vals:
                        continue
                    if name in defaults and defaults.get(name) is not None:
                        safe_vals[name] = defaults.get(name)

        self._apply_create_fallbacks(env_model, safe_vals)
        return safe_vals

    def _selection_options(self, env_model, field_name: str) -> List[str]:
        field = (env_model._fields or {}).get(field_name)
        if not field:
            return []
        try:
            raw_selection = getattr(field, "selection", [])
            if callable(raw_selection):
                raw = raw_selection(env_model.env)
            elif isinstance(raw_selection, str):
                resolver = getattr(env_model, raw_selection, None)
                raw = resolver() if callable(resolver) else []
            else:
                raw = raw_selection
        except Exception:
            raw = []
        return [str(item[0]) for item in (raw or []) if isinstance(item, (list, tuple)) and item]

    def _fill_selection_fallback(self, env_model, safe_vals: Dict[str, Any], field_name: str, preferred: str = "") -> bool:
        if field_name not in env_model._fields:
            return False
        current = safe_vals.get(field_name)
        if current not in (None, ""):
            return False
        options = self._selection_options(env_model, field_name)
        if preferred and preferred in options:
            safe_vals[field_name] = preferred
            return True
        if options:
            safe_vals[field_name] = options[0]
            return True
        return False

    def _apply_create_fallbacks(self, env_model, safe_vals: Dict[str, Any]) -> None:
        # 通用兜底：创建用户/公司/激活状态。
        if "user_id" in env_model._fields and safe_vals.get("user_id") in (None, False, ""):
            uid = int(getattr(env_model.env, "uid", 0) or 0)
            if uid > 0:
                safe_vals["user_id"] = uid
        if "company_id" in env_model._fields and safe_vals.get("company_id") in (None, False, ""):
            try:
                company = env_model.env.user.company_id
                if company and company.id:
                    safe_vals["company_id"] = company.id
            except Exception:
                pass
        if "active" in env_model._fields and safe_vals.get("active") in (None, ""):
            safe_vals["active"] = True

        # 扩展兜底：行业模块可以注入模型级 fallback，不在平台层硬编码。
        payload = call_extension_hook_first(
            env_model.env,
            "smart_core_create_field_fallbacks",
            env_model.env,
            env_model._name,
        )
        if isinstance(payload, dict):
            selection_defaults = payload.get("selection_defaults") if isinstance(payload.get("selection_defaults"), dict) else {}
            for field_name, preferred in selection_defaults.items():
                self._fill_selection_fallback(env_model, safe_vals, str(field_name), preferred=str(preferred or ""))

    def _extract_not_null_column(self, error: Exception) -> str:
        message = str(error or "")
        match = _NOT_NULL_COLUMN_RE.search(message)
        return str(match.group(1) if match else "").strip()

    def _friendly_create_error(self, error: Exception) -> str:
        message = str(error or "")
        if _UNIQUE_VIOLATION_RE.search(message):
            return "已有相同记录，请先搜索并选择已有记录；如确需新建，请使用不同名称。"
        if "psycopg2" in message or "Traceback" in message or "DETAIL:" in message:
            return "创建失败，请检查填写内容后重试。"
        return message or "创建失败，请检查填写内容后重试。"

    def _mutation_policy(self, model: str, op: str) -> Dict[str, Any]:
        payload = call_extension_hook_first(
            self.env,
            "smart_core_api_data_mutation_policy",
            self.env,
            model,
            op,
        )
        if isinstance(payload, dict):
            return payload
        return {"allowed": True, "reason_code": REASON_OK, "source": "smart_core_default"}

    def _check_mutation_policy(self, model: str, op: str):
        policy = self._mutation_policy(model, op)
        if policy.get("allowed") is not False:
            return None

        reason_code = str(policy.get("reason_code") or REASON_READONLY_PROJECTION_MUTATION_DENIED).strip()
        message = str(policy.get("message") or "当前数据为只读投影，不允许通过公开数据接口创建或修改。").strip()
        error = self._err(403, message, reason_code=reason_code)
        meta = failure_meta_for_reason(reason_code)
        if meta:
            error.setdefault("error", {}).update(meta)
        error.setdefault("error", {})["policy_source"] = str(policy.get("source") or "").strip()
        return error

    def _create_execution_policy(self, model: str, vals: Dict[str, Any], ctx: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        payload = call_extension_hook_first(
            self.env,
            "smart_core_api_data_create_execution_policy",
            self.env,
            model,
            vals,
            ctx,
            params,
        )
        if isinstance(payload, dict):
            return payload
        return {"sudo": False, "source": "smart_core_default"}

    def _fill_not_null_column_fallback(self, env_model, safe_vals: Dict[str, Any], column: str) -> bool:
        if not column or column not in env_model._fields:
            return False
        field = env_model._fields.get(column)
        ttype = str(getattr(field, "type", "") or getattr(field, "ttype", "")).strip().lower()
        if ttype == "selection":
            return self._fill_selection_fallback(env_model, safe_vals, column)
        if ttype in {"char", "text", "html"}:
            safe_vals[column] = ""
            return True
        if ttype == "boolean":
            safe_vals[column] = False
            return True
        if ttype in {"float", "monetary"}:
            safe_vals[column] = 0.0
            return True
        if ttype == "integer":
            safe_vals[column] = 0
            return True
        return False

    def _record_field_value_for_child(self, parent, field_name: str):
        if not parent or field_name not in parent._fields:
            return None
        try:
            value = parent[field_name]
        except Exception:
            return None
        if hasattr(value, "id"):
            return value.id or None
        return value if value not in (None, False, "") else None

    def _prepare_one2many_create_vals(self, parent, parent_field, raw_vals: Dict[str, Any]) -> Dict[str, Any]:
        comodel_name = str(getattr(parent_field, "comodel_name", "") or "").strip()
        if not comodel_name or comodel_name not in self.env:
            return raw_vals
        inverse_name = str(getattr(parent_field, "inverse_name", "") or "").strip()
        child_model = self.env[comodel_name].with_context(
            dict(self.env.context, **({f"default_{inverse_name}": parent.id} if inverse_name and parent and parent.id else {}))
        )
        vals = dict(raw_vals or {})
        if inverse_name and inverse_name in child_model._fields and parent and parent.id and vals.get(inverse_name) in (None, False, ""):
            vals[inverse_name] = parent.id

        # Copy same-name backend-owned fields for child records when a subview
        # omits hidden required values; this preserves ORM facts and does not
        # classify partners or infer customer/supplier semantics.
        for name in ("company_id", "currency_id", "partner_id"):
            if name in child_model._fields and vals.get(name) in (None, False, ""):
                parent_value = self._record_field_value_for_child(parent, name)
                if parent_value:
                    vals[name] = parent_value
        if "date_planned" in child_model._fields and vals.get("date_planned") in (None, False, ""):
            parent_date = self._record_field_value_for_child(parent, "date_order")
            if parent_date:
                vals["date_planned"] = parent_date
        if "product_id" in child_model._fields and "product_uom" in child_model._fields and vals.get("product_uom") in (None, False, ""):
            product_id = vals.get("product_id")
            if isinstance(product_id, (list, tuple)) and product_id:
                product_id = product_id[0]
            try:
                product_id = int(product_id or 0)
            except Exception:
                product_id = 0
            if product_id and "product.product" in self.env:
                product = self.env["product.product"].browse(product_id).exists()
                if product:
                    uom = product.uom_po_id or product.uom_id
                    if uom:
                        vals["product_uom"] = uom.id

        return self._prepare_create_vals(child_model, vals) or vals

    def _prepare_write_vals(self, env_model, recs, vals: Dict[str, Any]) -> Dict[str, Any]:
        safe_vals = {k: v for k, v in vals.items() if k in env_model._fields}
        if not safe_vals or len(recs) != 1:
            return safe_vals
        parent = recs[0]
        prepared = dict(safe_vals)
        for name, value in list(prepared.items()):
            field = env_model._fields.get(name)
            if not field or str(getattr(field, "type", "") or "").strip().lower() != "one2many":
                continue
            if not isinstance(value, list):
                continue
            commands = []
            changed = False
            for command in value:
                if not isinstance(command, (list, tuple)) or len(command) < 3:
                    commands.append(command)
                    continue
                op = int(command[0] or 0)
                if op != 0 or not isinstance(command[2], dict):
                    commands.append(command)
                    continue
                child_vals = self._prepare_one2many_create_vals(parent, field, command[2])
                commands.append([command[0], command[1], child_vals])
                changed = True
            if changed:
                prepared[name] = commands
        return prepared

    # ----------------- 主处理 -----------------

    def handle(self, **kwargs) -> Tuple[Dict[str, Any], Dict[str, Any]] | Dict[str, Any]:
        p = self._collect_params(kwargs)

        try:
            _logger.debug("[api.data] keys=%s payload.keys=%s params.keys=%s",
                         list(p.keys()),
                         list((p.get("payload") or {}).keys()) if isinstance(p.get("payload"), dict) else None,
                         list((p.get("params") or {}).keys()) if isinstance(p.get("params"), dict) else None)
        except Exception:
            pass

        op = (self._get_str(p, "op", "list") or "list").strip().lower()
        model = self._pick_model(p)
        if not model:
            return self._err(400, "缺少参数 model")
        if model not in self.env:
            return self._err(404, f"未知模型: {model}")

        context = self._request_context(p)
        if_none_match = self._read_if_none_match(p)

        use_sudo = resolve_api_data_sudo(p)
        if client_requested_sudo(p):
            _logger.warning("api.data ignored client sudo request model=%s op=%s", model, op)

        if op == "list":
            return self._with_etag_if_match(self._op_list(model, p, context, use_sudo), model, op, context, if_none_match)
        elif op == "read":
            return self._with_etag_if_match(self._op_read(model, p, context, use_sudo), model, op, context, if_none_match)
        elif op in ("default_get", "defaults"):
            return self._with_etag_if_match(self._op_default_get(model, p, context, use_sudo), model, op, context, if_none_match)
        elif op in ("count", "search_count"):
            return self._with_etag_if_match(self._op_count(model, p, context, use_sudo), model, op, context, if_none_match)
        elif op in ("create",):
            return self._op_create(model, p, context, use_sudo)
        elif op in ("write",):
            return self._op_write(model, p, context, use_sudo)
        elif op in ("export_csv",):
            return self._op_export_csv(model, p, context, use_sudo)
        else:
            return self._err(400, f"不支持的操作: {op}")

    def _with_etag_if_match(self, result, model: str, op: str, ctx: Dict[str, Any], if_none_match: str):
        if not isinstance(result, tuple) or len(result) != 2:
            return result
        data, meta = result
        if not isinstance(data, dict) or not isinstance(meta, dict):
            return result
        etag = self._build_etag(model=model, op=op, ctx=ctx, data=data, meta=meta)
        meta_out = dict(meta)
        meta_out["etag"] = etag
        if if_none_match and if_none_match == etag:
            return {"ok": True, "data": None, "meta": {"op": op, "model": model, "etag": etag}, "code": 304}
        return data, meta_out

    # ----------------- 操作实现 -----------------

    def _op_list(self, model: str, p: Dict[str, Any], ctx: Dict[str, Any], sudo: bool):
        fields, fields_error = self._read_fields_param(p, [])
        if fields_error:
            return fields_error
        limit, limit_error = self._read_positive_param(p, "limit", 40)
        if limit_error:
            return limit_error
        offset, offset_error = self._read_non_negative_param(p, "offset", 0)
        if offset_error:
            return offset_error
        order = self._get_str(p, "order", "")
        domain, domain_error = self._read_domain_param(p)
        if domain_error:
            return domain_error
        domain_raw = self._get_str(p, "domain_raw", "").strip()
        context_raw = self._get_str(p, "context_raw", "").strip()
        group_by, group_by_error = self._read_group_by_param(p)
        if group_by_error:
            return group_by_error
        group_page_offsets, group_page_offsets_error = self._normalize_group_page_offsets(self._dig(p, "group_page_offsets"))
        if group_page_offsets_error:
            return group_page_offsets_error
        group_offset, group_offset_error = self._read_non_negative_param(p, "group_offset", 0)
        if group_offset_error:
            return group_offset_error
        need_group_total = self._get_bool(p, "need_group_total", False)
        group_page_size, group_page_size_error = self._read_positive_param(p, "group_page_size", 0)
        if group_page_size_error:
            return group_page_size_error
        group_page_size = min(group_page_size, 8)
        default_group_limit = min(limit or 20, 30)
        group_limit, group_limit_error = self._read_positive_param(p, "group_limit", default_group_limit)
        if group_limit_error:
            return group_limit_error
        group_limit = max(1, min(group_limit, 50))
        group_sample_limit, group_sample_limit_error = self._read_positive_param(p, "group_sample_limit", 3)
        if group_sample_limit_error:
            return group_sample_limit_error
        search_term = ""

        if context_raw:
            parsed_ctx = self._safe_eval_with_runtime(context_raw)
            if not isinstance(parsed_ctx, dict):
                return self._err(400, "context_raw 无效")
            ctx = {**ctx, **parsed_ctx}
            if group_by is None:
                group_by = self._normalize_group_by(parsed_ctx.get("group_by"))

        if group_by is not None:
            ctx = {**ctx, "group_by": group_by}

        if domain_raw:
            parsed_domain = self._safe_eval_with_runtime(domain_raw)
            if not isinstance(parsed_domain, list):
                return self._err(400, "domain_raw 无效")
            if not domain:
                domain = parsed_domain
            elif parsed_domain:
                # 同时存在 domain 与 domain_raw 时，按 AND 语义合并，确保快捷筛选生效。
                domain = parsed_domain + domain

        env_model = self.env[model].with_context(ctx)
        if sudo:
            env_model = env_model.sudo()

        # fields="*" ⇒ 所有字段
        if fields == ["*"] or fields == "*":
            fields = list(env_model._fields.keys())

        # 先按 groups 过滤一遍，避免 AccessError
        fields_safe = self._filter_readable_fields(env_model, fields or ["id", "name"])
        domain, search_term = self._apply_search_term_domain(env_model, domain, p, fields_safe)
        domain, project_scope_meta = self._apply_record_scope(env_model, domain, p, ctx)

        try:
            rows, order_error, python_order_applied = self._search_read_with_order(
                env_model,
                domain,
                fields_safe,
                order,
                limit,
                offset,
            )
            if order_error:
                return order_error
        except AccessError as ae:
            # 兜底：仍然被 field-level 权限阻断时，退回最小安全字段集
            _logger.warning("read() AccessError on %s, fallback to minimal fields. err=%s", model, ae)
            fallback_fields = ["id", "name", "display_name"] if "display_name" in env_model._fields else ["id", "name"]
            rows, order_error, python_order_applied = self._search_read_with_order(
                env_model,
                domain,
                fallback_fields,
                order,
                limit,
                offset,
            )
            if order_error:
                return order_error

        need_total = self._get_bool(p, "need_total", False)
        skip_default_total = bool(getattr(env_model, "_sc_skip_default_list_total", False))
        total = env_model.search_count(domain or []) if need_total and not skip_default_total else None
        need_aggregates = self._get_bool(p, "need_aggregates", False)
        aggregates = self._build_numeric_aggregates(env_model, domain, fields_safe) if need_aggregates else {}
        group_summary_probe = self._build_group_summary_with_offset(
            env_model,
            domain,
            group_by,
            limit=group_limit + 1,
            offset=group_offset,
        )
        group_has_more = len(group_summary_probe) > group_limit
        group_summary = group_summary_probe[:group_limit]
        group_total = self._count_group_total(env_model, domain, group_by) if need_group_total else None
        next_group_offset = (group_offset + len(group_summary)) if group_has_more else None
        prev_group_offset = max(0, group_offset - group_limit) if group_offset > 0 else None
        group_window_start = (group_offset + 1) if group_summary else 0
        group_window_end = (group_offset + len(group_summary)) if group_summary else 0
        group_window_span = max(0, group_window_end - group_window_start + 1) if group_summary else 0
        primary_group_field = self._primary_group_by_field(group_by)
        group_query_fingerprint = self._build_group_query_fingerprint(
            model,
            domain,
            group_by,
            order,
            search_term,
            ctx,
        )
        group_window_id = self._build_group_window_id(
            primary_group_field,
            group_offset,
            group_limit,
            group_query_fingerprint,
        )
        group_window_digest = self._build_group_window_digest(group_window_id, group_summary)
        group_window_identity_key = self._build_group_window_identity_key(group_window_id, group_window_digest)
        effective_page_size = min(group_page_size, 8)
        effective_page_size = effective_page_size if effective_page_size > 0 else min(group_sample_limit, 8)
        effective_page_size = max(1, int(effective_page_size or 1))
        group_window_identity = {
            "model": model,
            "group_by_field": primary_group_field or None,
            "window_id": group_window_id,
            "query_fingerprint": group_query_fingerprint,
            "window_digest": group_window_digest,
            "version": self.GROUP_WINDOW_IDENTITY_VERSION,
            "algo": self.GROUP_WINDOW_IDENTITY_ALGO,
            "key": group_window_identity_key,
            "window_empty": len(group_summary) <= 0,
            "window_start": group_window_start,
            "window_end": group_window_end,
            "window_span": group_window_span,
            "prev_group_offset": prev_group_offset,
            "next_group_offset": next_group_offset,
            "has_more": group_has_more,
            "group_offset": group_offset,
            "group_limit": group_limit,
            "group_count": len(group_summary),
            "page_size": effective_page_size,
            "has_group_page_offsets": bool(group_page_offsets),
        }
        if group_total is not None:
            group_window_identity["group_total"] = int(group_total)
        grouped_rows = self._build_grouped_rows(
            env_model,
            domain,
            group_by,
            fields_safe,
            limit=group_limit,
            sample_limit=min(group_sample_limit, 8),
            group_page_size=group_page_size if group_page_size > 0 else None,
            group_page_offsets=group_page_offsets,
            group_summary=group_summary,
            order=order,
        )

        data = {
            "records": rows,
            "next_offset": offset + len(rows),
            "group_summary": group_summary,
            "grouped_rows": grouped_rows,
            "group_paging": {
                "group_by_field": primary_group_field or None,
                "group_limit": group_limit,
                "group_offset": group_offset,
                "group_count": len(group_summary),
                "has_more": group_has_more,
                "next_group_offset": next_group_offset,
                "prev_group_offset": prev_group_offset,
                "window_start": group_window_start,
                "window_end": group_window_end,
                "window_id": group_window_id,
                "query_fingerprint": group_query_fingerprint,
                "window_digest": group_window_digest,
                "window_key": group_window_identity_key,
                "window_identity": group_window_identity,
                "page_size": effective_page_size,
                "has_group_page_offsets": bool(group_page_offsets),
            },
        }
        if group_total is not None and isinstance(data.get("group_paging"), dict):
            data["group_paging"]["group_total"] = int(group_total)
        if need_total:
            data["total"] = int(total or 0)
        if need_aggregates:
            data["aggregates"] = aggregates

        meta = {
            "op": "list",
            "model": model,
            "source_authority": self._source_authority_contract(model, "list"),
            "limit": limit,
            "offset": offset,
            "order": order,
            "python_order_applied": bool(python_order_applied),
            "count": len(rows),
            "aggregates": bool(aggregates),
            "fields": fields_safe,
            "domain_raw_applied": bool(domain_raw),
            "context_raw_applied": bool(context_raw),
            "group_by": group_by,
            "group_by_field": primary_group_field or None,
            "group_count": len(group_summary),
            "group_has_more": group_has_more,
            "next_group_offset": next_group_offset,
            "prev_group_offset": prev_group_offset,
            "group_window_start": group_window_start,
            "group_window_end": group_window_end,
            "group_window_id": group_window_id,
            "group_query_fingerprint": group_query_fingerprint,
            "group_window_digest": group_window_digest,
            "group_window_key": group_window_identity_key,
            "group_window_identity": group_window_identity,
            "need_group_total": need_group_total,
            "group_page_size": int(group_page_size or 0) or None,
            "group_limit": group_limit,
            "group_offset": group_offset,
            "project_scope": project_scope_meta,
            "record_scope": project_scope_meta,
        }
        if group_total is not None:
            meta["group_total"] = int(group_total)
        return data, meta

    def _op_read(self, model: str, p: Dict[str, Any], ctx: Dict[str, Any], sudo: bool):
        ids, ids_error = self._read_ids_param(p)
        if ids_error:
            return ids_error
        fields, fields_error = self._read_fields_param(p, ["id", "name"])
        if fields_error:
            return fields_error

        env_model = self.env[model].with_context(ctx)
        if sudo:
            env_model = env_model.sudo()

        fields_safe = self._filter_readable_fields(env_model, fields)
        scoped_error = self._ensure_records_in_record_scope(env_model, ids, p, ctx)
        if scoped_error:
            return scoped_error
        recs = env_model.browse(ids).exists()
        try:
            rows = recs.read(fields_safe or ["id", "name"])
        except AccessError as ae:
            _logger.warning("read() AccessError on %s(read), fallback. err=%s", model, ae)
            rows = recs.read(["id", "name", "display_name"] if "display_name" in env_model._fields else ["id", "name"])

        data = {"records": rows}
        _, project_scope_meta = self._apply_record_scope(env_model, [], p, ctx)
        meta = {
            "op": "read",
            "model": model,
            "source_authority": self._source_authority_contract(model, "read"),
            "count": len(rows),
            "fields": fields_safe,
            "project_scope": project_scope_meta,
            "record_scope": project_scope_meta,
        }
        return data, meta

    def _op_default_get(self, model: str, p: Dict[str, Any], ctx: Dict[str, Any], sudo: bool):
        fields, fields_error = self._read_fields_param(p, ["id", "name"])
        if fields_error:
            return fields_error

        env_model = self.env[model].with_context(ctx)
        if sudo:
            env_model = env_model.sudo()

        fields_safe = self._filter_readable_fields(env_model, fields)
        try:
            defaults = env_model.default_get([name for name in fields_safe if name != "id"]) or {}
        except AccessError as ae:
            _logger.warning("default_get() AccessError on %s, fallback. err=%s", model, ae)
            defaults = {}
        data = {"record": defaults}
        _, project_scope_meta = self._apply_record_scope(env_model, [], p, ctx)
        meta = {
            "op": "default_get",
            "model": model,
            "source_authority": self._source_authority_contract(model, "default_get"),
            "fields": fields_safe,
            "project_scope": project_scope_meta,
            "record_scope": project_scope_meta,
        }
        return data, meta

    def _op_count(self, model: str, p: Dict[str, Any], ctx: Dict[str, Any], sudo: bool):
        domain, domain_error = self._read_domain_param(p)
        if domain_error:
            return domain_error
        env_model = self.env[model].with_context(ctx)
        if sudo:
            env_model = env_model.sudo()
        fields_safe = self._filter_readable_fields(env_model, ["id", "name"])
        domain, search_term = self._apply_search_term_domain(env_model, domain, p, fields_safe)
        domain, project_scope_meta = self._apply_record_scope(env_model, domain, p, ctx)

        total = env_model.search_count(domain or [])
        data = {"total": int(total or 0)}
        meta = {
            "op": "count",
            "model": model,
            "source_authority": self._source_authority_contract(model, "count"),
            "project_scope": project_scope_meta,
            "record_scope": project_scope_meta,
        }
        if search_term:
            meta["search_term_applied"] = True
        return data, meta

    def _op_create(self, model: str, p: Dict[str, Any], ctx: Dict[str, Any], sudo: bool):
        vals = self._dig(p, "vals") or self._dig(p, "values") or {}
        if not isinstance(vals, dict) or not vals:
            return self._err(400, "缺少参数 vals")

        denied = self._check_mutation_policy(model, "create")
        if denied:
            return denied

        create_policy = self._create_execution_policy(model, vals, ctx, p)
        if create_policy.get("allowed") is False:
            return self._err(
                int(create_policy.get("code") or 403),
                str(create_policy.get("message") or "当前数据不允许创建。"),
                reason_code=str(create_policy.get("reason_code") or "CREATE_POLICY_DENIED"),
            )
        if create_policy.get("sudo") and not sudo:
            sudo = True

        env_model = self.env[model].with_context(ctx)
        if sudo:
            env_model = env_model.sudo()

        # 过滤非法字段并补齐后端默认值，避免交付表单必须暴露技术字段
        safe_vals = self._prepare_create_vals(env_model, vals)
        if not safe_vals:
            return self._err(400, "vals 中无可写字段")
        create_policy = self._create_execution_policy(model, safe_vals, ctx, p)
        if create_policy.get("allowed") is False:
            return self._err(
                int(create_policy.get("code") or 403),
                str(create_policy.get("message") or "当前数据不允许创建。"),
                reason_code=str(create_policy.get("reason_code") or "CREATE_POLICY_DENIED"),
            )
        if create_policy.get("sudo") and not sudo:
            env_model = env_model.sudo()
            safe_vals = self._prepare_create_vals(env_model, vals)
            if not safe_vals:
                return self._err(400, "vals 中无可写字段")
        project_id = self._current_project_id(p, ctx)
        _, project_scope_meta = self._apply_record_scope(env_model, [], p, ctx)
        if project_scope_meta.get("project_operation_strategy_mismatch"):
            return self._record_scope_denied("当前记录上下文与经营方式不一致，禁止创建业务数据", project_scope_meta)
        scope_company_id = int(project_scope_meta.get("company_id") or 0)
        if scope_company_id and "company_id" in env_model._fields:
            incoming_company_id = safe_vals.get("company_id")
            if incoming_company_id in (None, False, ""):
                safe_vals["company_id"] = scope_company_id
            else:
                try:
                    incoming_company_id = int(incoming_company_id or 0)
                except Exception:
                    incoming_company_id = 0
                if incoming_company_id != scope_company_id:
                    return self._record_scope_denied("当前公司上下文不允许创建到其他公司", project_scope_meta)
        scope_operation_strategy = str(project_scope_meta.get("operation_strategy") or "").strip()
        operation_field = env_model._fields.get("operation_strategy")
        if (
            scope_operation_strategy
            and operation_field
            and not getattr(operation_field, "related", None)
        ):
            incoming_operation_strategy = str(safe_vals.get("operation_strategy") or "").strip()
            if not incoming_operation_strategy:
                safe_vals["operation_strategy"] = scope_operation_strategy
            elif incoming_operation_strategy != scope_operation_strategy:
                return self._record_scope_denied("当前经营方式上下文不允许创建到其他经营方式", project_scope_meta)
        if project_scope_meta.get("project_id") and "project_id" in env_model._fields:
            incoming_project_id = safe_vals.get("project_id")
            if incoming_project_id in (None, False, ""):
                safe_vals["project_id"] = project_id
            else:
                try:
                    incoming_project_id = int(incoming_project_id or 0)
                except Exception:
                    incoming_project_id = 0
                if incoming_project_id != int(project_id or 0):
                    return self._record_scope_denied("当前记录上下文不允许创建到其他记录", project_scope_meta)

        try:
            rec = env_model.create(safe_vals)
        except AccessError as ae:
            _logger.warning("create AccessError on %s: %s", model, ae)
            return self._err(403, "无创建权限")
        except Exception as e:
            column = self._extract_not_null_column(e)
            if column and safe_vals.get(column) in (None, ""):
                retry_vals = dict(safe_vals)
                changed = self._fill_not_null_column_fallback(env_model, retry_vals, column)
                if changed:
                    try:
                        rec = env_model.create(retry_vals)
                        safe_vals = retry_vals
                    except Exception:
                        _logger.exception("create failed on %s (retry column=%s)", model, column)
                        return self._err(500, self._friendly_create_error(e))
                else:
                    _logger.exception("create failed on %s (unresolved column=%s)", model, column)
                    return self._err(500, self._friendly_create_error(e))
            else:
                _logger.exception("create failed on %s", model)
                return self._err(500, self._friendly_create_error(e))

        data = {"id": rec.id}
        meta = {
            "op": "create",
            "model": model,
            "source_authority": self._source_authority_contract(model, "create"),
            "id": rec.id,
            "project_scope": project_scope_meta,
            "record_scope": project_scope_meta,
        }
        return data, meta

    def _op_write(self, model: str, p: Dict[str, Any], ctx: Dict[str, Any], sudo: bool):
        ids, ids_error = self._read_ids_param(p)
        if ids_error:
            return ids_error
        vals = self._dig(p, "vals") or self._dig(p, "values") or {}
        if_match = self._read_if_match(p)
        if not isinstance(vals, dict) or not vals:
            return self._err(400, "缺少参数 vals")

        denied = self._check_mutation_policy(model, "write")
        if denied:
            return denied

        env_model = self.env[model].with_context(ctx)
        if sudo:
            env_model = env_model.sudo()
        scoped_error = self._ensure_records_in_record_scope(env_model, ids, p, ctx)
        if scoped_error:
            return scoped_error
        project_id = self._current_project_id(p, ctx)
        _, project_scope_meta = self._apply_record_scope(env_model, [], p, ctx)
        if project_scope_meta.get("project_id") and "project_id" in env_model._fields and "project_id" in vals:
            try:
                incoming_project_id = int(vals.get("project_id") or 0)
            except Exception:
                incoming_project_id = 0
            if incoming_project_id and incoming_project_id != int(project_id or 0):
                return self._record_scope_denied("当前记录上下文不允许移动到其他记录", project_scope_meta)

        recs = env_model.browse(ids).exists()
        if not recs:
            return self._err(404, "记录不存在")

        safe_vals = self._prepare_write_vals(env_model, recs, vals)
        if not safe_vals:
            return self._err(400, "vals 中无可写字段")

        try:
            if if_match and len(recs) == 1 and "write_date" in env_model._fields:
                current = self._format_write_date(recs.write_date)
                if current and current != if_match:
                    return self._err(
                        409,
                        "数据已被其他操作更新，请重新加载后再保存。",
                        reason_code=REASON_RECORD_VERSION_CONFLICT,
                    )
            recs.write(safe_vals)
        except AccessError as ae:
            _logger.warning("write AccessError on %s: %s", model, ae)
            return self._err(403, "无写入权限")
        except Exception as e:
            _logger.exception("write failed on %s", model)
            return self._err(500, str(e))

        data = {"ids": recs.ids}
        if len(recs) == 1 and "write_date" in env_model._fields:
            data["record_version"] = self._format_write_date(recs.write_date)
        meta = {
            "op": "write",
            "model": model,
            "source_authority": self._source_authority_contract(model, "write"),
            "count": len(recs),
            "project_scope": project_scope_meta,
            "record_scope": project_scope_meta,
        }
        return data, meta

    def _format_csv_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            if len(value) == 2 and isinstance(value[1], str):
                return value[1]
            return ",".join(str(v) for v in value)
        if isinstance(value, dict):
            try:
                return str(value)
            except Exception:
                return ""
        return str(value)

    def _op_export_csv(self, model: str, p: Dict[str, Any], ctx: Dict[str, Any], sudo: bool):
        limit, limit_error = self._read_positive_param(p, "limit", 2000)
        if limit_error:
            return limit_error
        limit = min(limit, 10000)

        order = self._get_str(p, "order", "")
        domain, domain_error = self._read_domain_param(p)
        if domain_error:
            return domain_error
        raw_ids = self._dig(p, "ids", None)
        if raw_ids is None or (isinstance(raw_ids, str) and not raw_ids.strip()):
            ids = []
        else:
            ids, ids_error = self._read_ids_param(p)
            if ids_error:
                return ids_error
        fields, fields_error = self._read_fields_param(p, [])
        if fields_error:
            return fields_error

        env_model = self.env[model].with_context(ctx)
        if sudo:
            env_model = env_model.sudo()

        if fields == ["*"] or fields == "*":
            fields = list(env_model._fields.keys())
        if not fields:
            fallback = ["id", "name"] if "name" in env_model._fields else ["id"]
            fields = fallback
        fields_safe = self._filter_readable_fields(env_model, fields)

        if ids:
            scoped_error = self._ensure_records_in_record_scope(env_model, ids, p, ctx)
            if scoped_error:
                return scoped_error
            _, project_scope_meta = self._apply_record_scope(env_model, [], p, ctx)
            recs = env_model.browse(ids).exists()
        else:
            domain, _search_term = self._apply_search_term_domain(env_model, domain, p, fields_safe)
            domain, project_scope_meta = self._apply_record_scope(env_model, domain, p, ctx)
            recs = env_model.search(domain or [], order=order or None, limit=limit)
        if not recs:
            data = {
                "file_name": f"{model.replace('.', '_')}_empty.csv",
                "mime_type": "text/csv",
                "content_b64": "",
                "count": 0,
                "fields": fields_safe,
            }
            meta = {
                "op": "export_csv",
                "model": model,
                "source_authority": self._source_authority_contract(model, "export_csv"),
                "count": 0,
                "project_scope": project_scope_meta,
                "record_scope": project_scope_meta,
            }
            return data, meta

        try:
            rows = recs.read(fields_safe)
        except AccessError as ae:
            _logger.warning("export_csv AccessError on %s, fallback fields. err=%s", model, ae)
            safe_min = ["id", "name"] if "name" in env_model._fields else ["id"]
            fields_safe = self._filter_readable_fields(env_model, safe_min)
            rows = recs.read(fields_safe)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(fields_safe)
        for row in rows:
            writer.writerow([self._format_csv_value(row.get(col)) for col in fields_safe])
        raw = buf.getvalue().encode("utf-8-sig")
        b64 = base64.b64encode(raw).decode("ascii")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        data = {
            "file_name": f"{model.replace('.', '_')}_{stamp}.csv",
            "mime_type": "text/csv",
            "content_b64": b64,
            "count": len(rows),
            "fields": fields_safe,
        }
        meta = {
            "op": "export_csv",
            "model": model,
            "source_authority": self._source_authority_contract(model, "export_csv"),
            "count": len(rows),
            "limit": limit,
            "project_scope": project_scope_meta,
            "record_scope": project_scope_meta,
        }
        return data, meta
