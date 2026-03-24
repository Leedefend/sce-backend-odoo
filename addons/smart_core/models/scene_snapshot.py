# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields, models


class ScSceneSnapshot(models.Model):
    _name = "sc.scene.snapshot"
    _description = "SC Scene Snapshot"
    _order = "product_key, scene_key, channel, version desc, id desc"

    active = fields.Boolean(default=True)
    is_active = fields.Boolean(default=True, index=True)
    scene_key = fields.Char(required=True, index=True)
    product_key = fields.Char(required=True, index=True)
    capability_key = fields.Char(index=True)
    label = fields.Char()
    route = fields.Char()
    version = fields.Char(required=True, default="v1", index=True)
    channel = fields.Selection(
        [("stable", "Stable"), ("beta", "Beta")],
        default="stable",
        required=True,
        index=True,
    )
    source_type = fields.Char(default="release_surface")
    source_ref = fields.Char()
    source_contract_version = fields.Char(default="scene_contract_standard_v1")
    contract_json = fields.Json(required=True, default=dict)
    meta_json = fields.Json(required=True, default=dict)
    cloned_from_snapshot_id = fields.Many2one("sc.scene.snapshot", string="Cloned From", ondelete="set null")
    note = fields.Char()

    _sql_constraints = [
        (
            "sc_scene_snapshot_uniq",
            "unique(product_key, scene_key, version, channel)",
            "Scene snapshot version must be unique within product and channel.",
        ),
    ]

    def to_runtime_dict(self) -> dict:
        self.ensure_one()
        return {
            "id": int(self.id),
            "scene_key": str(self.scene_key or "").strip(),
            "product_key": str(self.product_key or "").strip(),
            "capability_key": str(self.capability_key or "").strip(),
            "label": str(self.label or "").strip(),
            "route": str(self.route or "").strip(),
            "version": str(self.version or "").strip() or "v1",
            "channel": str(self.channel or "").strip() or "stable",
            "is_active": bool(self.is_active),
            "source_type": str(self.source_type or "").strip(),
            "source_ref": str(self.source_ref or "").strip(),
            "source_contract_version": str(self.source_contract_version or "").strip() or "scene_contract_standard_v1",
            "contract_json": self.contract_json if isinstance(self.contract_json, dict) else {},
            "meta_json": self.meta_json if isinstance(self.meta_json, dict) else {},
            "cloned_from_snapshot_id": int(self.cloned_from_snapshot_id.id) if self.cloned_from_snapshot_id else 0,
        }
