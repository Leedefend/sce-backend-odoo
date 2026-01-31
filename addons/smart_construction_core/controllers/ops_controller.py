# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http, fields
from odoo.http import request
from odoo.exceptions import AccessDenied
from odoo.addons.smart_core.security.auth import get_user_from_token

from .api_base import fail, fail_from_exception, ok
from .pack_controller import PackController


def _has_admin(user):
    return user.has_group("smart_construction_core.group_sc_cap_config_admin") or user.has_group("base.group_system")


class OpsController(http.Controller):
    @http.route("/api/ops/tenants", type="http", auth="public", methods=["GET"], csrf=False)
    def tenants(self, **params):
        try:
            user = get_user_from_token()
            if not _has_admin(user):
                raise AccessDenied("insufficient permissions")
            env = request.env(user=user)
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
            return ok({"tenants": data, "count": len(data)}, status=200)
        except AccessDenied as exc:
            return fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

    @http.route("/api/ops/subscription/set", type="http", auth="public", methods=["POST"], csrf=False)
    def set_subscription(self, **params):
        try:
            user = get_user_from_token()
            if not _has_admin(user):
                raise AccessDenied("insufficient permissions")
            env = request.env(user=user)
            body = request.httprequest.get_json(force=True, silent=True) or {}
            company_id = body.get("company_id")
            plan_code = body.get("plan_code") or "default"
            state = body.get("state") or "active"
            if not company_id:
                return fail("BAD_REQUEST", "company_id required", http_status=400)
            Plan = env["sc.subscription.plan"].sudo()
            plan = Plan.search([("code", "=", plan_code)], limit=1)
            if not plan:
                return fail("BAD_REQUEST", "plan_code not found", http_status=400)
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
            return ok({"subscription_id": sub.id}, status=200)
        except AccessDenied as exc:
            return fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

    @http.route("/api/ops/packs/batch_upgrade", type="http", auth="public", methods=["POST"], csrf=False)
    def batch_upgrade(self, **params):
        try:
            user = get_user_from_token()
            if not _has_admin(user):
                raise AccessDenied("insufficient permissions")
            env = request.env(user=user)
            body = request.httprequest.get_json(force=True, silent=True) or {}
            pack_id = body.get("pack_id")
            company_ids = body.get("company_ids") or []
            if not pack_id:
                return fail("BAD_REQUEST", "pack_id required", http_status=400)
            Job = env["sc.ops.job"].sudo()
            job = Job.create({
                "name": f"batch_upgrade:{pack_id}",
                "job_type": "batch_upgrade",
                "status": "running",
                "started_at": fields.Datetime.now(),
                "payload_json": body,
                "trace_id": body.get("trace_id"),
            })
            results = []
            controller = PackController()
            companies = env["res.company"].sudo().browse(company_ids) if company_ids else [env.company]
            for company in companies:
                company_user = user.with_company(company)
                company_env = request.env(user=company_user)
                res = controller._install_pack(
                    company_user,
                    company_env,
                    pack_id,
                    (body.get("mode") or "merge").strip().lower(),
                    bool(body.get("dry_run")),
                    bool(body.get("confirm")),
                    bool(body.get("strict")),
                )
                results.append({"company_id": company.id, "result": res})
            job.write({"status": "done", "finished_at": fields.Datetime.now(), "result_json": results})
            return ok({"job_id": job.id, "status": job.status, "results": results}, status=200)
        except AccessDenied as exc:
            return fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

    @http.route("/api/ops/packs/batch_rollback", type="http", auth="public", methods=["POST"], csrf=False)
    def batch_rollback(self, **params):
        try:
            user = get_user_from_token()
            if not _has_admin(user):
                raise AccessDenied("insufficient permissions")
            env = request.env(user=user)
            body = request.httprequest.get_json(force=True, silent=True) or {}
            pack_id = body.get("pack_id")
            if not pack_id:
                return fail("BAD_REQUEST", "pack_id required", http_status=400)
            # minimal rollback: re-apply current pack payload
            body.setdefault("mode", "merge")
            body.setdefault("confirm", True)
            body.setdefault("dry_run", False)
            return self.batch_upgrade(**params)
        except AccessDenied as exc:
            return fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

    @http.route("/api/ops/audit/search", type="http", auth="public", methods=["GET"], csrf=False)
    def audit_search(self, **params):
        try:
            user = get_user_from_token()
            if not _has_admin(user):
                raise AccessDenied("insufficient permissions")
            env = request.env(user=user)
            event = (params.get("event") or "").strip()
            domain = []
            if event:
                domain.append(("event", "=", event))
            logs = env["sc.scene.audit.log"].sudo().search(domain, order="created_at desc, id desc", limit=200)
            data = [
                {
                    "event": log.event,
                    "actor_user_id": log.actor_user_id.id if log.actor_user_id else None,
                    "scene_id": log.scene_id.id if log.scene_id else None,
                    "version_id": log.version_id.id if log.version_id else None,
                    "created_at": log.created_at,
                    "payload_diff": log.payload_diff or {},
                }
                for log in logs
            ]
            return ok({"items": data, "count": len(data)}, status=200)
        except AccessDenied as exc:
            return fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

    @http.route("/api/ops/job/status", type="http", auth="public", methods=["GET"], csrf=False)
    def job_status(self, **params):
        try:
            user = get_user_from_token()
            if not _has_admin(user):
                raise AccessDenied("insufficient permissions")
            env = request.env(user=user)
            job_id = params.get("job_id")
            if not job_id:
                return fail("BAD_REQUEST", "job_id required", http_status=400)
            job = env["sc.ops.job"].sudo().browse(int(job_id))
            if not job.exists():
                return fail("NOT_FOUND", "job not found", http_status=404)
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
            return ok(data, status=200)
        except AccessDenied as exc:
            return fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)
