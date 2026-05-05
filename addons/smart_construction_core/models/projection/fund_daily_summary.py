# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScFundDailySummary(models.Model):
    _name = "sc.fund.daily.summary"
    _description = "企业资金日报汇总"
    _auto = False
    _rec_name = "display_name"
    _order = "document_date desc, business_entity_id"

    display_name = fields.Char(string="汇总项", readonly=True)
    document_date = fields.Date(string="日期", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="隔离公司", readonly=True, index=True)
    business_entity_id = fields.Many2one("sc.business.entity", string="业务核算主体", readonly=True, index=True)
    business_entity_name = fields.Char(string="业务核算主体名称", readonly=True)
    project_id = fields.Many2one("project.project", string="来源项目", readonly=True, index=True)
    project_name = fields.Char(string="来源项目名称", readonly=True)
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
        self._cr.execute("SELECT to_regclass('sc_legacy_fund_daily_snapshot_fact')")
        if not self._cr.fetchone()[0]:
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH normalized_snapshot AS (
                    SELECT
                        s.id,
                        s.snapshot_date AS document_date,
                        s.company_id,
                        s.business_entity_id,
                        be.name AS business_entity_name,
                        s.project_id,
                        COALESCE(p.name->>'zh_CN', p.name->>'en_US', s.legacy_project_name) AS project_name,
                        s.source_account_balance_total,
                        s.source_bank_balance_total,
                        s.source_bank_system_difference
                    FROM sc_legacy_fund_daily_snapshot_fact s
                    LEFT JOIN sc_business_entity be ON be.id = s.business_entity_id
                    LEFT JOIN project_project p ON p.id = s.project_id
                    WHERE s.document_scope = 'enterprise'
                      AND s.business_entity_id IS NOT NULL
                )
                SELECT
                    MIN(n.id) AS id,
                    COALESCE(
                        to_char(n.document_date, 'YYYY-MM-DD') || ' / ' ||
                        COALESCE(n.business_entity_name, '未匹配业务主体'),
                        '企业资金日报汇总'
                    ) AS display_name,
                    n.document_date AS document_date,
                    n.company_id AS company_id,
                    n.business_entity_id AS business_entity_id,
                    n.business_entity_name AS business_entity_name,
                    n.project_id AS project_id,
                    n.project_name AS project_name,
                    NULL::varchar AS account_name,
                    NULL::varchar AS bank_account_no,
                    COUNT(*)::integer AS line_count,
                    0.0::double precision AS daily_income,
                    0.0::double precision AS daily_expense,
                    0.0::double precision AS net_amount,
                    COALESCE(SUM(n.source_account_balance_total), 0.0) AS account_balance,
                    COALESCE(SUM(n.source_account_balance_total), 0.0) AS current_account_balance,
                    COALESCE(SUM(n.source_bank_balance_total), 0.0) AS current_bank_balance,
                    COALESCE(SUM(n.source_bank_system_difference), 0.0) AS bank_system_difference
                FROM normalized_snapshot n
                GROUP BY
                    n.document_date,
                    n.company_id,
                    n.business_entity_id,
                    n.business_entity_name,
                    n.project_id,
                    n.project_name
            )
            """
        )
