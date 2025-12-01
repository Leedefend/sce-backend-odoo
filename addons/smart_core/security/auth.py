# smart_core/security/auth.py
import jwt
import logging
from odoo.http import request
from odoo import http, SUPERUSER_ID, api
from odoo.exceptions import AccessDenied
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)

SECRET_KEY = "odoo-smart-core"
ALGORITHM = "HS256"

def generate_token(user_id):
    payload = {"user_id": user_id}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AccessDenied("Token 已过期")
    except jwt.InvalidTokenError:
        raise AccessDenied("无效的 Token")

def get_user_from_token():
    """
    从请求中提取 Token 并解析用户对象。兼容系统原生登录与自定义 Token 登录。
    """
    auth_header = request.httprequest.headers.get("Authorization")
    session_uid = request.session.uid

    if auth_header:
        token = auth_header.split(" ")[-1]
        payload = decode_token(token)
        user_id = payload.get("user_id")
        user = request.env["res.users"].browse(user_id)
        if not user.exists():
            raise AccessDenied("Token 中指定的用户不存在")
        return user

    elif session_uid:
        user = request.env["res.users"].browse(session_uid)
        if not user.exists():
            raise AccessDenied("系统 Session 中的用户无效")
        return user

    else:
        raise AccessDenied("未提供 Token 或未登录 Session")

def authenticate_user(login, password):
    """
    基于用户名和密码校验用户身份，并返回登录用户对象
    """
    db = request.session.db or request.httprequest.args.get("db") or "odoo17-dev01"
    if not db:
        raise AccessDenied("未指定数据库")
    registry = Registry(db)

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        user_record = env["res.users"].sudo().search([("login", "=", login)], limit=1)

        if not user_record:
            raise AccessDenied("用户名不存在")

        # ✅ 正确方式：构建含 interactive 的 context
        context = dict(env.context, interactive=True)
        user_env = api.Environment(cr, user_record.id, context)

        try:
            user_record.with_env(user_env)._check_credentials(password,user_env)
        except AccessDenied:
            raise AccessDenied("密码错误")

        return {
            "id": user_record.id,
            "login": user_record.login,
            "name": user_record.name,
        }
