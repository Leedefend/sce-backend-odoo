# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields, models


class ScPackRegistry(models.Model):
    _name = "sc.pack.registry"
    _description = "SC Pack Registry"
    _order = "published_at desc, id desc"

    active = fields.Boolean(default=True)
    pack_id = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    pack_version = fields.Char(required=True)
    vendor = fields.Char()
    channel = fields.Selection(
        [("stable", "Stable"), ("beta", "Beta"), ("dev", "Dev")],
        default="stable",
        required=True,
    )
    pack_type = fields.Selection(
        [("platform", "Platform"), ("industry", "Industry"), ("customer", "Customer")],
        default="platform",
        required=True,
    )
    industry_code = fields.Char()
    depends_on_ids = fields.Many2many(
        "sc.pack.registry",
        "sc_pack_dep_rel",
        "pack_id",
        "depends_on_id",
        string="Depends On",
    )
    pack_hash = fields.Char()
    signed_by = fields.Char()
    published_at = fields.Datetime()
    published_by = fields.Many2one("res.users")
    notes = fields.Char()
    changelog = fields.Text()
    payload_json = fields.Json()

    _sql_constraints = [
        ("sc_pack_registry_pack_id_uniq", "unique(pack_id)", "Pack id must be unique."),
    ]


class ScPackInstallation(models.Model):
    _name = "sc.pack.installation"
    _description = "SC Pack Installation"
    _order = "installed_at desc, id desc"

    pack_id = fields.Many2one("sc.pack.registry", required=True, ondelete="cascade")
    installed_version = fields.Char()
    installed_at = fields.Datetime()
    installed_by = fields.Many2one("res.users")
    status = fields.Selection(
        [("installed", "Installed"), ("upgraded", "Upgraded"), ("failed", "Failed")],
        default="installed",
        required=True,
    )
    last_diff_json = fields.Json()
    source_hash = fields.Char()
    upgrade_history = fields.Json()
