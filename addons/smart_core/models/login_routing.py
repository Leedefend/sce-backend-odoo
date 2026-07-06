# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, fields, models


class ScLoginRoute(models.Model):
    _name = "sc.login.route"
    _description = "SC Unified Login Route"
    _order = "sequence, id"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    login = fields.Char(required=True, index=True)
    target_db = fields.Char(required=True, index=True)
    entry_kind = fields.Selection(
        [("tenant", "Tenant"), ("platform_admin", "Platform Admin")],
        default="tenant",
        required=True,
        index=True,
    )
    product_key = fields.Char(default="platform")
    label = fields.Char()
    note = fields.Text()

    _sql_constraints = [
        ("sc_login_route_login_uniq", "unique(login)", "Login route must be unique per login."),
    ]

    @api.model
    def ensure_platform_default_login_routes(self):
        current_db = ""
        try:
            current_db = str(self.env.cr.dbname or "").strip()
        except Exception:
            current_db = ""
        raw_logins = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sc.login.platform_admin_logins", "admin")
        )
        for login in [item.strip() for item in str(raw_logins or "").split(",") if item.strip()]:
            route = self.sudo().search([("login", "=", login)], limit=1)
            vals = {
                "login": login,
                "target_db": current_db,
                "entry_kind": "platform_admin",
                "product_key": "platform",
                "label": "Platform Admin",
                "active": True,
            }
            if route:
                route.sudo().write({key: vals[key] for key in ("target_db", "entry_kind", "product_key", "label", "active")})
            elif current_db:
                self.sudo().create(vals)
        return True

    def to_runtime_dict(self) -> dict:
        self.ensure_one()
        return {
            "login": (self.login or "").strip(),
            "target_db": (self.target_db or "").strip(),
            "entry_kind": (self.entry_kind or "").strip(),
            "product_key": (self.product_key or "").strip(),
            "label": (self.label or "").strip(),
        }
