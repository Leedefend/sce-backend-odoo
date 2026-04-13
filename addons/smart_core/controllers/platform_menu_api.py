# -*- coding: utf-8 -*-
import json

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied

from odoo.addons.smart_core.core.trace import get_trace_id
from odoo.addons.smart_core.delivery.menu_fact_service import MenuFactService
from odoo.addons.smart_core.delivery.menu_delivery_convergence_service import MenuDeliveryConvergenceService
from odoo.addons.smart_core.delivery.menu_target_interpreter_service import MenuTargetInterpreterService
from odoo.addons.smart_core.security.auth import get_user_from_token
from odoo.addons.smart_core.core.exceptions import (
    AUTH_REQUIRED,
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


def _json_response(payload: dict, status: int = 200):
    return request.make_response(
        json.dumps(payload, ensure_ascii=False, default=str),
        headers=[('Content-Type', 'application/json; charset=utf-8')],
        status=status,
    )


def _resolve_request_env():
    user = get_user_from_token()
    return request.env(user=user)


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


def _is_admin_user(env) -> bool:
    try:
        return bool(env.user.has_group('base.group_system'))
    except Exception:
        return False


class PlatformMenuAPI(http.Controller):
    @http.route('/api/menu/tree', type='http', auth='public', csrf=False, cors='*', methods=['POST'])
    def api_menu_tree(self, **kwargs):
        del kwargs
        trace_id = get_trace_id(request.httprequest.headers)
        try:
            env = _resolve_request_env()
        except AccessDenied as exc:
            return _json_response(
                _error_resp(AUTH_REQUIRED, str(exc) or '登录态无效，请重新登录。', trace_id),
                status=401,
            )
        facts = MenuFactService(env).export_visible_menu_facts()
        if not facts.flat:
            return _json_response(_error_resp(BAD_REQUEST, '未找到平台菜单根节点。', trace_id), status=400)
        nav_fact = {
            "flat": [_flat_fact_node(node) for node in facts.flat],
            "tree": [_fact_node(node) for node in facts.tree],
        }
        nav_explained = MenuTargetInterpreterService(env).interpret(nav_fact, scene_map={}, policy={})
        nav_fact_filtered, _, convergence = MenuDeliveryConvergenceService().apply(
            nav_fact,
            nav_explained,
            is_admin=_is_admin_user(env),
        )
        return _json_response({'ok': True, 'nav_fact': nav_fact_filtered, 'meta': {**_meta(trace_id), 'delivery_convergence': convergence}})

    @http.route('/api/user_menus', type='http', auth='public', csrf=False, cors='*', methods=['POST'])
    def api_user_menus(self, **kwargs):
        return self.api_menu_tree(**kwargs)

    @http.route('/api/menu/navigation', type='http', auth='public', csrf=False, cors='*', methods=['POST'])
    def api_menu_navigation(self, **kwargs):
        payload = kwargs if isinstance(kwargs, dict) else {}
        if not payload:
            json_payload = request.httprequest.get_json(silent=True)
            payload = json_payload if isinstance(json_payload, dict) else {}
        trace_id = get_trace_id(request.httprequest.headers)
        try:
            env = _resolve_request_env()
        except AccessDenied as exc:
            return _json_response(
                _error_resp(AUTH_REQUIRED, str(exc) or '登录态无效，请重新登录。', trace_id),
                status=401,
            )
        facts = MenuFactService(env).export_visible_menu_facts()
        if not facts.flat:
            return _json_response(_error_resp(BAD_REQUEST, '未找到平台菜单根节点。', trace_id), status=400)

        nav_fact = {
            "flat": [_flat_fact_node(node) for node in facts.flat],
            "tree": [_fact_node(node) for node in facts.tree],
        }
        scene_map = payload.get("scene_map") if isinstance(payload.get("scene_map"), dict) else {}
        policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
        nav_explained = MenuTargetInterpreterService(env).interpret(
            nav_fact,
            scene_map=scene_map,
            policy=policy,
        )
        nav_fact_filtered, nav_explained_filtered, convergence = MenuDeliveryConvergenceService().apply(
            nav_fact,
            nav_explained,
            is_admin=_is_admin_user(env),
        )
        return _json_response(
            {
                'ok': True,
                'nav_fact': nav_fact_filtered,
                'nav_explained': nav_explained_filtered,
                'meta': {**_meta(trace_id), 'delivery_convergence': convergence},
            }
        )
