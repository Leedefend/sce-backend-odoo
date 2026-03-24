# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields, models


class ScProductPolicy(models.Model):
    _name = "sc.product.policy"
    _description = "SC Product Policy"
    _order = "product_key, id"

    active = fields.Boolean(default=True)
    product_key = fields.Char(required=True, index=True)
    label = fields.Char(required=True)
    version = fields.Char(default="v1")
    menu_groups = fields.Json(required=True, default=list)
    scene_entries = fields.Json(required=True, default=list)
    capability_entries = fields.Json(required=True, default=list)
    scene_version_bindings = fields.Json(required=True, default=dict)

    _sql_constraints = [
        ("sc_product_policy_key_uniq", "unique(product_key)", "Product policy key must be unique."),
    ]

    def to_runtime_dict(self) -> dict:
        self.ensure_one()
        return {
            "product_key": str(self.product_key or "").strip(),
            "label": str(self.label or "").strip(),
            "version": str(self.version or "").strip() or "v1",
            "menu_groups": self.menu_groups if isinstance(self.menu_groups, list) else [],
            "scenes": self.scene_entries if isinstance(self.scene_entries, list) else [],
            "capabilities": self.capability_entries if isinstance(self.capability_entries, list) else [],
            "scene_version_bindings": self.scene_version_bindings if isinstance(self.scene_version_bindings, dict) else {},
        }
