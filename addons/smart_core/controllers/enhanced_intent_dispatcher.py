# smart_core/controllers/enhanced_intent_dispatcher.py
# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging
import json

from ..core.intent_router import route_intent_payload   # ✅ 改用结构化路由
from ..core.enhanced_intent_router import route_intent_enhanced, enhanced_router  # ✅ 增强路由（可选）
from ..core.context import RequestContext
from ..security.intent_permission import check_intent_permission
from ..handlers.enhanced_ui_contract import register_middlewares

_logger = logging.getLogger(__name__)

# 注册额外的中间件
register_middlewares(enhanced_router)

class IntentDispatcher(http.Controller):
    @http.route('/api/v1/intent', type='http', auth='public', methods=['POST'], csrf=False)
    def handle_intent(self, **kwargs):
        try:
            # ------- 请求解析 -------
            _logger.info("Request type: %s", type(request))
            body = request.httprequest.get_json(force=True, silent=True) or {}
            _logger.info("Request data: %s", json.dumps(body, ensure_ascii=False))

            # 统一上下文（含 env/user/uid/request）
            ctx = RequestContext.from_http_request()
            _logger.info("Context params: %s", getattr(ctx, "params", {}))

            # ------- 兼容旧形状：只有 intent/context 的请求 -------
            # 期望新形状：{"intent": "...", "params": {...}, "ctx": {...}, "options": {...}}
            payload = dict(body) if isinstance(body, dict) else {}
            intent_name = (payload.get("intent") or getattr(ctx, "params", {}).get("intent") or "").strip()
            if not intent_name:
                return request.make_json_response(
                    {"ok": False, "error": {"code": 400, "message": "缺少 intent 参数"}, "code": 400},
                    status=400
                )

            # 旧：把 body.context 当成 params 兜底（登录/早期调用）
            if "params" not in payload and isinstance(payload.get("context"), dict):
                payload["params"] = payload["context"]
            payload.setdefault("params", {})
            payload.setdefault("ctx", {})
            payload.setdefault("options", {})

            # ------- 权限（登录意图跳过） -------
            if intent_name not in ("login", "auth.login"):
                check_intent_permission(ctx)

            # ------- 调度执行 -------
            # 把 intent 写回 payload（防止上面从 ctx.params 兜底时未同步）
            payload["intent"] = intent_name

            # 为路由器准备一个轻量 context（需含 request/env/user/uid）
            # RequestContext.from_http_request() 已经具备这些属性
            result = route_intent_payload(payload, ctx)

            # ------- HTTP 状态码 & 304 处理 -------
            status = int(result.get("code", 200)) if isinstance(result, dict) else 200

            # 写 ETag 响应头（如有）
            headers = {}
            if isinstance(result, dict):
                etag = (result.get("meta") or {}).get("etag")
                if etag:
                    headers["ETag"] = f'"{etag}"'

            # 304：按规范无 body，交由前端用缓存
            if status == 304:
                return request.make_response(None, headers=headers, status=304)

            # 其余：直接透传 Handler 的结构（不再外层包 {status,message,data}）
            return request.make_json_response(result, status=status, headers=headers)

        except Exception as e:
            _logger.exception("Intent 处理异常：%s", str(e))
            return request.make_json_response(
                {"ok": False, "error": {"code": 500, "message": f"执行异常: {str(e)}"}, "code": 500},
                status=500
            )
    
    @http.route('/api/v2/intent', type='http', auth='public', methods=['POST'], csrf=False)
    def handle_enhanced_intent(self, **kwargs):
        """增强意图处理端点"""
        try:
            # ------- 请求解析 -------
            _logger.info("Enhanced request type: %s", type(request))
            body = request.httprequest.get_json(force=True, silent=True) or {}
            _logger.info("Enhanced request data: %s", json.dumps(body, ensure_ascii=False))

            # 统一上下文（含 env/user/uid/request）
            ctx = RequestContext.from_http_request()
            _logger.info("Enhanced context params: %s", getattr(ctx, "params", {}))

            # ------- 兼容旧形状：只有 intent/context 的请求 -------
            # 期望新形状：{"intent": "...", "params": {...}, "ctx": {...}, "options": {...}}
            payload = dict(body) if isinstance(body, dict) else {}
            intent_name = (payload.get("intent") or getattr(ctx, "params", {}).get("intent") or "").strip()
            if not intent_name:
                return request.make_json_response(
                    {"ok": False, "error": {"code": 400, "message": "缺少 intent 参数"}, "code": 400},
                    status=400
                )

            # 旧：把 body.context 当成 params 兜底（登录/早期调用）
            if "params" not in payload and isinstance(payload.get("context"), dict):
                payload["params"] = payload["context"]
            payload.setdefault("params", {})
            payload.setdefault("ctx", {})
            payload.setdefault("options", {})

            # ------- 权限（登录意图跳过） -------
            if intent_name not in ("login", "auth.login"):
                check_intent_permission(ctx)

            # ------- 调度执行 -------
            # 把 intent 写回 payload（防止上面从 ctx.params 兜底时未同步）
            payload["intent"] = intent_name

            # 为路由器准备一个轻量 context（需含 request/env/user/uid）
            # RequestContext.from_http_request() 已经具备这些属性
            result = route_intent_enhanced(payload, ctx)

            # ------- HTTP 状态码 & 304 处理 -------
            status = int(result.get("code", 200)) if isinstance(result, dict) else 200

            # 写 ETag 响应头（如有）
            headers = {}
            if isinstance(result, dict):
                etag = (result.get("meta") or {}).get("etag")
                if etag:
                    headers["ETag"] = f'"{etag}"'

            # 304：按规范无 body，交由前端用缓存
            if status == 304:
                return request.make_response(None, headers=headers, status=304)

            # 其余：直接透传 Handler 的结构（不再外层包 {status,message,data}）
            return request.make_json_response(result, status=status, headers=headers)

        except Exception as e:
            _logger.exception("Enhanced intent 处理异常：%s", str(e))
            return request.make_json_response(
                {"ok": False, "error": {"code": 500, "message": f"执行异常: {str(e)}"}, "code": 500},
                status=500
            )