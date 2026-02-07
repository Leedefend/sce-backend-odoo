# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request

from odoo.exceptions import AccessDenied
from odoo.addons.smart_core.security.auth import get_user_from_token

from .api_base import fail, fail_from_exception, ok


class CapabilityCatalogController(http.Controller):
    @http.route("/api/capabilities/export", type="http", auth="public", methods=["GET"], csrf=False)
    def export_capabilities(self, **params):
        try:
            user = get_user_from_token()
            env = request.env(user=user)
            Cap = env["sc.capability"].sudo()
            records = Cap.search([("active", "=", True)], order="sequence, id")
            data = [rec.to_public_dict(user) for rec in records if rec._user_visible(user)]
            payload = {"capabilities": data, "count": len(data)}
            return ok(payload, status=200)
        except AccessDenied as exc:
            return fail("AUTH_REQUIRED", str(exc), http_status=401)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

    @http.route("/api/capabilities/search", type="http", auth="public", methods=["GET"], csrf=False)
    def search_capabilities(self, **params):
        try:
            user = get_user_from_token()
            env = request.env(user=user)
            Cap = env["sc.capability"].sudo()
            domain = [("active", "=", True)]

            q = (params.get("q") or params.get("query") or "").strip()
            if q:
                domain.extend(["|", "|", ("key", "ilike", q), ("name", "ilike", q), ("ui_label", "ilike", q)])

            status = (params.get("status") or "").strip()
            if status:
                statuses = [s.strip() for s in status.split(",") if s.strip()]
                domain.append(("status", "in", statuses))

            intent = (params.get("intent") or "").strip()
            if intent:
                domain.append(("intent", "=", intent))

            smoke = (params.get("smoke") or "").strip().lower()
            if smoke in ("1", "true", "yes", "y"):
                domain.append(("smoke_test", "=", True))

            records = Cap.search(domain, order="sequence, id")
            include_all = (params.get("include_all") or "").strip().lower() in ("1", "true", "yes", "y")
            allow_all = include_all and (
                env.user.has_group("smart_construction_core.group_sc_cap_config_admin")
                or env.user.has_group("base.group_system")
            )
            tag_filters = [t.strip() for t in (params.get("tags") or "").split(",") if t.strip()]
            tag_set = set(tag_filters)

            data = []
            for rec in records:
                if not allow_all and not rec._user_visible(user):
                    continue
                if tag_set:
                    rec_tags = {t.strip() for t in (rec.tags or "").split(",") if t.strip()}
                    if not (rec_tags & tag_set):
                        continue
                data.append(rec.to_public_dict(user))

            payload = {"capabilities": data, "count": len(data)}
            return ok(payload, status=200)
        except AccessDenied as exc:
            return fail("AUTH_REQUIRED", str(exc), http_status=401)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

    @http.route("/api/capabilities/lint", type="http", auth="public", methods=["GET"], csrf=False)
    def lint_capabilities(self, **params):
        try:
            user = get_user_from_token()
            env = request.env(user=user)
            if not env.user.has_group("base.group_system"):
                return fail("PERMISSION_DENIED", "Admin required", http_status=403)

            ignore_keys = [k.strip() for k in (params.get("ignore_keys") or "").split(",") if k.strip()]
            include_tests = (params.get("include_tests") or "").strip().lower() in ("1", "true", "yes", "y")
            issues = env["sc.capability"].sudo().lint_capabilities(
                ignore_keys=ignore_keys,
                include_tests=include_tests,
            )
            status = "pass" if not issues else "fail"
            payload = {"status": status, "issues": issues, "count": len(issues)}
            return ok(payload, status=200)
        except AccessDenied as exc:
            return fail("AUTH_REQUIRED", str(exc), http_status=401)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)
