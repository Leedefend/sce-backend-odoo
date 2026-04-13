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
from ..utils.reason_codes import REASON_PERMISSION_DENIED, failure_meta_for_reason
from .intent_request_normalizer import normalize_dispatch_payload, resolve_effective_db
from .intent_effect_policy import should_commit_write_effect
from .intent_governance import canon_intent, resolve_request_schema_key
from .intent_permission_details import build_permission_error_details
from .intent_legacy_compat import apply_legacy_load_view_compat

_logger = logging.getLogger(__name__)

# ✅ 匿名白名单（仅在“匿名请求”识别为真时生效；见 _is_anon_req）
ANON_ALLOWLIST = {"login", "auth.login", "sys.intents", "session.bootstrap"}

API_VERSION = "v1"
CONTRACT_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"

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

def _error_response(
    code: str,
    message: str,
    status: int,
    trace_id: str,
    details: dict | None = None,
    error_fields: dict | None = None,
):
    payload = build_error_envelope(
        code=code,
        message=message,
        trace_id=trace_id,
        details=details,
        api_version=API_VERSION,
        contract_version=CONTRACT_VERSION,
    )
    if error_fields and isinstance(payload.get("error"), dict):
        payload["error"].update(error_fields)
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

    if hasattr(res, "to_legacy_dict") and callable(getattr(res, "to_legacy_dict")):
        try:
            legacy_payload = res.to_legacy_dict()
            if isinstance(legacy_payload, dict):
                out = dict(legacy_payload)
                out.setdefault("ok", True)
                out.setdefault("data", {})
                out.setdefault("meta", {})
                return out
        except Exception:
            pass

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


def _validate_dispatch_request(body: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(body, dict):
        return ["request_body_not_object"]

    if "intent" in body and not isinstance(body.get("intent"), str):
        errors.append("intent_must_be_string")
    if "params" in body and not isinstance(body.get("params"), dict):
        errors.append("params_must_be_object")
    if "payload" in body and not isinstance(body.get("payload"), dict):
        errors.append("payload_must_be_object")
    if "context" in body and not isinstance(body.get("context"), dict):
        errors.append("context_must_be_object")

    return errors


def _prepare_dispatch_request(*, kwargs: Dict[str, Any], trace_id: str, runtime_state: Dict[str, Any]):
    raw_body = request.httprequest.get_json(force=True, silent=True)
    if raw_body is None:
        raw_body = {}

    intent_candidate = ""
    if isinstance(raw_body, dict):
        intent_candidate = canon_intent(str(raw_body.get("intent") or "").strip())

    validation_errors = _validate_dispatch_request(raw_body)
    if validation_errors:
        return None, _error_response(
            BAD_REQUEST,
            "请求参数格式错误",
            400,
            trace_id,
            details={
                "validation_errors": validation_errors,
                "schema_key": resolve_request_schema_key(intent_candidate),
            },
        )

    body = raw_body if isinstance(raw_body, dict) else {}

    intent_name = canon_intent((body.get("intent") or "").strip())
    runtime_state["intent_name"] = intent_name
    if not intent_name:
        return None, _error_response(BAD_REQUEST, "缺少 intent 参数", 400, trace_id)

    normalized_payload = normalize_dispatch_payload(body)
    params = normalized_payload["params"]
    context_in = normalized_payload["context"]
    runtime_state["params"] = params

    hdr = request.httprequest.headers
    x_db_hdr = hdr.get("X-Odoo-DB") or hdr.get("X-DB")

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

    effective_db, db_source = resolve_effective_db(
        params=params,
        kwargs=kwargs,
        x_db_header=x_db_hdr,
        session_db=request.session.db,
        env_db=_default_db(),
        remote_addr=request.httprequest.remote_addr,
        host=request.httprequest.host,
        is_admin=_user_is_admin(),
        env_name=os.environ.get("ENV"),
    )

    if effective_db and db_source in {"params", "query", "header"} and (params.get("db") != effective_db):
        _logger.warning("Blocked db override from %s in non-dev env", db_source)

    if effective_db:
        params["db"] = params.get("db") or effective_db
        if request.session.db != effective_db:
            request.session.db = effective_db

    is_anon = _is_anon_req(hdr) or intent_name == "session.bootstrap"
    payload = {
        "intent": intent_name,
        "params": params,
        "context": context_in,
        "meta": body.get("meta") or {},
    }

    ctx = RequestContext.from_http_request()
    setattr(ctx, "trace_id", trace_id)
    setattr(ctx, "is_anonymous", is_anon)
    setattr(ctx, "db", params.get("db"))
    context_in["trace_id"] = trace_id

    prepared = {
        "intent_name": intent_name,
        "params": params,
        "is_anon": is_anon,
        "payload": payload,
        "ctx": ctx,
    }
    return prepared, None


def _finalize_dispatch_response(*, result: Any, intent_name: str, trace_id: str, ts0: float, params: Dict[str, Any]):
    normalized = _normalize_result_shape(result)
    normalized = apply_legacy_load_view_compat(normalized, intent_name)

    status = 200
    headers = _cors_headers()
    headers["X-Trace-Id"] = trace_id

    if isinstance(normalized, dict):
        status = int(normalized.get("code", 200)) if isinstance(normalized.get("code"), (int, str)) else 200
        etag = (normalized.get("meta") or {}).get("etag")
        if etag:
            headers["ETag"] = f'"{etag}"'

        meta = normalized.setdefault("meta", {})
        meta.setdefault("trace_id", trace_id)
        meta.setdefault("intent", intent_name)
        meta.setdefault("elapsed_ms", int((time.time() - ts0) * 1000))
        meta.setdefault("api_version", API_VERSION)
        meta.setdefault("contract_version", CONTRACT_VERSION)
        meta.setdefault("schema_version", SCHEMA_VERSION)

        if normalized.get("ok") is False:
            err = normalized.get("error") if isinstance(normalized.get("error"), dict) else {}
            if "code" not in err or "message" not in err:
                normalized = build_error_envelope(
                    code=map_http_status_to_code(status),
                    message=str(err or "请求失败"),
                    trace_id=trace_id,
                    api_version=API_VERSION,
                    contract_version=CONTRACT_VERSION,
                )
                status = status if status and status >= 400 else 500
            elif isinstance(err.get("code"), int):
                err["code"] = map_http_status_to_code(status)
                normalized["error"] = err

    if status == 304:
        resp = request.make_response("", status=304)
        resp.headers.update(headers)
        return resp

    if should_commit_write_effect(
        normalized=normalized,
        status=status,
        intent_name=intent_name,
        params=params,
    ):
        try:
            request.env.cr.commit()
        except Exception:
            _logger.exception("intent commit failed: intent=%s trace=%s", intent_name, trace_id)
            return _error_response(INTERNAL_ERROR, "内部错误", 500, trace_id)

    return request.make_json_response(normalized, status=status, headers=headers)


def _execute_intent_request(
    *,
    kwargs: Dict[str, Any],
    trace_id: str,
    ts0: float,
    controller_name: str,
    controller_module: str,
    runtime_state: Dict[str, Any],
):
    _logger.info(
        "[intent] controller=%s module=%s trace=%s",
        controller_name,
        controller_module,
        trace_id,
    )

    if request.httprequest.method == "OPTIONS":
        return _respond_empty(status=204, trace_id=trace_id)

    prepared, early_response = _prepare_dispatch_request(kwargs=kwargs, trace_id=trace_id, runtime_state=runtime_state)
    if early_response is not None:
        return early_response

    intent_name = prepared["intent_name"]
    params = prepared["params"]
    is_anon = prepared["is_anon"]
    payload = prepared["payload"]
    ctx = prepared["ctx"]

    _logger.info(
        "[intent] trace=%s intent=%s anon=%s db=%s params.keys=%s",
        trace_id,
        intent_name,
        is_anon,
        params.get("db"),
        ",".join(sorted(params.keys())) if params else "-",
    )

    skip_auth = is_anon and intent_name in ANON_ALLOWLIST
    if intent_name == "session.bootstrap":
        skip_auth = True
    if not skip_auth:
        check_intent_permission(ctx)

    raw_result = route_intent_payload(payload, ctx=ctx)
    if _is_response(raw_result):
        resp = raw_result
        resp.headers.update(_cors_headers())
        return resp

    return _finalize_dispatch_response(
        result=raw_result,
        intent_name=intent_name,
        trace_id=trace_id,
        ts0=ts0,
        params=params,
    )


# ===================== 控制器 =====================

class IntentDispatcher(http.Controller):

    @http.route('/api/v1/intent', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False)
    def handle_intent(self, **kwargs):
        ts0 = time.time()
        headers = request.httprequest.headers
        trace_id = get_trace_id(headers)
        runtime_state: Dict[str, Any] = {
            "intent_name": None,
            "params": {},
        }

        try:
            return _execute_intent_request(
                kwargs=kwargs,
                trace_id=trace_id,
                ts0=ts0,
                controller_name=self.__class__.__name__,
                controller_module=self.__class__.__module__,
                runtime_state=runtime_state,
            )
        except AccessDenied:
            return _error_response(AUTH_REQUIRED, "认证失败或 token 无效", 401, trace_id)
        except AccessError as e:
            intent_name = runtime_state.get("intent_name")
            params = runtime_state.get("params") or {}
            msg = str(e)
            if msg.startswith("FEATURE_DISABLED"):
                return _error_response("FEATURE_DISABLED", msg, 403, trace_id)
            if msg.startswith("LIMIT_EXCEEDED"):
                return _error_response("LIMIT_EXCEEDED", msg, 429, trace_id)
            return _error_response(
                PERMISSION_DENIED,
                msg,
                403,
                trace_id,
                details=build_permission_error_details(intent_name, params, msg),
                error_fields={
                    "reason_code": REASON_PERMISSION_DENIED,
                    **failure_meta_for_reason(REASON_PERMISSION_DENIED),
                },
            )
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
