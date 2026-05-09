# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScExpenseReimbursementSummary(models.Model):
    _name = "sc.expense.reimbursement.summary"
    _description = "报销统计"
    _auto = False
    _rec_name = "display_name"
    _order = "project_id, expense_type, applicant_name"

    display_name = fields.Char(string="汇总项", readonly=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", readonly=True, index=True)
    applicant_name = fields.Char(string="申请人", readonly=True, index=True)
    expense_type = fields.Char(string="费用类型", readonly=True, index=True)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        readonly=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submit", "已提交"),
            ("approved", "已批准"),
            ("done", "已完成"),
            ("legacy_confirmed", "历史已确认"),
            ("cancel", "已取消"),
        ],
        string="状态",
        readonly=True,
        index=True,
    )
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    amount = fields.Monetary(string="申请金额", currency_field="currency_id", readonly=True)
    approved_amount = fields.Monetary(string="批准金额", currency_field="currency_id", readonly=True)
    claim_count = fields.Integer(string="报销单数", readonly=True)
    legacy_count = fields.Integer(string="历史报销数", readonly=True)
    manual_count = fields.Integer(string="新系统报销数", readonly=True)
    first_date = fields.Date(string="最早日期", readonly=True)
    last_date = fields.Date(string="最晚日期", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def init(self):
        self._cr.execute(
            "SELECT to_regclass('sc_expense_claim'), to_regclass('project_project'), to_regclass('res_company')"
        )
        claim_table, project_table, company_table = self._cr.fetchone()
        if not (claim_table and project_table and company_table):
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    row_number() OVER (
                        ORDER BY c.project_id NULLS LAST, c.expense_type, c.applicant_name, c.source_origin, c.state
                    )::integer AS id,
                    CONCAT_WS(
                        ' / ',
                        COALESCE(p.name->>'zh_CN', p.name->>'en_US', '未匹配项目'),
                        COALESCE(NULLIF(c.expense_type, ''), '未填写费用类型'),
                        COALESCE(NULLIF(c.applicant_name, ''), '未填写申请人'),
                        CASE c.source_origin WHEN 'legacy' THEN '历史迁移' ELSE '新系统登记' END
                    ) AS display_name,
                    c.company_id,
                    c.project_id,
                    c.partner_id,
                    COALESCE(NULLIF(c.applicant_name, ''), '未填写申请人') AS applicant_name,
                    COALESCE(NULLIF(c.expense_type, ''), '未填写费用类型') AS expense_type,
                    c.source_origin,
                    c.state,
                    COALESCE(c.currency_id, rc.currency_id, (SELECT currency_id FROM res_company ORDER BY id LIMIT 1))
                        AS currency_id,
                    COALESCE(SUM(c.amount), 0.0) AS amount,
                    COALESCE(SUM(c.approved_amount), 0.0) AS approved_amount,
                    COUNT(*)::integer AS claim_count,
                    COUNT(*) FILTER (WHERE c.source_origin = 'legacy')::integer AS legacy_count,
                    COUNT(*) FILTER (WHERE c.source_origin = 'manual')::integer AS manual_count,
                    MIN(c.date_claim) AS first_date,
                    MAX(c.date_claim) AS last_date,
                    '按项目、费用类型、申请人、来源和状态汇总费用报销事实' AS coverage_note
                FROM sc_expense_claim c
                LEFT JOIN project_project p ON p.id = c.project_id
                LEFT JOIN res_company rc ON rc.id = c.company_id
                WHERE c.active IS TRUE
                  AND c.claim_type = 'expense'
                  AND c.state <> 'cancel'
                GROUP BY
                    c.company_id,
                    c.project_id,
                    c.partner_id,
                    c.applicant_name,
                    c.expense_type,
                    c.source_origin,
                    c.state,
                    c.currency_id,
                    rc.currency_id,
                    p.name->>'zh_CN',
                    p.name->>'en_US'
            )
            """
        )
