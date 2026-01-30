# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.service import db as service_db
from odoo.addons.smart_core.core.trace import get_trace_id
from odoo.addons.smart_core.core.exceptions import (
    BAD_REQUEST,
    AUTH_REQUIRED,
    INTERNAL_ERROR,
    DEFAULT_API_VERSION,
    DEFAULT_CONTRACT_VERSION,
    build_error_envelope,
)

# ------- 工具函数 -------

def _get_payload(kwargs: dict) -> dict:
    """
    稳健获取前端 JSON 体：
    1) 优先用 request.jsonrequest（type='json' 自动解析）
    2) 回退用 request.httprequest.get_json()
    3) 最后回空 dict
    """
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
    """
    尽可能稳健地获取数据库名称，兼容 db / database 字段，并在单库时回退到唯一库。
    """
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

# ------- 控制器 -------

class FrontendAPI(http.Controller):

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

            user = request.env['res.users'].sudo().browse(uid)
            return {
                'ok': True,
                'uid': uid,
                'session_id': request.session.sid,
                'db': db,
                'user': {'id': user.id, 'name': user.name, 'login': user.login},
                'meta': _meta(trace_id),
            }
        except Exception as e:
            request.env.cr.rollback()
            return _error_resp(INTERNAL_ERROR, '内部错误', trace_id, {'error': str(e)})

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
        user = request.env['res.users'].sudo().browse(uid)
        return {
            'ok': True,
            'logged_in': True,
            'uid': uid,
            'db': request.session.db or request.db,
            'user': {'id': user.id, 'name': user.name, 'login': user.login},
            'meta': _meta(trace_id),
        }

    @http.route('/api/menu/tree', type='json', auth='user', csrf=False, cors='*', methods=['POST'])
    def api_menu_tree(self, **kwargs):
        trace_id = get_trace_id(request.httprequest.headers)
        """从我们模块根菜单（external id：smart_construction_enterprise.menu_sc_root）返回可见树。"""
        try:
            root = request.env.ref('smart_construction_enterprise.menu_sc_root').sudo()
        except Exception:
            return _error_resp(BAD_REQUEST, '未找到业务根菜单。', trace_id)

        def serialize(menu):
            children = menu.child_id.sorted(lambda m: m.sequence or 10)
            return {
                'id': menu.id,
                'name': menu.name,
                'action': menu.action and menu.action.id or None,
                'children': [serialize(ch) for ch in children],
            }

        return {'ok': True, 'menu': serialize(root), 'meta': _meta(trace_id)}

    @http.route('/api/user_menus', type='json', auth='user', csrf=False, cors='*', methods=['POST'])
    def api_user_menus(self, **kwargs):
        """等价于 /api/menu/tree，保持向后兼容。"""
        return self.api_menu_tree()
