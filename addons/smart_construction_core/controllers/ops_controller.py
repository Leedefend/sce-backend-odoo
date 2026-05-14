# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
from odoo.addons.smart_core.security.auth import get_user_from_token
from odoo.addons.smart_core.security.platform_company_access import (
    finish_platform_ops_job,
    start_platform_ops_job,
)
from odoo.addons.smart_core.security.platform_admin import user_is_platform_admin

from .api_base import fail, fail_from_exception, ok
from .pack_controller import PackController


class OpsController(http.Controller):
    @http.route("/api/ops/packs/batch_upgrade", type="http", auth="public", methods=["POST"], csrf=False)
    def batch_upgrade(self, **params):
        try:
            user = get_user_from_token()
            if not user_is_platform_admin(user):
                raise AccessDenied("insufficient permissions")
            env = request.env(user=user)
            body = request.httprequest.get_json(force=True, silent=True) or {}
            pack_id = body.get("pack_id")
            company_ids = body.get("company_ids") or []
            if not pack_id:
                return fail("BAD_REQUEST", "pack_id required", http_status=400)
            job = start_platform_ops_job(env, {
                "name": f"batch_upgrade:{pack_id}",
                "job_type": "batch_upgrade",
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
            finish_platform_ops_job(job, result_json=results)
            return ok({"job_id": job.id, "status": job.status, "results": results}, status=200)
        except AccessDenied as exc:
            return fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

    @http.route("/api/ops/packs/batch_rollback", type="http", auth="public", methods=["POST"], csrf=False)
    def batch_rollback(self, **params):
        try:
            user = get_user_from_token()
            if not user_is_platform_admin(user):
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
            if not user_is_platform_admin(user):
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
