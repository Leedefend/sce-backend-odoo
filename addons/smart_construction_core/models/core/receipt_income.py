# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScReceiptIncome(models.Model):
    _name = "sc.receipt.income"
    _description = "收款与收入登记"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
    _order = "date_receipt desc, id desc"

    name = fields.Char(string="单据号", required=True, default="新建", copy=False)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    source_kind = fields.Selection(
        [
            ("receipt_income", "收款收入"),
            ("residual_receipt", "残余收款"),
        ],
        string="业务类型",
        default="receipt_income",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("received", "已收款"),
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
    contract_id = fields.Many2one("construction.contract", string="合同", index=True)
    payment_request_id = fields.Many2one("payment.request", string="收款申请", index=True, ondelete="set null")
    treasury_ledger_id = fields.Many2one("sc.treasury.ledger", string="资金台账", index=True, ondelete="set null")
    date_receipt = fields.Date(string="收款日期", default=fields.Date.context_today, index=True)
    document_no = fields.Char(string="来源单号", index=True)
    receipt_type = fields.Char(string="收款类型", index=True)
    income_category = fields.Char(string="收入类别", index=True)
    payment_method = fields.Char(string="收款方式", index=True)
    receiving_account = fields.Char(string="收款账户", index=True)
    bill_no = fields.Char(string="票据号", index=True)
    invoice_ref = fields.Char(string="发票引用", index=True)
    amount = fields.Monetary(string="收款金额", currency_field="currency_id", required=True)
    deducted_invoice_amount = fields.Monetary(string="已抵发票金额", currency_field="currency_id")
    deducted_tax_amount = fields.Monetary(string="已抵税额", currency_field="currency_id")
    settlement_amount = fields.Monetary(string="结算金额", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    legacy_residual_reason = fields.Char(string="残余原因", index=True, readonly=True)
    legacy_attachment_ref = fields.Char(string="历史附件引用", readonly=True)
    reject_reason = fields.Char(string="驳回原因", readonly=True, copy=False)
    note = fields.Text(string="备注")
    active = fields.Boolean("有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "Legacy receipt income source must be unique.",
        ),
        ("amount_nonnegative", "CHECK(amount >= 0)", "Receipt amount must be non-negative."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.receipt.income") or _("Receipt Income")
        return super().create(vals_list)

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {
                "payment_request_id",
                "treasury_ledger_id",
                "partner_id",
                "contract_id",
                "note",
                "active",
                "write_uid",
                "write_date",
            }
            if set(vals) - allowed:
                raise UserError(_("历史迁移收款/收入单据已确认，只允许补充业务锚点和备注。"))
        return super().write(vals)

    def action_confirm(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state == "draft":
                if policy.is_approval_required(rec._name, company=rec.company_id):
                    company = rec.company_id or self.env.company
                    rec.with_company(company).with_context(allowed_company_ids=[company.id])._request_document_approval()
                else:
                    rec.write({"state": "confirmed", "reject_reason": False})

    def action_received(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state in ("draft", "confirmed"):
                if policy.is_approval_required(rec._name, company=rec.company_id) and rec.validation_status != "validated":
                    raise UserError(_("收款收入尚未完成统一审批流程。"))
                rec.state = "received"

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移收款/收入单据不能在新系统取消。"))
            if rec.state != "cancel":
                rec.state = "cancel"

    def _request_document_approval(self):
        self.ensure_one()
        if self.review_ids and self.validation_status == "rejected":
            self.restart_validation()
        elif not self.review_ids or self.validation_status == "no":
            reviews = self.request_validation()
            if not reviews:
                raise UserError(_("收款收入已启用审批，但没有匹配的统一审批规则，请检查业务审批配置。"))
        else:
            raise UserError(_("收款收入已经在统一审批流程中，请等待审批完成。"))

    def _check_state_from_condition(self):
        self.ensure_one()
        parent = getattr(super(), "_check_state_from_condition", None)
        base_ok = parent() if parent else False
        return base_ok or self.state == "draft"

    def _get_tier_reject_reason(self):
        self.ensure_one()
        reviews = self.review_ids.filtered(lambda review: review.status == "rejected" and review.comment)
        if reviews:
            return reviews.sorted(lambda review: review.write_date or review.create_date, reverse=True)[0].comment
        return _("OCA审批驳回（未填写原因）")

    def action_on_tier_approved(self):
        for rec in self:
            if rec.state == "draft":
                rec.with_context(skip_validation_check=True).write({"state": "confirmed", "reject_reason": False})

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state == "draft":
                rec.with_context(skip_validation_check=True).write(
                    {"reject_reason": reason or rec._get_tier_reject_reason()}
                )
