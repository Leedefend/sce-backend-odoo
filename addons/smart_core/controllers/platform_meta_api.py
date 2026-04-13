# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime

from odoo import http
from odoo.http import request

from odoo.addons.smart_core.core.trace import get_trace_id
from odoo.addons.smart_core.core.industry_runtime_service_adapter import (
    describe_project_capabilities,
)


CONTRACT_VERSION = "v1"


def _server_time() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _json_response(payload, status=200):
    return request.make_response(
        json.dumps(payload, ensure_ascii=False, default=str),
        headers=[("Content-Type", "application/json; charset=utf-8")],
        status=status,
    )


def _ok(data, status=200):
    trace_id = get_trace_id(request.httprequest.headers)
    return _json_response(
        {
            "ok": True,
            "data": data,
            "error": None,
            "meta": {
                "contract_version": CONTRACT_VERSION,
                "server_time": _server_time(),
                "trace_id": trace_id,
                "warnings": [],
            },
            "effect": None,
        },
        status=status,
    )


def _fail(code, message, details=None, http_status=400):
    trace_id = get_trace_id(request.httprequest.headers)
    return _json_response(
        {
            "ok": False,
            "data": None,
            "error": {
                "code": str(code),
                "message": message,
                "details": details or {},
                "trace_id": trace_id,
            },
            "meta": {
                "contract_version": CONTRACT_VERSION,
                "server_time": _server_time(),
                "trace_id": trace_id,
                "warnings": [],
            },
            "effect": None,
        },
        status=http_status,
    )


def _fail_from_exception(error, http_status=500):
    return _fail(
        "SERVER_ERROR",
        "Internal server error",
        details={"error": str(error)},
        http_status=http_status,
    )


def _merge_payload(params):
    payload = dict(params or {})
    try:
        if request.jsonrequest:
            payload.update(request.jsonrequest)
    except Exception:
        pass
    return payload


def _resolve_model_env(model_name):
    if model_name not in request.env:
        return None
    return request.env[model_name]


def _project_model_env():
    return request.env["project.project"]


def _serialize_model_fields(fields):
    output = []
    for field_name, info in fields.items():
        output.append(
            {
                "name": field_name,
                "string": info.get("string"),
                "ttype": info.get("type"),
                "required": bool(info.get("required")),
                "readonly": bool(info.get("readonly")),
                "relation": info.get("relation"),
                "selection": info.get("selection"),
                "domain": info.get("domain"),
                "help": info.get("help"),
            }
        )
    return output


class PlatformMetaAPI(http.Controller):
    @http.route("/api/meta/project_capabilities", type="http", auth="user", methods=["GET", "POST"], csrf=False)
    def describe_project_capabilities(self, **params):
        payload = _merge_payload(params)
        project_id = payload.get("project_id") or payload.get("id")
        if not project_id:
            return _fail("BAD_REQUEST", "project_id required", http_status=400)
        try:
            project_id = int(project_id)
        except Exception:
            return _fail("BAD_REQUEST", "project_id invalid", http_status=400)

        project_env = _project_model_env()
        project = project_env.browse(project_id)
        if not project.exists():
            return _fail("NOT_FOUND", "Project not found", details={"project_id": project_id}, http_status=404)

        try:
            project.check_access_rights("read")
            project.check_access_rule("read")
        except Exception:
            return _fail("FORBIDDEN", "Access denied", http_status=403)

        try:
            data = describe_project_capabilities(request.env, project)
        except Exception as error:
            return _fail_from_exception(error, http_status=500)

        data["project_id"] = project_id
        data["schema_version"] = "lifecycle-capability-v1"
        return _ok(data, status=200)

    @http.route("/api/meta/describe_model", type="http", auth="user", methods=["GET", "POST"], csrf=False)
    def describe_model(self, **params):
        payload = _merge_payload(params)
        model = (payload.get("model") or "").strip()
        if not model:
            return _fail("BAD_REQUEST", "model required", http_status=400)

        model_env = _resolve_model_env(model)
        if model_env is None:
            return _fail("NOT_FOUND", "Unknown model", details={"model": model}, http_status=404)

        try:
            model_env.check_access_rights("read")
        except Exception:
            return _fail("FORBIDDEN", "Access denied", http_status=403)

        try:
            out_fields = _serialize_model_fields(model_env.fields_get())
        except Exception as error:
            return _fail_from_exception(error, http_status=500)

        data = {
            "model": model,
            "fields": out_fields,
            "schema_version": "model-fields-v1",
        }
        return _ok(data, status=200)
