# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScExpenseClaim(models.Model):
    _name = "sc.expense.claim"
    _description = "费用与保证金单据"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
    _order = "date_claim desc, id desc"

    name = fields.Char(string="单据号", required=True, default="新建", copy=False)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    claim_type = fields.Selection(
        [
            ("expense", "费用报销"),
            ("deposit_pay", "保证金支付"),
            ("deposit_refund", "保证金退回"),
            ("deposit_receive", "保证金收取"),
        ],
        string="业务类型",
        default="expense",
        required=True,
        index=True,
    )
    direction = fields.Selection(
        [("outflow", "流出"), ("inflow", "流入")],
        string="资金方向",
        compute="_compute_direction",
        store=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submit", "已提交"),
            ("approved", "已批准"),
            ("done", "已完成"),
            ("legacy_confirmed", "历史已确认"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        required=True,
        index=True,
    )
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="project_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True)
    applicant_name = fields.Char(string="申请人", index=True)
    payee = fields.Char(string="收款人", index=True)
    payee_account = fields.Char(string="收款账号")
    payee_bank = fields.Char(string="开户行")
    date_claim = fields.Date(string="单据日期", default=fields.Date.context_today, index=True)
    expense_type = fields.Char(string="费用类型", index=True)
    summary = fields.Char(string="摘要", index=True)
    amount = fields.Monetary(string="申请金额", currency_field="currency_id", required=True)
    approved_amount = fields.Monetary(string="批准金额", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    payment_request_id = fields.Many2one("payment.request", string="付款/收款申请", index=True, ondelete="set null")
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_no = fields.Char(string="历史单据号", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    reject_reason = fields.Char(string="驳回原因", readonly=True, copy=False)
    note = fields.Text(string="备注")
    active = fields.Boolean("有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "Legacy expense/deposit claim source must be unique.",
        ),
        ("amount_nonnegative", "CHECK(amount >= 0)", "Claim amount must be non-negative."),
    ]

    @api.depends("claim_type")
    def _compute_direction(self):
        for rec in self:
            rec.direction = "inflow" if rec.claim_type in ("deposit_refund", "deposit_receive") else "outflow"

    @api.onchange("amount")
    def _onchange_amount(self):
        for rec in self:
            if not rec.approved_amount:
                rec.approved_amount = rec.amount

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.expense.claim") or _("Expense Claim")
            vals.setdefault("approved_amount", vals.get("amount", 0.0))
        return super().create(vals_list)

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {"payment_request_id", "partner_id", "note", "active", "write_uid", "write_date"}
            if set(vals) - allowed:
                raise UserError(_("历史迁移费用/保证金单据已确认，只允许补充支付锚点、往来单位和备注。"))
        return super().write(vals)

    def action_submit(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state != "draft":
                continue
            if policy.is_approval_required(rec._name, company=rec.company_id):
                rec.write({"state": "submit", "reject_reason": False})
                company = rec.company_id or self.env.company
                rec.with_company(company).with_context(
                    allowed_company_ids=[company.id],
                ).request_validation()
            else:
                rec.write({"state": "approved", "reject_reason": False})

    def action_approve(self):
        policy_model = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state != "submit":
                continue
            if policy_model.is_approval_required(rec._name, company=rec.company_id):
                if rec.validation_status != "validated":
                    raise UserError(_("请先完成统一审批流程后再批准费用/保证金单据。"))
            else:
                policy = policy_model.get_active_policy(rec._name, company=rec.company_id)
                if policy:
                    policy.assert_user_can_approve()
            rec.state = "approved"

    def _check_state_from_condition(self):
        self.ensure_one()
        parent = getattr(super(), "_check_state_from_condition", None)
        base_ok = parent() if parent else False
        return base_ok or self.state == "submit"

    def _get_tier_reject_reason(self):
        self.ensure_one()
        reviews = self.review_ids.filtered(lambda review: review.status == "rejected" and review.comment)
        if reviews:
            return reviews.sorted(lambda review: review.write_date or review.create_date, reverse=True)[0].comment
        return _("OCA审批驳回（未填写原因）")

    def action_on_tier_approved(self):
        for rec in self:
            if rec.state != "submit":
                continue
            if rec.validation_status != "validated":
                raise UserError(_("费用/保证金单据尚未完成统一审批流程。"))
            rec.write({"state": "approved", "reject_reason": False})

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state != "submit":
                continue
            rec.write(
                {
                    "state": "draft",
                    "reject_reason": reason or rec._get_tier_reject_reason(),
                }
            )

    def action_done(self):
        for rec in self:
            if rec.state == "approved":
                rec.state = "done"

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移费用/保证金单据不能在新系统取消。"))
            if rec.state not in ("done", "cancel"):
                rec.state = "cancel"
