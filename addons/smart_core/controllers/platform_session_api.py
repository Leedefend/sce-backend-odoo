# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api, http
from odoo.http import request
from odoo.modules.registry import Registry
from odoo.service import db as service_db

from odoo.addons.smart_core.core.trace import get_trace_id
from odoo.addons.smart_core.core.exceptions import (
    AUTH_REQUIRED,
    BAD_REQUEST,
    DEFAULT_API_VERSION,
    DEFAULT_CONTRACT_VERSION,
    INTERNAL_ERROR,
    build_error_envelope,
)


def _get_payload(kwargs: dict) -> dict:
    data = getattr(request, "jsonrequest", None)
    if isinstance(data, dict):
        return data
    try:
        data2 = request.httprequest.get_json()
        if isinstance(data2, dict):
            return data2
    except Exception:
        pass
    return {}


def _pick_db(payload: dict, kwargs: dict) -> str | None:
    db = (
        payload.get("db")
        or payload.get("database")
        or kwargs.get("db")
        or kwargs.get("database")
        or request.session.db
        or request.db
    )
    if db:
        return db
    try:
        dbs = service_db.list_dbs()
        if len(dbs) == 1:
            return dbs[0]
    except Exception:
        pass
    return None


def _meta(trace_id: str) -> dict:
    return {
        "trace_id": trace_id,
        "api_version": DEFAULT_API_VERSION,
        "contract_version": DEFAULT_CONTRACT_VERSION,
    }


def _error_resp(code: str, message: str, trace_id: str, details: dict | None = None):
    return build_error_envelope(
        code=code,
        message=message,
        trace_id=trace_id,
        details=details,
        api_version=DEFAULT_API_VERSION,
        contract_version=DEFAULT_CONTRACT_VERSION,
    )


def _load_user_basic(db: str, uid: int) -> dict | None:
    try:
        registry = Registry(db)
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            user = env["res.users"].sudo().browse(int(uid))
            if not user.exists():
                return None
            return {"id": user.id, "name": user.name, "login": user.login}
    except Exception:
        return None


class PlatformSessionAPI(http.Controller):
    @http.route('/api/login', type='json', auth='public', csrf=False, cors='*', methods=['POST'])
    def api_login(self, **kwargs):
        trace_id = get_trace_id(request.httprequest.headers)
        payload = _get_payload(kwargs)
        login = payload.get('login') or kwargs.get('login')
        password = payload.get('password') or kwargs.get('password')
        db = _pick_db(payload, kwargs)

        if not db:
            return _error_resp(BAD_REQUEST, '缺少数据库参数 db / database。', trace_id)
        if not login or not password:
            return _error_resp(BAD_REQUEST, '缺少用户名或密码。', trace_id)

        try:
            uid = request.session.authenticate(db, login, password)
            if not uid:
                return _error_resp(AUTH_REQUIRED, '账号或密码错误。', trace_id)

            user = _load_user_basic(db, uid)
            if not user:
                return _error_resp(INTERNAL_ERROR, '内部错误', trace_id, {'error': 'user profile load failed'})
            return {
                'ok': True,
                'uid': uid,
                'session_id': request.session.sid,
                'db': db,
                'user': user,
                'meta': _meta(trace_id),
            }
        except Exception as error:
            request.env.cr.rollback()
            return _error_resp(INTERNAL_ERROR, '内部错误', trace_id, {'error': str(error)})

    @http.route('/api/logout', type='json', auth='public', csrf=False, cors='*', methods=['POST'])
    def api_logout(self, **kwargs):
        trace_id = get_trace_id(request.httprequest.headers)
        request.session.logout(keep_db=True)
        return {'ok': True, 'meta': _meta(trace_id)}

    @http.route('/api/session/get', type='json', auth='public', csrf=False, cors='*', methods=['POST'])
    def api_session_get(self, **kwargs):
        trace_id = get_trace_id(request.httprequest.headers)
        uid = request.session.uid
        if not uid:
            return {'ok': True, 'logged_in': False, 'db': request.session.db or request.db, 'meta': _meta(trace_id)}
        db = request.session.db or request.db or ""
        user = _load_user_basic(db, uid) if db else None
        if not user:
            return {'ok': True, 'logged_in': False, 'db': db, 'meta': _meta(trace_id)}
        return {
            'ok': True,
            'logged_in': True,
            'uid': uid,
            'db': db,
            'user': user,
            'meta': _meta(trace_id),
        }
