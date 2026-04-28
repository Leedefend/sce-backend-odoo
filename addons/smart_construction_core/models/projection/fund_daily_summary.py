# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScFundDailySummary(models.Model):
    _name = "sc.fund.daily.summary"
    _description = "资金日报汇总"
    _auto = False
    _rec_name = "display_name"
    _order = "document_date desc, project_id, account_name"

    display_name = fields.Char(string="汇总项", readonly=True)
    document_date = fields.Date(string="日期", readonly=True, index=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True)
    account_name = fields.Char(string="账户名称", readonly=True, index=True)
    bank_account_no = fields.Char(string="银行账号", readonly=True)
    line_count = fields.Integer(string="明细数", readonly=True)
    daily_income = fields.Float(string="当日收入", readonly=True)
    daily_expense = fields.Float(string="当日支出", readonly=True)
    net_amount = fields.Float(string="收支净额", readonly=True)
    account_balance = fields.Float(string="账面余额", readonly=True)
    current_account_balance = fields.Float(string="当前账面余额", readonly=True)
    current_bank_balance = fields.Float(string="当前银行余额", readonly=True)
    bank_system_difference = fields.Float(string="账实差异", readonly=True)

    def init(self):
        self._cr.execute("SELECT to_regclass('sc_legacy_fund_daily_line')")
        if not self._cr.fetchone()[0]:
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH normalized_line AS (
                    SELECT
                        l.id,
                        l.document_date,
                        l.project_id,
                        COALESCE(p.name->>'zh_CN', p.name->>'en_US', l.project_name) AS project_name,
                        NULLIF(l.account_name, '') AS account_name,
                        NULLIF(l.bank_account_no, '') AS bank_account_no,
                        l.daily_income,
                        l.daily_expense,
                        l.account_balance,
                        l.current_account_balance,
                        l.current_bank_balance,
                        l.bank_system_difference
                    FROM sc_legacy_fund_daily_line l
                    LEFT JOIN project_project p ON p.id = l.project_id
                    WHERE l.active IS TRUE
                )
                SELECT
                    MIN(n.id) AS id,
                    COALESCE(
                        to_char(n.document_date, 'YYYY-MM-DD') || ' / ' ||
                        COALESCE(n.project_name, '未匹配项目') || ' / ' ||
                        COALESCE(n.account_name, '未填账户'),
                        '资金日报汇总'
                    ) AS display_name,
                    n.document_date AS document_date,
                    n.project_id AS project_id,
                    n.project_name AS project_name,
                    n.account_name AS account_name,
                    n.bank_account_no AS bank_account_no,
                    COUNT(*)::integer AS line_count,
                    COALESCE(SUM(n.daily_income), 0.0) AS daily_income,
                    COALESCE(SUM(n.daily_expense), 0.0) AS daily_expense,
                    COALESCE(SUM(n.daily_income), 0.0) - COALESCE(SUM(n.daily_expense), 0.0) AS net_amount,
                    COALESCE(SUM(n.account_balance), 0.0) AS account_balance,
                    COALESCE(SUM(n.current_account_balance), 0.0) AS current_account_balance,
                    COALESCE(SUM(n.current_bank_balance), 0.0) AS current_bank_balance,
                    COALESCE(SUM(n.bank_system_difference), 0.0) AS bank_system_difference
                FROM normalized_line n
                GROUP BY
                    n.document_date,
                    n.project_id,
                    n.project_name,
                    n.account_name,
                    n.bank_account_no
            )
            """
        )
