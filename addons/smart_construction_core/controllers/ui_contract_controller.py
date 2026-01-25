# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request

from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler

from .api_base import fail, fail_from_exception, ok


class UiContractController(http.Controller):

    @http.route("/api/ui/contract", type="http", auth="user", methods=["GET", "POST"], csrf=False)
    def ui_contract(self, **params):
        payload = _merge_payload(params)
        model = (payload.get("model") or "").strip()
        if not model:
            return fail("BAD_REQUEST", "model required", http_status=400)

        view_type = (payload.get("view_type") or payload.get("viewType") or "form").strip().lower()
        if view_type == "tree":
            view_type = "list"
        payload.setdefault("op", "model")
        payload["model"] = model
        payload["view_type"] = view_type

        handler = UiContractHandler(request.env, request=request, payload=payload)
        try:
            res = handler.handle(payload=payload)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)
        if isinstance(res, dict) and res.get("ok") is False:
            err = res.get("error") or {}
            raw_code = err.get("code") or "BAD_REQUEST"
            message = err.get("message") or "Invalid request"
            details = {"source": "ui_contract_handler"}
            if isinstance(raw_code, int):
                status = raw_code
            elif str(raw_code).isdigit():
                status = int(raw_code)
            else:
                status = 400
            code = _normalize_code(raw_code, status)
            return fail(code, message, details=details, http_status=status)

        data = res.get("data") if isinstance(res, dict) else {}
        normalized = _normalize_contract(data, model=model, view_type=view_type)
        normalized["raw"] = data
        return ok(normalized, status=200)


def _normalize_contract(data, model, view_type):
    views = (data or {}).get("views") or {}
    if view_type == "form":
        form = views.get("form") or {}
        title_field = getattr(request.env[model], "_rec_name", None) or "name"
        return {
            "model": model,
            "view_type": "form",
            "titleField": title_field,
            "headerButtons": form.get("header_buttons") or [],
            "statButtons": form.get("stat_buttons") or form.get("button_box") or [],
            "ribbon": form.get("ribbon"),
            "sheet": form.get("layout") or [],
            "chatter": form.get("chatter") or {},
        }

    tree = views.get("tree") or views.get("list") or {}
    return {
        "model": model,
        "view_type": "list",
        "columns": tree.get("columns") or [],
        "columnsSchema": tree.get("columns_schema") or [],
    }


def _merge_payload(params):
    payload = dict(params or {})
    try:
        if request.jsonrequest:
            payload.update(request.jsonrequest)
    except Exception:
        pass
    return payload


def _normalize_code(raw_code, status):
    if isinstance(raw_code, str) and raw_code.isupper():
        return raw_code
    if status == 403:
        return "FORBIDDEN"
    if status == 404:
        return "NOT_FOUND"
    if status >= 500:
        return "SERVER_ERROR"
    return "BAD_REQUEST"
