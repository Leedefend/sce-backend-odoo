# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields, models


class ScProductPolicy(models.Model):
    _name = "sc.product.policy"
    _description = "SC Product Policy"
    _order = "product_key, id"

    active = fields.Boolean(default=True)
    product_key = fields.Char(required=True, index=True)
    base_product_key = fields.Char(required=True, default="construction", index=True)
    edition_key = fields.Char(required=True, default="standard", index=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("ready", "Ready"),
            ("preview", "Preview"),
            ("stable", "Stable"),
            ("deprecated", "Deprecated"),
        ],
        default="draft",
        required=True,
        index=True,
    )
    access_level = fields.Selection(
        [
            ("public", "Public"),
            ("role_restricted", "Role Restricted"),
            ("internal", "Internal"),
        ],
        default="public",
        required=True,
    )
    allowed_role_codes = fields.Json(default=list)
    activated_at = fields.Datetime()
    deprecated_at = fields.Datetime()
    state_reason = fields.Char()
    promotion_note = fields.Text()
    promoted_from_policy_id = fields.Many2one("sc.product.policy", string="Promoted From", ondelete="set null")
    label = fields.Char(required=True)
    version = fields.Char(default="v1")
    menu_groups = fields.Json(required=True, default=list)
    scene_entries = fields.Json(required=True, default=list)
    capability_entries = fields.Json(required=True, default=list)
    scene_version_bindings = fields.Json(required=True, default=dict)

    _sql_constraints = [
        ("sc_product_policy_key_uniq", "unique(product_key)", "Product policy key must be unique."),
        ("sc_product_policy_edition_uniq", "unique(base_product_key, edition_key)", "Product edition must be unique."),
    ]

    def to_runtime_dict(self) -> dict:
        self.ensure_one()
        return {
            "product_key": str(self.product_key or "").strip(),
            "base_product_key": str(self.base_product_key or "").strip(),
            "edition_key": str(self.edition_key or "").strip(),
            "state": str(self.state or "").strip() or "draft",
            "access_level": str(self.access_level or "").strip() or "public",
            "allowed_role_codes": self.allowed_role_codes if isinstance(self.allowed_role_codes, list) else [],
            "activated_at": self.activated_at.isoformat() if self.activated_at else "",
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else "",
            "state_reason": str(self.state_reason or "").strip(),
            "promotion_note": str(self.promotion_note or "").strip(),
            "promoted_from_policy_id": int(self.promoted_from_policy_id.id) if self.promoted_from_policy_id else 0,
            "label": str(self.label or "").strip(),
            "version": str(self.version or "").strip() or "v1",
            "menu_groups": self.menu_groups if isinstance(self.menu_groups, list) else [],
            "scenes": self.scene_entries if isinstance(self.scene_entries, list) else [],
            "capabilities": self.capability_entries if isinstance(self.capability_entries, list) else [],
            "scene_version_bindings": self.scene_version_bindings if isinstance(self.scene_version_bindings, dict) else {},
        }
