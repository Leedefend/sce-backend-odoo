# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..support.state_machine import ScStateMachine


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
        ScStateMachine.selection(ScStateMachine.SETTLEMENT),
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
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿结算单可以确认。"))
            rec._check_business_anchor()
            rec.write({"state": "confirmed"})

    def action_done(self):
        for rec in self:
            if rec.state != "confirmed":
                raise UserError(_("只有已确认结算单可以完成。"))
            rec._check_business_anchor()
            rec.write({"state": "done"})

    def action_cancel(self):
        for rec in self:
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认结算单可以取消。"))
            rec.write({"state": "cancel"})

    def _check_business_anchor(self):
        for rec in self:
            if not rec.date_settle:
                raise UserError(_("结算单必须填写结算日期。"))
            if rec.amount <= 0:
                raise UserError(_("结算金额必须大于 0。"))
            if rec.contract_id:
                if rec.contract_id.project_id != rec.project_id:
                    raise UserError(_("结算单合同必须属于当前项目。"))
                if rec.contract_id.partner_id and rec.contract_id.partner_id != rec.partner_id:
                    raise UserError(_("结算单往来单位必须与合同相对方一致。"))


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
