# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScFundAccountOperation(models.Model):
    _name = "sc.fund.account.operation"
    _description = "资金账户操作单"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "operation_date desc, id desc"

    name = fields.Char(string="单据编号", required=True, default="/", copy=False, tracking=True)
    operation_type = fields.Selection(
        [
            ("transfer_out", "资金划拨"),
            ("transfer_between", "资金调拨"),
            ("balance_adjustment", "余额调整"),
            ("fund_daily_report", "资金日报表"),
        ],
        string="业务类型",
        required=True,
        default=lambda self: self.env.context.get("default_operation_type") or "transfer_between",
        tracking=True,
        index=True,
    )
    operation_date = fields.Date(
        string="单据日期",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        index=True,
    )
    source_account_id = fields.Many2one(
        "sc.fund.account",
        string="付款账户",
        index=True,
        ondelete="restrict",
        tracking=True,
    )
    target_account_id = fields.Many2one(
        "sc.fund.account",
        string="收款账户",
        index=True,
        ondelete="restrict",
        tracking=True,
    )
    fund_account_id = fields.Many2one(
        "sc.fund.account",
        string="账户",
        index=True,
        ondelete="restrict",
        tracking=True,
    )
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    operation_strategy = fields.Selection(
        related="project_id.operation_strategy",
        string="经营方式",
        store=True,
        readonly=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    amount = fields.Monetary(string="金额", currency_field="currency_id", tracking=True)
    daily_income = fields.Monetary(string="当日收入", currency_field="currency_id", tracking=True)
    daily_expense = fields.Monetary(string="当日支出", currency_field="currency_id", tracking=True)
    account_balance = fields.Monetary(string="账面余额", currency_field="currency_id", tracking=True)
    bank_balance = fields.Monetary(string="银行余额", currency_field="currency_id", tracking=True)
    before_balance = fields.Monetary(string="调整前余额", currency_field="currency_id", tracking=True)
    after_balance = fields.Monetary(string="调整后余额", currency_field="currency_id", tracking=True)
    operation_reason = fields.Char(string="操作原因", required=True, tracking=True)
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("done", "已完成"),
            ("cancelled", "已取消"),
        ],
        string="状态",
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )
    note = fields.Text(string="备注")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_fund_account_operation_attachment_rel",
        "operation_id",
        "attachment_id",
        string="附件",
    )
    legacy_source_model = fields.Char(string="历史来源模型", readonly=True, index=True)
    legacy_source_table = fields.Char(string="历史来源表", readonly=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", readonly=True, index=True)
    legacy_document_state = fields.Char(string="历史单据状态", readonly=True, index=True)
    legacy_visible_document_no = fields.Char(string="历史可见单据编号", readonly=True)
    legacy_visible_project_name = fields.Char(string="历史可见项目名称", readonly=True)
    legacy_visible_account_name = fields.Char(string="历史可见账户号码", readonly=True)
    legacy_visible_counterparty_account_name = fields.Char(string="历史可见收款账户", readonly=True)
    legacy_visible_transfer_type = fields.Char(string="历史可见转账类别", readonly=True)
    legacy_visible_reason = fields.Char(string="历史可见事由", readonly=True)
    legacy_visible_note = fields.Text(string="历史可见备注", readonly=True)
    legacy_attachment_ref = fields.Char(string="历史附件引用", readonly=True)
    creator_legacy_user_id = fields.Char(string="历史录入人ID", readonly=True, index=True)
    creator_name = fields.Char(string="历史录入人", readonly=True, index=True)
    created_time = fields.Datetime(string="历史录入时间", readonly=True, index=True)
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "同一历史资金操作只能迁移一次。",
        ),
    ]

    @api.model
    def _context_project_id(self):
        project_id = self.env.context.get("default_project_id") or self.env.context.get("current_project_id")
        try:
            return int(project_id) if project_id else False
        except (TypeError, ValueError):
            return False

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        project_id = res.get("project_id") or self._context_project_id()
        if project_id and "project_id" in fields_list:
            res["project_id"] = project_id
        return res

    @api.constrains("operation_type", "source_account_id", "target_account_id", "amount", "before_balance", "after_balance")
    def _check_operation_values(self):
        for record in self:
            if record.operation_type in ("transfer_out", "transfer_between"):
                if not record.source_account_id or not record.target_account_id:
                    raise ValidationError(_("资金划拨/调拨必须填写转出账户和转入账户。"))
                if record.source_account_id == record.target_account_id:
                    raise ValidationError(_("转出账户和转入账户不能相同。"))
                if record.amount <= 0:
                    raise ValidationError(_("资金划拨/调拨金额必须大于 0。"))
            if record.operation_type == "balance_adjustment":
                if record.before_balance == record.after_balance:
                    raise ValidationError(_("余额调整前后金额不能相同。"))
            if record.operation_type == "fund_daily_report" and not record.fund_account_id:
                raise ValidationError(_("资金日报表必须填写账户。"))

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"].sudo()
        for vals in vals_list:
            project_id = self._context_project_id()
            if project_id:
                vals.setdefault("project_id", project_id)
            if vals.get("name", "/") == "/":
                vals["name"] = seq.next_by_code("sc.fund.account.operation") or _("资金账户操作单")
        return super().create(vals_list)

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_reset_draft(self):
        self.write({"state": "draft"})
