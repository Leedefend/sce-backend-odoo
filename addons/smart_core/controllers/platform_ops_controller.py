# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from odoo import fields, http
from odoo.exceptions import AccessDenied
from odoo.http import request

from odoo.addons.smart_core.security.auth import get_user_from_token
from odoo.addons.smart_core.security.platform_admin import user_is_platform_admin
from odoo.addons.smart_core.core.trace import get_trace_id

CONTRACT_VERSION = "v1"


def _server_time() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_response(payload: dict[str, Any], status: int = 200):
    return request.make_response(
        json.dumps(payload, ensure_ascii=False, default=str),
        headers=[("Content-Type", "application/json; charset=utf-8")],
        status=status,
    )


def _ok(data: Any, status: int = 200):
    trace_id = get_trace_id()
    return _json_response(
        {
            "ok": True,
            "contract_version": CONTRACT_VERSION,
            "server_time": _server_time(),
            "trace_id": trace_id,
            "warnings": [],
            "data": data,
        },
        status=status,
    )


def _fail(code: str, message: str, *, details: dict[str, Any] | None = None, http_status: int = 400):
    trace_id = get_trace_id()
    return _json_response(
        {
            "ok": False,
            "contract_version": CONTRACT_VERSION,
            "server_time": _server_time(),
            "trace_id": trace_id,
            "warnings": [],
            "error": {
                "code": str(code),
                "message": message,
                "details": details or {},
                "trace_id": trace_id,
            },
        },
        status=http_status,
    )


def _fail_from_exception(exc: Exception, http_status: int = 500):
    return _fail(
        "SERVER_ERROR",
        "Internal server error",
        details={"error": str(exc)},
        http_status=http_status,
    )


def _platform_env():
    user = get_user_from_token()
    if not user_is_platform_admin(user):
        raise AccessDenied("insufficient permissions")
    return user, request.env(user=user)


class PlatformOpsController(http.Controller):
    @http.route("/api/ops/tenants", type="http", auth="public", methods=["GET"], csrf=False)
    def tenants(self, **params):
        try:
            _user, env = _platform_env()
            Company = env["res.company"].sudo()
            Entitlement = env.get("sc.entitlement")
            Usage = env.get("sc.usage.counter")
            Subscription = env.get("sc.subscription")
            companies = Company.search([], order="id")
            data = []
            for company in companies:
                ent_payload = {}
                if Entitlement:
                    ent = Entitlement.get_effective(company)
                    ent_payload = {
                        "plan_code": ent.plan_id.code if ent.plan_id else None,
                        "flags": ent.effective_flags_json or {},
                        "limits": ent.effective_limits_json or {},
                    }
                usage = Usage.get_usage_map(company) if Usage else {}
                sub = None
                if Subscription:
                    sub = Subscription.search([("company_id", "=", company.id)], order="start_date desc, id desc", limit=1)
                data.append({
                    "company_id": company.id,
                    "company_name": company.name,
                    "plan_code": ent_payload.get("plan_code"),
                    "flags": ent_payload.get("flags") or {},
                    "limits": ent_payload.get("limits") or {},
                    "usage": usage,
                    "subscription_state": sub.state if sub else None,
                })
            return _ok({"tenants": data, "count": len(data)}, status=200)
        except AccessDenied as exc:
            return _fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return _fail_from_exception(exc, http_status=500)

    @http.route("/api/ops/subscription/set", type="http", auth="public", methods=["POST"], csrf=False)
    def set_subscription(self, **params):
        try:
            _user, env = _platform_env()
            body = request.httprequest.get_json(force=True, silent=True) or {}
            company_id = body.get("company_id")
            plan_code = body.get("plan_code") or "default"
            state = body.get("state") or "active"
            if not company_id:
                return _fail("BAD_REQUEST", "company_id required", http_status=400)
            Plan = env["sc.subscription.plan"].sudo()
            plan = Plan.search([("code", "=", plan_code)], limit=1)
            if not plan:
                return _fail("BAD_REQUEST", "plan_code not found", http_status=400)
            Subscription = env["sc.subscription"].sudo()
            sub = Subscription.search([("company_id", "=", company_id)], limit=1)
            vals = {
                "company_id": company_id,
                "plan_id": plan.id,
                "state": state,
                "is_trial": state == "trial",
                "start_date": fields.Date.context_today(env.user),
            }
            if sub:
                sub.write(vals)
            else:
                sub = Subscription.create(vals)
            return _ok({"subscription_id": sub.id}, status=200)
        except AccessDenied as exc:
            return _fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return _fail_from_exception(exc, http_status=500)

    @http.route("/api/ops/job/status", type="http", auth="public", methods=["GET"], csrf=False)
    def job_status(self, **params):
        try:
            _user, env = _platform_env()
            job_id = params.get("job_id")
            if not job_id:
                return _fail("BAD_REQUEST", "job_id required", http_status=400)
            job = env["sc.ops.job"].sudo().browse(int(job_id))
            if not job.exists():
                return _fail("NOT_FOUND", "job not found", http_status=404)
            data = {
                "job_id": job.id,
                "name": job.name,
                "job_type": job.job_type,
                "status": job.status,
                "started_at": job.started_at,
                "finished_at": job.finished_at,
                "result": job.result_json or {},
                "error": job.error_message or "",
            }
            return _ok(data, status=200)
        except AccessDenied as exc:
            return _fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return _fail_from_exception(exc, http_status=500)
