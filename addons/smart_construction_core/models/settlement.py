# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ProjectSettlement(models.Model):
    _name = "project.settlement"
    _description = "Project Settlement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="结算单号", required=True, default="New", copy=False)
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        ondelete="cascade",
    )
    type = fields.Selection(
        [
            ("pay", "支出结算"),
            ("receive", "收入结算"),
        ],
        string="类型",
        required=True,
        default="pay",
    )
    contract_id = fields.Many2one(
        "construction.contract",
        string="合同",
        domain="[('project_id', '=', project_id)]",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="往来单位",
        required=True,
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    amount = fields.Monetary(
        string="结算金额",
        currency_field="currency_id",
        help="Phase 1 暂不做自动汇总，允许人工录入。",
    )
    date_settle = fields.Date(
        string="结算日期",
        default=fields.Date.context_today,
    )
    line_ids = fields.One2many(
        "project.settlement.line",
        "settlement_id",
        string="结算行",
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("done", "完成"),
            ("cancel", "取消"),
        ],
        string="状态",
        default="draft",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = seq.next_by_code("project.settlement") or _("Settlement")
        return super().create(vals_list)

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancel"})


class ProjectSettlementLine(models.Model):
    _name = "project.settlement.line"
    _description = "Project Settlement Line"
    _order = "id"

    settlement_id = fields.Many2one(
        "project.settlement",
        string="结算单",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(string="序号", default=10)
    name = fields.Char(string="名称", required=True)
    amount = fields.Monetary(string="金额", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="settlement_id.currency_id",
        store=True,
        readonly=True,
    )
