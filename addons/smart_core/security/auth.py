# smart_core/security/auth.py
import jwt
import logging
import os
import time
import uuid
from typing import Any, Dict
from odoo.http import request
from odoo import http, SUPERUSER_ID, api
from odoo.exceptions import AccessDenied
from odoo.modules.registry import Registry
from odoo.tools import config

_logger = logging.getLogger(__name__)

DEFAULT_SECRET_KEY = "odoo-smart-core"
ALGORITHM = "HS256"
DEFAULT_EXP_SECONDS = 8 * 60 * 60  # 8h
_warned_missing_secret = False


def _get_secret_key():
    global _warned_missing_secret
    secret = os.getenv("SC_JWT_SECRET") or os.getenv("JWT_SECRET")
    env = getattr(request, "env", None)
    if not secret and env is not None:
        try:
            secret = env["ir.config_parameter"].sudo().get_param("sc.jwt.secret")
        except Exception:
            secret = None
    if not secret:
        if not _warned_missing_secret:
            _logger.warning("JWT secret not configured; falling back to default secret.")
            _warned_missing_secret = True
        secret = DEFAULT_SECRET_KEY
    return secret


def get_token_exp_seconds():
    env = getattr(request, "env", None)
    raw = os.getenv("SC_JWT_EXP_SECONDS")
    if not raw and env is not None:
        try:
            raw = env["ir.config_parameter"].sudo().get_param("sc.jwt.exp_seconds")
        except Exception:
            raw = None
    try:
        val = int(raw)
        if val > 0:
            return val
    except Exception:
        pass
    return DEFAULT_EXP_SECONDS

def generate_token(user_id, token_version: int | None = None, db: str | None = None):
    now = int(time.time())
    exp = now + get_token_exp_seconds()
    payload = {
        "user_id": user_id,
        "iat": now,
        "exp": exp,
        "jti": uuid.uuid4().hex,
    }
    if token_version is not None:
        payload["token_version"] = int(token_version)
    if db:
        payload["db"] = str(db).strip()
    return jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)

def decode_token(token):
    try:
        return jwt.decode(
            token,
            _get_secret_key(),
            algorithms=[ALGORITHM],
            options={"require": ["exp", "iat", "jti", "token_version"]},
        )
    except jwt.ExpiredSignatureError:
        raise AccessDenied("Token 已过期")
    except jwt.MissingRequiredClaimError:
        raise AccessDenied("Token 缺少必要字段")
    except jwt.InvalidTokenError:
        raise AccessDenied("无效的 Token")

def get_user_from_token():
    """
    从请求中提取 Token 并解析用户对象。兼容系统原生登录与自定义 Token 登录。
    """
    auth_header = request.httprequest.headers.get("Authorization")
    session = getattr(request, "session", None)
    session_uid = getattr(session, "uid", None)

    if auth_header:
        token = auth_header.split(" ")[-1]
        payload = decode_token(token)
        user_id = payload.get("user_id")
        token_db = str(payload.get("db") or "").strip()
        db_name = token_db or getattr(getattr(request, "session", None), "db", None) or getattr(request, "db", None)
        if not db_name:
            raise AccessDenied("Token 缺少数据库信息")
        registry = Registry(db_name)
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            user = env["res.users"].sudo().browse(user_id)
            if not user.exists():
                raise AccessDenied("Token 中指定的用户不存在")
            current_version = int(getattr(user, "token_version", 0) or 0)
        token_version = int(payload.get("token_version") or 0)
        if token_version != current_version:
            raise AccessDenied("Token 已撤销")
        # Return a user record bound to the current request env/cursor.
        # The `user` record above was created on a temporary cursor.
        request_user = request.env["res.users"].sudo().browse(user_id)
        if not request_user.exists():
            raise AccessDenied("Token 中指定的用户不存在")
        return request_user

    elif session_uid:
        user = request.env["res.users"].browse(session_uid)
        if not user.exists():
            raise AccessDenied("系统 Session 中的用户无效")
        return user

    else:
        raise AccessDenied("未提供 Token 或未登录 Session")

def authenticate_user(login, password, db: str | None = None):
    """
    基于用户名和密码校验用户身份，并返回登录用户对象
    """
    timings_ms: Dict[str, int] = {}

    def _mark(stage: str, started_at: float) -> float:
        timings_ms[stage] = int((time.perf_counter() - started_at) * 1000)
        return time.perf_counter()

    stage_ts = time.perf_counter()
    session_db = getattr(getattr(request, "session", None), "db", None)
    query_db = None
    if getattr(request, "httprequest", None) is not None:
        try:
            query_db = request.httprequest.args.get("db")
        except Exception:
            query_db = None
    env_db = getattr(getattr(getattr(request, "env", None), "cr", None), "dbname", None)
    config_db = config.get("db_name")
    if isinstance(config_db, str) and "," in config_db:
        config_db = next((item.strip() for item in config_db.split(",") if item.strip()), None)
    elif isinstance(config_db, (list, tuple)):
        config_db = next((str(item).strip() for item in config_db if str(item).strip()), None)

    db = db or session_db or query_db or env_db or config_db
    stage_ts = _mark("db_resolution", stage_ts)
    if not db:
        raise AccessDenied("未指定数据库")
    registry = Registry(db)
    stage_ts = _mark("registry_acquire", stage_ts)

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        user_record = env["res.users"].sudo().search([("login", "=", login)], limit=1)
        stage_ts = _mark("user_lookup", stage_ts)

        if not user_record:
            raise AccessDenied("用户名不存在")

        # ✅ 正确方式：构建含 interactive 的 context
        context = dict(env.context, interactive=True)
        user_env = api.Environment(cr, user_record.id, context)
        stage_ts = _mark("user_env_build", stage_ts)

        try:
            user_record.with_env(user_env)._check_credentials(password,user_env)
        except AccessDenied:
            raise AccessDenied("密码错误")
        _mark("check_credentials", stage_ts)

        return {
            "id": user_record.id,
            "login": user_record.login,
            "name": user_record.name,
            "db": db,
            "timings_ms": timings_ms,
        }
