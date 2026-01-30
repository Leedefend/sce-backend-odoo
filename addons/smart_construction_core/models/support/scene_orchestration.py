# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import models, fields


class ScCapability(models.Model):
    _name = "sc.capability"
    _description = "SC Capability Catalog"
    _order = "sequence, id"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    key = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    ui_label = fields.Char()
    ui_hint = fields.Char()
    intent = fields.Char(help="Intent to execute, e.g. ui.contract / api.data / execute_button")
    default_payload = fields.Json()
    required_group_ids = fields.Many2many("res.groups", string="Required Groups")
    tags = fields.Char(help="Comma-separated tags, e.g. project,contract,cost")
    status = fields.Selection(
        [("alpha", "Alpha"), ("beta", "Beta"), ("ga", "GA")],
        default="alpha",
        required=True,
    )
    version = fields.Char(default="v0.1")

    _sql_constraints = [
        ("sc_capability_key_uniq", "unique(key)", "Capability key must be unique."),
    ]

    def _user_allowed(self, user):
        if not self.required_group_ids:
            return True
        return bool(self.required_group_ids & user.groups_id)

    def to_public_dict(self, user):
        self.ensure_one()
        group_xmlids = self.required_group_ids.get_external_id()
        return {
            "key": self.key,
            "name": self.name,
            "ui_label": self.ui_label or self.name,
            "ui_hint": self.ui_hint or "",
            "intent": self.intent or "",
            "default_payload": self.default_payload or {},
            "required_groups": [
                group_xmlids.get(g.id)
                for g in self.required_group_ids
                if group_xmlids.get(g.id)
            ],
            "tags": [t.strip() for t in (self.tags or "").split(",") if t.strip()],
            "status": self.status,
            "version": self.version,
        }


class ScScene(models.Model):
    _name = "sc.scene"
    _description = "SC Scene"
    _order = "sequence, id"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    layout = fields.Selection([("grid", "Grid"), ("flow", "Flow")], default="grid")
    is_default = fields.Boolean(default=False)
    version = fields.Char(default="v0.1")
    state = fields.Selection(
        [("draft", "Draft"), ("published", "Published"), ("archived", "Archived")],
        default="draft",
        required=True,
    )
    published_at = fields.Datetime()
    published_by = fields.Many2one("res.users")
    active_version_id = fields.Many2one("sc.scene.version", ondelete="set null")
    target_group_ids = fields.Many2many("res.groups", string="Target Groups")
    description = fields.Char()
    tile_ids = fields.One2many("sc.scene.tile", "scene_id", string="Tiles")

    _sql_constraints = [
        ("sc_scene_code_uniq", "unique(code)", "Scene code must be unique."),
    ]

    def _user_allowed(self, user):
        if not self.target_group_ids:
            return True
        return bool(self.target_group_ids & user.groups_id)

    def to_public_dict(self, user):
        self.ensure_one()
        version_payload = self.active_version_id.payload_json if self.active_version_id else None
        if self.state == "published" and isinstance(version_payload, dict):
            return version_payload
        tiles = []
        for tile in self.tile_ids.filtered(lambda t: t.active and t.visible):
            if tile.capability_id and not tile.capability_id._user_allowed(user):
                continue
            tiles.append(tile.to_public_dict(user))
        return {
            "code": self.code,
            "name": self.name,
            "layout": self.layout,
            "is_default": bool(self.is_default),
            "version": self.version,
            "tiles": tiles,
        }

    def _build_version_payload(self, user=None):
        self.ensure_one()
        user = user or self.env.user
        tiles = []
        for tile in self.tile_ids.filtered(lambda t: t.active and t.visible):
            if tile.capability_id and not tile.capability_id._user_allowed(user):
                continue
            tiles.append(tile.to_public_dict(user))
        return {
            "code": self.code,
            "name": self.name,
            "layout": self.layout,
            "is_default": bool(self.is_default),
            "version": self.version,
            "tiles": tiles,
        }

    def action_publish(self):
        for scene in self:
            payload = scene._build_version_payload(scene.env.user)
            version_seq = scene.env["sc.scene.version"].search_count([("scene_id", "=", scene.id)]) + 1
            ver = scene.env["sc.scene.version"].create({
                "scene_id": scene.id,
                "version": f"v{version_seq}",
                "payload_json": payload,
            })
            scene.write({
                "active_version_id": ver.id,
                "state": "published",
                "published_at": fields.Datetime.now(),
                "published_by": scene.env.user.id,
            })

    def action_archive(self):
        self.write({"state": "archived"})

    def action_set_active_version(self, version_id):
        version = self.env["sc.scene.version"].browse(version_id)
        if version and version.scene_id and version.scene_id.id in self.ids:
            version.scene_id.write({
                "active_version_id": version.id,
                "state": "published",
                "published_at": fields.Datetime.now(),
                "published_by": self.env.user.id,
            })


class ScSceneTile(models.Model):
    _name = "sc.scene.tile"
    _description = "SC Scene Tile"
    _order = "sequence, id"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    scene_id = fields.Many2one("sc.scene", required=True, ondelete="cascade")
    capability_id = fields.Many2one("sc.capability", required=True, ondelete="restrict")
    title = fields.Char()
    subtitle = fields.Char()
    icon = fields.Char()
    badge = fields.Char()
    visible = fields.Boolean(default=True)
    span = fields.Integer(default=1)
    min_width = fields.Integer(default=200)
    payload_override = fields.Json()
    version = fields.Char(default="v0.1")

    def _merge_payload(self, base_payload, override_payload):
        payload = dict(base_payload or {})
        if isinstance(override_payload, dict):
            payload.update(override_payload)
        return payload

    def to_public_dict(self, user):
        self.ensure_one()
        cap = self.capability_id
        payload = self._merge_payload(cap.default_payload or {}, self.payload_override or {})
        if payload.get("action_xmlid") and not payload.get("action_id"):
            action_ref = self.env.ref(payload.get("action_xmlid"), raise_if_not_found=False)
            if action_ref:
                payload["action_id"] = action_ref.id
        if payload.get("menu_xmlid") and not payload.get("menu_id"):
            menu_ref = self.env.ref(payload.get("menu_xmlid"), raise_if_not_found=False)
            if menu_ref:
                payload["menu_id"] = menu_ref.id
        return {
            "key": cap.key,
            "title": self.title or cap.ui_label or cap.name,
            "subtitle": self.subtitle or cap.ui_hint or "",
            "icon": self.icon or "",
            "badge": self.badge or "",
            "visible": bool(self.visible),
            "span": self.span,
            "min_width": self.min_width,
            "intent": cap.intent or "",
            "payload": payload,
            "status": cap.status,
            "version": cap.version,
        }


class ScSceneVersion(models.Model):
    _name = "sc.scene.version"
    _description = "SC Scene Version"
    _order = "create_date desc, id desc"

    scene_id = fields.Many2one("sc.scene", required=True, ondelete="cascade")
    version = fields.Char(required=True)
    payload_json = fields.Json(required=True)
    create_date = fields.Datetime(readonly=True)
    create_uid = fields.Many2one("res.users", readonly=True)


class ScUserPreference(models.Model):
    _name = "sc.user.preference"
    _description = "SC User Preference"
    _order = "id desc"

    user_id = fields.Many2one("res.users", required=True, index=True, ondelete="cascade")
    default_scene_id = fields.Many2one("sc.scene", ondelete="set null")
    pinned_tile_keys = fields.Json()
    recent_tiles = fields.Json()

    _sql_constraints = [
        ("sc_user_pref_user_uniq", "unique(user_id)", "Preference already exists for user."),
    ]

    @classmethod
    def get_or_create(cls, env, user):
        pref = env["sc.user.preference"].sudo().search([("user_id", "=", user.id)], limit=1)
        if pref:
            return pref
        return env["sc.user.preference"].sudo().create({"user_id": user.id})
