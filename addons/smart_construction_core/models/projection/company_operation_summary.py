# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScCompanyOperationSummary(models.Model):
    _name = "sc.company.operation.summary"
    _description = "公司经营情况表"
    _auto = False
    _rec_name = "display_name"
    _order = "company_id, display_name"

    display_name = fields.Char(string="汇总项", readonly=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)

    receipt_amount = fields.Monetary(string="收款收入", currency_field="currency_id", readonly=True)
    company_finance_income_amount = fields.Monetary(string="公司财务收入", currency_field="currency_id", readonly=True)
    claim_inflow_amount = fields.Monetary(string="其他流入", currency_field="currency_id", readonly=True)
    income_amount = fields.Monetary(string="收入合计（已承载）", currency_field="currency_id", readonly=True)

    company_finance_expense_amount = fields.Monetary(string="公司财务支出", currency_field="currency_id", readonly=True)
    expense_reimbursement_amount = fields.Monetary(string="费用报销", currency_field="currency_id", readonly=True)
    salary_gross_amount = fields.Monetary(string="应发工资", currency_field="currency_id", readonly=True)
    salary_net_amount = fields.Monetary(string="实发工资", currency_field="currency_id", readonly=True)
    claim_outflow_amount = fields.Monetary(string="其他流出", currency_field="currency_id", readonly=True)
    expense_amount = fields.Monetary(string="支出合计（已承载）", currency_field="currency_id", readonly=True)

    output_tax_amount = fields.Monetary(string="销项税额", currency_field="currency_id", readonly=True)
    input_tax_amount = fields.Monetary(string="进项税额", currency_field="currency_id", readonly=True)
    prepaid_tax_amount = fields.Monetary(string="预缴税额", currency_field="currency_id", readonly=True)
    net_operation_amount = fields.Monetary(string="经营净额（已承载）", currency_field="currency_id", readonly=True)

    receipt_count = fields.Integer(string="收款单数", readonly=True)
    expense_claim_count = fields.Integer(string="费用/保证金单数", readonly=True)
    salary_line_count = fields.Integer(string="工资明细数", readonly=True)
    invoice_count = fields.Integer(string="发票数", readonly=True)
    source_line_count = fields.Integer(string="来源明细数", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('res_company'),
                to_regclass('project_project'),
                to_regclass('sc_receipt_income'),
                to_regclass('sc_expense_claim'),
                to_regclass('sc_legacy_account_transaction_line'),
                to_regclass('sc_legacy_salary_line'),
                to_regclass('sc_invoice_registration')
            """
        )
        (
            company_table,
            project_table,
            receipt_table,
            claim_table,
            transaction_table,
            salary_table,
            invoice_table,
        ) = self._cr.fetchone()
        if not (
            company_table
            and project_table
            and receipt_table
            and claim_table
            and transaction_table
            and salary_table
            and invoice_table
        ):
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH receipt_by_company AS (
                    SELECT
                        p.company_id,
                        COALESCE(SUM(r.amount), 0.0) AS receipt_amount,
                        COUNT(*)::integer AS receipt_count
                    FROM sc_receipt_income r
                    LEFT JOIN project_project p ON p.id = r.project_id
                    WHERE r.active IS TRUE
                      AND r.state <> 'cancel'
                    GROUP BY p.company_id
                ),
                account_tx_by_company AS (
                    SELECT
                        p.company_id,
                        COALESCE(SUM(CASE
                            WHEN t.source_table = 'C_CWSFK_GSCWSR'
                             AND t.direction = 'income'
                            THEN t.amount ELSE 0 END), 0.0) AS company_finance_income_amount,
                        COALESCE(SUM(CASE
                            WHEN t.source_table = 'C_CWSFK_GSCWZC'
                             AND t.direction = 'expense'
                            THEN t.amount ELSE 0 END), 0.0) AS company_finance_expense_amount,
                        COUNT(*)::integer AS source_line_count
                    FROM sc_legacy_account_transaction_line t
                    LEFT JOIN project_project p ON p.id = t.project_id
                    WHERE t.active IS TRUE
                    GROUP BY p.company_id
                ),
                claim_by_company AS (
                    SELECT
                        p.company_id,
                        COALESCE(SUM(CASE
                            WHEN c.claim_type = 'expense' THEN c.amount ELSE 0 END), 0.0)
                            AS expense_reimbursement_amount,
                        COALESCE(SUM(CASE
                            WHEN c.direction = 'inflow' THEN c.amount ELSE 0 END), 0.0)
                            AS claim_inflow_amount,
                        COALESCE(SUM(CASE
                            WHEN c.direction = 'outflow' AND c.claim_type <> 'expense'
                            THEN c.amount ELSE 0 END), 0.0) AS claim_outflow_amount,
                        COUNT(*)::integer AS expense_claim_count
                    FROM sc_expense_claim c
                    LEFT JOIN project_project p ON p.id = c.project_id
                    WHERE c.active IS TRUE
                      AND c.state <> 'cancel'
                    GROUP BY p.company_id
                ),
                salary_by_company AS (
                    SELECT
                        p.company_id,
                        COALESCE(SUM(s.gross_amount), 0.0) AS salary_gross_amount,
                        COALESCE(SUM(s.net_salary), 0.0) AS salary_net_amount,
                        COUNT(*)::integer AS salary_line_count
                    FROM sc_legacy_salary_line s
                    LEFT JOIN project_project p ON p.id = s.project_id
                    WHERE s.active IS TRUE
                    GROUP BY p.company_id
                ),
                invoice_by_company AS (
                    SELECT
                        p.company_id,
                        COALESCE(SUM(CASE WHEN i.direction = 'output' THEN i.tax_amount ELSE 0 END), 0.0)
                            AS output_tax_amount,
                        COALESCE(SUM(CASE WHEN i.direction = 'input' THEN i.tax_amount ELSE 0 END), 0.0)
                            AS input_tax_amount,
                        COALESCE(SUM(CASE WHEN i.direction = 'prepaid' THEN i.tax_amount ELSE 0 END), 0.0)
                            AS prepaid_tax_amount,
                        COUNT(*)::integer AS invoice_count
                    FROM sc_invoice_registration i
                    LEFT JOIN project_project p ON p.id = i.project_id
                    WHERE i.active IS TRUE
                      AND i.state <> 'cancel'
                    GROUP BY p.company_id
                ),
                company_keys AS (
                    SELECT company_id FROM receipt_by_company
                    UNION
                    SELECT company_id FROM account_tx_by_company
                    UNION
                    SELECT company_id FROM claim_by_company
                    UNION
                    SELECT company_id FROM salary_by_company
                    UNION
                    SELECT company_id FROM invoice_by_company
                )
                SELECT
                    row_number() OVER (
                        ORDER BY k.company_id NULLS LAST
                    )::integer AS id,
                    COALESCE(c.name, '未匹配公司') AS display_name,
                    k.company_id,
                    COALESCE(c.currency_id, (SELECT currency_id FROM res_company ORDER BY id LIMIT 1))
                        AS currency_id,
                    COALESCE(r.receipt_amount, 0.0) AS receipt_amount,
                    COALESCE(t.company_finance_income_amount, 0.0) AS company_finance_income_amount,
                    COALESCE(cl.claim_inflow_amount, 0.0) AS claim_inflow_amount,
                    (
                        COALESCE(r.receipt_amount, 0.0)
                        + COALESCE(t.company_finance_income_amount, 0.0)
                        + COALESCE(cl.claim_inflow_amount, 0.0)
                    ) AS income_amount,
                    COALESCE(t.company_finance_expense_amount, 0.0) AS company_finance_expense_amount,
                    COALESCE(cl.expense_reimbursement_amount, 0.0) AS expense_reimbursement_amount,
                    COALESCE(s.salary_gross_amount, 0.0) AS salary_gross_amount,
                    COALESCE(s.salary_net_amount, 0.0) AS salary_net_amount,
                    COALESCE(cl.claim_outflow_amount, 0.0) AS claim_outflow_amount,
                    (
                        COALESCE(t.company_finance_expense_amount, 0.0)
                        + COALESCE(cl.expense_reimbursement_amount, 0.0)
                        + COALESCE(s.salary_net_amount, 0.0)
                        + COALESCE(cl.claim_outflow_amount, 0.0)
                    ) AS expense_amount,
                    COALESCE(i.output_tax_amount, 0.0) AS output_tax_amount,
                    COALESCE(i.input_tax_amount, 0.0) AS input_tax_amount,
                    COALESCE(i.prepaid_tax_amount, 0.0) AS prepaid_tax_amount,
                    (
                        COALESCE(r.receipt_amount, 0.0)
                        + COALESCE(t.company_finance_income_amount, 0.0)
                        + COALESCE(cl.claim_inflow_amount, 0.0)
                        - COALESCE(t.company_finance_expense_amount, 0.0)
                        - COALESCE(cl.expense_reimbursement_amount, 0.0)
                        - COALESCE(s.salary_net_amount, 0.0)
                        - COALESCE(cl.claim_outflow_amount, 0.0)
                    ) AS net_operation_amount,
                    COALESCE(r.receipt_count, 0)::integer AS receipt_count,
                    COALESCE(cl.expense_claim_count, 0)::integer AS expense_claim_count,
                    COALESCE(s.salary_line_count, 0)::integer AS salary_line_count,
                    COALESCE(i.invoice_count, 0)::integer AS invoice_count,
                    COALESCE(t.source_line_count, 0)::integer AS source_line_count,
                    CASE
                        WHEN COALESCE(s.salary_line_count, 0) = 0 THEN
                            '已承载收款、公司财务收支、费用/保证金、发票税额；工资事实当前为空，工资列不计入完整口径'
                        ELSE
                            '已承载收款、公司财务收支、费用/保证金、工资、发票税额'
                    END AS coverage_note
                FROM company_keys k
                LEFT JOIN res_company c ON c.id = k.company_id
                LEFT JOIN receipt_by_company r ON r.company_id IS NOT DISTINCT FROM k.company_id
                LEFT JOIN account_tx_by_company t ON t.company_id IS NOT DISTINCT FROM k.company_id
                LEFT JOIN claim_by_company cl ON cl.company_id IS NOT DISTINCT FROM k.company_id
                LEFT JOIN salary_by_company s ON s.company_id IS NOT DISTINCT FROM k.company_id
                LEFT JOIN invoice_by_company i ON i.company_id IS NOT DISTINCT FROM k.company_id
            )
            """
        )
