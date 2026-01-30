# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http, fields
from odoo.http import request
from odoo.exceptions import AccessDenied
from odoo.addons.smart_core.security.auth import get_user_from_token

from .api_base import fail, fail_from_exception, ok
from .scene_template_controller import _apply_pack, _pack_hash


def _has_admin(user):
    return user.has_group("smart_construction_core.group_sc_cap_config_admin") or user.has_group("base.group_system")


class PackController(http.Controller):
    @http.route("/api/packs/publish", type="http", auth="public", methods=["POST"], csrf=False)
    def publish_pack(self, **params):
        try:
            user = get_user_from_token()
            if not _has_admin(user):
                raise AccessDenied("insufficient permissions")
            env = request.env(user=user)
            body = request.httprequest.get_json(force=True, silent=True) or {}

            pack_meta = body.get("pack_meta") or {}
            pack_id = pack_meta.get("pack_id") or body.get("pack_id")
            if not pack_id:
                return fail("BAD_REQUEST", "pack_id required", http_status=400)
            pack_version = pack_meta.get("pack_version") or body.get("pack_version") or "v0.2"
            payload_core = {
                "upgrade_policy": body.get("upgrade_policy") or {},
                "capabilities": body.get("capabilities") or [],
                "scenes": body.get("scenes") or [],
            }
            payload_hash = pack_meta.get("payload_hash") or _pack_hash(payload_core)
            vendor = pack_meta.get("vendor") or body.get("vendor") or "local"
            channel = pack_meta.get("channel") or body.get("channel") or "stable"
            pack_type = pack_meta.get("pack_type") or body.get("pack_type") or "platform"
            industry_code = pack_meta.get("industry_code") or body.get("industry_code") or ""
            depends_on = pack_meta.get("depends_on") or body.get("depends_on") or []

            Registry = env["sc.pack.registry"].sudo()
            record = Registry.search([("pack_id", "=", pack_id)], limit=1)
            vals = {
                "pack_id": pack_id,
                "name": body.get("name") or pack_meta.get("name") or pack_id,
                "pack_version": pack_version,
                "vendor": vendor,
                "channel": channel,
                "pack_type": pack_type,
                "industry_code": industry_code,
                "pack_hash": payload_hash,
                "signed_by": pack_meta.get("signed_by") or "",
                "published_at": fields.Datetime.now(),
                "published_by": user.id,
                "notes": pack_meta.get("notes") or "",
                "changelog": pack_meta.get("changelog") or "",
                "payload_json": body,
            }
            dep_ids = []
            for dep in depends_on:
                dep_rec = Registry.search([("pack_id", "=", dep)], limit=1)
                if dep_rec:
                    dep_ids.append(dep_rec.id)
            if record:
                record.write(vals)
                if dep_ids:
                    record.write({"depends_on_ids": [(6, 0, dep_ids)]})
            else:
                if dep_ids:
                    vals["depends_on_ids"] = [(6, 0, dep_ids)]
                record = Registry.create(vals)
            return ok({"status": "ok", "pack_id": record.pack_id}, status=200)
        except AccessDenied as exc:
            return fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

    @http.route("/api/packs/catalog", type="http", auth="public", methods=["GET"], csrf=False)
    def catalog(self, **params):
        try:
            user = get_user_from_token()
            env = request.env(user=user)
            Registry = env["sc.pack.registry"].sudo()
            Installation = env["sc.pack.installation"].sudo()
            domain = [("active", "=", True)]
            pack_type = (params.get("pack_type") or "").strip()
            if pack_type:
                domain.append(("pack_type", "=", pack_type))
            industry_code = (params.get("industry_code") or "").strip()
            if industry_code:
                domain.append(("industry_code", "=", industry_code))
            channel = (params.get("channel") or "").strip()
            if channel:
                domain.append(("channel", "=", channel))
            vendor = (params.get("vendor") or "").strip()
            if vendor:
                domain.append(("vendor", "=", vendor))
            records = Registry.search(domain, order="published_at desc, id desc")
            data = []
            for rec in records:
                inst = Installation.search([("pack_id", "=", rec.id)], limit=1)
                data.append({
                    "pack_id": rec.pack_id,
                    "name": rec.name,
                    "pack_version": rec.pack_version,
                    "vendor": rec.vendor,
                    "channel": rec.channel,
                    "pack_type": rec.pack_type,
                    "industry_code": rec.industry_code,
                    "pack_hash": rec.pack_hash,
                    "published_at": rec.published_at,
                    "installed_version": inst.installed_version if inst else None,
                })
            return ok({"packs": data, "count": len(data)}, status=200)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

    def _install_pack(self, user, env, pack_id, mode, dry_run, confirm, strict):
        Registry = env["sc.pack.registry"].sudo()
        Installation = env["sc.pack.installation"].sudo()
        record = Registry.search([("pack_id", "=", pack_id)], limit=1)
        if not record:
            return {"ok": False, "http_status": 404, "error": {"code": "PACK_NOT_FOUND", "message": "Pack not found"}}

        # dependency check
        missing = []
        for dep in record.depends_on_ids:
            dep_inst = Installation.search([("pack_id", "=", dep.id)], limit=1)
            if not dep_inst:
                missing.append(dep.pack_id)
        if missing:
            return {
                "ok": False,
                "http_status": 400,
                "error": {"code": "DEPENDENCY_MISSING", "message": "Pack dependencies not installed", "details": {"missing": missing}},
            }

        payload = record.payload_json or {}
        payload["mode"] = mode
        payload["dry_run"] = dry_run
        payload["confirm"] = confirm
        payload["strict"] = strict
        result = _apply_pack(env, user, payload)
        if not result.get("ok"):
            return result

        data = result.get("data") or {}
        if not dry_run:
            inst = Installation.search([("pack_id", "=", record.id)], limit=1)
            vals = {
                "pack_id": record.id,
                "installed_version": record.pack_version,
                "installed_at": fields.Datetime.now(),
                "installed_by": user.id,
                "status": "installed",
                "last_diff_json": data.get("diff_v2") or {},
                "source_hash": record.pack_hash,
            }
            if inst:
                history = inst.upgrade_history or []
                history.append({
                    "version": record.pack_version,
                    "at": fields.Datetime.now(),
                    "by": user.id,
                })
                vals["upgrade_history"] = history
                inst.write(vals)
            else:
                Installation.create(vals)

        return {"ok": True, "http_status": 200, "data": data}

    @http.route("/api/packs/install", type="http", auth="public", methods=["POST"], csrf=False)
    def install_pack(self, **params):
        try:
            user = get_user_from_token()
            if not _has_admin(user):
                raise AccessDenied("insufficient permissions")
            env = request.env(user=user)
            body = request.httprequest.get_json(force=True, silent=True) or {}
            pack_id = body.get("pack_id")
            mode = (body.get("mode") or "merge").strip().lower()
            dry_run = bool(body.get("dry_run"))
            confirm = bool(body.get("confirm"))
            strict = bool(body.get("strict"))
            result = self._install_pack(user, env, pack_id, mode, dry_run, confirm, strict)
            if not result.get("ok"):
                error = result.get("error") or {}
                return fail(
                    error.get("code") or "BAD_REQUEST",
                    error.get("message") or "install failed",
                    details=error.get("details") or {},
                    http_status=result.get("http_status") or 400,
                )
            return ok(result.get("data") or {}, status=200)
        except AccessDenied as exc:
            return fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

    @http.route("/api/packs/upgrade", type="http", auth="public", methods=["POST"], csrf=False)
    def upgrade_pack(self, **params):
        try:
            user = get_user_from_token()
            if not _has_admin(user):
                raise AccessDenied("insufficient permissions")
            env = request.env(user=user)
            body = request.httprequest.get_json(force=True, silent=True) or {}
            pack_id = body.get("pack_id")
            mode = (body.get("mode") or "merge").strip().lower()
            dry_run = bool(body.get("dry_run"))
            confirm = bool(body.get("confirm"))
            strict = bool(body.get("strict"))
            result = self._install_pack(user, env, pack_id, mode, dry_run, confirm, strict)
            if not result.get("ok"):
                error = result.get("error") or {}
                return fail(
                    error.get("code") or "BAD_REQUEST",
                    error.get("message") or "upgrade failed",
                    details=error.get("details") or {},
                    http_status=result.get("http_status") or 400,
                )
            return ok(result.get("data") or {}, status=200)
        except AccessDenied as exc:
            return fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)
