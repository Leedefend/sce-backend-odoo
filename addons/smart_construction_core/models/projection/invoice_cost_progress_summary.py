# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScInvoiceCostProgressSummary(models.Model):
    _name = "sc.invoice.cost.progress.summary"
    _description = "发票成本进度报表"
    _auto = False
    _rec_name = "project_name"
    _order = "project_name"

    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    progress_receipt_amount = fields.Monetary(string="工程进度收款", currency_field="currency_id", readonly=True)
    output_invoice_amount = fields.Monetary(string="开票登记金额", currency_field="currency_id", readonly=True)
    input_invoice_amount = fields.Monetary(string="进项上报金额", currency_field="currency_id", readonly=True)
    cost_difference_amount = fields.Monetary(string="成本差额", currency_field="currency_id", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('project_project'),
                to_regclass('res_company'),
                to_regclass('sc_receipt_income'),
                to_regclass('sc_invoice_registration')
            """
        )
        if not all(self._cr.fetchone()):
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH progress_receipt AS (
                    SELECT
                        project_id,
                        SUM(COALESCE(amount, 0.0)) AS progress_receipt_amount
                    FROM sc_receipt_income
                    WHERE active IS TRUE
                      AND state <> 'cancel'
                      AND legacy_source_table = 'C_JFHKLR'
                      AND project_id IS NOT NULL
                    GROUP BY project_id
                ),
                output_invoice AS (
                    SELECT
                        project_id,
                        SUM(COALESCE(amount_total, 0.0)) AS output_invoice_amount
                    FROM sc_invoice_registration
                    WHERE active IS TRUE
                      AND state <> 'cancel'
                      AND direction = 'output'
                      AND legacy_source_table = 'C_JXXP_XXKPDJ'
                      AND project_id IS NOT NULL
                    GROUP BY project_id
                ),
                input_invoice AS (
                    SELECT
                        project_id,
                        SUM(COALESCE(amount_total, 0.0)) AS input_invoice_amount
                    FROM sc_invoice_registration
                    WHERE active IS TRUE
                      AND state <> 'cancel'
                      AND direction = 'input'
                      AND legacy_source_table = 'C_JXXP_ZYFPJJD'
                      AND project_id IS NOT NULL
                    GROUP BY project_id
                )
                SELECT
                    p.id::integer AS id,
                    p.id AS project_id,
                    COALESCE(p.name->>'zh_CN', p.name->>'en_US', '') AS project_name,
                    p.company_id,
                    COALESCE(c.currency_id, (SELECT currency_id FROM res_company ORDER BY id LIMIT 1)) AS currency_id,
                    COALESCE(pr.progress_receipt_amount, 0.0) AS progress_receipt_amount,
                    COALESCE(oi.output_invoice_amount, 0.0) AS output_invoice_amount,
                    COALESCE(ii.input_invoice_amount, 0.0) AS input_invoice_amount,
                    GREATEST(COALESCE(oi.output_invoice_amount, 0.0) - COALESCE(ii.input_invoice_amount, 0.0), 0.0)
                        AS cost_difference_amount,
                    '按旧发票成本进度报表 SQLID 996ae8837cd54d72975eb238cbb7c9d3：项目维度汇总工程进度收款、开票登记、进项上报和成本差额'
                        AS coverage_note
                FROM project_project p
                LEFT JOIN res_company c ON c.id = p.company_id
                LEFT JOIN progress_receipt pr ON pr.project_id = p.id
                LEFT JOIN output_invoice oi ON oi.project_id = p.id
                LEFT JOIN input_invoice ii ON ii.project_id = p.id
                WHERE p.active IS TRUE
                  AND (
                    COALESCE(pr.progress_receipt_amount, 0.0) <> 0.0
                    OR COALESCE(oi.output_invoice_amount, 0.0) <> 0.0
                    OR COALESCE(ii.input_invoice_amount, 0.0) <> 0.0
                  )
            )
            """
        )
