# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScTreasuryReconciliation(models.Model):
    _name = "sc.treasury.reconciliation"
    _description = "资金对账"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
    _order = "date_document desc, id desc"

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
            ("daily_line", "资金日报"),
            ("fund_confirmation", "资金确认"),
        ],
        string="业务类型",
        default="daily_line",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("reconciled", "已对账"),
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
    date_document = fields.Date(string="业务日期", default=fields.Date.context_today, required=True, index=True)
    document_no = fields.Char(string="来源单号", index=True)
    account_name = fields.Char(string="账户名称", index=True)
    bank_account_no = fields.Char(string="银行账号", index=True)
    confirmation_item_name = fields.Char(string="确认事项", index=True)
    account_balance = fields.Monetary(string="账面余额", currency_field="currency_id")
    bank_balance = fields.Monetary(string="银行余额", currency_field="currency_id")
    system_difference = fields.Monetary(string="银企差额", currency_field="currency_id")
    daily_income = fields.Monetary(string="本日收入", currency_field="currency_id")
    daily_expense = fields.Monetary(string="本日支出", currency_field="currency_id")
    confirmation_amount = fields.Monetary(string="确认金额", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    treasury_ledger_id = fields.Many2one("sc.treasury.ledger", string="资金台账", index=True, ondelete="set null")
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    reject_reason = fields.Char(string="驳回原因", readonly=True, copy=False)
    note = fields.Text(string="备注")
    active = fields.Boolean("有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "Legacy treasury reconciliation source must be unique.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.treasury.reconciliation") or _("Treasury Reconciliation")
        return super().create(vals_list)

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {"treasury_ledger_id", "note", "active", "write_uid", "write_date"}
            if set(vals) - allowed:
                raise UserError(_("历史迁移资金对账单已确认，只允许补充资金台账关联和备注。"))
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

    def action_reconcile(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state in ("draft", "confirmed"):
                if policy.is_approval_required(rec._name, company=rec.company_id) and rec.validation_status != "validated":
                    raise UserError(_("资金对账尚未完成统一审批流程。"))
                rec.state = "reconciled"

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移资金对账单不能在新系统取消。"))
            if rec.state != "cancel":
                rec.state = "cancel"

    def _request_document_approval(self):
        self.ensure_one()
        if self.review_ids and self.validation_status == "rejected":
            self.restart_validation()
        elif not self.review_ids or self.validation_status == "no":
            reviews = self.request_validation()
            if not reviews:
                raise UserError(_("资金对账已启用审批，但没有匹配的统一审批规则，请检查业务审批配置。"))
        else:
            raise UserError(_("资金对账已经在统一审批流程中，请等待审批完成。"))

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
