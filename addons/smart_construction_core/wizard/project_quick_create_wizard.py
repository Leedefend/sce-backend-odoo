# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, fields, models
from odoo.addons.smart_construction_scene.services.project_management_entry_target import (
    resolve_project_management_entry_target,
)


class ProjectQuickCreateWizard(models.TransientModel):
    _name = "project.quick.create.wizard"
    _description = "项目快速创建向导"

    name = fields.Char(string="项目名称", required=True)
    manager_id = fields.Many2one("res.users", string="项目经理", required=True)
    owner_id = fields.Many2one("res.partner", string="业主单位")

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        if "manager_id" in fields_list and not result.get("manager_id"):
            result["manager_id"] = int(self.env.user.id)
        return result

    def action_quick_create(self):
        self.ensure_one()
        vals = {
            "name": self.name,
            "manager_id": int(self.manager_id.id),
        }
        if self.owner_id:
            vals["owner_id"] = int(self.owner_id.id)
        project = self.env["project.project"].create(vals)
        target = resolve_project_management_entry_target(self.env)
        return {
            "type": "ir.actions.act_url",
            "url": str(target.get("route") or ""),
            "target": "self",
        }
