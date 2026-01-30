# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.service import db as service_db

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


# ------- 控制器 -------

class FrontendAPI(http.Controller):

    @http.route('/api/login', type='json', auth='public', csrf=False, cors='*', methods=['POST'])
    def api_login(self, **kwargs):
        payload = _get_payload(kwargs)
        login = payload.get('login') or kwargs.get('login')
        password = payload.get('password') or kwargs.get('password')
        db = _pick_db(payload, kwargs)

        if not db:
            return {'ok': False, 'code': 'missing_db', 'message': '缺少数据库参数 db / database。'}
        if not login or not password:
            return {'ok': False, 'code': 'missing_credentials', 'message': '缺少用户名或密码。'}

        try:
            uid = request.session.authenticate(db, login, password)
            if not uid:
                return {'ok': False, 'code': 'auth_failed', 'message': '账号或密码错误。'}

            user = request.env['res.users'].sudo().browse(uid)
            return {
                'ok': True,
                'uid': uid,
                'session_id': request.session.sid,
                'db': db,
                'user': {'id': user.id, 'name': user.name, 'login': user.login},
            }
        except Exception as e:
            request.env.cr.rollback()
            return {'ok': False, 'code': 'server_error', 'message': str(e)}

    @http.route('/api/logout', type='json', auth='public', csrf=False, cors='*', methods=['POST'])
    def api_logout(self, **kwargs):
        request.session.logout(keep_db=True)
        return {'ok': True}

    @http.route('/api/session/get', type='json', auth='public', csrf=False, cors='*', methods=['POST'])
    def api_session_get(self, **kwargs):
        uid = request.session.uid
        if not uid:
            return {'ok': True, 'logged_in': False, 'db': request.session.db or request.db}
        user = request.env['res.users'].sudo().browse(uid)
        return {
            'ok': True,
            'logged_in': True,
            'uid': uid,
            'db': request.session.db or request.db,
            'user': {'id': user.id, 'name': user.name, 'login': user.login},
        }

    @http.route('/api/menu/tree', type='json', auth='user', csrf=False, cors='*', methods=['POST'])
    def api_menu_tree(self, **kwargs):
        """从我们模块根菜单（external id：smart_construction_enterprise.menu_sc_root）返回可见树。"""
        try:
            root = request.env.ref('smart_construction_enterprise.menu_sc_root').sudo()
        except Exception:
            return {'ok': False, 'code': 'menu_not_found', 'message': '未找到业务根菜单。'}

        def serialize(menu):
            children = menu.child_id.sorted(lambda m: m.sequence or 10)
            return {
                'id': menu.id,
                'name': menu.name,
                'action': menu.action and menu.action.id or None,
                'children': [serialize(ch) for ch in children],
            }

        return {'ok': True, 'menu': serialize(root)}

    @http.route('/api/user_menus', type='json', auth='user', csrf=False, cors='*', methods=['POST'])
    def api_user_menus(self, **kwargs):
        """等价于 /api/menu/tree，保持向后兼容。"""
        return self.api_menu_tree()
