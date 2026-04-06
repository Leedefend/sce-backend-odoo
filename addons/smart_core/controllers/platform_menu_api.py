# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

from odoo.addons.smart_core.core.trace import get_trace_id
from odoo.addons.smart_core.core.exceptions import (
    BAD_REQUEST,
    DEFAULT_API_VERSION,
    DEFAULT_CONTRACT_VERSION,
    build_error_envelope,
)


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


def _serialize_menu(menu):
    children = menu.child_id.sorted(lambda m: m.sequence or 10)
    return {
        'id': menu.id,
        'name': menu.name,
        'action': menu.action and menu.action.id or None,
        'children': [_serialize_menu(child) for child in children],
    }


def _resolve_generic_root_menu():
    root = request.env.ref('base.menu_root', raise_if_not_found=False)
    if root:
        return root.sudo()
    menu_model = request.env['ir.ui.menu'].sudo()
    fallback = menu_model.search([('parent_id', '=', False)], limit=1, order='sequence,id')
    return fallback if fallback else None


class PlatformMenuAPI(http.Controller):
    @http.route('/api/menu/tree', type='json', auth='user', csrf=False, cors='*', methods=['POST'])
    def api_menu_tree(self, **kwargs):
        del kwargs
        trace_id = get_trace_id(request.httprequest.headers)
        root = _resolve_generic_root_menu()
        if not root:
            return _error_resp(BAD_REQUEST, '未找到平台菜单根节点。', trace_id)
        return {'ok': True, 'menu': _serialize_menu(root), 'meta': _meta(trace_id)}

    @http.route('/api/user_menus', type='json', auth='user', csrf=False, cors='*', methods=['POST'])
    def api_user_menus(self, **kwargs):
        return self.api_menu_tree(**kwargs)
