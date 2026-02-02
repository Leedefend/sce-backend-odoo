# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/api_data.py
# 统一数据读取意图（P0）：list / read / count
# - list:  search + read（支持分页/排序/fields="*"）
# - read:  read(ids)
# - count: search_count

import logging
from typing import Any, Dict, Tuple, List, Optional
from ast import literal_eval

from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler

_logger = logging.getLogger(__name__)


class ApiDataHandler(BaseIntentHandler):
    INTENT_TYPE = "api.data"
    DESCRIPTION = "通用数据读取：list/read/count（P0 可用版）"
    VERSION = "2.1.1"
    ETAG_ENABLED = False  # 列表不缓存，避免错判

    # ----------------- 通用取参 -----------------

    def _err(self, code: int, message: str):
        return {"ok": False, "error": {"code": code, "message": message}}

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
            context["active_test"] = self._get_bool(p, "active_test", False)

        use_sudo = self._get_bool(p, "sudo", False)

        if op == "list":
            return self._op_list(model, p, context, use_sudo)
        elif op == "read":
            return self._op_read(model, p, context, use_sudo)
        elif op in ("count", "search_count"):
            return self._op_count(model, p, context, use_sudo)
        elif op in ("create",):
            return self._op_create(model, p, context, use_sudo)
        elif op in ("write",):
            return self._op_write(model, p, context, use_sudo)
        else:
            return self._err(400, f"不支持的操作: {op}")

    # ----------------- 操作实现 -----------------

    def _op_list(self, model: str, p: Dict[str, Any], ctx: Dict[str, Any], sudo: bool):
        fields = self._get_list(p, "fields", [])
        limit = self._get_int(p, "limit", 40)
        offset = self._get_int(p, "offset", 0)
        order = self._get_str(p, "order", "")
        domain = self._normalize_domain(self._dig(p, "domain"))

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

        data = {
            "records": rows,
            "next_offset": offset + len(rows),
        }
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
        }
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

        # 过滤非法字段，避免写入不存在字段
        safe_vals = {k: v for k, v in vals.items() if k in env_model._fields}
        if not safe_vals:
            return self._err(400, "vals 中无可写字段")

        try:
            rec = env_model.create(safe_vals)
        except AccessError as ae:
            _logger.warning("create AccessError on %s: %s", model, ae)
            return self._err(403, "无创建权限")
        except Exception as e:
            _logger.exception("create failed on %s", model)
            return self._err(500, str(e))

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
