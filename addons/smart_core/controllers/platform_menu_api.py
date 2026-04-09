# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

from odoo.addons.smart_core.core.trace import get_trace_id
from odoo.addons.smart_core.delivery.menu_fact_service import MenuFactService
from odoo.addons.smart_core.delivery.menu_target_interpreter_service import MenuTargetInterpreterService
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


def _fact_node(node: dict) -> dict:
    children = node.get("children") if isinstance(node.get("children"), list) else []
    menu_id = node.get("menu_id")
    return {
        "menu_id": menu_id,
        "key": f"menu:{menu_id}" if isinstance(menu_id, int) else "menu:unknown",
        "name": str(node.get("name") or ""),
        "parent_id": node.get("parent_id"),
        "complete_name": str(node.get("complete_name") or ""),
        "sequence": node.get("sequence"),
        "groups": node.get("groups") if isinstance(node.get("groups"), list) else [],
        "web_icon": str(node.get("web_icon") or ""),
        "has_children": bool(children),
        "action_raw": str(node.get("action_raw") or ""),
        "action_type": str(node.get("action_type") or ""),
        "action_id": node.get("action_id"),
        "action_exists": bool(node.get("action_exists")),
        "action_meta": node.get("action_meta") if isinstance(node.get("action_meta"), dict) else {},
        "children": [_fact_node(child) for child in children],
    }


def _flat_fact_node(node: dict) -> dict:
    menu_id = node.get("menu_id")
    child_ids = node.get("child_ids") if isinstance(node.get("child_ids"), list) else []
    return {
        "menu_id": menu_id,
        "key": f"menu:{menu_id}" if isinstance(menu_id, int) else "menu:unknown",
        "name": str(node.get("name") or ""),
        "parent_id": node.get("parent_id"),
        "complete_name": str(node.get("complete_name") or ""),
        "sequence": node.get("sequence"),
        "groups": node.get("groups") if isinstance(node.get("groups"), list) else [],
        "web_icon": str(node.get("web_icon") or ""),
        "has_children": bool(child_ids),
        "action_raw": str(node.get("action_raw") or ""),
        "action_type": str(node.get("action_type") or ""),
        "action_id": node.get("action_id"),
        "action_exists": bool(node.get("action_exists")),
        "action_meta": node.get("action_meta") if isinstance(node.get("action_meta"), dict) else {},
        "child_ids": child_ids,
    }


class PlatformMenuAPI(http.Controller):
    @http.route('/api/menu/tree', type='json', auth='user', csrf=False, cors='*', methods=['POST'])
    def api_menu_tree(self, **kwargs):
        del kwargs
        trace_id = get_trace_id(request.httprequest.headers)
        facts = MenuFactService(request.env).export_visible_menu_facts()
        if not facts.flat:
            return _error_resp(BAD_REQUEST, '未找到平台菜单根节点。', trace_id)
        nav_fact = {
            "flat": [_flat_fact_node(node) for node in facts.flat],
            "tree": [_fact_node(node) for node in facts.tree],
        }
        return {'ok': True, 'nav_fact': nav_fact, 'meta': _meta(trace_id)}

    @http.route('/api/user_menus', type='json', auth='user', csrf=False, cors='*', methods=['POST'])
    def api_user_menus(self, **kwargs):
        return self.api_menu_tree(**kwargs)

    @http.route('/api/menu/navigation', type='json', auth='user', csrf=False, cors='*', methods=['POST'])
    def api_menu_navigation(self, **kwargs):
        payload = kwargs if isinstance(kwargs, dict) else {}
        trace_id = get_trace_id(request.httprequest.headers)
        facts = MenuFactService(request.env).export_visible_menu_facts()
        if not facts.flat:
            return _error_resp(BAD_REQUEST, '未找到平台菜单根节点。', trace_id)

        nav_fact = {
            "flat": [_flat_fact_node(node) for node in facts.flat],
            "tree": [_fact_node(node) for node in facts.tree],
        }
        scene_map = payload.get("scene_map") if isinstance(payload.get("scene_map"), dict) else {}
        policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
        nav_explained = MenuTargetInterpreterService(request.env).interpret(
            nav_fact,
            scene_map=scene_map,
            policy=policy,
        )
        return {
            'ok': True,
            'nav_fact': nav_fact,
            'nav_explained': nav_explained,
            'meta': _meta(trace_id),
        }
