# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields, models


class EvidenceException(models.Model):
    _name = "sc.evidence.exception"
    _description = "Evidence Exception"
    _rec_name = "name"
    _order = "write_date desc, id desc"

    name = fields.Char(string="异常标题", required=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    risk_code = fields.Char(string="风险编码", required=True, index=True)
    severity = fields.Selection(
        [
            ("low", "低"),
            ("medium", "中"),
            ("high", "高"),
            ("critical", "严重"),
        ],
        string="风险等级",
        default="medium",
        required=True,
        index=True,
    )
    status = fields.Selection(
        [
            ("open", "待处理"),
            ("processing", "处理中"),
            ("resolved", "已处理"),
            ("ignored", "已忽略"),
        ],
        string="状态",
        default="open",
        required=True,
        index=True,
    )
    evidence_refs = fields.Text(string="证据引用")
    assigned_to = fields.Many2one("res.users", string="指派给", index=True)
    resolution_note = fields.Text(string="处理说明")
    risk_action_id = fields.Many2one("project.risk.action", string="关联风险动作", readonly=True, index=True)
    active = fields.Boolean(default=True)

    def action_assign(self, user_id=None):
        user_id = int(user_id or self.env.user.id or 0)
        for rec in self:
            values = {"status": "processing"}
            if user_id > 0:
                values["assigned_to"] = user_id
            rec.write(values)
        return True

    def action_processing(self, user_id=None, note=None):
        user_id = int(user_id or self.env.user.id or 0)
        for rec in self:
            values = {"status": "processing"}
            if user_id > 0:
                values["assigned_to"] = user_id
            if note:
                values["resolution_note"] = str(note)
            rec.write(values)
        return True

    def action_resolve(self, note=None):
        for rec in self:
            values = {"status": "resolved"}
            if note:
                values["resolution_note"] = str(note)
            rec.write(values)
        return True

    def action_ignore(self, note=None):
        for rec in self:
            values = {"status": "ignored"}
            if note:
                values["resolution_note"] = str(note)
            rec.write(values)
        return True
