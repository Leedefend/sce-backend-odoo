# -*- coding: utf-8 -*-
from uuid import uuid4

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class ScLegacyExpenseDepositFact(models.Model):
    _name = "sc.legacy.expense.deposit.fact"
    _description = "Legacy Expense and Deposit Fact"
    _order = "document_date desc, id desc"
    _rec_name = "display_name"

    def _manual_entry_source_table(self):
        return "manual.sc.legacy.expense.deposit.fact"

    def _apply_manual_entry_defaults(self, vals):
        if vals.get("legacy_source_table") and vals.get("legacy_record_id"):
            return vals
        vals = dict(vals)
        vals.setdefault("legacy_source_table", self._manual_entry_source_table())
        vals.setdefault("legacy_record_id", "MANUAL-%s" % uuid4().hex)
        vals.setdefault("source_amount_field", "manual_source_amount")
        project_id = vals.get("project_id")
        if project_id and not vals.get("legacy_project_id"):
            project = self.env["project.project"].browse(project_id)
            vals["legacy_project_id"] = project.legacy_project_id or project.project_code or str(project.id)
            vals.setdefault("legacy_project_name", project.name)
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._apply_manual_entry_defaults(vals) for vals in vals_list])

    display_name = fields.Char(string="摘要", compute="_compute_display_name", store=True)
    legacy_source_table = fields.Char(
        string="旧系统来源表",
        required=True,
        index=True,
        copy=False,
    )
    legacy_record_id = fields.Char(
        string="旧系统记录ID",
        required=True,
        index=True,
        copy=False,
    )
    legacy_pid = fields.Char(string="旧系统PID", index=True, copy=False)
    source_family = fields.Selection(
        [
            ("expense_reimbursement", "报销申请"),
            ("company_financial_outflow", "公司财务支出"),
            ("pay_guarantee_deposit", "付保证金"),
            ("pay_guarantee_deposit_refund", "付保证金退回"),
            ("self_funded_income_refund", "自筹垫付退回"),
            ("received_guarantee_deposit_refund", "收保证金退回"),
            ("project_deduction_refund", "项目扣款实缴退回"),
            ("received_guarantee_deposit_register", "收保证金登记"),
        ],
        string="来源业务家族",
        required=True,
        index=True,
    )
    direction = fields.Selection(
        [
            ("outflow", "支出"),
            ("inflow", "收入"),
            ("inflow_or_refund", "收入/退回"),
        ],
        string="来源方向",
        required=True,
        index=True,
        help="保留旧业务方向，仅用于事实分类；不生成会计、收付款或结算状态。",
    )
    document_no = fields.Char(string="旧系统单据号", index=True, copy=False)
    document_date = fields.Date(string="旧系统单据日期", index=True)
    legacy_state = fields.Char(string="旧系统状态", index=True, copy=False)

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        ondelete="restrict",
        help="旧业务事实必须锚定项目；缺失或无法确认项目的记录不进入核心资产。",
    )
    legacy_project_id = fields.Char(string="旧系统项目ID", required=True, index=True, copy=False)
    legacy_project_name = fields.Char(string="旧系统项目名称", copy=False)
    partner_id = fields.Many2one(
        "res.partner",
        string="相对方",
        index=True,
        ondelete="restrict",
        help="旧系统有明确企业或个人相对方并已资产化时填充；无法确认时保留文本。",
    )
    legacy_partner_id = fields.Char(string="旧系统相对方ID", index=True, copy=False)
    legacy_partner_name = fields.Char(string="旧系统相对方名称", index=True, copy=False)

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    source_amount = fields.Monetary(
        string="来源金额",
        currency_field="currency_id",
        required=True,
        help="旧表中的正金额业务事实；不代表 account.move、付款完成或结算完成。",
    )
    source_amount_field = fields.Char(string="金额来源字段", required=True, copy=False)
    note = fields.Text(string="旧系统备注")

    import_batch = fields.Char(
        string="导入批次",
        default="legacy_expense_deposit_asset_v1",
        required=True,
        index=True,
        copy=False,
    )
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "uniq_legacy_exp_dep_batch",
            "unique(legacy_source_table, legacy_record_id, import_batch)",
            "同一批次中旧系统费用/保证金事实不可重复。",
        )
    ]

    @api.depends("legacy_source_table", "document_no", "source_family", "source_amount", "currency_id")
    def _compute_display_name(self):
        family_labels = dict(self._fields["source_family"].selection)
        for rec in self:
            family = family_labels.get(rec.source_family) or rec.source_family or "旧业务事实"
            amount = rec.source_amount or 0.0
            currency = rec.currency_id.name or ""
            doc = rec.document_no or rec.legacy_record_id or ""
            rec.display_name = "%s / %s / %.2f %s" % (family, doc, amount, currency)

    @api.constrains("source_amount")
    def _check_source_amount_positive(self):
        for rec in self:
            currency = rec.currency_id or rec.env.company.currency_id
            rounding = currency.rounding if currency else 0.01
            if float_compare(rec.source_amount or 0.0, 0.0, precision_rounding=rounding) <= 0:
                raise ValidationError("费用/保证金来源金额必须大于 0。")

    @api.constrains("legacy_project_id", "project_id")
    def _check_project_anchor(self):
        for rec in self:
            if not rec.project_id or not (rec.legacy_project_id or "").strip():
                raise ValidationError("费用/保证金旧业务事实必须保留项目锚点。")
