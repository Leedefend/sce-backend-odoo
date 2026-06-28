# smart_core/core/base_handler.py
# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict, Optional
from odoo import api, SUPERUSER_ID
from odoo.exceptions import AccessError
from odoo.addons.smart_core.security.platform_admin import user_is_platform_admin
import  inspect
from .intent_operation_policy import is_write_intent

_logger = logging.getLogger(__name__)
SOURCE_KIND = "intent_handler_runtime_base"
SOURCE_AUTHORITIES = ("handler_payload", "odoo.env", "ir.model.access", "res.groups")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> Dict[str, Any]:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "write_proxy": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "runtime_carrier": "base_intent_handler",
    }

class BaseIntentHandler:
    SOURCE_KIND = SOURCE_KIND
    SOURCE_AUTHORITIES = SOURCE_AUTHORITIES
    NO_BUSINESS_FACT_AUTHORITY = NO_BUSINESS_FACT_AUTHORITY

    @classmethod
    def source_authority_contract(cls) -> Dict[str, Any]:
        return source_authority_contract()

    """
    统一的意图处理基类
    - 通过 __init__ 注入 env/su_env/request/context/payload
    - run() 统一把 payload/ctx 传给 handle()
    - 子类只需要实现 handle(self, payload=None, ctx=None)
    """

    # 元信息（子类可覆盖）
    INTENT_TYPE: str = "base.intent"
    DESCRIPTION: str = ""
    VERSION: str = "1.0.0"
    ETAG_ENABLED: bool = False
    ALIASES = []              # 兼容别名
    REQUIRED_GROUPS = []      # 权限（可选）

    def __init__(
        self,
        env,
        su_env=None,
        request=None,
        context: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        # ---- 必要上下文（缺 env 直接报错，早失败）----
        if env is None:
            raise RuntimeError(f"{self.__class__.__name__} requires a valid env")

        self.env = env
         # 显式构造超级环境（不要调用 env.sudo()）
        self.su_env = su_env or api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))
        self.request = request
        self.context = (env.context or {}).copy()
        if context:
            self.context.update(context)

        
               # 让 handler 既能用 self.payload 也能用 self.params（兼容旧代码）
        self.payload = payload or {}
        if isinstance(self.payload, dict) and "params" in self.payload:
            self.params = self.payload.get("params") or {}
        else:
            self.params = self.payload or {}
        # 路径参数（增强路由可用）
        if isinstance(self.context, dict) and "path_params" in self.context:
            self.path_params = self.context.get("path_params") or {}
        else:
            self.path_params = {}
    # ---- 权限校验（按需覆盖/增强）----
    def _check_permissions(self):
        # 这里可以做 REQUIRED_GROUPS 校验（按 xmlid 或 id）
        # 留空默认放行；你的系统里若有统一中间件可不用这里
        return True

    def is_write(self) -> bool:
        non_idempotent = bool(str(getattr(self, "NON_IDEMPOTENT_ALLOWED", "") or "").strip())
        params = self.params if isinstance(self.params, dict) else {}
        payload = self.payload if isinstance(self.payload, dict) else {}
        intent = str(payload.get("intent") or getattr(self, "INTENT_TYPE", "") or "")
        return is_write_intent(intent, params, non_idempotent=non_idempotent)

    def enforce_required_groups(self):
        required = getattr(self, "REQUIRED_GROUPS", []) or []
        required_xmlids = [str(x).strip() for x in required if str(x).strip()]
        if not required_xmlids:
            raise AccessError(f"PERMISSION_DENIED: write intent requires REQUIRED_GROUPS ({self.__class__.__name__})")
        user = self.env.user
        try:
            if user and user_is_platform_admin(user):
                return True
        except Exception:
            pass
        for xmlid in required_xmlids:
            try:
                if user.has_group(xmlid):
                    return True
            except Exception:
                pass
        raise AccessError(
            "PERMISSION_DENIED: missing any required group for intent {} (required=[{}])".format(
                str(getattr(self, "INTENT_TYPE", "") or self.__class__.__name__),
                ", ".join(required_xmlids),
            )
        )

    # ---- 统一执行入口 ----
    def run(self, payload: Optional[Dict[str, Any]] = None, ctx: Optional[Dict[str, Any]] = None):
        """
        统一执行入口（向下兼容）：
        - 支持新签名：handle(self, payload=None, ctx=None)
        - 也兼容旧签名：handle(self)、handle(self, params, context)、handle(self, p, ctx) 等
        """
        if not hasattr(self, "handle"):
            raise NotImplementedError(f"{self.__class__.__name__} must implement handle(...)")

        # 覆盖/同步 payload 与 params
        if payload is not None:
            self.payload = payload
            if isinstance(payload, dict) and "params" in payload:
                self.params = payload.get("params") or {}
            else:
                self.params = payload or {}

        # 权限（可选）
        self._check_permissions()
        if self.is_write():
            self.enforce_required_groups()

        # ---- 智能适配调用 ----
        try:
            sig = inspect.signature(self.handle)
        except (TypeError, ValueError):
            # 极端情况下拿不到签名，退化为最常见的两种尝试
            try:
                return self.handle(self.params, ctx)
            except TypeError:
                return self.handle()

        # 统一映射表（命名别名全部支持）
        mapped_payload = self.payload
        mapped_params  = self.params
        mapped_ctx     = ctx or self.context
        mapping = {
            "payload": mapped_payload,
            "p": mapped_payload,                 # 某些老代码用 p 表示 payload
            "params": mapped_params,             # 老代码常用
            "ctx": mapped_ctx,
            "context": mapped_ctx,
            "env": self.env,
            "su_env": self.su_env,
            "request": self.request,
        }

        # 仅传入对方签名里声明的参数；若 handler 接收 **kwargs，则显式提供完整运行上下文。
        kwargs = {}
        for param in sig.parameters.values():
            if param.name == "self":
                continue
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                kwargs.update(mapping)
                continue
            if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.VAR_POSITIONAL):
                continue
            if param.name in mapping:
                kwargs[param.name] = mapping[param.name]

        return self.handle(**kwargs)

    # ---- 轻量工具方法（供测试/增强 handler 使用）----
    def err(self, code: int, message: str):
        return {"ok": False, "error": {"code": code, "message": message}, "code": code}

    def get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        val = self.params.get(key) if isinstance(self.params, dict) else None
        if val is None:
            return default
        return str(val)

    def get_int(self, key: str, default: int = 0) -> int:
        val = self.params.get(key) if isinstance(self.params, dict) else None
        try:
            return int(val)
        except Exception:
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self.params.get(key) if isinstance(self.params, dict) else None
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return bool(val)
        if isinstance(val, str):
            return val.strip().lower() in ("1", "true", "yes", "y", "on")
        return default

    def get_enum(self, key: str, allowed: list, default: Optional[str] = None) -> Optional[str]:
        val = self.get_str(key, default)
        if val in allowed:
            return val
        return default

    def get_path_param(self, name: str, default: Any = None) -> Any:
        if isinstance(self.path_params, dict) and name in self.path_params:
            return self.path_params.get(name, default)
        if isinstance(self.context, dict):
            ctx_pp = self.context.get("path_params")
            if isinstance(ctx_pp, dict) and name in ctx_pp:
                return ctx_pp.get(name, default)
        if isinstance(self.params, dict) and name in self.params:
            return self.params.get(name, default)
        return default
