# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScCompanyOperationSummary(models.Model):
    _name = "sc.company.operation.summary"
    _description = "公司经营情况表"
    _auto = False
    _rec_name = "period_label"
    _order = "period_year desc, period_month desc"

    period_label = fields.Char(string="年-月份", readonly=True)
    period_year = fields.Integer(string="年度", readonly=True, index=True)
    period_month = fields.Integer(string="月份", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)

    revenue_amount = fields.Monetary(string="营收", currency_field="currency_id", readonly=True)

    deduction_management_fee_amount = fields.Monetary(string="扣款实缴登记/管理费", currency_field="currency_id", readonly=True)
    deduction_enterprise_income_tax_amount = fields.Monetary(string="扣款实缴登记/企业所得税", currency_field="currency_id", readonly=True)
    deduction_vat_surcharge_amount = fields.Monetary(string="扣款实缴登记/增值税附加", currency_field="currency_id", readonly=True)
    deduction_vat_surcharge_nonrefundable_amount = fields.Monetary(
        string="扣款实缴登记/增值税附加(不可退)",
        currency_field="currency_id",
        readonly=True,
    )
    company_interest_income_amount = fields.Monetary(string="财务收入/利息公司", currency_field="currency_id", readonly=True)
    bid_document_fee_income_amount = fields.Monetary(string="财务收入/标书制作费", currency_field="currency_id", readonly=True)
    appearance_fee_income_amount = fields.Monetary(string="财务收入/出场费", currency_field="currency_id", readonly=True)
    certificate_fee_income_amount = fields.Monetary(string="财务收入/证书费", currency_field="currency_id", readonly=True)
    company_operation_income_amount = fields.Monetary(string="财务收入/公司经营收入", currency_field="currency_id", readonly=True)
    union_fee_income_amount = fields.Monetary(string="财务收入/工会经费", currency_field="currency_id", readonly=True)
    branch_annual_fee_income_amount = fields.Monetary(string="财务收入/分公司年费", currency_field="currency_id", readonly=True)
    disability_fund_income_amount = fields.Monetary(string="财务收入/残保金", currency_field="currency_id", readonly=True)
    personal_income_tax_income_amount = fields.Monetary(string="财务收入/个人所得税", currency_field="currency_id", readonly=True)
    income_amount = fields.Monetary(string="收入合计", currency_field="currency_id", readonly=True)

    expense_amount = fields.Monetary(string="支出合计", currency_field="currency_id", readonly=True)
    reimbursement_amount = fields.Monetary(string="报销申请/报销", currency_field="currency_id", readonly=True)
    salary_amount = fields.Monetary(string="工资登记/工资", currency_field="currency_id", readonly=True)
    employee_social_security_amount = fields.Monetary(string="社保登记/员工社保", currency_field="currency_id", readonly=True)
    certificate_social_security_amount = fields.Monetary(string="社保登记/证书社保", currency_field="currency_id", readonly=True)
    deduction_refund_surcharge_amount = fields.Monetary(string="扣款实缴退回/增值税附加退项目", currency_field="currency_id", readonly=True)
    company_enterprise_income_tax_expense_amount = fields.Monetary(string="公司财务支出/企业所得税", currency_field="currency_id", readonly=True)
    company_personal_income_tax_expense_amount = fields.Monetary(string="公司财务支出/个人所得税", currency_field="currency_id", readonly=True)
    company_vat_surcharge_tax_bureau_amount = fields.Monetary(string="公司财务支出/增值税附加交税务局", currency_field="currency_id", readonly=True)
    tender_fee_expense_amount = fields.Monetary(string="公司财务支出/投标费", currency_field="currency_id", readonly=True)
    appearance_fee_expense_amount = fields.Monetary(string="公司财务支出/出场费", currency_field="currency_id", readonly=True)
    company_operation_expense_amount = fields.Monetary(string="公司财务支出/公司经营支出", currency_field="currency_id", readonly=True)
    company_interest_expense_amount = fields.Monetary(string="公司财务支出/利息公司", currency_field="currency_id", readonly=True)
    disability_fund_expense_amount = fields.Monetary(string="公司财务支出/残保金", currency_field="currency_id", readonly=True)
    union_fee_expense_amount = fields.Monetary(string="公司财务支出/工会经费", currency_field="currency_id", readonly=True)
    service_fee_expense_amount = fields.Monetary(string="公司财务支出/手续费", currency_field="currency_id", readonly=True)

    source_line_count = fields.Integer(string="来源明细数", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('res_company'),
                to_regclass('sc_receipt_income'),
                to_regclass('sc_expense_claim'),
                to_regclass('sc_legacy_account_transaction_line'),
                to_regclass('sc_hr_payroll_document'),
                to_regclass('sc_legacy_expense_reimbursement_line'),
                to_regclass('sc_legacy_deduction_adjustment_line')
            """
        )
        (
            company_table,
            receipt_table,
            claim_table,
            transaction_table,
            salary_table,
            reimbursement_line_table,
            deduction_line_table,
        ) = self._cr.fetchone()
        if not (
            company_table
            and receipt_table
            and claim_table
            and transaction_table
            and salary_table
            and reimbursement_line_table
            and deduction_line_table
        ):
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH default_company AS (
                    SELECT id AS company_id, currency_id
                    FROM res_company
                    ORDER BY id
                    LIMIT 1
                ),
                month_keys AS (
                    SELECT date_trunc('month', t.transaction_date)::date AS month_start
                    FROM sc_legacy_account_transaction_line t
                    WHERE t.active IS TRUE AND t.transaction_date IS NOT NULL
                    UNION
                    SELECT date_trunc('month', d.document_date)::date AS month_start
                    FROM sc_legacy_deduction_adjustment_line d
                    WHERE d.active IS TRUE AND d.document_date IS NOT NULL
                    UNION
                    SELECT date_trunc('month', r.date_receipt)::date AS month_start
                    FROM sc_receipt_income r
                    WHERE r.active IS TRUE AND r.date_receipt IS NOT NULL
                    UNION
                    SELECT date_trunc('month', c.date_claim)::date AS month_start
                    FROM sc_expense_claim c
                    WHERE c.active IS TRUE AND c.date_claim IS NOT NULL
                    UNION
                    SELECT make_date(s.period_year, s.period_month, 1) AS month_start
                    FROM sc_hr_payroll_document s
                    WHERE s.active IS TRUE AND s.period_year > 0 AND s.period_month BETWEEN 1 AND 12
                    UNION
                    SELECT date_trunc('month', rl.document_date::date)::date AS month_start
                    FROM sc_legacy_expense_reimbursement_line rl
                    WHERE rl.active IS TRUE
                      AND rl.document_date ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}'
                ),
                deduction_paid AS (
                    SELECT
                        date_trunc('month', d.document_date)::date AS month_start,
                        SUM(CASE
                            WHEN d.adjustment_item_name = '管理费' AND COALESCE(d.returned_flag, '') = '否'
                            THEN d.current_actual_amount ELSE 0 END
                        ) AS deduction_management_fee_amount,
                        SUM(CASE WHEN d.adjustment_item_name = '企业所得税' THEN d.current_actual_amount ELSE 0 END)
                            AS deduction_enterprise_income_tax_amount,
                        SUM(CASE WHEN d.adjustment_item_name = '增值税附加' THEN d.current_actual_amount ELSE 0 END)
                            AS deduction_vat_surcharge_amount,
                        SUM(CASE WHEN d.adjustment_item_name IN ('增值税附加（不可退）', '增值税附加(不可退)') THEN d.current_actual_amount ELSE 0 END)
                            AS deduction_vat_surcharge_nonrefundable_amount,
                        COUNT(*)::integer AS source_line_count
                    FROM sc_legacy_deduction_adjustment_line d
                    WHERE d.active IS TRUE
                      AND d.document_date IS NOT NULL
                    GROUP BY date_trunc('month', d.document_date)::date
                ),
                company_income AS (
                    SELECT
                        date_trunc('month', r.date_receipt)::date AS month_start,
                        SUM(CASE WHEN r.income_category = '利息公司' THEN r.amount ELSE 0 END) AS company_interest_income_amount,
                        SUM(CASE WHEN r.income_category = '标书制作费' THEN r.amount ELSE 0 END) AS bid_document_fee_income_amount,
                        SUM(CASE WHEN r.income_category = '出场费' THEN r.amount ELSE 0 END) AS appearance_fee_income_amount,
                        SUM(CASE WHEN r.income_category = '证书费' THEN r.amount ELSE 0 END) AS certificate_fee_income_amount,
                        SUM(CASE WHEN r.income_category = '公司经营收入' THEN r.amount ELSE 0 END) AS company_operation_income_amount,
                        SUM(CASE WHEN r.income_category = '工会经费' THEN r.amount ELSE 0 END) AS union_fee_income_amount,
                        SUM(CASE WHEN r.income_category = '分公司年费' THEN r.amount ELSE 0 END) AS branch_annual_fee_income_amount,
                        SUM(CASE WHEN r.income_category = '残保金' THEN r.amount ELSE 0 END) AS disability_fund_income_amount,
                        SUM(CASE WHEN r.income_category = '个人所得税' THEN r.amount ELSE 0 END) AS personal_income_tax_income_amount,
                        COUNT(*)::integer AS source_line_count
                    FROM sc_receipt_income r
                    WHERE r.active IS TRUE
                      AND r.legacy_source_table = 'C_CWSFK_GSCWSR'
                      AND r.date_receipt IS NOT NULL
                    GROUP BY date_trunc('month', r.date_receipt)::date
                ),
                reimbursement AS (
                    SELECT
                        date_trunc('month', rl.document_date::date)::date AS month_start,
                        SUM(COALESCE(rl.amount, 0.0)) AS reimbursement_amount,
                        COUNT(*)::integer AS source_line_count
                    FROM sc_legacy_expense_reimbursement_line rl
                    WHERE rl.active IS TRUE
                      AND rl.document_date ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}'
                    GROUP BY date_trunc('month', rl.document_date::date)::date
                ),
                payroll AS (
                    SELECT
                        make_date(s.period_year, s.period_month, 1) AS month_start,
                        SUM(CASE
                            WHEN s.fact_type = 'salary_registration'
                             AND COALESCE(dept.name->>'zh_CN', dept.name->>'en_US', dept.name::text, '') IN ('公司', '保盛云南分公司')
                            THEN COALESCE(s.net_salary, s.amount, 0.0) ELSE 0 END
                        )
                            AS salary_amount,
                        SUM(CASE WHEN s.fact_type = 'social_registration' THEN COALESCE(s.company_amount, 0.0) + COALESCE(s.individual_amount, 0.0) ELSE 0 END)
                            AS employee_social_security_amount,
                        0.0 AS certificate_social_security_amount,
                        COUNT(*)::integer AS source_line_count
                    FROM sc_hr_payroll_document s
                    LEFT JOIN hr_department dept ON dept.id = s.department_id
                    WHERE s.active IS TRUE
                      AND s.period_year > 0
                      AND s.period_month BETWEEN 1 AND 12
                    GROUP BY make_date(s.period_year, s.period_month, 1)
                ),
                deduction_refund AS (
                    SELECT
                        date_trunc('month', t.transaction_date)::date AS month_start,
                        SUM(CASE WHEN t.category = '增值税附加' THEN t.amount ELSE 0 END) AS deduction_refund_surcharge_amount,
                        COUNT(*)::integer AS source_line_count
                    FROM sc_legacy_account_transaction_line t
                    WHERE t.active IS TRUE
                      AND t.source_table = 'T_KK_SJTHB_CB'
                      AND t.transaction_date IS NOT NULL
                    GROUP BY date_trunc('month', t.transaction_date)::date
                ),
                company_expense AS (
                    SELECT
                        date_trunc('month', t.transaction_date)::date AS month_start,
                        SUM(CASE WHEN t.note ILIKE '%企业所得税%' THEN t.amount ELSE 0 END) AS company_enterprise_income_tax_expense_amount,
                        SUM(CASE WHEN t.note ILIKE '%个人所得税%' THEN t.amount ELSE 0 END) AS company_personal_income_tax_expense_amount,
                        SUM(CASE
                            WHEN (
                                t.note ILIKE '%增值税附加%'
                                OR t.note ILIKE '%教育费附加%'
                                OR t.note ILIKE '%城市维护建设税%'
                            )
                            AND NOT (
                                substring(t.note from '增值税([0-9]+(\\.[0-9]+)?)') IS NOT NULL
                                AND abs(
                                    t.amount
                                    - (substring(t.note from '增值税([0-9]+(\\.[0-9]+)?)'))::float
                                ) < 0.01
                            )
                            THEN t.amount ELSE 0 END
                        )
                            AS company_vat_surcharge_tax_bureau_amount,
                        SUM(CASE WHEN t.note ILIKE '%投标费%' OR t.note ILIKE '%报名费%' OR t.note ILIKE '%标书费%' THEN t.amount ELSE 0 END)
                            AS tender_fee_expense_amount,
                        SUM(CASE WHEN t.note ILIKE '%出场费%' THEN t.amount ELSE 0 END) AS appearance_fee_expense_amount,
                        SUM(CASE WHEN t.note ILIKE '%经营支出%' THEN t.amount ELSE 0 END) AS company_operation_expense_amount,
                        SUM(CASE WHEN t.note ILIKE '%贷款利息%' OR t.note ILIKE '%利息公司%' THEN t.amount ELSE 0 END) AS company_interest_expense_amount,
                        SUM(CASE WHEN t.note ILIKE '%残保金%' THEN t.amount ELSE 0 END) AS disability_fund_expense_amount,
                        SUM(CASE WHEN t.note ILIKE '%工会经费%' OR t.note ILIKE '%会费%' THEN t.amount ELSE 0 END) AS union_fee_expense_amount,
                        SUM(CASE WHEN t.note ILIKE '%手续费%' THEN t.amount ELSE 0 END) AS service_fee_expense_amount,
                        COUNT(*)::integer AS source_line_count
                    FROM sc_legacy_account_transaction_line t
                    WHERE t.active IS TRUE
                      AND t.source_table = 'C_CWSFK_GSCWZC'
                      AND t.transaction_date IS NOT NULL
                    GROUP BY date_trunc('month', t.transaction_date)::date
                )
                SELECT
                    row_number() OVER (ORDER BY k.month_start DESC)::integer AS id,
                    to_char(k.month_start, 'YYYY"年-"FMMM"月"') AS period_label,
                    EXTRACT(YEAR FROM k.month_start)::integer AS period_year,
                    EXTRACT(MONTH FROM k.month_start)::integer AS period_month,
                    dc.company_id,
                    dc.currency_id,
                    (
                        COALESCE(dp.deduction_management_fee_amount, 0.0)
                        + COALESCE(dp.deduction_enterprise_income_tax_amount, 0.0)
                        + COALESCE(dp.deduction_vat_surcharge_amount, 0.0)
                        + COALESCE(dp.deduction_vat_surcharge_nonrefundable_amount, 0.0)
                        + COALESCE(ci.company_interest_income_amount, 0.0)
                        + COALESCE(ci.bid_document_fee_income_amount, 0.0)
                        + COALESCE(ci.appearance_fee_income_amount, 0.0)
                        + COALESCE(ci.certificate_fee_income_amount, 0.0)
                        + COALESCE(ci.company_operation_income_amount, 0.0)
                        + COALESCE(ci.union_fee_income_amount, 0.0)
                        + COALESCE(ci.branch_annual_fee_income_amount, 0.0)
                        + COALESCE(ci.disability_fund_income_amount, 0.0)
                        + COALESCE(ci.personal_income_tax_income_amount, 0.0)
                        - (
                            COALESCE(re.reimbursement_amount, 0.0)
                            + COALESCE(py.salary_amount, 0.0)
                            + COALESCE(py.employee_social_security_amount, 0.0)
                            + COALESCE(py.certificate_social_security_amount, 0.0)
                            + COALESCE(dr.deduction_refund_surcharge_amount, 0.0)
                            + COALESCE(ce.company_enterprise_income_tax_expense_amount, 0.0)
                            + COALESCE(ce.company_personal_income_tax_expense_amount, 0.0)
                            + COALESCE(ce.company_vat_surcharge_tax_bureau_amount, 0.0)
                            + COALESCE(ce.tender_fee_expense_amount, 0.0)
                            + COALESCE(ce.appearance_fee_expense_amount, 0.0)
                            + COALESCE(ce.company_operation_expense_amount, 0.0)
                            + COALESCE(ce.company_interest_expense_amount, 0.0)
                            + COALESCE(ce.disability_fund_expense_amount, 0.0)
                            + COALESCE(ce.union_fee_expense_amount, 0.0)
                            + COALESCE(ce.service_fee_expense_amount, 0.0)
                        )
                    ) AS revenue_amount,
                    COALESCE(dp.deduction_management_fee_amount, 0.0) AS deduction_management_fee_amount,
                    COALESCE(dp.deduction_enterprise_income_tax_amount, 0.0) AS deduction_enterprise_income_tax_amount,
                    COALESCE(dp.deduction_vat_surcharge_amount, 0.0) AS deduction_vat_surcharge_amount,
                    COALESCE(dp.deduction_vat_surcharge_nonrefundable_amount, 0.0) AS deduction_vat_surcharge_nonrefundable_amount,
                    COALESCE(ci.company_interest_income_amount, 0.0) AS company_interest_income_amount,
                    COALESCE(ci.bid_document_fee_income_amount, 0.0) AS bid_document_fee_income_amount,
                    COALESCE(ci.appearance_fee_income_amount, 0.0) AS appearance_fee_income_amount,
                    COALESCE(ci.certificate_fee_income_amount, 0.0) AS certificate_fee_income_amount,
                    COALESCE(ci.company_operation_income_amount, 0.0) AS company_operation_income_amount,
                    COALESCE(ci.union_fee_income_amount, 0.0) AS union_fee_income_amount,
                    COALESCE(ci.branch_annual_fee_income_amount, 0.0) AS branch_annual_fee_income_amount,
                    COALESCE(ci.disability_fund_income_amount, 0.0) AS disability_fund_income_amount,
                    COALESCE(ci.personal_income_tax_income_amount, 0.0) AS personal_income_tax_income_amount,
                    (
                        COALESCE(dp.deduction_management_fee_amount, 0.0)
                        + COALESCE(dp.deduction_enterprise_income_tax_amount, 0.0)
                        + COALESCE(dp.deduction_vat_surcharge_amount, 0.0)
                        + COALESCE(dp.deduction_vat_surcharge_nonrefundable_amount, 0.0)
                        + COALESCE(ci.company_interest_income_amount, 0.0)
                        + COALESCE(ci.bid_document_fee_income_amount, 0.0)
                        + COALESCE(ci.appearance_fee_income_amount, 0.0)
                        + COALESCE(ci.certificate_fee_income_amount, 0.0)
                        + COALESCE(ci.company_operation_income_amount, 0.0)
                        + COALESCE(ci.union_fee_income_amount, 0.0)
                        + COALESCE(ci.branch_annual_fee_income_amount, 0.0)
                        + COALESCE(ci.disability_fund_income_amount, 0.0)
                        + COALESCE(ci.personal_income_tax_income_amount, 0.0)
                    ) AS income_amount,
                    (
                        COALESCE(re.reimbursement_amount, 0.0)
                        + COALESCE(py.salary_amount, 0.0)
                        + COALESCE(py.employee_social_security_amount, 0.0)
                        + COALESCE(py.certificate_social_security_amount, 0.0)
                        + COALESCE(dr.deduction_refund_surcharge_amount, 0.0)
                        + COALESCE(ce.company_enterprise_income_tax_expense_amount, 0.0)
                        + COALESCE(ce.company_personal_income_tax_expense_amount, 0.0)
                        + COALESCE(ce.company_vat_surcharge_tax_bureau_amount, 0.0)
                        + COALESCE(ce.tender_fee_expense_amount, 0.0)
                        + COALESCE(ce.appearance_fee_expense_amount, 0.0)
                        + COALESCE(ce.company_operation_expense_amount, 0.0)
                        + COALESCE(ce.company_interest_expense_amount, 0.0)
                        + COALESCE(ce.disability_fund_expense_amount, 0.0)
                        + COALESCE(ce.union_fee_expense_amount, 0.0)
                        + COALESCE(ce.service_fee_expense_amount, 0.0)
                    ) AS expense_amount,
                    COALESCE(re.reimbursement_amount, 0.0) AS reimbursement_amount,
                    COALESCE(py.salary_amount, 0.0) AS salary_amount,
                    COALESCE(py.employee_social_security_amount, 0.0) AS employee_social_security_amount,
                    COALESCE(py.certificate_social_security_amount, 0.0) AS certificate_social_security_amount,
                    COALESCE(dr.deduction_refund_surcharge_amount, 0.0) AS deduction_refund_surcharge_amount,
                    COALESCE(ce.company_enterprise_income_tax_expense_amount, 0.0) AS company_enterprise_income_tax_expense_amount,
                    COALESCE(ce.company_personal_income_tax_expense_amount, 0.0) AS company_personal_income_tax_expense_amount,
                    COALESCE(ce.company_vat_surcharge_tax_bureau_amount, 0.0) AS company_vat_surcharge_tax_bureau_amount,
                    COALESCE(ce.tender_fee_expense_amount, 0.0) AS tender_fee_expense_amount,
                    COALESCE(ce.appearance_fee_expense_amount, 0.0) AS appearance_fee_expense_amount,
                    COALESCE(ce.company_operation_expense_amount, 0.0) AS company_operation_expense_amount,
                    COALESCE(ce.company_interest_expense_amount, 0.0) AS company_interest_expense_amount,
                    COALESCE(ce.disability_fund_expense_amount, 0.0) AS disability_fund_expense_amount,
                    COALESCE(ce.union_fee_expense_amount, 0.0) AS union_fee_expense_amount,
                    COALESCE(ce.service_fee_expense_amount, 0.0) AS service_fee_expense_amount,
                    (
                        COALESCE(dp.source_line_count, 0)
                        + COALESCE(ci.source_line_count, 0)
                        + COALESCE(re.source_line_count, 0)
                        + COALESCE(py.source_line_count, 0)
                        + COALESCE(dr.source_line_count, 0)
                        + COALESCE(ce.source_line_count, 0)
                    )::integer AS source_line_count,
                    '按旧表样式改为月份口径；已承载扣款实缴、财务收入、报销、工资社保、扣款退回和可识别公司财务支出；证书社保等无结构字段细项待旧过程继续核对' AS coverage_note
                FROM month_keys k
                CROSS JOIN default_company dc
                LEFT JOIN deduction_paid dp ON dp.month_start = k.month_start
                LEFT JOIN company_income ci ON ci.month_start = k.month_start
                LEFT JOIN reimbursement re ON re.month_start = k.month_start
                LEFT JOIN payroll py ON py.month_start = k.month_start
                LEFT JOIN deduction_refund dr ON dr.month_start = k.month_start
                LEFT JOIN company_expense ce ON ce.month_start = k.month_start
            )
            """
        )
