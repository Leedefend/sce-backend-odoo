# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScArApCompanySummary(models.Model):
    _name = "sc.ar.ap.company.summary"
    _description = "应收应付报表"
    _auto = False
    _rec_name = "display_name"
    _order = "project_id"

    display_name = fields.Char(string="汇总项", readonly=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True, index=True)
    partner_count = fields.Integer(string="往来单位数", readonly=True)
    income_contract_amount = fields.Float(string="收入合同金额", readonly=True)
    output_invoice_amount = fields.Float(string="已开票", readonly=True)
    receipt_amount = fields.Float(string="已收款", readonly=True)
    receivable_unpaid_amount = fields.Float(string="未收款", readonly=True)
    invoiced_unreceived_amount = fields.Float(string="已开票未收款", readonly=True)
    received_uninvoiced_amount = fields.Float(string="已收款未开票", readonly=True)
    payable_contract_amount = fields.Float(string="应付合同金额", readonly=True)
    payable_pricing_method_text = fields.Char(string="计价方式", readonly=True)
    input_invoice_amount = fields.Float(string="已收供应商发票", readonly=True)
    paid_amount = fields.Float(string="已付款", readonly=True)
    payable_unpaid_amount = fields.Float(string="未付款", readonly=True)
    paid_uninvoiced_amount = fields.Float(string="付款超票", readonly=True)
    output_tax_amount = fields.Float(string="销项税额", readonly=True)
    input_tax_amount = fields.Float(string="进项税额", readonly=True)
    deduction_tax_amount = fields.Float(string="抵扣税额", readonly=True)
    tax_deduction_rate = fields.Float(
        string="抵扣比例",
        readonly=True,
        help="项目级指标：按项目抵扣税额合计 / 项目销项税额合计计算。"
        "本报表每个项目只展示一次，导出或透视时不应跨项目简单平均。",
    )
    output_surcharge_amount = fields.Float(string="销项附加税", readonly=True)
    input_surcharge_amount = fields.Float(string="进项附加税", readonly=True)
    deduction_surcharge_amount = fields.Float(string="抵扣附加税", readonly=True)
    self_funding_income_amount = fields.Float(string="自筹收入金额", readonly=True)
    self_funding_refund_amount = fields.Float(string="自筹退回金额", readonly=True)
    self_funding_unreturned_amount = fields.Float(string="自筹未退金额", readonly=True)
    actual_available_balance = fields.Float(
        string="实际可用余额",
        readonly=True,
        help="项目级指标：来自旧库项目资金余额。本报表每个项目只展示一次。",
    )

    def init(self):
        self._cr.execute("SELECT to_regclass('sc_ar_ap_project_summary')")
        if not self._cr.fetchone()[0]:
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH pricing AS (
                    SELECT
                        project_id,
                        string_agg(DISTINCT pricing_method, ', ' ORDER BY pricing_method)
                            AS payable_pricing_method_text
                    FROM (
                        SELECT
                            summary.project_id,
                            trim(split_value.value) AS pricing_method
                        FROM sc_ar_ap_project_summary summary
                        CROSS JOIN LATERAL regexp_split_to_table(
                            summary.payable_pricing_method_text,
                            ','
                        ) AS split_value(value)
                        WHERE NULLIF(trim(split_value.value), '') IS NOT NULL
                    ) split_pricing
                    GROUP BY project_id
                )
                SELECT
                    row_number() OVER (ORDER BY s.project_id) AS id,
                    COALESCE(MAX(s.project_name), '未匹配项目') AS display_name,
                    s.project_id,
                    COALESCE(MAX(s.project_name), '未匹配项目') AS project_name,
                    COUNT(DISTINCT NULLIF(s.partner_key, '')) AS partner_count,
                    SUM(COALESCE(s.income_contract_amount, 0.0)) AS income_contract_amount,
                    SUM(COALESCE(s.output_invoice_amount, 0.0)) AS output_invoice_amount,
                    SUM(COALESCE(s.receipt_amount, 0.0)) AS receipt_amount,
                    SUM(COALESCE(s.receivable_unpaid_amount, 0.0)) AS receivable_unpaid_amount,
                    SUM(COALESCE(s.invoiced_unreceived_amount, 0.0)) AS invoiced_unreceived_amount,
                    SUM(COALESCE(s.received_uninvoiced_amount, 0.0)) AS received_uninvoiced_amount,
                    SUM(COALESCE(s.payable_contract_amount, 0.0)) AS payable_contract_amount,
                    COALESCE(MAX(p.payable_pricing_method_text), '') AS payable_pricing_method_text,
                    SUM(COALESCE(s.input_invoice_amount, 0.0)) AS input_invoice_amount,
                    SUM(COALESCE(s.paid_amount, 0.0)) AS paid_amount,
                    SUM(COALESCE(s.payable_unpaid_amount, 0.0)) AS payable_unpaid_amount,
                    SUM(COALESCE(s.paid_uninvoiced_amount, 0.0)) AS paid_uninvoiced_amount,
                    SUM(COALESCE(s.output_tax_amount, 0.0)) AS output_tax_amount,
                    SUM(COALESCE(s.input_tax_amount, 0.0)) AS input_tax_amount,
                    SUM(COALESCE(s.deduction_tax_amount, 0.0)) AS deduction_tax_amount,
                    MAX(COALESCE(s.tax_deduction_rate, 0.0)) AS tax_deduction_rate,
                    SUM(COALESCE(s.output_surcharge_amount, 0.0)) AS output_surcharge_amount,
                    SUM(COALESCE(s.input_surcharge_amount, 0.0)) AS input_surcharge_amount,
                    SUM(COALESCE(s.deduction_surcharge_amount, 0.0)) AS deduction_surcharge_amount,
                    SUM(COALESCE(s.self_funding_income_amount, 0.0)) AS self_funding_income_amount,
                    SUM(COALESCE(s.self_funding_refund_amount, 0.0)) AS self_funding_refund_amount,
                    SUM(COALESCE(s.self_funding_unreturned_amount, 0.0)) AS self_funding_unreturned_amount,
                    MAX(COALESCE(s.actual_available_balance, 0.0)) AS actual_available_balance
                FROM sc_ar_ap_project_summary s
                LEFT JOIN pricing p ON p.project_id IS NOT DISTINCT FROM s.project_id
                GROUP BY s.project_id
            )
            """
        )
