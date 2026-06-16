# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ScFundAccount(models.Model):
    _name = "sc.fund.account"
    _description = "资金账户"
    _order = "sequence, account_type, name, id"
    _rec_name = "name"

    sequence = fields.Integer(string="排序号", default=10, index=True)
    name = fields.Char(string="账户名称", required=True, index=True)
    display_name = fields.Char(string="显示名称", compute="_compute_display_name", store=True, index=True)
    account_no = fields.Char(string="账号", index=True)
    account_type = fields.Char(string="账户类型", index=True)
    bank_name = fields.Char(string="开户行", index=True)
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
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    opening_balance = fields.Monetary(string="期初余额", currency_field="currency_id")
    current_account_balance = fields.Monetary(string="当前账面余额", currency_field="currency_id")
    current_bank_balance = fields.Monetary(string="当前银行余额", currency_field="currency_id")
    balance_as_of_date = fields.Date(string="余额日期", index=True)
    current_balance_source = fields.Selection(
        [
            ("opening", "期初余额"),
            ("fund_daily_report", "资金日报"),
            ("balance_adjustment", "余额调整"),
        ],
        string="余额来源",
        default="opening",
        index=True,
    )
    balance_source_operation_id = fields.Many2one(
        "sc.fund.account.operation",
        string="余额来源单据",
        readonly=True,
        ondelete="set null",
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: (self.env.ref("base.CNY", raise_if_not_found=False) or self.env.company.currency_id).id,
    )
    is_default = fields.Boolean(string="默认账户")
    fixed_account = fields.Boolean(string="固定账户")
    state = fields.Selection(
        [("active", "启用"), ("inactive", "停用")],
        string="状态",
        default="active",
        required=True,
        index=True,
    )
    note = fields.Text(string="备注")

    source_origin = fields.Selection(
        [("manual", "手工创建"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
        readonly=True,
    )
    legacy_source_model = fields.Char(string="历史来源模型", readonly=True, index=True)
    legacy_source_table = fields.Char(string="历史来源表", readonly=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", readonly=True, index=True)
    legacy_account_id = fields.Char(string="历史账户ID", readonly=True, index=True)
    legacy_state = fields.Char(string="历史状态", readonly=True, index=True)
    legacy_project_id = fields.Char(string="历史项目ID", readonly=True, index=True)

    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "同一历史账户只能投影一次。",
        ),
    ]

    @api.depends("name", "account_no", "bank_name")
    def _compute_display_name(self):
        for record in self:
            parts = [record.name]
            if record.account_no:
                parts.append(record.account_no)
            if record.bank_name:
                parts.append(record.bank_name)
            record.display_name = " / ".join(part for part in parts if part)

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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            project_id = self._context_project_id()
            if project_id:
                vals.setdefault("project_id", project_id)
            if "current_account_balance" not in vals and vals.get("opening_balance"):
                vals["current_account_balance"] = vals["opening_balance"]
                vals.setdefault("current_balance_source", "opening")
        return super().create(vals_list)
