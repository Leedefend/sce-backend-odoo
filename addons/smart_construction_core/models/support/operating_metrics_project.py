# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScOperatingMetricsProject(models.Model):
    """
    经营指标（项目维度）SQL 视图：
    - 只读聚合视图，不在查询时创建数据；
    - 指标口径依赖结算单（store=True）聚合，风险数在视图内近似统计。
    """

    _name = "sc.operating.metrics.project"
    _description = "经营指标（项目）"
    _rec_name = "project_id"
    _order = "project_id desc"
    _auto = False

    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, readonly=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)

    receipt_amount = fields.Monetary(string="本期收款", currency_field="currency_id", readonly=True)
    output_invoice_amount = fields.Monetary(string="销项开票金额", currency_field="currency_id", readonly=True)
    output_tax_amount = fields.Monetary(string="销项税额", currency_field="currency_id", readonly=True)
    input_invoice_amount = fields.Monetary(string="进项发票金额", currency_field="currency_id", readonly=True)
    input_tax_amount = fields.Monetary(string="进项税额", currency_field="currency_id", readonly=True)
    prepaid_tax_amount = fields.Monetary(string="预缴税额", currency_field="currency_id", readonly=True)
    deduction_amount = fields.Monetary(string="抵扣金额", currency_field="currency_id", readonly=True)
    deduction_tax_amount = fields.Monetary(string="抵扣税额", currency_field="currency_id", readonly=True)
    deduction_surcharge_amount = fields.Monetary(string="抵扣附加税", currency_field="currency_id", readonly=True)
    company_finance_income_amount = fields.Monetary(string="公司财务收入", currency_field="currency_id", readonly=True)
    company_finance_expense_amount = fields.Monetary(string="公司财务支出", currency_field="currency_id", readonly=True)
    deduction_paid_amount = fields.Monetary(string="扣款实缴", currency_field="currency_id", readonly=True)
    deduction_refund_amount = fields.Monetary(string="扣款退回", currency_field="currency_id", readonly=True)
    expense_amount = fields.Monetary(string="费用/保证金支出", currency_field="currency_id", readonly=True)
    net_cash_amount = fields.Monetary(string="经营现金净额", currency_field="currency_id", readonly=True)
    tax_balance_amount = fields.Monetary(string="税额净额", currency_field="currency_id", readonly=True)
    settlement_amount_total = fields.Monetary(string="结算总额", currency_field="currency_id", readonly=True)
    settlement_amount_paid = fields.Monetary(string="已付金额", currency_field="currency_id", readonly=True)
    settlement_amount_payable = fields.Monetary(string="可付余额", currency_field="currency_id", readonly=True)

    receipt_count = fields.Integer(string="收款单数", readonly=True)
    invoice_count = fields.Integer(string="发票数", readonly=True)
    tax_deduction_count = fields.Integer(string="抵扣登记数", readonly=True)
    source_line_count = fields.Integer(string="来源明细数", readonly=True)
    overpay_risk_count = fields.Integer(string="超付风险单数", readonly=True)
    three_way_missing_count = fields.Integer(string="三单缺失项", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def init(self):
        # 依赖的表若尚未创建（新装阶段），跳过视图创建，等待下次加载再建
        self._cr.execute(
            """
            SELECT
                to_regclass('sc_settlement_order'),
                to_regclass('payment_request'),
                to_regclass('sc_receipt_income'),
                to_regclass('sc_invoice_registration'),
                to_regclass('sc_tax_deduction_registration'),
                to_regclass('sc_legacy_account_transaction_line'),
                to_regclass('sc_expense_claim')
            """
        )
        required_tables = self._cr.fetchone()
        if not all(required_tables):
            return
        # 强制清理残留表/视图，再重建只读视图
        tools.drop_view_if_exists(self._cr, self._table)
        # 若曾误生成表，清理之
        try:
            self._cr.execute(f"DROP TABLE IF EXISTS {self._table} CASCADE")
        except Exception:
            self._cr.rollback()
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH settlement_agg AS (
                    SELECT
                        project_id,
                        COALESCE(SUM(amount_total), 0.0)   AS settlement_amount_total,
                        COALESCE(SUM(amount_paid), 0.0)    AS settlement_amount_paid,
                        COALESCE(SUM(amount_payable), 0.0) AS settlement_amount_payable
                    FROM sc_settlement_order
                    WHERE state = 'approve'
                    GROUP BY project_id
                ),
                receipt_agg AS (
                    SELECT
                        project_id,
                        COALESCE(SUM(amount), 0.0) AS receipt_amount,
                        COUNT(*)::integer AS receipt_count
                    FROM sc_receipt_income
                    WHERE active IS TRUE
                      AND state <> 'cancel'
                    GROUP BY project_id
                ),
                invoice_agg AS (
                    SELECT
                        project_id,
                        COALESCE(SUM(CASE WHEN direction = 'output' THEN amount_total ELSE 0 END), 0.0)
                            AS output_invoice_amount,
                        COALESCE(SUM(CASE WHEN direction = 'output' THEN tax_amount ELSE 0 END), 0.0)
                            AS output_tax_amount,
                        COALESCE(SUM(CASE WHEN direction = 'input' THEN amount_total ELSE 0 END), 0.0)
                            AS input_invoice_amount,
                        COALESCE(SUM(CASE WHEN direction = 'input' THEN tax_amount ELSE 0 END), 0.0)
                            AS input_tax_amount,
                        COALESCE(SUM(CASE WHEN direction = 'prepaid' THEN tax_amount ELSE 0 END), 0.0)
                            AS prepaid_tax_amount,
                        COUNT(*)::integer AS invoice_count
                    FROM sc_invoice_registration
                    WHERE active IS TRUE
                      AND state <> 'cancel'
                    GROUP BY project_id
                ),
                deduction_agg AS (
                    SELECT
                        project_id,
                        COALESCE(SUM(deduction_amount), 0.0) AS deduction_amount,
                        COALESCE(SUM(deduction_tax_amount), 0.0) AS deduction_tax_amount,
                        COALESCE(SUM(deduction_surcharge_amount), 0.0) AS deduction_surcharge_amount,
                        COUNT(*)::integer AS tax_deduction_count
                    FROM sc_tax_deduction_registration
                    WHERE active IS TRUE
                      AND state <> 'cancel'
                    GROUP BY project_id
                ),
                account_tx_agg AS (
                    SELECT
                        project_id,
                        COALESCE(SUM(CASE
                            WHEN source_table = 'C_CWSFK_GSCWSR' AND direction = 'income'
                            THEN amount ELSE 0 END), 0.0) AS company_finance_income_amount,
                        COALESCE(SUM(CASE
                            WHEN source_table = 'C_CWSFK_GSCWZC' AND direction = 'expense'
                            THEN amount ELSE 0 END), 0.0) AS company_finance_expense_amount,
                        COALESCE(SUM(CASE
                            WHEN source_table = 'T_KK_SJDJB_CB' AND direction = 'expense'
                            THEN amount ELSE 0 END), 0.0) AS deduction_paid_amount,
                        COALESCE(SUM(CASE
                            WHEN source_table = 'T_KK_SJTHB_CB' AND direction = 'income'
                            THEN amount ELSE 0 END), 0.0) AS deduction_refund_amount,
                        COUNT(*)::integer AS source_line_count
                    FROM sc_legacy_account_transaction_line
                    WHERE active IS TRUE
                    GROUP BY project_id
                ),
                claim_agg AS (
                    SELECT
                        project_id,
                        COALESCE(SUM(CASE
                            WHEN direction = 'outflow' THEN amount ELSE 0 END), 0.0) AS expense_amount
                    FROM sc_expense_claim
                    WHERE active IS TRUE
                      AND state <> 'cancel'
                    GROUP BY project_id
                ),
                overpay_risk AS (
                    -- 近似口径：付款申请金额 > 结算可付余额 视为超付风险（与 UI 标记一致）
                    SELECT
                        pr.project_id,
                        COUNT(*) AS overpay_risk_count
                    FROM payment_request pr
                    JOIN sc_settlement_order s ON s.id = pr.settlement_id
                    WHERE pr.type = 'pay'
                      AND COALESCE(s.amount_payable, 0.0) < COALESCE(pr.amount, 0.0)
                    GROUP BY pr.project_id
                )
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    p.id AS project_id,
                    p.company_id AS company_id,
                    rc.currency_id AS currency_id,

                    COALESCE(ra.receipt_amount, 0.0) AS receipt_amount,
                    COALESCE(ia.output_invoice_amount, 0.0) AS output_invoice_amount,
                    COALESCE(ia.output_tax_amount, 0.0) AS output_tax_amount,
                    COALESCE(ia.input_invoice_amount, 0.0) AS input_invoice_amount,
                    COALESCE(ia.input_tax_amount, 0.0) AS input_tax_amount,
                    COALESCE(ia.prepaid_tax_amount, 0.0) AS prepaid_tax_amount,
                    COALESCE(da.deduction_amount, 0.0) AS deduction_amount,
                    COALESCE(da.deduction_tax_amount, 0.0) AS deduction_tax_amount,
                    COALESCE(da.deduction_surcharge_amount, 0.0) AS deduction_surcharge_amount,
                    COALESCE(ta.company_finance_income_amount, 0.0) AS company_finance_income_amount,
                    COALESCE(ta.company_finance_expense_amount, 0.0) AS company_finance_expense_amount,
                    COALESCE(ta.deduction_paid_amount, 0.0) AS deduction_paid_amount,
                    COALESCE(ta.deduction_refund_amount, 0.0) AS deduction_refund_amount,
                    COALESCE(ca.expense_amount, 0.0) AS expense_amount,
                    (
                        COALESCE(ra.receipt_amount, 0.0)
                        + COALESCE(ta.company_finance_income_amount, 0.0)
                        + COALESCE(ta.deduction_refund_amount, 0.0)
                        - COALESCE(ta.company_finance_expense_amount, 0.0)
                        - COALESCE(ta.deduction_paid_amount, 0.0)
                        - COALESCE(ca.expense_amount, 0.0)
                    ) AS net_cash_amount,
                    (
                        COALESCE(ia.output_tax_amount, 0.0)
                        + COALESCE(ia.prepaid_tax_amount, 0.0)
                        - COALESCE(ia.input_tax_amount, 0.0)
                        - COALESCE(da.deduction_tax_amount, 0.0)
                    ) AS tax_balance_amount,
                    COALESCE(sa.settlement_amount_total, 0.0)   AS settlement_amount_total,
                    COALESCE(sa.settlement_amount_paid, 0.0)    AS settlement_amount_paid,
                    COALESCE(sa.settlement_amount_payable, 0.0) AS settlement_amount_payable,

                    COALESCE(ra.receipt_count, 0)::integer AS receipt_count,
                    COALESCE(ia.invoice_count, 0)::integer AS invoice_count,
                    COALESCE(da.tax_deduction_count, 0)::integer AS tax_deduction_count,
                    COALESCE(ta.source_line_count, 0)::integer AS source_line_count,
                    COALESCE(rk.overpay_risk_count, 0) AS overpay_risk_count,
                    0::integer AS three_way_missing_count,
                    CASE
                        WHEN COALESCE(ra.receipt_count, 0) = 0
                         AND COALESCE(ia.invoice_count, 0) = 0
                         AND COALESCE(da.tax_deduction_count, 0) = 0
                         AND COALESCE(ta.source_line_count, 0) = 0
                        THEN '仅项目基础资料，暂无经营事实'
                        ELSE '已承载收款、发票税额、抵扣登记、公司财务收支、扣款实缴/退回和费用支出'
                    END AS coverage_note
                FROM project_project p
                LEFT JOIN res_company rc ON rc.id = p.company_id
                LEFT JOIN settlement_agg sa ON sa.project_id = p.id
                LEFT JOIN receipt_agg ra ON ra.project_id = p.id
                LEFT JOIN invoice_agg ia ON ia.project_id = p.id
                LEFT JOIN deduction_agg da ON da.project_id = p.id
                LEFT JOIN account_tx_agg ta ON ta.project_id = p.id
                LEFT JOIN claim_agg ca ON ca.project_id = p.id
                LEFT JOIN overpay_risk rk ON rk.project_id = p.id
            )
            """
        )
