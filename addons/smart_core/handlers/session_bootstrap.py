# -*- coding: utf-8 -*-
# 📁 smart_core/handlers/session_bootstrap.py
import os
import logging
from ..core.base_handler import BaseIntentHandler
from ..security.auth import generate_token

_logger = logging.getLogger(__name__)

class SessionBootstrapHandler(BaseIntentHandler):
    """
    intent: session.bootstrap
    仅用于 dev/test 生成服务账户 token，避免验证依赖明文账号密码。
    需要提供 X-Bootstrap-Secret 或 params.secret 与 SC_BOOTSTRAP_SECRET 匹配。
    """
    INTENT_TYPE = "session.bootstrap"
    DESCRIPTION = "Bootstrap a session token for tests (dev/test only)."
    REQUIRED_GROUPS = []

    def handle(self, payload=None, ctx=None):
        env_flag = (os.getenv("ENV") or "").lower()
        if env_flag not in {"dev", "test", "local"}:
            self._audit("deny_env", ctx)
            return self.err(403, "bootstrap disabled outside dev/test")

        secret_expected = os.getenv("SC_BOOTSTRAP_SECRET") or ""
        if not secret_expected:
            self._audit("missing_secret", ctx)
            # Hide endpoint existence when secret is not configured
            return self.err(404, "not found")

        params = payload.get("params") if isinstance(payload, dict) else None
        if not isinstance(params, dict):
            params = payload if isinstance(payload, dict) else {}
        secret = params.get("secret")
        if not secret and self.request:
            try:
                secret = self.request.httprequest.headers.get("X-Bootstrap-Secret")
            except Exception:
                secret = None

        if not secret or secret != secret_expected:
            self._audit("invalid_secret", ctx)
            return self.err(401, "invalid bootstrap secret")

        login = (params.get("login") or os.getenv("SC_BOOTSTRAP_LOGIN") or "svc_project_ro").strip()
        user = self.env["res.users"].sudo().search([("login", "=", login)], limit=1)
        if not user:
            self._audit("user_not_found", ctx, login=login)
            return self.err(404, f"bootstrap user not found: {login}")

        token_version = int(getattr(user, "token_version", 0) or 0)
        token = generate_token(user.id, token_version=token_version)
        self._audit("ok", ctx, login=login, uid=user.id)
        return {
            "ok": True,
            "data": {
                "token": token,
                "token_type": "Bearer",
                "user": {"id": user.id, "login": user.login, "name": user.name},
            },
        }

    def _audit(self, status: str, ctx=None, **extra):
        try:
            trace_id = getattr(ctx, "trace_id", None) if ctx else None
            ip = None
            if self.request:
                ip = self.request.httprequest.remote_addr
            info = {
                "status": status,
                "ip": ip,
                "trace_id": trace_id,
            }
            info.update(extra)
            _logger.info("[session.bootstrap] %s", info)
        except Exception:
            pass
