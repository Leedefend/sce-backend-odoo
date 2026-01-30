# -*- coding: utf-8 -*-
import logging
import time
from typing import Dict, Any, Optional

from odoo.http import request
from ..core.base_handler import BaseIntentHandler
from ..security.auth import authenticate_user, generate_token, get_token_exp_seconds, get_user_from_token
from ..core.handler_registry import HANDLER_REGISTRY  # 全局注册表

_logger = logging.getLogger(__name__)


def _safe_env():
    """优先用 BaseIntentHandler 注入的 env；兜底用 request.env。"""
    env = getattr(request, "env", None)
    if env is None:
        raise RuntimeError("无法获取 Odoo 环境（env 为空）")
    return env


def _user_groups_xmlids(user) -> list[str]:
    """把用户所属组转成外部ID列表（module.xmlid），无外部ID的过滤掉。"""
    try:
        mapping = user.groups_id.get_external_id() or {}
        return [mapping[g.id] for g in user.groups_id if mapping.get(g.id)]
    except Exception:
        return []


def _company_ids(user) -> Dict[str, Any]:
    """提取公司信息，尽量不触发额外查询。"""
    try:
        allowed = user.company_ids.ids or []
        current = user.company_id.id if user.company_id else None
        return {
            "company_id": current,
            "allowed_company_ids": allowed,
        }
    except Exception:
        return {"company_id": None, "allowed_company_ids": []}


class LoginHandler(BaseIntentHandler):
    """
    用户登录处理器
    - INTENT_TYPE 保持 'login' 兼容；若你的前端已统一用 'auth.login'，可改为 'auth.login'
    - 登录为写语义，不参与 ETag/304
    """
    INTENT_TYPE  = "login"   # 兼容历史；亦可注册别名见文末
    DESCRIPTION  = "用户登录处理器"
    VERSION      = "2.2.0"
    ETAG_ENABLED = False

    def handle(self):
        # 1) 取参（支持 db / database / company_id 可选）
        params: Dict[str, Any] = self.params or {}
        login    = (params.get("login") or "").strip()
        password = (params.get("password") or "").strip()
        # 可选：db/公司/语言/时区（按需扩展）
        db = params.get("db") or params.get("database")
        want_company_id = params.get("company_id")

        if not login or not password:
            return self.err(400, "缺少登录信息")

        # 2) 鉴权（自定义逻辑，建议内部做 active 检查 / 锁定策略 / 审计）
        try:
            # authenticate_user 可自行支持 db 选择（若你有多库登录）
            user_dict = authenticate_user(login, password, db=db)
        except Exception as e:
            # 避免回显敏感信息
            _logger.info("Login failed for %s: %s", login, e)
            return self.err(401, "用户名或密码错误")

        user_id = int(user_dict["id"])

        # 3) 汇总用户信息（sudo 只用于读取自身静态资料）
        env = _safe_env()
        user = env["res.users"].sudo().browse(user_id)

        # 4) 生成访问令牌（JWT/HMAC 等）
        token_version = int(getattr(user, "token_version", 0) or 0)
        token = generate_token(user_id, token_version=token_version)
        token_type = "Bearer"
        expires_at = int(time.time()) + get_token_exp_seconds()

        # 可选：切换公司（若传入）
        if want_company_id:
            try:
                want_company_id = int(want_company_id)
                if want_company_id in user.company_ids.ids:
                    # 注意：这里只返回信息，不在服务器端持久化切公司，
                    # 具体上下文切换应由前端后续请求带上下文或单独意图处理
                    pass
            except Exception:
                pass

        groups_xmlids = _user_groups_xmlids(user)
        comp = _company_ids(user)

        data = {
            "token": token,
            "token_type": token_type,
            "expires_at": expires_at,
            "user": {
                "id": user.id,
                "name": user.name,
                "login": user.login,
                "groups": groups_xmlids,
                "lang": user.lang,
                "tz": user.tz or "Asia/Shanghai",
                **comp,
            },
            # 与前端契约保持：预留 system/intents 占位
            "system": {
                "menus": [],
                "models": [],
                "views": [],
                "intents": _list_available_intents(),
            },
        }
        return data, {}


class LogoutHandler(BaseIntentHandler):
    """
    注销处理器（幂等空操作）
    - JWT 为无状态：后端不需“销毁”，前端丢弃即可
    - 若同域下曾登录过 /web，这里顺手清 Odoo session
    """
    INTENT_TYPE  = "auth.logout"
    DESCRIPTION  = "用户登出处理器（幂等）"
    VERSION      = "1.0.0"
    ETAG_ENABLED = False

    def handle(self):
        try:
            # 有 Cookie session 时清掉（即使你前端不用 Cookie，也可防误带）
            if getattr(request, "session", None):
                request.session.logout()
        except Exception as e:
            _logger.debug("auth.logout: session.logout ignored: %s", e)

        # 撤销当前 token（若存在且有效）
        try:
            user = get_user_from_token()
            if user and user.exists():
                user.sudo().write({"token_version": int(getattr(user, "token_version", 0) or 0) + 1})
        except Exception:
            # 无 token 或 token 已无效时保持幂等
            pass

        # 如需“拉黑 token”（有 jti/redis 黑名单机制），可在此记录
        return {"message": "logged out"}, {}


def _list_available_intents() -> list[Dict[str, str]]:
    """从全局注册表导出意图清单；失败时返回空列表不阻断登录。"""
    out = []
    try:
        for name, handler_cls in (HANDLER_REGISTRY or {}).items():
            desc = getattr(handler_cls, "DESCRIPTION", None) or getattr(handler_cls, "__doc__", "") or ""
            out.append({"name": name, "description": desc})
    except Exception:
        return []
    return out


# --- 注册“别名意图”：如果前端有的发 login，有的发 auth.login，都能命中 ---
# 你的注册表是 dict，通常由装饰器填充。这里显式塞入别名，避免改前端。
try:
    HANDLER_REGISTRY.setdefault("auth.login", LoginHandler)
except Exception:
    pass
