# smart_core/controllers/intent_dispatcher.py
# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import logging, time
import os
from typing import Dict, Any

from werkzeug.exceptions import Unauthorized, Forbidden, BadRequest, NotFound
from odoo.exceptions import AccessError, MissingError, AccessDenied

from ..core.intent_router import route_intent_payload
from ..core.context import RequestContext
from ..security.intent_permission import check_intent_permission
from ..core.trace import get_trace_id
from ..core.exceptions import (
    BAD_REQUEST,
    AUTH_REQUIRED,
    PERMISSION_DENIED,
    INTENT_NOT_FOUND,
    INTERNAL_ERROR,
    map_http_status_to_code,
    build_error_envelope,
)

_logger = logging.getLogger(__name__)

# ✅ 匿名白名单（仅在“匿名请求”识别为真时生效；见 _is_anon_req）
ANON_ALLOWLIST = {"login", "auth.login", "sys.intents", "session.bootstrap"}

# ✅ 意图别名：统一规范后再做白名单与分发
INTENT_ALIASES = {
    "bootstrap": "session.bootstrap",
    "app.init": "system.init",
    "system.init": "system.init",
    "auth.login": "login",
}

API_VERSION = "v1"
CONTRACT_VERSION = "v0.1"

def _canon_intent(name: str) -> str:
    return INTENT_ALIASES.get(name or "", name or "")

# ===================== CORS 工具 =====================

def _cors_headers() -> Dict[str, str]:
    """
    统一 CORS 响应头：
    - 有 Origin：回显 Origin，并允许凭据（Cookie/Authorization）
    - 无 Origin（同源调用）：允许 '*'
    """
    origin = request.httprequest.headers.get("Origin")
    allow_origin = origin or "*"
    headers = {
        "Access-Control-Allow-Origin": allow_origin,
        "Vary": "Origin",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": (
            "Content-Type, Authorization, X-Odoo-DB, X-DB, X-Anonymous-Intent, "
            "X-Trace-Id, X-Tenant, If-None-Match, If-Match, Accept, X-Requested-With"
        ),
        "Access-Control-Expose-Headers": "ETag",
        "Access-Control-Max-Age": "86400",
    }
    # 有 Origin 才允许凭据（与 * 互斥）
    if origin:
        headers["Access-Control-Allow-Credentials"] = "true"
    return headers


def _respond_json(payload: Any, *, status: int = 200):
    """统一 JSON 返回（所有分支必须走这里保证带 CORS 头）"""
    return request.make_json_response(payload, status=status, headers=_cors_headers())


def _respond_empty(*, status: int = 204, trace_id: str | None = None):
    """统一空返回（预检/304 等）"""
    resp = request.make_response("", status=status)
    resp.headers.update(_cors_headers())
    if trace_id:
        resp.headers["X-Trace-Id"] = trace_id
    return resp


def _is_response(obj: Any) -> bool:
    """鸭子类型判断是否为 Response 对象"""
    return hasattr(obj, "headers") and hasattr(obj, "status_code") and hasattr(obj, "get_data")


def _is_anon_req(headers) -> bool:
    """宽松识别匿名意图触发标记"""
    v = (headers.get("X-Anonymous-Intent") or "").strip().lower()
    return v in {"1", "true", "yes", "on"}

def _error_response(code: str, message: str, status: int, trace_id: str, details: dict | None = None):
    payload = build_error_envelope(
        code=code,
        message=message,
        trace_id=trace_id,
        details=details,
        api_version=API_VERSION,
        contract_version=CONTRACT_VERSION,
    )
    resp = _respond_json(payload, status=status)
    resp.headers["X-Trace-Id"] = trace_id
    return resp

# ===================== 结果归一化 =====================

def _normalize_result_shape(res: Any) -> Dict[str, Any]:
    """
    归一化 handler 返回：
    - (data, meta|code)：
        * 若第二项为 int → 视为 HTTP code
        * 若第二项为 dict → 视为 meta（其中的 code 会被提取到顶层）
    - 仅 data 且包含 token/user/system → {"ok": True, "data": res, "meta": {}}
    - dict 但未含 ok/data/meta → 自动补齐
    - 其他类型 → {"ok": True, "data": {"raw": res}, "meta": {}}
    - 若是 Response 对象 → {"__response__": res}（上层直接透传并补 CORS）
    """
    if _is_response(res):
        return {"__response__": res}

    if isinstance(res, (list, tuple)):
        if len(res) == 2 and isinstance(res[0], dict):
            data, second = res
            code = None
            meta = {}
            if isinstance(second, int):
                code = second
            elif isinstance(second, dict):
                meta = second or {}
                if isinstance(meta.get("code"), int):
                    code = meta["code"]
            out = {"ok": True, "data": data or {}, "meta": meta}
            if code is not None:
                out["code"] = code
            return out
        return {"ok": True, "data": {"raw": res}, "meta": {}}

    if isinstance(res, dict):
        # 某些 Handler 会直接返回 {"token":...,"user":...}
        if "data" not in res and ("token" in res or "user" in res or "system" in res):
            return {"ok": True, "data": res, "meta": {}}
        out = dict(res)
        out.setdefault("ok", True)
        out.setdefault("data", {})
        out.setdefault("meta", {})
        return out

    return {"ok": True, "data": {"raw": res}, "meta": {}}


# ===================== 控制器 =====================

class IntentDispatcher(http.Controller):

    @http.route('/api/v1/intent', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False)
    def handle_intent(self, **kwargs):
        ts0 = time.time()
        headers = request.httprequest.headers
        trace_id = get_trace_id(headers)
        intent_name = None  # 便于异常日志打印

        try:
            _logger.info(
                "[intent] controller=%s module=%s trace=%s",
                self.__class__.__name__,
                self.__class__.__module__,
                trace_id,
            )
            # ---------- 预检短路 ----------
            if request.httprequest.method == "OPTIONS":
                return _respond_empty(status=204, trace_id=trace_id)

            # ---------- 读取并归一请求体 ----------
            body = request.httprequest.get_json(force=True, silent=True) or {}
            if not isinstance(body, dict):
                body = {}

            # 统一/规范化意图名
            intent_name_in = (body.get("intent") or "").strip()
            intent_name = _canon_intent(intent_name_in)
            if not intent_name:
                return _error_response(BAD_REQUEST, "缺少 intent 参数", 400, trace_id)

            # 兼容 params/payload
            params = body.get("params")
            params = params if isinstance(params, dict) else {}
            if not params and isinstance(body.get("payload"), dict):
                params = body.get("payload")

            # 仅接收 dict 的 context
            context_in: Dict[str, Any] = body.get("context") if isinstance(body.get("context"), dict) else {}

            # 兼容：旧 context 里可能混入业务字段，不覆盖 params 显式给出的
            for k in ("db", "database", "login", "username", "password", "lang", "tz", "company_id"):
                if k in context_in and k not in params:
                    params[k] = context_in[k]

            # 修复 Header 传 DB 但后端不读的问题：统一 DB 解析优先级 + 安全边界
            hdr = request.httprequest.headers
            x_db_hdr = hdr.get("X-Odoo-DB") or hdr.get("X-DB")

            def _is_local_request() -> bool:
                try:
                    remote = request.httprequest.remote_addr or ""
                    host = request.httprequest.host or ""
                except Exception:
                    return False
                if remote in {"127.0.0.1", "::1"}:
                    return True
                return "localhost" in host or "127.0.0.1" in host

            def _env_is_dev() -> bool:
                env = (os.environ.get("ENV") or "").lower()
                if env in {"dev", "test", "local"}:
                    return True
                # 未设置 ENV 时，允许本地请求作为 DEV
                if not env and _is_local_request():
                    return True
                return False

            def _user_is_admin() -> bool:
                try:
                    return request.env.user.has_group("base.group_system")
                except Exception:
                    return False

            def _default_db() -> str | None:
                if request.session.db:
                    return request.session.db
                if hasattr(request.env, "cr") and request.env.cr:
                    return request.env.cr.dbname
                return None

            # DB 解析优先级: params > query > header > session > env
            effective_db = None
            db_source = "unknown"

            if params.get("db"):
                effective_db = params.get("db")
                db_source = "params"
            elif kwargs.get("db"):
                effective_db = kwargs.get("db")
                db_source = "query"
            elif x_db_hdr:
                effective_db = x_db_hdr
                db_source = "header"
            elif request.session.db:
                effective_db = request.session.db
                db_source = "session"

            # 非 DEV 且非管理员：禁止通过 params/query/header 覆盖 DB
            if effective_db and db_source in {"params", "query", "header"} and not _env_is_dev() and not _user_is_admin():
                _logger.warning("Blocked db override from %s in non-dev env", db_source)
                effective_db = _default_db()
                db_source = "session" if request.session.db else "env_default"

            if not effective_db:
                effective_db = _default_db()
                db_source = "session" if request.session.db else "env_default"

            if effective_db:
                params["db"] = params.get("db") or effective_db
                if request.session.db != effective_db:
                    request.session.db = effective_db

            is_anon = _is_anon_req(hdr) or intent_name == "session.bootstrap"

            # 统一 payload 下发给路由
            payload = {
                "intent": intent_name,
                "params": params,
                "context": context_in,
                "meta": body.get("meta") or {}
            }

            # ---------- 统一上下文 ----------
            ctx = RequestContext.from_http_request()
            setattr(ctx, "trace_id", trace_id)
            setattr(ctx, "is_anonymous", is_anon)
            setattr(ctx, "db", params.get("db"))
            # 将 trace_id 透传给 handler
            context_in["trace_id"] = trace_id

            _logger.info(
                "[intent] trace=%s intent=%s anon=%s db=%s params.keys=%s",
                trace_id, intent_name, is_anon, params.get("db"),
                ",".join(sorted(params.keys())) if params else "-"
            )

            # ---------- 权限校验 ----------
            skip_auth = is_anon and intent_name in ANON_ALLOWLIST
            if intent_name == "session.bootstrap":
                skip_auth = True
            if not skip_auth:
                check_intent_permission(ctx)

            # ---------- 分发（关键：传递正确的 ctx） ----------
            raw_result = route_intent_payload(payload, ctx=ctx)

            # Handler 若直接返回 Response：补 CORS 后原样返回
            if _is_response(raw_result):
                resp = raw_result
                resp.headers.update(_cors_headers())
                return resp

            result = _normalize_result_shape(raw_result)

            # Backward-compat: legacy load_view handlers may return view payload at top-level
            if intent_name == "load_view" and isinstance(result, dict):
                data = result.get("data")
                if not data and any(k in result for k in ("layout", "view_type", "model", "permissions", "fields")):
                    legacy_data = {
                        k: result.pop(k)
                        for k in list(result.keys())
                        if k not in {"ok", "data", "meta", "code", "error", "status"}
                    }
                    result["data"] = legacy_data

            # ---------- 统一响应（含 CORS/ETag/304） ----------
            status = 200
            headers = _cors_headers()
            headers["X-Trace-Id"] = trace_id

            if isinstance(result, dict):
                status = int(result.get("code", 200)) if isinstance(result.get("code"), (int, str)) else 200
                etag = (result.get("meta") or {}).get("etag")
                if etag:
                    headers["ETag"] = f'"{etag}"'

                meta = result.setdefault("meta", {})
                meta.setdefault("trace_id", trace_id)
                meta.setdefault("intent", intent_name)
                meta.setdefault("elapsed_ms", int((time.time() - ts0) * 1000))
                meta.setdefault("api_version", API_VERSION)
                meta.setdefault("contract_version", CONTRACT_VERSION)

                # 标准化错误结构
                if result.get("ok") is False:
                    err = result.get("error") if isinstance(result.get("error"), dict) else {}
                    if "code" not in err or "message" not in err:
                        result = build_error_envelope(
                            code=map_http_status_to_code(status),
                            message=str(err or "请求失败"),
                            trace_id=trace_id,
                            api_version=API_VERSION,
                            contract_version=CONTRACT_VERSION,
                        )
                        status = status if status and status >= 400 else 500
                    else:
                        if isinstance(err.get("code"), int):
                            err["code"] = map_http_status_to_code(status)
                            result["error"] = err

            if status == 304:
                # 304 必须空体，但要带 ETag/CORS 头
                resp = request.make_response("", status=304)
                resp.headers.update(headers)
                return resp

            return request.make_json_response(result, status=status, headers=headers)
        except AccessDenied:
            return _error_response(AUTH_REQUIRED, "认证失败或 token 无效", 401, trace_id)
        except AccessError as e:
            msg = str(e)
            if msg.startswith("FEATURE_DISABLED"):
                return _error_response("FEATURE_DISABLED", msg, 403, trace_id)
            if msg.startswith("LIMIT_EXCEEDED"):
                return _error_response("LIMIT_EXCEEDED", msg, 429, trace_id)
            return _error_response(PERMISSION_DENIED, msg, 403, trace_id)
        except MissingError as e:
            return _error_response(INTENT_NOT_FOUND, str(e), 404, trace_id)
        except (BadRequest, Unauthorized, Forbidden, NotFound) as e:
            status = getattr(e, "code", 400) or 400
            code = map_http_status_to_code(status)
            return _error_response(code, str(e), status, trace_id)
        except Exception as e:
            if isinstance(e, AccessDenied) or e.__class__.__name__ == "AccessDenied":
                return _error_response(AUTH_REQUIRED, "认证失败或 token 无效", 401, trace_id)
            _logger.exception("intent dispatcher failed: %s", e)
            return _error_response(INTERNAL_ERROR, "内部错误", 500, trace_id)
