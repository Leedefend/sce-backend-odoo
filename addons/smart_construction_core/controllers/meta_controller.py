# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request

from .api_base import fail, fail_from_exception, ok


class MetaController(http.Controller):

    @http.route("/api/meta/describe_model", type="http", auth="user", methods=["GET", "POST"], csrf=False)
    def describe_model(self, **params):
        payload = _merge_payload(params)
        model = (payload.get("model") or "").strip()
        if not model:
            return fail("BAD_REQUEST", "model required", http_status=400)
        if model not in request.env:
            return fail("NOT_FOUND", "Unknown model", details={"model": model}, http_status=404)

        env = request.env[model]
        try:
            env.check_access_rights("read")
        except Exception:
            return fail("FORBIDDEN", "Access denied", http_status=403)

        try:
            fields = env.fields_get()
            out_fields = []
            for name, info in fields.items():
                out_fields.append({
                    "name": name,
                    "string": info.get("string"),
                    "ttype": info.get("type"),
                    "required": bool(info.get("required")),
                    "readonly": bool(info.get("readonly")),
                    "relation": info.get("relation"),
                    "selection": info.get("selection"),
                    "domain": info.get("domain"),
                    "help": info.get("help"),
                })
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

        data = {
            "model": model,
            "fields": out_fields,
            "schema_version": "model-fields-v1",
        }
        return ok(data, status=200)

    @http.route("/api/meta/project_capabilities", type="http", auth="user", methods=["GET", "POST"], csrf=False)
    def describe_project_capabilities(self, **params):
        payload = _merge_payload(params)
        project_id = payload.get("project_id") or payload.get("id")
        if not project_id:
            return fail("BAD_REQUEST", "project_id required", http_status=400)
        try:
            project_id = int(project_id)
        except Exception:
            return fail("BAD_REQUEST", "project_id invalid", http_status=400)

        Project = request.env["project.project"]
        project = Project.browse(project_id)
        if not project.exists():
            return fail("NOT_FOUND", "Project not found", details={"project_id": project_id}, http_status=404)

        try:
            project.check_access_rights("read")
            project.check_access_rule("read")
        except Exception:
            return fail("FORBIDDEN", "Access denied", http_status=403)

        try:
            from odoo.addons.smart_construction_core.services.lifecycle_capability_service import (
                LifecycleCapabilityService,
            )

            service = LifecycleCapabilityService(request.env)
            data = service.describe_project(project)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

        data["project_id"] = project_id
        data["schema_version"] = "lifecycle-capability-v1"
        return ok(data, status=200)


def _merge_payload(params):
    payload = dict(params or {})
    try:
        if request.jsonrequest:
            payload.update(request.jsonrequest)
    except Exception:
        pass
    return payload
