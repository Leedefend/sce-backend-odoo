# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScArApReportSummary(models.Model):
    _name = "sc.ar.ap.report.summary"
    _description = "应收应付报表"
    _auto = False
    _rec_name = "project_name"
    _order = "project_name"

    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True, index=True)
    legacy_project_id = fields.Char(string="旧项目ID", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)

    income_contract_amount = fields.Monetary(string="施工合同价", currency_field="currency_id", readonly=True)
    receipt_amount = fields.Monetary(string="已收款", currency_field="currency_id", readonly=True)
    output_invoice_amount = fields.Monetary(string="已开票", currency_field="currency_id", readonly=True)
    received_uninvoiced_amount = fields.Monetary(string="已收款未开票", currency_field="currency_id", readonly=True)
    invoiced_unreceived_amount = fields.Monetary(string="已开票未收款", currency_field="currency_id", readonly=True)
    payable_contract_amount = fields.Monetary(string="供货合同价", currency_field="currency_id", readonly=True)
    paid_amount = fields.Monetary(string="已付款", currency_field="currency_id", readonly=True)
    input_invoice_amount = fields.Monetary(string="已开票(应付)", currency_field="currency_id", readonly=True)
    payable_unpaid_amount = fields.Monetary(string="开票未付款", currency_field="currency_id", readonly=True)
    paid_uninvoiced_amount = fields.Monetary(string="付款未开票", currency_field="currency_id", readonly=True)
    output_tax_amount = fields.Monetary(string="开票登记税额", currency_field="currency_id", readonly=True)
    input_tax_amount = fields.Monetary(string="进项上报税额", currency_field="currency_id", readonly=True)
    deduction_tax_amount = fields.Monetary(string="抵扣总额", currency_field="currency_id", readonly=True)
    tax_burden_rate = fields.Float(string="税负", digits=(16, 6), readonly=True)
    output_surcharge_amount = fields.Monetary(string="销项附加税额", currency_field="currency_id", readonly=True)
    input_surcharge_amount = fields.Monetary(string="进项附加税额", currency_field="currency_id", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('sc_legacy_ar_ap_report_fact'),
                to_regclass('project_project'),
                to_regclass('res_company')
            """
        )
        if not all(self._cr.fetchone()):
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    f.id::integer AS id,
                    f.project_id,
                    COALESCE(NULLIF(f.legacy_project_name, ''), p.name->>'zh_CN', p.name->>'en_US', '') AS project_name,
                    f.legacy_project_id,
                    p.company_id,
                    COALESCE(c.currency_id, (SELECT currency_id FROM res_company ORDER BY id LIMIT 1)) AS currency_id,
                    COALESCE(f.income_contract_amount, 0.0) AS income_contract_amount,
                    COALESCE(f.receipt_amount, 0.0) AS receipt_amount,
                    COALESCE(f.output_invoice_amount, 0.0) AS output_invoice_amount,
                    COALESCE(f.received_uninvoiced_amount, 0.0) AS received_uninvoiced_amount,
                    COALESCE(f.invoiced_unreceived_amount, 0.0) AS invoiced_unreceived_amount,
                    COALESCE(f.payable_contract_amount, 0.0) AS payable_contract_amount,
                    COALESCE(f.paid_amount, 0.0) AS paid_amount,
                    COALESCE(f.input_invoice_amount, 0.0) AS input_invoice_amount,
                    COALESCE(f.payable_unpaid_amount, 0.0) AS payable_unpaid_amount,
                    COALESCE(f.paid_uninvoiced_amount, 0.0) AS paid_uninvoiced_amount,
                    COALESCE(f.output_tax_amount, 0.0) AS output_tax_amount,
                    COALESCE(f.input_tax_amount, 0.0) AS input_tax_amount,
                    COALESCE(f.deduction_tax_amount, 0.0) AS deduction_tax_amount,
                    COALESCE(f.tax_burden_rate, 0.0) AS tax_burden_rate,
                    COALESCE(f.output_surcharge_amount, 0.0) AS output_surcharge_amount,
                    COALESCE(f.input_surcharge_amount, 0.0) AS input_surcharge_amount,
                    '按旧存储过程 UP_USP_SELECT_YSYFHZB_XM_ZJ 默认日期口径导入项目汇总行'
                        AS coverage_note
                FROM sc_legacy_ar_ap_report_fact f
                LEFT JOIN project_project p ON p.id = f.project_id
                LEFT JOIN res_company c ON c.id = p.company_id
            )
            """
        )
