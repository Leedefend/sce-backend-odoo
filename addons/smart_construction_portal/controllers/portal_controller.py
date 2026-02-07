# -*- coding: utf-8 -*-
from __future__ import annotations

from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

from odoo import http
from odoo.http import request

from odoo.addons.smart_construction_core.controllers.api_base import ok, fail
from odoo.addons.smart_construction_portal.services.portal_contract_service import (
    PortalContractService,
)
from odoo.addons.smart_core.security.auth import decode_token


class PortalController(http.Controller):
    @http.route("/portal/bridge", type="http", auth="public", methods=["GET"], csrf=False)
    def portal_bridge(self, **params):
        token = (params.get("token") or "").strip()
        next_url = _sanitize_portal_next(params.get("next"))
        db_name = (params.get("db") or request.session.db or request.env.cr.dbname or "").strip()
        if not token:
            return request.redirect("/web/login?redirect=%s" % next_url)
        user = _resolve_user_from_token(token)
        if not user:
            return request.redirect("/web/login?redirect=%s" % next_url)
        if db_name:
            request.session.db = db_name
        _bind_session_user(user)
        next_url = _append_token_query(next_url, token)
        return request.redirect(next_url)

    @http.route("/portal/lifecycle", type="http", auth="public", methods=["GET"], csrf=False)
    def portal_lifecycle(self, **params):
        if not _ensure_portal_user(params):
            return request.redirect("/web/login?redirect=/portal/lifecycle")
        if not _portal_enabled(request.env):
            return request.not_found()
        payload = _merge_payload(params)
        project_id = payload.get("project_id") or payload.get("id")
        return request.render(
            "smart_construction_portal.portal_lifecycle_page",
            {"project_id": project_id or ""},
        )

    @http.route("/portal/capability-matrix", type="http", auth="public", methods=["GET"], csrf=False)
    def portal_capability_matrix(self, **params):
        if not _ensure_portal_user(params):
            return request.redirect("/web/login?redirect=/portal/capability-matrix")
        if not _portal_capability_matrix_enabled(request.env):
            return request.not_found()
        return request.render(
            "smart_construction_portal.portal_capability_matrix_page",
            {},
        )

    @http.route("/portal/dashboard", type="http", auth="public", methods=["GET"], csrf=False)
    def portal_dashboard(self, **params):
        if not _ensure_portal_user(params):
            return request.redirect("/web/login?redirect=/portal/dashboard")
        if not _portal_dashboard_enabled(request.env):
            return request.not_found()
        return request.render(
            "smart_construction_portal.portal_dashboard_page",
            {},
        )

    @http.route("/api/portal/contract", type="http", auth="public", methods=["GET", "POST"], csrf=False)
    def portal_contract(self, **params):
        if not _ensure_portal_user(params):
            return fail("AUTH_REQUIRED", "认证失败或 token 无效", http_status=401)
        if not _portal_enabled(request.env):
            return fail("NOT_FOUND", "Portal disabled", http_status=404)
        payload = _merge_payload(params)
        route = payload.get("route") or "/portal/lifecycle"
        trace_id = payload.get("trace_id")
        service = PortalContractService(request.env)
        data = service.build_lifecycle_dashboard(route=route, trace_id=trace_id)
        return ok(data, status=200)


def _merge_payload(params):
    payload = dict(params or {})
    try:
        if request.jsonrequest:
            payload.update(request.jsonrequest)
    except Exception:
        pass
    return payload


def _portal_enabled(env):
    value = env["ir.config_parameter"].sudo().get_param("sc.portal.lifecycle.enabled", "1")
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _portal_capability_matrix_enabled(env):
    value = env["ir.config_parameter"].sudo().get_param("sc.portal.capability_matrix.enabled", "1")
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _portal_dashboard_enabled(env):
    value = env["ir.config_parameter"].sudo().get_param("sc.portal.dashboard.enabled", "1")
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _sanitize_portal_next(next_url):
    candidate = str(next_url or "").strip()
    if not candidate.startswith("/portal/"):
        return "/portal/lifecycle"
    return candidate


def _resolve_user_from_token(token):
    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
        user = request.env["res.users"].sudo().browse(int(user_id))
        if not user.exists():
            return None
        current_version = int(getattr(user, "token_version", 0) or 0)
        token_version = int(payload.get("token_version") or 0)
        if token_version != current_version:
            return None
        return user
    except Exception:
        return None


def _append_token_query(url, token):
    if not token:
        return url
    try:
        split = urlsplit(url)
        q = dict(parse_qsl(split.query, keep_blank_values=True))
        q.setdefault("st", token)
        return urlunsplit((split.scheme, split.netloc, split.path, urlencode(q), split.fragment))
    except Exception:
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}st={token}"


def _extract_token(params):
    payload = params or {}
    token = (payload.get("st") or payload.get("token") or "").strip()
    if token:
        return token
    auth_header = request.httprequest.headers.get("Authorization") or ""
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return ""


def _ensure_portal_user(params):
    session_uid = getattr(getattr(request, "session", None), "uid", None)
    if session_uid:
        user = request.env["res.users"].sudo().browse(int(session_uid))
        if user.exists():
            return user
    token = _extract_token(params)
    if not token:
        return None
    user = _resolve_user_from_token(token)
    if not user:
        return None
    _bind_session_user(user)
    try:
        request.update_env(user=user.id)
    except Exception:
        pass
    return user


def _bind_session_user(user):
    try:
        request.session.uid = user.id
        request.session.login = user.login
        sid = getattr(request.session, "sid", None)
        if sid and hasattr(user, "_compute_session_token"):
            request.session.session_token = user._compute_session_token(sid)
    except Exception:
        pass
