# -*- coding: utf-8 -*-
from odoo import fields, models


class ScSceneGovernanceLog(models.Model):
    _name = "sc.scene.governance.log"
    _description = "SC Scene Governance Log"
    _order = "created_at desc, id desc"

    action = fields.Selection(
        [
            ("switch_channel", "Switch Channel"),
            ("pin_stable", "Pin Stable"),
            ("rollback", "Rollback"),
            ("export_contract", "Export Contract"),
            ("update_snapshot", "Update Snapshot"),
            ("auto_degrade_triggered", "Auto Degrade Triggered"),
            ("package_export", "Package Export"),
            ("package_import", "Package Import"),
        ],
        required=True,
    )
    actor_id = fields.Many2one("res.users")
    company_id = fields.Many2one("res.company")
    from_channel = fields.Char()
    to_channel = fields.Char()
    reason = fields.Text(required=True)
    trace_id = fields.Char()
    payload_json = fields.Json()
    created_at = fields.Datetime(default=fields.Datetime.now)
