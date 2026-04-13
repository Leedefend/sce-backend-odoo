# -*- coding: utf-8 -*-
# smart_core/core/intent_router.py
from odoo.http import request
from odoo import api, SUPERUSER_ID
import logging
from typing import Optional, Type, Dict, Any, Tuple
from .base_handler import BaseIntentHandler
from .handler_registry import HANDLER_REGISTRY  # import 时已完成注册
from .extension_loader import load_extensions
from .intent_env_policy import build_dispatch_envs, finalize_dispatch_cursor
from .intent_route_mode_policy import resolve_intent_route_mode
from .intent_shadow_compare_executor import run_shadow_compare

_logger = logging.getLogger(__name__)

# ---------- 工具：健壮解析 intent 名 ----------
def _normalize_intent_key(s: str) -> str:
    s = (s or "").strip()
    return s

def resolve_handler(intent: str) -> Optional[Type[BaseIntentHandler]]:
    key = _normalize_intent_key(intent)
    if not key:
        return None
    # 直接命中
    h = HANDLER_REGISTRY.get(key)
    if h:
        return h
    # 宽容：小写再试一次（注册表若用小写 key）
    h = HANDLER_REGISTRY.get(key.lower())
    if h:
        return h
    return None

def _dispatch(intent: str, params: dict, context: dict):
    """
    统一分发：显式依据 params.db 选择环境，合并 context，实例化 Handler 并调用。
    """
    import logging
    _logger = logging.getLogger(__name__)
    
    # 调试：打印参数
    _logger.info("[intent_router][debug] _dispatch called with intent: %s", intent)
    _logger.info("[intent_router][debug] params: %s", params)
    _logger.info("[intent_router][debug] params.get('db'): %s", params.get('db'))
    
    handler_cls = resolve_handler(intent)
    if not handler_cls:
        return {"ok": False, "error": {"code": 404, "message": f"Unknown intent: {intent}"}}

    # 1) 构造 env / su_env（必要时切库）
    env, su_env, extra_cr = build_dispatch_envs(params or {}, context or {})
    dispatch_succeeded = False
    try:
        # 2) 实例化 handler，注入 env/su_env/context/params
        handler = handler_cls(env=env, su_env=su_env, request=request, context=context or {}, payload=params or {})
        # 兼容旧字段
        try:
            setattr(handler, "params", params or {})
            setattr(handler, "payload", params or {})  # 兼容早期字段名
        except Exception:
            pass
        # 兼容：部分旧代码会直接访问 registry/cr/uid
        if not getattr(handler, "registry", None):
            handler.registry = env.registry
        if not getattr(handler, "cr", None):
            handler.cr = env.cr
        if not getattr(handler, "uid", None):
            handler.uid = env.uid

        # 3) 统一把参数传给 run（BaseIntentHandler.run 会转调 handle(payload, ctx)）
        result = handler.run(
            payload={"intent": intent, "params": params or {}, "context": context or {}},
            ctx=context or {},
        )
        dispatch_succeeded = True
        return result
    finally:
        # 若新开了 cursor：成功请求要提交，否则关闭时会隐式回滚。
        finalize_dispatch_cursor(
            extra_cursor=extra_cr,
            dispatch_succeeded=dispatch_succeeded,
            intent=intent,
            dbname=env.cr.dbname,
        )


def _dispatch_v2(intent: str, params: dict, context: dict):
    from ..v2.dispatcher import dispatch_intent

    return dispatch_intent(
        intent=intent,
        payload=params or {},
        context=context or {},
    )


def _enrich_v2_auth_context(context: dict) -> dict:
    enriched = dict(context or {})

    user_id = int(enriched.get("user_id") or 0)
    if user_id <= 0:
        try:
            request_uid = int(getattr(request, "uid", 0) or 0)
        except Exception:
            request_uid = 0
        if request_uid <= 0:
            try:
                request_uid = int(getattr(getattr(request, "session", None), "uid", 0) or 0)
            except Exception:
                request_uid = 0
        if request_uid <= 0:
            try:
                request_uid = int(getattr(getattr(request, "env", None), "uid", 0) or 0)
            except Exception:
                request_uid = 0
        if request_uid > 0:
            enriched["user_id"] = request_uid

    company_id = int(enriched.get("company_id") or 0)
    if company_id <= 0:
        try:
            company_id = int(getattr(getattr(request.env.user, "company_id", None), "id", 0) or 0)
        except Exception:
            company_id = 0
        if company_id > 0:
            enriched["company_id"] = company_id

    return enriched

def route_intent_payload(payload: dict, ctx) -> dict:
    """
    控制器调用的统一入口。
    payload: { "intent": "...", "params": {...}, "context": {...}, "meta": {...} }
    """
    # Load extension modules once (if configured)
    try:
        load_extensions(request.env, HANDLER_REGISTRY)
    except Exception:
        _logger.exception("[intent_router] extension loader failed")

    intent = (payload or {}).get("intent") or ""
    params = (payload or {}).get("params") or {}
    context = (payload or {}).get("context") or {}
    # 小日志帮助定位 DB 实际选择
    try:
        db = params.get("db") or request.env.cr.dbname
        _logger.debug("[intent_router] intent=%s db=%s params.keys=%s",
                      intent, db, ",".join(sorted(params.keys())) if params else "-")
    except Exception:
        pass

    route_decision = resolve_intent_route_mode(intent)
    mode = str(route_decision.get("mode") or "legacy_only")
    _logger.info(
        "[intent_router][route_mode] intent=%s mode=%s reason=%s snapshot=%s",
        intent,
        mode,
        str(route_decision.get("reason") or ""),
        str(route_decision.get("snapshot_id") or ""),
    )

    v2_context = _enrich_v2_auth_context(context)

    if mode == "v2_primary":
        return _dispatch_v2(intent, params, v2_context)

    if mode == "v2_shadow":
        primary_result = _dispatch(intent, params, context)
        compare_summary = run_shadow_compare(
            intent=intent,
            route_mode=mode,
            params=params or {},
            context=v2_context,
            v1_result=primary_result,
            v2_runner=lambda i, p, c: _dispatch_v2(i, p, c),
        )
        _logger.info(
            "[intent_router][v2_shadow_compare] intent=%s trace_id=%s same_shape=%s same_reason_code=%s diff=%s",
            str(compare_summary.get("intent") or ""),
            str(compare_summary.get("trace_id") or ""),
            bool(compare_summary.get("same_shape")),
            bool(compare_summary.get("same_reason_code")),
            ",".join(compare_summary.get("diff_summary") or []),
        )
        return primary_result

    # legacy_only 继续走 v1 主执行。
    return _dispatch(intent, params, context)
