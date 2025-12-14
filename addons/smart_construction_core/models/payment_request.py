# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PaymentRequest(models.Model):
    _name = "payment.request"
    _description = "Payment Request"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
    _order = "id desc"

    name = fields.Char(string="申请单号", required=True, default="New", copy=False, tracking=True)
    type = fields.Selection(
        [("pay", "付款"), ("receive", "收款")],
        string="类型",
        default="pay",
        required=True,
        tracking=True,
    )
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="project_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    contract_id = fields.Many2one(
        "construction.contract",
        string="合同",
        domain="[('project_id', '=', project_id)]",
        tracking=True,
    )
    settlement_id = fields.Many2one(
        "project.settlement",
        string="关联结算单",
        domain="[('project_id', '=', project_id)]",
        tracking=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="往来单位",
        required=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    amount = fields.Monetary(
        string="申请金额",
        currency_field="currency_id",
        required=True,
        tracking=True,
    )
    date_request = fields.Date(
        string="申请日期",
        default=fields.Date.context_today,
    )
    note = fields.Text(string="备注")

    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submit", "提交"),
            ("approve", "审批中"),
            ("approved", "已批准"),
            ("done", "已完成"),
            ("cancel", "已取消"),
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
                vals["name"] = seq.next_by_code("payment.request") or _("Payment Request")
        return super().create(vals_list)

    @api.constrains("settlement_id", "type")
    def _check_settlement_type(self):
        for rec in self:
            if rec.settlement_id and rec.settlement_id.type != rec.type:
                raise ValidationError(_("结算单类型必须与付款申请类型一致。"))

    def action_submit(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_finance_user"):
            raise ValidationError(_("你没有提交付款/收款申请的权限。"))
        self.write(
            {
                "state": "submit",
            }
        )
        self.invalidate_recordset()
        for rec in self:
            company = rec.company_id or self.env.company
            rec.with_context(
                allowed_company_ids=[company.id],
                force_company=company.id,
            ).request_validation()
        self.message_post(body=_("付款/收款申请已提交，进入审批流程。"))

    def action_approve(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager"):
            raise ValidationError(_("你没有审批付款/收款申请的权限。"))
        self.write({"state": "approve"})

    def action_set_approved(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager"):
            raise ValidationError(_("你没有批准付款/收款申请的权限。"))
        self.write({"state": "approved"})

    def action_done(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager"):
            raise ValidationError(_("你没有完成付款/收款申请的权限。"))
        self.write({"state": "done"})

    def action_cancel(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager"):
            raise ValidationError(_("你没有取消付款/收款申请的权限。"))
        self.write({"state": "cancel"})

    def _check_state_from_condition(self):
        self.ensure_one()
        parent = getattr(super(), "_check_state_from_condition", None)
        base_ok = parent() if parent else False
        return base_ok or self.state == "submit"

    def action_on_tier_approved(self):
        for rec in self:
            if rec.state != "submit":
                continue
            rec.write(
                {
                    "state": "approved",
                }
            )
            rec.message_post(body=_("付款/收款申请审批通过。"))

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state != "submit":
                continue
            rec.write(
                {
                    "state": "draft",
                }
            )
            rec.message_post(body=_("付款/收款申请审批驳回：%s") % (reason or _("未填写原因")))
