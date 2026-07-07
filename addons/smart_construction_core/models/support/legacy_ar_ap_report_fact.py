# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyArApReportFact(models.Model):
    _name = "sc.legacy.ar.ap.report.fact"
    _description = "历史应收应付报表事实"
    _order = "legacy_project_name"

    legacy_project_id = fields.Char(string="旧项目ID", required=True, index=True)
    legacy_project_name = fields.Char(string="旧项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    import_batch = fields.Char(string="导入批次", index=True)

    income_contract_amount = fields.Monetary(string="施工合同价", currency_field="currency_id")
    output_invoice_amount = fields.Monetary(string="已开票(应收)", currency_field="currency_id")
    receipt_amount = fields.Monetary(string="已收款", currency_field="currency_id")
    receivable_unpaid_amount = fields.Monetary(string="未收款", currency_field="currency_id")
    invoiced_unreceived_amount = fields.Monetary(string="已开票未收款", currency_field="currency_id")
    received_uninvoiced_amount = fields.Monetary(string="已收款未开票", currency_field="currency_id")
    payable_contract_amount = fields.Monetary(string="供货合同价", currency_field="currency_id")
    paid_amount = fields.Monetary(string="已付款", currency_field="currency_id")
    input_invoice_amount = fields.Monetary(string="已开票(应付)", currency_field="currency_id")
    payable_unpaid_amount = fields.Monetary(string="开票未付款", currency_field="currency_id")
    paid_uninvoiced_amount = fields.Monetary(string="付款未开票", currency_field="currency_id")
    output_tax_amount = fields.Monetary(string="开票登记税额", currency_field="currency_id")
    input_tax_amount = fields.Monetary(string="进项上报税额", currency_field="currency_id")
    deduction_tax_amount = fields.Monetary(string="抵扣总额", currency_field="currency_id")
    tax_burden_rate = fields.Float(string="税负", digits=(16, 6))
    actual_available_balance = fields.Monetary(string="实际可用余额", currency_field="currency_id")
    self_funding_income_amount = fields.Monetary(string="自筹收入金额", currency_field="currency_id")
    self_funding_refund_amount = fields.Monetary(string="自筹退回金额", currency_field="currency_id")
    self_funding_unreturned_amount = fields.Monetary(string="自筹未退金额", currency_field="currency_id")
    output_surcharge_amount = fields.Monetary(string="销项附加税额", currency_field="currency_id")
    input_surcharge_amount = fields.Monetary(string="进项附加税额", currency_field="currency_id")
    deduction_surcharge_amount = fields.Monetary(string="抵扣附加税额", currency_field="currency_id")

    company_id = fields.Many2one(related="project_id.company_id", string="公司", store=True, readonly=True)
    currency_id = fields.Many2one(related="project_id.company_id.currency_id", string="币种", readonly=True)

    _sql_constraints = [
        ("legacy_ar_ap_report_fact_unique", "unique(legacy_project_id)", "历史应收应付报表事实已存在。")
    ]
