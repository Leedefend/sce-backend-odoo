# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import http
from odoo.http import request

from odoo.exceptions import AccessDenied
from odoo.addons.smart_core.security.auth import get_user_from_token

from .api_base import fail, fail_from_exception, ok


def _get_json_body():
    body = request.httprequest.get_json(force=True, silent=True)
    return body if isinstance(body, dict) else {}


def _has_admin(user):
    return user.has_group("smart_construction_core.group_sc_cap_config_admin") or user.has_group("base.group_system")


class SceneTemplateController(http.Controller):
    @http.route("/api/scenes/export", type="http", auth="public", methods=["GET"], csrf=False)
    def export_scenes(self, **params):
        try:
            user = get_user_from_token()
            if not _has_admin(user):
                raise AccessDenied("insufficient permissions")
            env = request.env(user=user)
            code = (params.get("code") or "").strip()
            include_caps = str(params.get("include_caps") or "1").lower() in {"1", "true", "yes"}

            Scene = env["sc.scene"].sudo()
            domain = [("code", "=", code)] if code else []
            scenes = Scene.search(domain, order="sequence, id")
            out_scenes = []
            cap_keys = set()
            for scene in scenes:
                tiles = []
                for tile in scene.tile_ids:
                    cap = tile.capability_id
                    if not cap:
                        continue
                    cap_keys.add(cap.key)
                    tiles.append({
                        "capability_key": cap.key,
                        "title": tile.title or "",
                        "subtitle": tile.subtitle or "",
                        "icon": tile.icon or "",
                        "badge": tile.badge or "",
                        "visible": bool(tile.visible),
                        "span": tile.span,
                        "min_width": tile.min_width,
                        "payload_override": tile.payload_override or {},
                        "sequence": tile.sequence,
                        "active": bool(tile.active),
                    })
                out_scenes.append({
                    "code": scene.code,
                    "name": scene.name,
                    "layout": scene.layout,
                    "is_default": bool(scene.is_default),
                    "version": scene.version,
                    "state": scene.state,
                    "tiles": tiles,
                })

            out_caps = []
            if include_caps and cap_keys:
                Cap = env["sc.capability"].sudo()
                caps = Cap.search([("key", "in", list(cap_keys))])
                for cap in caps:
                    group_xmlids = cap.required_group_ids.get_external_id()
                    out_caps.append({
                        "key": cap.key,
                        "name": cap.name,
                        "ui_label": cap.ui_label or "",
                        "ui_hint": cap.ui_hint or "",
                        "intent": cap.intent or "",
                        "default_payload": cap.default_payload or {},
                        "required_groups": [
                            group_xmlids.get(g.id)
                            for g in cap.required_group_ids
                            if group_xmlids.get(g.id)
                        ],
                        "tags": cap.tags or "",
                        "status": cap.status,
                        "version": cap.version,
                    })

            payload = {
                "capabilities": out_caps,
                "scenes": out_scenes,
            }
            return ok(payload, status=200)
        except AccessDenied as exc:
            return fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)

    @http.route("/api/scenes/import", type="http", auth="public", methods=["POST"], csrf=False)
    def import_scenes(self, **params):
        try:
            user = get_user_from_token()
            if not _has_admin(user):
                raise AccessDenied("insufficient permissions")
            env = request.env(user=user)
            body = _get_json_body()
            mode = (body.get("mode") or "merge").strip().lower()
            if mode not in {"merge", "replace"}:
                mode = "merge"

            Cap = env["sc.capability"].sudo()
            Scene = env["sc.scene"].sudo()
            Tile = env["sc.scene.tile"].sudo()

            # upsert capabilities
            caps_in = body.get("capabilities") or []
            for cap in caps_in:
                key = (cap.get("key") or "").strip()
                if not key:
                    continue
                rec = Cap.search([("key", "=", key)], limit=1)
                group_ids = []
                for xmlid in cap.get("required_groups") or []:
                    g = env.ref(xmlid, raise_if_not_found=False)
                    if g:
                        group_ids.append(g.id)
                vals = {
                    "name": cap.get("name") or key,
                    "ui_label": cap.get("ui_label") or "",
                    "ui_hint": cap.get("ui_hint") or "",
                    "intent": cap.get("intent") or "",
                    "default_payload": cap.get("default_payload") or {},
                    "tags": cap.get("tags") or "",
                    "status": cap.get("status") or "alpha",
                    "version": cap.get("version") or "v0.1",
                    "required_group_ids": [(6, 0, group_ids)],
                }
                if rec:
                    rec.write(vals)
                else:
                    vals["key"] = key
                    Cap.create(vals)

            # upsert scenes + tiles
            scenes_in = body.get("scenes") or []
            for scene_in in scenes_in:
                code = (scene_in.get("code") or "").strip()
                if not code:
                    continue
                scene = Scene.search([("code", "=", code)], limit=1)
                vals = {
                    "name": scene_in.get("name") or code,
                    "layout": scene_in.get("layout") or "grid",
                    "is_default": bool(scene_in.get("is_default")),
                    "version": scene_in.get("version") or "v0.1",
                    "state": scene_in.get("state") or "draft",
                }
                if scene:
                    scene.write(vals)
                else:
                    vals["code"] = code
                    scene = Scene.create(vals)

                if mode == "replace":
                    Tile.search([("scene_id", "=", scene.id)]).unlink()

                tiles_in = scene_in.get("tiles") or []
                for tile_in in tiles_in:
                    cap_key = (tile_in.get("capability_key") or "").strip()
                    if not cap_key:
                        continue
                    cap = Cap.search([("key", "=", cap_key)], limit=1)
                    if not cap:
                        continue
                    tile_vals = {
                        "scene_id": scene.id,
                        "capability_id": cap.id,
                        "title": tile_in.get("title") or "",
                        "subtitle": tile_in.get("subtitle") or "",
                        "icon": tile_in.get("icon") or "",
                        "badge": tile_in.get("badge") or "",
                        "visible": bool(tile_in.get("visible", True)),
                        "span": int(tile_in.get("span") or 1),
                        "min_width": int(tile_in.get("min_width") or 200),
                        "payload_override": tile_in.get("payload_override") or {},
                        "sequence": int(tile_in.get("sequence") or 10),
                        "active": bool(tile_in.get("active", True)),
                    }
                    existing = Tile.search([
                        ("scene_id", "=", scene.id),
                        ("capability_id", "=", cap.id),
                    ], limit=1)
                    if existing and mode == "merge":
                        existing.write(tile_vals)
                    else:
                        Tile.create(tile_vals)

                if scene.state == "published":
                    scene.action_publish()

            return ok({"status": "ok"}, status=200)
        except AccessDenied as exc:
            return fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)
