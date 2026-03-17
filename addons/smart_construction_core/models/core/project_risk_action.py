# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields, models


class ProjectRiskAction(models.Model):
    _name = "project.risk.action"
    _description = "项目风险动作"
    _rec_name = "name"
    _order = "write_date desc, id desc"

    name = fields.Char(string="风险事项", required=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    state = fields.Selection(
        [
            ("open", "待处理"),
            ("claimed", "已认领"),
            ("escalated", "已升级"),
            ("closed", "已关闭"),
        ],
        string="状态",
        default="open",
        required=True,
        index=True,
    )
    risk_level = fields.Selection(
        [
            ("low", "低"),
            ("medium", "中"),
            ("high", "高"),
            ("critical", "严重"),
        ],
        string="风险等级",
        default="medium",
        required=True,
    )
    owner_id = fields.Many2one("res.users", string="负责人", index=True)
    source_risk_id = fields.Many2one("project.risk", string="来源风险投影", readonly=True)
    note = fields.Text(string="说明")
    active = fields.Boolean(default=True)

    def action_claim(self, owner_id: int | None = None):
        for rec in self:
            values = {"state": "claimed"}
            if owner_id:
                values["owner_id"] = int(owner_id)
            elif not rec.owner_id:
                values["owner_id"] = self.env.user.id
            rec.write(values)
        return True

    def action_escalate(self, note: str | None = None):
        for rec in self:
            values = {"state": "escalated"}
            if note:
                values["note"] = str(note)
            rec.write(values)
        return True

    def action_close(self, note: str | None = None):
        for rec in self:
            values = {"state": "closed"}
            if note:
                values["note"] = str(note)
            rec.write(values)
        return True
