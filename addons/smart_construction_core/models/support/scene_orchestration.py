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
        return {
            "key": self.key,
            "name": self.name,
            "ui_label": self.ui_label or self.name,
            "ui_hint": self.ui_hint or "",
            "intent": self.intent or "",
            "default_payload": self.default_payload or {},
            "required_groups": [g.xml_id for g in self.required_group_ids if g.xml_id],
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
        tiles = []
        for tile in self.tile_ids.filtered(lambda t: t.active):
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
            "intent": cap.intent or "",
            "payload": payload,
            "status": cap.status,
            "version": cap.version,
        }
