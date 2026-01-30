# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import uuid
from odoo import http, fields
from odoo.http import request

from odoo.exceptions import AccessDenied, UserError
from odoo.addons.smart_core.security.auth import get_user_from_token

from .api_base import fail, fail_from_exception, ok


def _get_json_body():
    body = request.httprequest.get_json(force=True, silent=True)
    return body if isinstance(body, dict) else {}


def _has_admin(user):
    return user.has_group("smart_construction_core.group_sc_cap_config_admin") or user.has_group("base.group_system")


def _parse_bool(val, default=False):
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in {"1", "true", "yes", "y"}

def _normalize_pack_payload(payload):
    caps = payload.get("capabilities") or []
    scenes = payload.get("scenes") or []
    caps_sorted = sorted(caps, key=lambda c: c.get("key") or "")
    scenes_sorted = sorted(scenes, key=lambda s: s.get("code") or "")
    for scene in scenes_sorted:
        tiles = scene.get("tiles") or []
        scene["tiles"] = sorted(
            tiles,
            key=lambda t: (
                t.get("capability_key") or "",
                int(t.get("sequence") or 0),
            ),
        )
    payload["capabilities"] = caps_sorted
    payload["scenes"] = scenes_sorted
    return payload


def _pack_hash(payload):
    normalized = _normalize_pack_payload(dict(payload))
    raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _diff_fields(current, incoming):
    changed = []
    for key, val in incoming.items():
        if current.get(key) != val:
            changed.append(key)
    return changed


def _risk_level(diff_v2, mode):
    deletes = len(diff_v2.get("deletes") or [])
    updates = len(diff_v2.get("updates") or [])
    if mode == "replace" or deletes:
        return "high"
    if updates:
        return "medium"
    return "low"


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
            contract_version = env["ir.config_parameter"].sudo().get_param("sc.contract.version", "v0.1")

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

            pack_id = str(uuid.uuid4())
            upgrade_policy = {
                "default_mode": "merge",
                "replace_confirm_required": True,
                "merge_fields": {
                    "capability": [
                        "name",
                        "ui_label",
                        "ui_hint",
                        "intent",
                        "default_payload",
                        "tags",
                        "status",
                        "version",
                        "required_groups",
                        "smoke_test",
                        "is_test",
                    ],
                    "scene": [
                        "name",
                        "layout",
                        "is_default",
                        "version",
                        "state",
                    ],
                    "tile": [
                        "title",
                        "subtitle",
                        "icon",
                        "badge",
                        "visible",
                        "span",
                        "min_width",
                        "payload_override",
                        "sequence",
                        "active",
                    ],
                },
            }
            payload_core = {
                "upgrade_policy": upgrade_policy,
                "capabilities": out_caps,
                "scenes": out_scenes,
            }
            payload_hash = _pack_hash(payload_core)
            payload = {
                "pack_meta": {
                    "pack_id": pack_id,
                    "pack_version": "v0.2",
                    "hash_algo": "sha256",
                    "payload_hash": payload_hash,
                    "generated_at": fields.Datetime.now(),
                    "source_db": request.db,
                    "modules": ["smart_construction_core"],
                    "contract_version": contract_version,
                },
                "upgrade_policy": upgrade_policy,
                "capabilities": out_caps,
                "scenes": out_scenes,
            }
            env["sc.scene.audit.log"].sudo().create({
                "event": "export",
                "actor_user_id": user.id,
                "payload_diff": {"scene_count": len(out_scenes), "cap_count": len(out_caps)},
                "created_at": fields.Datetime.now(),
            })
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
            upgrade_policy = body.get("upgrade_policy") or {}
            default_mode = (upgrade_policy.get("default_mode") or "merge").strip().lower()
            mode = (body.get("mode") or default_mode).strip().lower()
            if mode not in {"merge", "replace"}:
                mode = "merge"
            dry_run = _parse_bool(body.get("dry_run"), False)
            confirm = _parse_bool(body.get("confirm"), False)
            if mode == "replace" and not confirm and not dry_run:
                return fail("BAD_REQUEST", "replace mode requires confirm=true", http_status=400)

            pack_meta = body.get("pack_meta") or {}
            payload_core = {
                "upgrade_policy": body.get("upgrade_policy") or {},
                "capabilities": body.get("capabilities") or [],
                "scenes": body.get("scenes") or [],
            }
            if pack_meta.get("payload_hash"):
                algo = (pack_meta.get("hash_algo") or "sha256").lower()
                if algo != "sha256":
                    return fail("BAD_REQUEST", "unsupported hash algo", http_status=400)
                expected = pack_meta.get("payload_hash")
                computed = _pack_hash(payload_core)
                if expected != computed:
                    return fail(
                        "PACK_HASH_MISMATCH",
                        "payload hash mismatch",
                        details={"expected": expected, "computed": computed},
                        http_status=400,
                    )

            Cap = env["sc.capability"].sudo()
            Scene = env["sc.scene"].sudo()
            Tile = env["sc.scene.tile"].sudo()

            diff = {
                "mode": mode,
                "dry_run": dry_run,
                "capabilities": {"create": [], "update": []},
                "scenes": {"create": [], "update": []},
                "tiles": {"create": [], "update": [], "delete": []},
            }
            diff_v2 = {
                "mode": mode,
                "dry_run": dry_run,
                "creates": [],
                "updates": [],
                "deletes": [],
                "risk_level": "low",
            }

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
                    "smoke_test": bool(cap.get("smoke_test", False)),
                    "is_test": bool(cap.get("is_test", False)),
                }
                if rec:
                    diff["capabilities"]["update"].append(key)
                    current = {
                        "name": rec.name,
                        "ui_label": rec.ui_label or "",
                        "ui_hint": rec.ui_hint or "",
                        "intent": rec.intent or "",
                        "default_payload": rec.default_payload or {},
                        "tags": rec.tags or "",
                        "status": rec.status,
                        "version": rec.version,
                        "required_groups": sorted(
                            [x for x in (rec.required_group_ids.get_external_id() or {}).values() if x]
                        ),
                        "smoke_test": bool(rec.smoke_test),
                        "is_test": bool(rec.is_test),
                    }
                    incoming = {
                        "name": vals.get("name"),
                        "ui_label": vals.get("ui_label") or "",
                        "ui_hint": vals.get("ui_hint") or "",
                        "intent": vals.get("intent") or "",
                        "default_payload": vals.get("default_payload") or {},
                        "tags": vals.get("tags") or "",
                        "status": vals.get("status"),
                        "version": vals.get("version"),
                        "required_groups": sorted(
                            [g for g in cap.get("required_groups") or [] if g]
                        ),
                        "smoke_test": bool(vals.get("smoke_test")),
                        "is_test": bool(vals.get("is_test")),
                    }
                    changed = _diff_fields(current, incoming)
                    diff_v2["updates"].append({
                        "entity_type": "capability",
                        "key": key,
                        "fields_changed": changed,
                    })
                    if not dry_run:
                        merge_fields = (upgrade_policy.get("merge_fields") or {}).get("capability") or []
                        write_vals = {k: v for k, v in vals.items() if k in merge_fields}
                        rec.write(write_vals)
                        env["sc.capability.audit.log"].sudo().create({
                            "event": "update",
                            "actor_user_id": user.id,
                            "capability_id": rec.id,
                            "source_pack_id": pack_meta.get("pack_id"),
                            "payload_diff": {"fields_changed": changed},
                            "created_at": fields.Datetime.now(),
                        })
                else:
                    vals["key"] = key
                    diff["capabilities"]["create"].append(key)
                    diff_v2["creates"].append({
                        "entity_type": "capability",
                        "key": key,
                        "fields_changed": list(vals.keys()),
                    })
                    if not dry_run:
                        new_cap = Cap.create(vals)
                        env["sc.capability.audit.log"].sudo().create({
                            "event": "create",
                            "actor_user_id": user.id,
                            "capability_id": new_cap.id,
                            "source_pack_id": pack_meta.get("pack_id"),
                            "payload_diff": {"fields_changed": list(vals.keys())},
                            "created_at": fields.Datetime.now(),
                        })

            # upsert scenes + tiles
            scenes_in = body.get("scenes") or []
            for scene_in in scenes_in:
                code = (scene_in.get("code") or "").strip()
                if not code:
                    continue
                scene = Scene.search([("code", "=", code)], limit=1)
                state_in = scene_in.get("state") or "draft"
                write_state = "draft" if state_in == "published" else state_in
                vals = {
                    "name": scene_in.get("name") or code,
                    "layout": scene_in.get("layout") or "grid",
                    "is_default": bool(scene_in.get("is_default")),
                    "version": scene_in.get("version") or "v0.1",
                    "state": write_state,
                }
                if scene:
                    diff["scenes"]["update"].append(code)
                    current = {
                        "name": scene.name,
                        "layout": scene.layout,
                        "is_default": bool(scene.is_default),
                        "version": scene.version,
                        "state": scene.state,
                    }
                    incoming = {
                        "name": vals.get("name"),
                        "layout": vals.get("layout"),
                        "is_default": bool(vals.get("is_default")),
                        "version": vals.get("version"),
                        "state": vals.get("state"),
                    }
                    changed = _diff_fields(current, incoming)
                    diff_v2["updates"].append({
                        "entity_type": "scene",
                        "key": code,
                        "fields_changed": changed,
                    })
                    if not dry_run:
                        merge_fields = (upgrade_policy.get("merge_fields") or {}).get("scene") or []
                        write_vals = {k: v for k, v in vals.items() if k in merge_fields}
                        scene.write(write_vals)
                else:
                    vals["code"] = code
                    diff["scenes"]["create"].append(code)
                    diff_v2["creates"].append({
                        "entity_type": "scene",
                        "key": code,
                        "fields_changed": list(vals.keys()),
                    })
                    if not dry_run:
                        scene = Scene.create(vals)
                    else:
                        scene = Scene.new(vals)

                if mode == "replace":
                    existing_tiles = Tile.search([("scene_id", "=", scene.id)])
                    if existing_tiles:
                        diff["tiles"]["delete"].extend([t.id for t in existing_tiles])
                        for t in existing_tiles:
                            diff_v2["deletes"].append({
                                "entity_type": "tile",
                                "scene": code,
                                "capability": t.capability_id.key,
                            })
                    if not dry_run:
                        existing_tiles.unlink()

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
                        diff["tiles"]["update"].append({"scene": code, "capability": cap_key})
                        current = {
                            "title": existing.title or "",
                            "subtitle": existing.subtitle or "",
                            "icon": existing.icon or "",
                            "badge": existing.badge or "",
                            "visible": bool(existing.visible),
                            "span": existing.span,
                            "min_width": existing.min_width,
                            "payload_override": existing.payload_override or {},
                            "sequence": existing.sequence,
                            "active": bool(existing.active),
                        }
                        incoming = {
                            "title": tile_vals.get("title") or "",
                            "subtitle": tile_vals.get("subtitle") or "",
                            "icon": tile_vals.get("icon") or "",
                            "badge": tile_vals.get("badge") or "",
                            "visible": bool(tile_vals.get("visible")),
                            "span": tile_vals.get("span"),
                            "min_width": tile_vals.get("min_width"),
                            "payload_override": tile_vals.get("payload_override") or {},
                            "sequence": tile_vals.get("sequence"),
                            "active": bool(tile_vals.get("active")),
                        }
                        changed = _diff_fields(current, incoming)
                        diff_v2["updates"].append({
                            "entity_type": "tile",
                            "scene": code,
                            "capability": cap_key,
                            "fields_changed": changed,
                        })
                        if not dry_run:
                            merge_fields = (upgrade_policy.get("merge_fields") or {}).get("tile") or []
                            write_vals = {k: v for k, v in tile_vals.items() if k in merge_fields}
                            existing.write(write_vals)
                    else:
                        diff["tiles"]["create"].append({"scene": code, "capability": cap_key})
                        diff_v2["creates"].append({
                            "entity_type": "tile",
                            "scene": code,
                            "capability": cap_key,
                            "fields_changed": list(tile_vals.keys()),
                        })
                        if not dry_run:
                            Tile.create(tile_vals)

                if not dry_run and state_in == "published":
                    try:
                        scene.with_context(publish_source="import").action_publish()
                    except UserError:
                        issues = []
                        validation = env["sc.scene.validation"].sudo().search(
                            [("scene_id", "=", scene.id)],
                            order="checked_at desc, id desc",
                            limit=1,
                        )
                        if validation:
                            issues = validation.issues_json or []
                        return fail(
                            "VALIDATION_ERROR",
                            "Scene validation failed",
                            details={"scene": code, "issues": issues},
                            http_status=400,
                        )

            diff_v2["risk_level"] = _risk_level(diff_v2, mode)

            if dry_run:
                return ok({"status": "dry_run", "diff": diff, "diff_v2": diff_v2}, status=200)

            env["sc.scene.audit.log"].sudo().create({
                "event": "import",
                "actor_user_id": user.id,
                "payload_diff": diff_v2,
                "created_at": fields.Datetime.now(),
            })
            return ok({"status": "ok", "diff": diff, "diff_v2": diff_v2}, status=200)
        except AccessDenied as exc:
            return fail("PERMISSION_DENIED", str(exc), http_status=403)
        except Exception as exc:
            return fail_from_exception(exc, http_status=500)
