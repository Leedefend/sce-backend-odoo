# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError

from odoo.addons.smart_construction_scene.services.scene_governance_service import SceneGovernanceService

CHANNELS = [("stable", "Stable"), ("beta", "Beta"), ("dev", "Dev")]
ACTIONS = [
    ("switch_channel", "Switch Company Channel"),
    ("pin_stable", "Pin Stable"),
    ("rollback", "Rollback Stable"),
    ("export_contract", "Export Contract"),
    ("update_snapshot", "Update Snapshot"),
]


class ScSceneGovernanceWizard(models.TransientModel):
    _name = "sc.scene.governance.wizard"
    _description = "SC Scene Governance Wizard"

    action = fields.Selection(ACTIONS, required=True)
    company_id = fields.Many2one("res.company")
    channel = fields.Selection(CHANNELS, default="stable")
    reason = fields.Text(required=True)

    def action_execute(self):
        self.ensure_one()
        svc = SceneGovernanceService(self.env, self.env.user)
        if self.action == "switch_channel":
            if not self.company_id:
                raise UserError("company is required")
            svc.set_company_channel(self.company_id.id, self.channel, self.reason, trace_id=self.env.context.get("trace_id"))
        elif self.action == "pin_stable":
            svc.pin_stable(self.reason, trace_id=self.env.context.get("trace_id"))
        elif self.action == "rollback":
            svc.rollback_stable(self.reason, trace_id=self.env.context.get("trace_id"))
        elif self.action == "export_contract":
            svc.export_contract(self.channel, self.reason, trace_id=self.env.context.get("trace_id"))
        elif self.action == "update_snapshot":
            svc.snapshot_update(self.channel, self.reason, trace_id=self.env.context.get("trace_id"))
        else:
            raise UserError("unsupported action")
        return {"type": "ir.actions.act_window_close"}
