# -*- coding: utf-8 -*-
# smart_core/core/intent_router.py
from odoo.http import request
from odoo import api, SUPERUSER_ID
import logging
from typing import Optional, Type, Dict, Any, Tuple
import odoo
from .base_handler import BaseIntentHandler
from .handler_registry import HANDLER_REGISTRY  # import 时已完成注册
from .extension_loader import load_extensions

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

# ---------- 工具：按 db/context 构造 env/su_env ----------
def _build_envs(params: Dict[str, Any], add_ctx: Dict[str, Any]) -> Tuple[api.Environment, api.Environment, Any]:
    """
    返回 (env, su_env, extra_cursor)
    - 如果切换了 DB，会新开 cursor，调用方必须在 finally 里 cr.close()
    - 如果没切库，extra_cursor 为 None
    """
    target_db = (params or {}).get("db") or request.env.cr.dbname
    cur_db = request.env.cr.dbname

    # 合并上下文：以传入的 add_ctx 覆盖 request.env.context
    base_ctx = dict(request.env.context or {})
    if add_ctx:
        base_ctx.update(add_ctx)

    if target_db == cur_db:
        env = request.env(context=base_ctx)  # 复用当前 cursor/uid，替换 context
        su_env = api.Environment(env.cr, SUPERUSER_ID, dict(env.context))
        return env, su_env, None

    # 切库：新开 registry+cursor
    reg = odoo.registry(target_db)
    try:
        reg.check_signaling()  # ← 关键：捕捉 install/update 导致的注册表变化
    except Exception:
        # 不致命，继续
        pass

    cr = reg.cursor()
    try:
        env = api.Environment(cr, request.uid, base_ctx)
        su_env = api.Environment(cr, SUPERUSER_ID, dict(env.context))
        return env, su_env, cr
    except Exception:
        cr.close()
        raise
def _dispatch(intent: str, params: dict, context: dict):
    """
    统一分发：显式依据 params.db 选择环境，合并 context，实例化 Handler 并调用。
    """
    handler_cls = resolve_handler(intent)
    if not handler_cls:
        return {"ok": False, "error": {"code": 404, "message": f"Unknown intent: {intent}"}}

    # 1) 构造 env / su_env（必要时切库）
    env, su_env, extra_cr = _build_envs(params or {}, context or {})
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
        return handler.run(
            payload={"intent": intent, "params": params or {}, "context": context or {}},
            ctx=context or {},
        )
    finally:
        # 若新开了 cursor，记得关闭
        if extra_cr is not None:
            try:
                extra_cr.close()
            except Exception:
                _logger.exception("[intent] close cursor failed (db=%s)", env.cr.dbname)

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
    return _dispatch(intent, params, context)
