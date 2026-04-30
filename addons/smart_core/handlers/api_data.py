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
from datetime import datetime
from urllib.parse import unquote

from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import AccessError
from odoo.http import request

from ..core.base_handler import BaseIntentHandler
from ..utils.extension_hooks import call_extension_hook_first

_logger = logging.getLogger(__name__)
_NOT_NULL_COLUMN_RE = re.compile(r'null value in column "([^"]+)"', re.IGNORECASE)
_UNIQUE_VIOLATION_RE = re.compile(r"(duplicate key value|unique constraint|already exists)", re.IGNORECASE)


def _json(o):
    return json.dumps(o, ensure_ascii=False, default=str, separators=(",", ":"))


class ApiDataHandler(BaseIntentHandler):
    INTENT_TYPE = "api.data"
    DESCRIPTION = "通用数据读取：list/read/count（P0 可用版）"
    VERSION = "2.1.1"
    ETAG_ENABLED = False  # 列表不缓存，避免错判
    GROUP_WINDOW_IDENTITY_VERSION = "v1"
    GROUP_WINDOW_IDENTITY_ALGO = "sha1"

    # ----------------- 通用取参 -----------------

    def _err(self, code: int, message: str):
        return {"ok": False, "error": {"code": code, "message": message}}

    def _read_if_none_match(self, p: Dict[str, Any]) -> str:
        if_none_match = str(self._dig(p, "if_none_match", "") or "").strip().strip('"')
        if if_none_match:
            return if_none_match
        try:
            return str((request.httprequest.headers.get("If-None-Match") or "")).strip().strip('"')
        except Exception:
            return ""

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

    def _normalize_group_page_offsets(self, val) -> Dict[str, int]:
        out: Dict[str, int] = {}
        if isinstance(val, dict):
            for raw_key, raw_offset in val.items():
                key = str(raw_key or "").strip()
                if not key:
                    continue
                try:
                    offset = int(raw_offset)
                except Exception:
                    continue
                if offset < 0:
                    continue
                out[key] = offset
            return out
        if isinstance(val, str):
            text = val.strip()
            if not text:
                return out
            # 兼容 route 风格: k1:0;k2:3（key 可能经过 encodeURIComponent）
            for pair in text.split(";"):
                if ":" not in pair:
                    continue
                raw_key, raw_offset = pair.split(":", 1)
                key = unquote(str(raw_key or "").strip())
                if not key:
                    continue
                try:
                    offset = int(raw_offset)
                except Exception:
                    continue
                if offset < 0:
                    continue
                out[key] = offset
        return out

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
                group_recs = env_model.search(group_domain, limit=page_limit, offset=page_offset)
                sample_rows = group_recs.read(row_fields)
            except Exception:
                _logger.exception("group sample query failed model=%s group=%s", env_model._name, item.get("label"))
                sample_rows = []
            out.append(
                {
                    "group_key": group_key,
                    "field": item.get("field"),
                    "value": item.get("value"),
                    "label": item.get("label"),
                    "count": item.get("count"),
                    "domain": group_domain,
                    "sample_rows": sample_rows,
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
        runtime_env = {
            "uid": int(getattr(self.env, "uid", 0) or 0),
            "user": self.env.user,
            "context_today": lambda: datetime.now().date(),
            "datetime": datetime,
        }
        try:
            return safe_eval(text, runtime_env)
        except Exception:
            return None

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

    # ----------------- 主处理 -----------------

    def handle(self, **kwargs) -> Tuple[Dict[str, Any], Dict[str, Any]] | Dict[str, Any]:
        p = self._collect_params(kwargs)

        try:
            _logger.info("[api.data] keys=%s payload.keys=%s params.keys=%s",
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

        context = self._dig(p, "context") or {}
        if not isinstance(context, dict):
            context = {}
        if "active_test" not in context:
            context["active_test"] = self._get_bool(p, "active_test", True)
        if_none_match = self._read_if_none_match(p)

        use_sudo = self._get_bool(p, "sudo", False)

        if op == "list":
            return self._with_etag_if_match(self._op_list(model, p, context, use_sudo), model, op, context, if_none_match)
        elif op == "read":
            return self._with_etag_if_match(self._op_read(model, p, context, use_sudo), model, op, context, if_none_match)
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
        fields = self._get_list(p, "fields", [])
        limit = self._get_int(p, "limit", 40)
        offset = self._get_int(p, "offset", 0)
        order = self._get_str(p, "order", "")
        domain = self._normalize_domain(self._dig(p, "domain"))
        domain_raw = self._get_str(p, "domain_raw", "").strip()
        context_raw = self._get_str(p, "context_raw", "").strip()
        group_by = self._normalize_group_by(self._dig(p, "group_by"))
        group_page_offsets = self._normalize_group_page_offsets(self._dig(p, "group_page_offsets"))
        group_offset = max(0, self._get_int(p, "group_offset", 0))
        need_group_total = self._get_bool(p, "need_group_total", False)
        group_page_size = min(self._get_int(p, "group_page_size", 0), 8)
        default_group_limit = min(limit or 20, 30)
        group_limit = self._get_int(p, "group_limit", default_group_limit)
        group_limit = max(1, min(group_limit, 50))
        search_term = self._get_str(p, "search_term", "").strip()

        if context_raw:
            parsed_ctx = self._safe_eval_with_runtime(context_raw)
            if isinstance(parsed_ctx, dict):
                ctx = {**ctx, **parsed_ctx}
                if group_by is None:
                    group_by = self._normalize_group_by(parsed_ctx.get("group_by"))

        if group_by is not None:
            ctx = {**ctx, "group_by": group_by}

        if domain_raw:
            parsed_domain = self._safe_eval_with_runtime(domain_raw)
            if isinstance(parsed_domain, list):
                if not domain:
                    domain = parsed_domain
                elif parsed_domain:
                    # 同时存在 domain 与 domain_raw 时，按 AND 语义合并，确保快捷筛选生效。
                    domain = parsed_domain + domain

        if search_term:
            try:
                search_id = int(search_term)
            except Exception:
                search_id = None
            if search_id is not None:
                domain = domain + ["|", ("name", "ilike", search_term), ("id", "=", search_id)]
            else:
                domain = domain + [("name", "ilike", search_term)]

        env_model = self.env[model].with_context(ctx)
        if sudo:
            env_model = env_model.sudo()

        # fields="*" ⇒ 所有字段
        if fields == ["*"] or fields == "*":
            fields = list(env_model._fields.keys())

        # 先按 groups 过滤一遍，避免 AccessError
        fields_safe = self._filter_readable_fields(env_model, fields or ["id", "name"])

        recs = env_model.search(domain or [], order=order or None, limit=limit or None, offset=offset or 0)
        try:
            rows: List[Dict[str, Any]] = recs.read(fields_safe or ["id", "name"])
        except AccessError as ae:
            # 兜底：仍然被 field-level 权限阻断时，退回最小安全字段集
            _logger.warning("read() AccessError on %s, fallback to minimal fields. err=%s", model, ae)
            rows = recs.read(["id", "name", "display_name"] if "display_name" in env_model._fields else ["id", "name"])

        need_total = self._get_bool(p, "need_total", False)
        total = env_model.search_count(domain or []) if need_total else None
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
        effective_page_size = min(self._get_int(p, "group_page_size", 0), 8)
        effective_page_size = effective_page_size if effective_page_size > 0 else min(self._get_int(p, "group_sample_limit", 3), 8)
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
            sample_limit=min(self._get_int(p, "group_sample_limit", 3), 8),
            group_page_size=group_page_size if group_page_size > 0 else None,
            group_page_offsets=group_page_offsets,
            group_summary=group_summary,
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

        meta = {
            "op": "list",
            "model": model,
            "limit": limit,
            "offset": offset,
            "order": order,
            "count": len(rows),
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
        }
        if group_total is not None:
            meta["group_total"] = int(group_total)
        return data, meta

    def _op_read(self, model: str, p: Dict[str, Any], ctx: Dict[str, Any], sudo: bool):
        ids = self._get_list(p, "ids", [])
        if not ids:
            return self._err(400, "缺少参数 ids")
        fields = self._get_list(p, "fields", ["id", "name"])

        env_model = self.env[model].with_context(ctx)
        if sudo:
            env_model = env_model.sudo()

        fields_safe = self._filter_readable_fields(env_model, fields)
        recs = env_model.browse(ids).exists()
        try:
            rows = recs.read(fields_safe or ["id", "name"])
        except AccessError as ae:
            _logger.warning("read() AccessError on %s(read), fallback. err=%s", model, ae)
            rows = recs.read(["id", "name", "display_name"] if "display_name" in env_model._fields else ["id", "name"])

        data = {"records": rows}
        meta = {"op": "read", "model": model, "count": len(rows), "fields": fields_safe}
        return data, meta

    def _op_count(self, model: str, p: Dict[str, Any], ctx: Dict[str, Any], sudo: bool):
        domain = self._normalize_domain(self._dig(p, "domain"))
        env_model = self.env[model].with_context(ctx)
        if sudo:
            env_model = env_model.sudo()

        total = env_model.search_count(domain or [])
        data = {"total": int(total or 0)}
        meta = {"op": "count", "model": model}
        return data, meta

    def _op_create(self, model: str, p: Dict[str, Any], ctx: Dict[str, Any], sudo: bool):
        vals = self._dig(p, "vals") or self._dig(p, "values") or {}
        if not isinstance(vals, dict) or not vals:
            return self._err(400, "缺少参数 vals")

        env_model = self.env[model].with_context(ctx)
        if sudo:
            env_model = env_model.sudo()

        # 过滤非法字段并补齐后端默认值，避免交付表单必须暴露技术字段
        safe_vals = self._prepare_create_vals(env_model, vals)
        if not safe_vals:
            return self._err(400, "vals 中无可写字段")

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
        meta = {"op": "create", "model": model, "id": rec.id}
        return data, meta

    def _op_write(self, model: str, p: Dict[str, Any], ctx: Dict[str, Any], sudo: bool):
        ids = self._get_list(p, "ids", [])
        vals = self._dig(p, "vals") or self._dig(p, "values") or {}
        if not ids:
            return self._err(400, "缺少参数 ids")
        if not isinstance(vals, dict) or not vals:
            return self._err(400, "缺少参数 vals")

        env_model = self.env[model].with_context(ctx)
        if sudo:
            env_model = env_model.sudo()

        recs = env_model.browse(ids).exists()
        if not recs:
            return self._err(404, "记录不存在")

        safe_vals = {k: v for k, v in vals.items() if k in env_model._fields}
        if not safe_vals:
            return self._err(400, "vals 中无可写字段")

        try:
            recs.write(safe_vals)
        except AccessError as ae:
            _logger.warning("write AccessError on %s: %s", model, ae)
            return self._err(403, "无写入权限")
        except Exception as e:
            _logger.exception("write failed on %s", model)
            return self._err(500, str(e))

        data = {"ids": recs.ids}
        meta = {"op": "write", "model": model, "count": len(recs)}
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
        limit = self._get_int(p, "limit", 2000)
        if limit <= 0:
            limit = 2000
        limit = min(limit, 10000)

        order = self._get_str(p, "order", "")
        domain = self._normalize_domain(self._dig(p, "domain"))
        ids = self._get_list(p, "ids", [])
        fields = self._get_list(p, "fields", [])

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
            recs = env_model.browse(ids).exists()
        else:
            recs = env_model.search(domain or [], order=order or None, limit=limit)
        if not recs:
            data = {
                "file_name": f"{model.replace('.', '_')}_empty.csv",
                "mime_type": "text/csv",
                "content_b64": "",
                "count": 0,
                "fields": fields_safe,
            }
            meta = {"op": "export_csv", "model": model, "count": 0}
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
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        data = {
            "file_name": f"{model.replace('.', '_')}_{stamp}.csv",
            "mime_type": "text/csv",
            "content_b64": b64,
            "count": len(rows),
            "fields": fields_safe,
        }
        meta = {"op": "export_csv", "model": model, "count": len(rows), "limit": limit}
        return data, meta
