# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ScCompanyContractorResponsibilitySummary(models.Model):
    _name = "sc.company.contractor.responsibility.summary"
    _description = "公司-承包人资金责任余额"
    _auto = False
    _rec_name = "display_name"
    _order = "project_id, partner_name"
    _sc_readonly_navigation_button_methods = {
        "action_open_responsibility_facts",
    }

    display_name = fields.Char(string="责任对象", readonly=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    partner_id = fields.Many2one("res.partner", string="承包人", readonly=True, index=True)
    partner_name = fields.Char(string="承包人名称", readonly=True, index=True)
    source_line_count = fields.Integer(string="责任明细数", readonly=True)
    arrival_line_count = fields.Integer(string="到款确认数", readonly=True)
    self_funding_income_line_count = fields.Integer(string="自筹垫付数", readonly=True)
    self_funding_refund_line_count = fields.Integer(string="自筹退回数", readonly=True)
    arrival_amount = fields.Monetary(string="到款金额", currency_field="currency_id", readonly=True)
    paid_amount = fields.Monetary(string="已拨付", currency_field="currency_id", readonly=True)
    deducted_amount = fields.Monetary(string="已扣款", currency_field="currency_id", readonly=True)
    arrival_processed_amount = fields.Monetary(string="到款已处理", currency_field="currency_id", readonly=True)
    arrival_unprocessed_amount = fields.Monetary(string="到款可处理余额", currency_field="currency_id", readonly=True)
    arrival_over_processed_amount = fields.Monetary(string="到款超处理金额", currency_field="currency_id", readonly=True)
    self_funding_income_amount = fields.Monetary(string="自筹垫付", currency_field="currency_id", readonly=True)
    self_funding_refund_amount = fields.Monetary(string="自筹退回", currency_field="currency_id", readonly=True)
    self_funding_balance = fields.Monetary(string="自筹未退余额", currency_field="currency_id", readonly=True)
    project_fund_status_effect = fields.Monetary(string="项目资金状态影响", currency_field="currency_id", readonly=True)
    contractor_responsibility_effect = fields.Monetary(string="承包人责任影响", currency_field="currency_id", readonly=True)
    responsibility_state = fields.Selection(
        [
            ("over_processed", "到款超处理"),
            ("open", "有待处理余额"),
            ("self_funding_open", "自筹未退"),
            ("settled", "已平衡"),
        ],
        string="责任状态",
        readonly=True,
        index=True,
    )
    coverage_note = fields.Char(string="口径说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("公司-承包人资金责任余额是只读汇总，请从到款确认或自筹业务单据维护数据。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def _facts_domain(self):
        self.ensure_one()
        domain = [("project_id", "=", self.project_id.id or False)]
        if self.partner_id:
            domain.append(("partner_id", "=", self.partner_id.id))
        else:
            domain.extend([("partner_id", "=", False), ("partner_name", "=", self.partner_name or False)])
        return domain

    def action_open_responsibility_facts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s / 责任明细" % (self.display_name or "公司-承包人资金责任"),
            "res_model": "sc.company.contractor.responsibility.fact",
            "view_mode": "tree,pivot,form",
            "domain": self._facts_domain(),
            "context": {"search_default_group_responsibility_type": 1},
        }

    def init(self):
        self._cr.execute("SELECT to_regclass('sc_company_contractor_responsibility_fact')")
        if not self._cr.fetchone()[0]:
            return

        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH grouped AS (
                    SELECT
                        project_id,
                        partner_id,
                        partner_name,
                        MIN(company_id) AS company_id,
                        MIN(currency_id) AS currency_id,
                        COUNT(*)::integer AS source_line_count,
                        COUNT(*) FILTER (WHERE responsibility_type = 'arrival_confirmation')::integer AS arrival_line_count,
                        COUNT(*) FILTER (WHERE responsibility_type = 'self_funding_income')::integer AS self_funding_income_line_count,
                        COUNT(*) FILTER (WHERE responsibility_type = 'self_funding_refund')::integer AS self_funding_refund_line_count,
                        COALESCE(SUM(arrival_amount), 0.0) AS arrival_amount,
                        COALESCE(SUM(paid_amount), 0.0) AS paid_amount,
                        COALESCE(SUM(deducted_amount), 0.0) AS deducted_amount,
                        COALESCE(SUM(paid_amount + deducted_amount), 0.0) AS arrival_processed_amount,
                        COALESCE(SUM(arrival_amount - paid_amount - deducted_amount), 0.0) AS arrival_unprocessed_amount,
                        GREATEST(-COALESCE(SUM(arrival_amount - paid_amount - deducted_amount), 0.0), 0.0) AS arrival_over_processed_amount,
                        COALESCE(SUM(self_funding_income_amount), 0.0) AS self_funding_income_amount,
                        COALESCE(SUM(self_funding_refund_amount), 0.0) AS self_funding_refund_amount,
                        COALESCE(SUM(self_funding_balance_effect), 0.0) AS self_funding_balance,
                        COALESCE(SUM(project_fund_status_effect), 0.0) AS project_fund_status_effect,
                        COALESCE(SUM(contractor_responsibility_effect), 0.0) AS contractor_responsibility_effect
                    FROM sc_company_contractor_responsibility_fact
                    GROUP BY project_id, partner_id, partner_name
                )
                SELECT
                    ROW_NUMBER() OVER (
                        ORDER BY g.project_id, COALESCE(g.partner_id, 0), COALESCE(g.partner_name, '')
                    )::integer AS id,
                    COALESCE(p.name->>'zh_CN', p.name->>'en_US', '未关联项目') || ' / ' || COALESCE(NULLIF(g.partner_name, ''), '未识别承包人') AS display_name,
                    g.company_id,
                    g.currency_id,
                    g.project_id,
                    g.partner_id,
                    COALESCE(NULLIF(g.partner_name, ''), '未识别承包人') AS partner_name,
                    g.source_line_count,
                    g.arrival_line_count,
                    g.self_funding_income_line_count,
                    g.self_funding_refund_line_count,
                    g.arrival_amount,
                    g.paid_amount,
                    g.deducted_amount,
                    g.arrival_processed_amount,
                    g.arrival_unprocessed_amount,
                    g.arrival_over_processed_amount,
                    g.self_funding_income_amount,
                    g.self_funding_refund_amount,
                    g.self_funding_balance,
                    g.project_fund_status_effect,
                    g.contractor_responsibility_effect,
                    CASE
                        WHEN g.arrival_unprocessed_amount < -0.01 THEN 'over_processed'
                        WHEN g.arrival_unprocessed_amount > 0.01 THEN 'open'
                        WHEN g.self_funding_balance > 0.01 THEN 'self_funding_open'
                        ELSE 'settled'
                    END AS responsibility_state,
                    '按项目和承包人归集到款确认、自筹垫付和自筹退回；到款可处理余额与自筹未退余额分开用于办理约束' AS coverage_note
                FROM grouped g
                LEFT JOIN project_project p ON p.id = g.project_id
            )
            """
        )
