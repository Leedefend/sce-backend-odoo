# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScAccountIncomeExpenseSummary(models.Model):
    _name = "sc.account.income.expense.summary"
    _description = "账户收支统计表"
    _auto = False
    _rec_name = "display_name"
    _order = "account_type, sort_key, account_name"

    display_name = fields.Char(string="统计项", readonly=True)
    row_level = fields.Selection(
        [("type", "账户类型"), ("account", "账户")],
        string="行级别",
        readonly=True,
        index=True,
    )
    parent_key = fields.Char(string="上级分类", readonly=True, index=True)
    account_type = fields.Char(string="账户类型", readonly=True, index=True)
    account_id = fields.Many2one("sc.legacy.account.master", string="账户", readonly=True, index=True)
    legacy_account_id = fields.Char(string="账户原编号", readonly=True, index=True)
    account_name = fields.Char(string="账户名称", readonly=True, index=True)
    account_no = fields.Char(string="账号", readonly=True, index=True)
    bank_name = fields.Char(string="开户行", readonly=True, index=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True, index=True)
    opening_balance = fields.Float(string="期初余额", readonly=True)
    income_amount = fields.Float(string="收入金额", readonly=True)
    expense_amount = fields.Float(string="支出金额", readonly=True)
    cumulative_receipt_amount = fields.Float(
        string="累计收款",
        readonly=True,
        help="第一版使用已承载资金日报收入合计作为可用累计收款口径。",
    )
    cumulative_expense_amount = fields.Float(
        string="累计支出",
        readonly=True,
        help="第一版使用已承载资金日报支出合计作为可用累计支出口径。",
    )
    account_transfer_amount = fields.Float(string="账户往来", readonly=True)
    current_account_balance = fields.Float(string="当前账户余额", readonly=True)
    current_bank_balance = fields.Float(string="当前银行余额", readonly=True)
    bank_system_difference = fields.Float(string="账实差异", readonly=True)
    line_count = fields.Integer(string="明细数", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)
    sort_key = fields.Char(string="排序键", readonly=True)

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('sc_legacy_account_master'),
                to_regclass('sc_legacy_fund_daily_line'),
                to_regclass('sc_legacy_account_transaction_line')
            """
        )
        account_table, fund_daily_table, transaction_table = self._cr.fetchone()
        if not account_table or not fund_daily_table or not transaction_table:
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH base_account AS (
                    SELECT
                        a.id,
                        a.legacy_account_id,
                        NULLIF(a.name, '') AS account_name,
                        NULLIF(a.account_no, '') AS account_no,
                        COALESCE(NULLIF(a.account_type, ''), '未分类账户') AS account_type,
                        a.bank_name,
                        a.project_id,
                        a.project_name,
                        COALESCE(a.opening_balance, 0.0) AS opening_balance,
                        a.sort_no
                    FROM sc_legacy_account_master a
                    WHERE a.active IS TRUE
                      AND COALESCE(a.fixed_account, FALSE) IS FALSE
                ),
                normalized_line AS (
                    SELECT
                        l.id,
                        l.document_date,
                        l.project_id,
                        l.project_name,
                        NULLIF(l.account_legacy_id, '') AS account_legacy_id,
                        NULLIF(l.account_name, '') AS account_name,
                        NULLIF(l.bank_account_no, '') AS bank_account_no,
                        COALESCE(l.daily_income, 0.0) AS daily_income,
                        COALESCE(l.daily_expense, 0.0) AS daily_expense,
                        l.current_account_balance,
                        l.current_bank_balance,
                        l.bank_system_difference
                    FROM sc_legacy_fund_daily_line l
                    WHERE l.active IS TRUE
                ),
                line_match AS (
                    SELECT
                        l.*,
                        COALESCE(
                            (
                                SELECT a.id
                                FROM base_account a
                                WHERE a.legacy_account_id = l.account_legacy_id
                                ORDER BY a.id
                                LIMIT 1
                            ),
                            (
                                SELECT a.id
                                FROM base_account a
                                WHERE a.account_no = l.bank_account_no
                                ORDER BY a.id
                                LIMIT 1
                            ),
                            (
                                SELECT a.id
                                FROM base_account a
                                WHERE lower(trim(a.account_name)) = lower(trim(l.account_name))
                                ORDER BY a.id
                                LIMIT 1
                            )
                        ) AS account_id
                    FROM normalized_line l
                ),
                line_by_account AS (
                    SELECT
                        m.account_id,
                        COUNT(*)::integer AS line_count,
                        COALESCE(SUM(m.daily_income), 0.0) AS income_amount,
                        COALESCE(SUM(m.daily_expense), 0.0) AS expense_amount
                    FROM line_match m
                    WHERE m.account_id IS NOT NULL
                    GROUP BY m.account_id
                ),
                transaction_by_account AS (
                    SELECT
                        t.account_id,
                        COALESCE(SUM(CASE WHEN t.metric_bucket = 'account_transfer' AND t.direction = 'income' THEN t.amount ELSE 0 END), 0.0) AS transfer_income,
                        COALESCE(SUM(CASE WHEN t.metric_bucket = 'account_transfer' AND t.direction = 'expense' THEN t.amount ELSE 0 END), 0.0) AS transfer_expense,
                        COALESCE(SUM(CASE WHEN t.metric_bucket = 'cumulative' AND t.direction = 'income' THEN t.amount ELSE 0 END), 0.0) AS cumulative_income,
                        COALESCE(SUM(CASE WHEN t.metric_bucket = 'cumulative' AND t.direction = 'expense' THEN t.amount ELSE 0 END), 0.0) AS cumulative_expense,
                        COUNT(*)::integer AS transaction_line_count
                    FROM sc_legacy_account_transaction_line t
                    WHERE t.active IS TRUE
                      AND t.account_id IS NOT NULL
                    GROUP BY t.account_id
                ),
                latest_balance AS (
                    SELECT DISTINCT ON (m.account_id)
                        m.account_id,
                        m.current_account_balance,
                        m.current_bank_balance,
                        m.bank_system_difference
                    FROM line_match m
                    WHERE m.account_id IS NOT NULL
                    ORDER BY m.account_id, m.document_date DESC NULLS LAST, m.id DESC
                ),
                account_rows AS (
                    SELECT
                        a.id AS id,
                        COALESCE(a.account_type, '未分类账户') || ' / ' || COALESCE(a.account_name, a.legacy_account_id) AS display_name,
                        'account'::varchar AS row_level,
                        COALESCE(a.account_type, '未分类账户') AS parent_key,
                        COALESCE(a.account_type, '未分类账户') AS account_type,
                        a.id AS account_id,
                        a.legacy_account_id,
                        a.account_name,
                        a.account_no,
                        a.bank_name,
                        a.project_id,
                        a.project_name,
                        a.opening_balance,
                        COALESCE(t.transfer_income, 0.0) AS income_amount,
                        COALESCE(t.transfer_expense, 0.0) AS expense_amount,
                        COALESCE(t.cumulative_income, l.income_amount, 0.0) AS cumulative_receipt_amount,
                        COALESCE(t.cumulative_expense, l.expense_amount, 0.0) AS cumulative_expense_amount,
                        COALESCE(t.transfer_income, 0.0) - COALESCE(t.transfer_expense, 0.0) AS account_transfer_amount,
                        COALESCE(
                            b.current_account_balance,
                            a.opening_balance
                                + COALESCE(t.transfer_income, 0.0)
                                - COALESCE(t.transfer_expense, 0.0)
                                + COALESCE(t.cumulative_income, l.income_amount, 0.0)
                                - COALESCE(t.cumulative_expense, l.expense_amount, 0.0)
                        ) AS current_account_balance,
                        COALESCE(b.current_bank_balance, 0.0) AS current_bank_balance,
                        COALESCE(b.bank_system_difference, 0.0) AS bank_system_difference,
                        (COALESCE(l.line_count, 0) + COALESCE(t.transaction_line_count, 0))::integer AS line_count,
                        CASE
                            WHEN COALESCE(t.transaction_line_count, 0) > 0 AND COALESCE(l.line_count, 0) > 0 THEN '账户主数据 + 账户往来 + 资金日报明细'
                            WHEN COALESCE(t.transaction_line_count, 0) > 0 THEN '账户主数据 + 账户往来'
                            WHEN COALESCE(l.line_count, 0) > 0 THEN '账户主数据 + 资金日报明细'
                            ELSE '仅账户主数据'
                        END AS coverage_note,
                        COALESCE(a.account_type, '未分类账户') || '/' || COALESCE(a.sort_no, '') || '/' || COALESCE(a.account_name, '') AS sort_key
                    FROM base_account a
                    LEFT JOIN line_by_account l ON l.account_id = a.id
                    LEFT JOIN transaction_by_account t ON t.account_id = a.id
                    LEFT JOIN latest_balance b ON b.account_id = a.id
                ),
                type_rows AS (
                    SELECT
                        900000000 + row_number() OVER (ORDER BY r.account_type)::integer AS id,
                        r.account_type AS display_name,
                        'type'::varchar AS row_level,
                        NULL::varchar AS parent_key,
                        r.account_type,
                        NULL::integer AS account_id,
                        NULL::varchar AS legacy_account_id,
                        NULL::varchar AS account_name,
                        NULL::varchar AS account_no,
                        NULL::varchar AS bank_name,
                        NULL::integer AS project_id,
                        NULL::varchar AS project_name,
                        COALESCE(SUM(r.opening_balance), 0.0) AS opening_balance,
                        COALESCE(SUM(r.income_amount), 0.0) AS income_amount,
                        COALESCE(SUM(r.expense_amount), 0.0) AS expense_amount,
                        COALESCE(SUM(r.cumulative_receipt_amount), 0.0) AS cumulative_receipt_amount,
                        COALESCE(SUM(r.cumulative_expense_amount), 0.0) AS cumulative_expense_amount,
                        COALESCE(SUM(r.account_transfer_amount), 0.0) AS account_transfer_amount,
                        COALESCE(SUM(r.current_account_balance), 0.0) AS current_account_balance,
                        COALESCE(SUM(r.current_bank_balance), 0.0) AS current_bank_balance,
                        COALESCE(SUM(r.bank_system_difference), 0.0) AS bank_system_difference,
                        COALESCE(SUM(r.line_count), 0)::integer AS line_count,
                        '账户类型汇总' AS coverage_note,
                        r.account_type AS sort_key
                    FROM account_rows r
                    GROUP BY r.account_type
                )
                SELECT * FROM type_rows
                UNION ALL
                SELECT * FROM account_rows
            )
            """
        )
