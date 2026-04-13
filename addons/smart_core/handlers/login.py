# -*- coding: utf-8 -*-
import logging
import time
from typing import Dict, Any

from odoo import SUPERUSER_ID, api
from odoo.modules.registry import Registry
from ..core.base_handler import BaseIntentHandler
from ..core.intent_execution_result import IntentExecutionResult
from ..security.auth import authenticate_user, generate_token, get_token_exp_seconds, get_user_from_token
from ..core.handler_registry import HANDLER_REGISTRY  # 全局注册表

_logger = logging.getLogger(__name__)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        return text in {"1", "true", "yes", "y", "on", "debug"}
    return False


def _resolve_contract_mode(params: Dict[str, Any]) -> str:
    raw = str(params.get("contract_mode") or "").strip().lower()
    if raw in {"default", "compat", "debug"}:
        return raw
    if _to_bool(params.get("debug")):
        return "debug"
    # New contract is the default surface.
    return "default"


def _resolve_compat_enabled(env, params: Dict[str, Any]) -> bool:
    if "compat_enabled" in params:
        return _to_bool(params.get("compat_enabled"))
    try:
        raw = env["ir.config_parameter"].sudo().get_param("smart_core.login.compat_enabled", "1")
    except Exception:
        raw = "1"
    return _to_bool(raw)


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
        current_name = user.company_id.display_name if user.company_id else ""
        return {
            "company_id": current,
            "company_name": current_name,
            "allowed_company_ids": allowed,
        }
    except Exception:
        return {"company_id": None, "company_name": "", "allowed_company_ids": []}


def _load_user_profile(db_name: str, user_id: int) -> Dict[str, Any]:
    """Read user profile from the authenticated DB to avoid cross-db env drift."""
    registry = Registry(db_name)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        user = env["res.users"].sudo().browse(int(user_id))
        if not user.exists():
            raise RuntimeError(f"user not found in db={db_name}: {user_id}")
        return {
            "id": user.id,
            "name": user.name,
            "login": user.login,
            "groups": _user_groups_xmlids(user),
            "lang": user.lang,
            "tz": user.tz or "Asia/Shanghai",
            **_company_ids(user),
            "token_version": int(getattr(user, "token_version", 0) or 0),
        }


def _is_internal_user(profile: Dict[str, Any]) -> bool:
    groups = set(profile.get("groups") or [])
    return "base.group_user" in groups


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
        contract_mode = _resolve_contract_mode(params)
        compat_requested = contract_mode == "compat"
        compat_enabled = _resolve_compat_enabled(self.env, params)
        if compat_requested and not compat_enabled:
            contract_mode = "default"

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
        auth_db = (user_dict.get("db") or db or "").strip()
        if not auth_db:
            return self.err(400, "缺少数据库参数")
        try:
            profile = _load_user_profile(auth_db, user_id)
        except Exception as e:
            _logger.info("Login profile load failed for %s on %s: %s", login, auth_db, e)
            return self.err(401, "用户名或密码错误")

        # 4) 生成访问令牌（JWT/HMAC 等）
        token_version = int(profile.get("token_version") or 0)
        token = generate_token(user_id, token_version=token_version, db=auth_db)
        token_type = "Bearer"
        expires_at = int(time.time()) + get_token_exp_seconds()

        # 可选：切换公司（若传入）
        if want_company_id:
            try:
                want_company_id = int(want_company_id)
                if want_company_id in (profile.get("allowed_company_ids") or []):
                    # 注意：这里只返回信息，不在服务器端持久化切公司，
                    # 具体上下文切换应由前端后续请求带上下文或单独意图处理
                    pass
            except Exception:
                pass

        user_data = {
            "id": profile["id"],
            "name": profile["name"],
            "login": profile["login"],
            "lang": profile["lang"],
            "tz": profile["tz"],
            "company_id": profile["company_id"],
            "company_name": profile.get("company_name") or "",
            "allowed_company_ids": profile["allowed_company_ids"],
        }

        can_switch_company = len(profile.get("allowed_company_ids") or []) > 1
        is_internal_user = _is_internal_user(profile)
        role_code = "internal_user" if is_internal_user else "external_user"

        data = {
            "session": {
                "token": token,
                "token_type": token_type,
                "expires_at": expires_at,
            },
            "user": user_data,
            "entitlement": {
                "role_code": role_code,
                "is_internal_user": is_internal_user,
                "can_switch_company": can_switch_company,
            },
            "bootstrap": {
                "next_intent": "system.init",
                "mode": "full",
                "allowed_exception_intents": ["session.bootstrap", "scene.health"],
            },
            "contract": {
                "contract_version": "1.0.0",
                "schema_version": "1.0.0",
                "response_mode": contract_mode,
                "mode": contract_mode,
                "compat_requested": compat_requested,
                "compat_enabled": compat_enabled,
                "compat_deprecated": True,
                "compat_sunset_phase": "next_iteration",
            },
        }

        if compat_requested and not compat_enabled:
            data["contract"]["deprecation_notice"] = "compat_mode_disabled_fallback_to_default"
        elif compat_requested:
            data["contract"]["deprecation_notice"] = "compat_mode_deprecated_use_default"

        # Compatibility surface: keep legacy top-level token fields for all modes.
        # Canonical source remains data.session.*; legacy fields are shim for old consumers.
        data["token"] = token
        data["token_type"] = token_type
        data["expires_at"] = expires_at

        if contract_mode == "debug":
            data["debug"] = {
                "groups": profile["groups"],
                "intents": _list_available_intents(),
            }
        return IntentExecutionResult(ok=True, data=data, meta={})


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
        for name in sorted((HANDLER_REGISTRY or {}).keys()):
            handler_cls = (HANDLER_REGISTRY or {})[name]
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
