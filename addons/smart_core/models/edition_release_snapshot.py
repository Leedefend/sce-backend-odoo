# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields, models


class ScEditionReleaseSnapshot(models.Model):
    _name = "sc.edition.release.snapshot"
    _description = "SC Edition Release Snapshot"
    _order = "product_key, version desc, id desc"

    active = fields.Boolean(default=True)
    is_active = fields.Boolean(default=False, index=True)
    product_key = fields.Char(required=True, index=True)
    base_product_key = fields.Char(required=True, index=True)
    edition_key = fields.Char(required=True, index=True)
    label = fields.Char()
    version = fields.Char(required=True, default="v1", index=True)
    channel = fields.Selection(
        [("preview", "Preview"), ("stable", "Stable")],
        default="stable",
        required=True,
        index=True,
    )
    frozen_at = fields.Datetime(required=True, default=fields.Datetime.now)
    activated_at = fields.Datetime()
    superseded_at = fields.Datetime()
    source_policy_id = fields.Many2one("sc.product.policy", string="Source Policy", ondelete="set null")
    rollback_target_snapshot_id = fields.Many2one(
        "sc.edition.release.snapshot",
        string="Rollback Target Snapshot",
        ondelete="set null",
    )
    replaced_by_snapshot_id = fields.Many2one(
        "sc.edition.release.snapshot",
        string="Replaced By Snapshot",
        ondelete="set null",
    )
    snapshot_json = fields.Json(required=True, default=dict)
    meta_json = fields.Json(required=True, default=dict)
    note = fields.Char()

    _sql_constraints = [
        (
            "sc_edition_release_snapshot_uniq",
            "unique(product_key, version)",
            "Edition release snapshot version must be unique within product.",
        ),
    ]

    def to_runtime_dict(self) -> dict:
        self.ensure_one()
        return {
            "id": int(self.id),
            "product_key": str(self.product_key or "").strip(),
            "base_product_key": str(self.base_product_key or "").strip(),
            "edition_key": str(self.edition_key or "").strip(),
            "label": str(self.label or "").strip(),
            "version": str(self.version or "").strip() or "v1",
            "channel": str(self.channel or "").strip() or "stable",
            "is_active": bool(self.is_active),
            "frozen_at": self.frozen_at.isoformat() if self.frozen_at else "",
            "activated_at": self.activated_at.isoformat() if self.activated_at else "",
            "superseded_at": self.superseded_at.isoformat() if self.superseded_at else "",
            "source_policy_id": int(self.source_policy_id.id) if self.source_policy_id else 0,
            "rollback_target_snapshot_id": int(self.rollback_target_snapshot_id.id) if self.rollback_target_snapshot_id else 0,
            "replaced_by_snapshot_id": int(self.replaced_by_snapshot_id.id) if self.replaced_by_snapshot_id else 0,
            "snapshot_json": self.snapshot_json if isinstance(self.snapshot_json, dict) else {},
            "meta_json": self.meta_json if isinstance(self.meta_json, dict) else {},
            "note": str(self.note or "").strip(),
        }
