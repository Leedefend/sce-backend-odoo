# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScFinancingLoan(models.Model):
    _name = "sc.financing.loan"
    _description = "融资与借款登记"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
    _order = "document_date desc, id desc"

    name = fields.Char(string="单据号", required=True, default="新建", copy=False)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    loan_type = fields.Selection(
        [
            ("loan_registration", "贷款登记"),
            ("borrowing_request", "借款申请"),
        ],
        string="业务类型",
        default="loan_registration",
        required=True,
        index=True,
    )
    direction = fields.Selection(
        [("financing_in", "融资流入"), ("borrowed_fund", "借入资金")],
        string="资金方向",
        default="financing_in",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
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
    document_no = fields.Char(string="来源单号", index=True)
    document_date = fields.Date(string="业务日期", default=fields.Date.context_today, index=True)
    due_date = fields.Date(string="到期日", index=True)
    amount = fields.Monetary(string="金额", currency_field="currency_id", required=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    purpose = fields.Text(string="用途说明")
    rate_label = fields.Char(string="利率/类型", index=True)
    extra_ref = fields.Char(string="扩展引用", index=True)
    extra_label = fields.Char(string="扩展标签", index=True)
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    legacy_counterparty_id = fields.Char(string="历史往来方ID", index=True, readonly=True)
    legacy_counterparty_name = fields.Char(string="历史往来方", index=True, readonly=True)
    legacy_amount_field = fields.Char(string="历史金额字段", index=True, readonly=True)
    reject_reason = fields.Char(string="驳回原因", readonly=True, copy=False)
    note = fields.Text(string="备注")
    active = fields.Boolean("有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "Legacy financing loan source must be unique.",
        ),
        ("amount_nonnegative", "CHECK(amount >= 0)", "Financing loan amount must be non-negative."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.financing.loan") or _("Financing Loan")
        return super().create(vals_list)

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {"partner_id", "note", "active", "write_uid", "write_date"}
            if set(vals) - allowed:
                raise UserError(_("历史迁移融资/借款单据已确认，只允许补充往来单位和备注。"))
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

    def action_done(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state in ("draft", "confirmed"):
                if policy.is_approval_required(rec._name, company=rec.company_id) and rec.validation_status != "validated":
                    raise UserError(_("融资借款尚未完成统一审批流程。"))
                rec.state = "done"

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移融资/借款单据不能在新系统取消。"))
            if rec.state != "cancel":
                rec.state = "cancel"

    def _request_document_approval(self):
        self.ensure_one()
        if self.review_ids and self.validation_status == "rejected":
            self.restart_validation()
        elif not self.review_ids or self.validation_status == "no":
            reviews = self.request_validation()
            if not reviews:
                raise UserError(_("融资借款已启用审批，但没有匹配的统一审批规则，请检查业务审批配置。"))
        else:
            raise UserError(_("融资借款已经在统一审批流程中，请等待审批完成。"))

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
