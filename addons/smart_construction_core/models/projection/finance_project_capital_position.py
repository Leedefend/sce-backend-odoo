# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.osv import expression
from odoo.exceptions import UserError


class ScFinanceProjectCapitalPosition(models.Model):
    _name = "sc.finance.project.capital.position"
    _description = "项目资金综合口径"
    _auto = False
    _rec_name = "display_name"
    _order = "project_id"

    display_name = fields.Char(string="项目资金口径", readonly=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    finance_group_count = fields.Integer(string="财务事实分组数", readonly=True)
    interfund_group_count = fields.Integer(string="资金往来分组数", readonly=True)
    finance_source_line_count = fields.Integer(string="财务事实明细数", readonly=True)
    interfund_source_line_count = fields.Integer(string="资金往来明细数", readonly=True)
    source_line_count = fields.Integer(string="综合明细数", readonly=True)

    arrival_amount = fields.Monetary(string="到款金额", currency_field="currency_id", readonly=True)
    arrival_paid_amount = fields.Monetary(string="到款拨付金额", currency_field="currency_id", readonly=True)
    deduction_net_amount = fields.Monetary(string="扣款净额", currency_field="currency_id", readonly=True)
    tax_deduction_amount = fields.Monetary(string="抵扣金额", currency_field="currency_id", readonly=True)
    tax_deduction_tax_amount = fields.Monetary(string="抵扣税额", currency_field="currency_id", readonly=True)
    self_funding_balance = fields.Monetary(string="自筹正式余额", currency_field="currency_id", readonly=True)
    guarantee_outstanding_amount = fields.Monetary(string="保证金在外余额", currency_field="currency_id", readonly=True)
    finance_balance_effect = fields.Monetary(string="财务余额影响", currency_field="currency_id", readonly=True)
    finance_cash_in_amount = fields.Monetary(string="财务现金流入", currency_field="currency_id", readonly=True)
    finance_cash_out_amount = fields.Monetary(string="财务现金流出", currency_field="currency_id", readonly=True)
    finance_cash_net_amount = fields.Monetary(string="财务现金净额", currency_field="currency_id", readonly=True)

    interfund_inflow_amount = fields.Monetary(string="往来项目流入", currency_field="currency_id", readonly=True)
    interfund_outflow_amount = fields.Monetary(string="往来项目流出", currency_field="currency_id", readonly=True)
    interfund_net_amount = fields.Monetary(string="往来项目净流入", currency_field="currency_id", readonly=True)
    internal_transfer_amount = fields.Monetary(string="项目内调拨", currency_field="currency_id", readonly=True)
    company_borrow_in_amount = fields.Monetary(string="公司借款流入", currency_field="currency_id", readonly=True)
    company_repay_out_amount = fields.Monetary(string="归还公司流出", currency_field="currency_id", readonly=True)
    project_transfer_in_amount = fields.Monetary(string="项目间调入", currency_field="currency_id", readonly=True)
    project_transfer_out_amount = fields.Monetary(string="项目间调出", currency_field="currency_id", readonly=True)
    contractor_borrow_out_amount = fields.Monetary(string="承包人借款流出", currency_field="currency_id", readonly=True)
    contractor_repay_in_amount = fields.Monetary(string="承包人还款流入", currency_field="currency_id", readonly=True)

    combined_balance_effect = fields.Monetary(string="综合余额影响", currency_field="currency_id", readonly=True)
    combined_cash_net_amount = fields.Monetary(string="综合现金净额", currency_field="currency_id", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("项目资金综合口径是只读投影，请从来源业务单据维护数据。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def _project_domain(self, field_name):
        self.ensure_one()
        if self.project_id:
            return [(field_name, "=", self.project_id.id)]
        return [(field_name, "=", False)]

    def action_open_finance_facts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "财务业务事实",
            "res_model": "sc.finance.business.fact",
            "view_mode": "tree,pivot,form",
            "domain": self._project_domain("project_id"),
            "context": {"search_default_group_business_domain": 1},
        }

    def action_open_interfund_facts(self):
        self.ensure_one()
        if self.project_id:
            domain = expression.OR(
                [
                    [("source_project_id", "=", self.project_id.id)],
                    [("target_project_id", "=", self.project_id.id)],
                    [("project_id", "=", self.project_id.id)],
                ]
            )
        else:
            domain = [
                ("source_project_id", "=", False),
                ("target_project_id", "=", False),
                ("project_id", "=", False),
            ]
        return {
            "type": "ir.actions.act_window",
            "name": "资金往来事实",
            "res_model": "sc.interfund.movement.fact",
            "view_mode": "tree,pivot,form",
            "domain": domain,
            "context": {"search_default_group_movement_type": 1},
        }

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('sc_finance_business_project_summary'),
                to_regclass('sc_interfund_movement_project_summary'),
                to_regclass('project_project')
            """
        )
        if not all(self._cr.fetchone()):
            return

        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH finance AS (
                    SELECT
                        COALESCE(project_id, 0) AS project_key,
                        project_id,
                        MIN(company_id) AS company_id,
                        MIN(currency_id) AS currency_id,
                        COUNT(*)::integer AS finance_group_count,
                        COALESCE(SUM(source_line_count), 0)::integer AS finance_source_line_count,
                        COALESCE(SUM(arrival_amount), 0.0) AS arrival_amount,
                        COALESCE(SUM(arrival_paid_amount), 0.0) AS arrival_paid_amount,
                        COALESCE(SUM(deduction_net_amount), 0.0) AS deduction_net_amount,
                        COALESCE(SUM(tax_deduction_amount), 0.0) AS tax_deduction_amount,
                        COALESCE(SUM(tax_deduction_tax_amount), 0.0) AS tax_deduction_tax_amount,
                        COALESCE(SUM(self_funding_balance), 0.0) AS self_funding_balance,
                        COALESCE(SUM(guarantee_outstanding_amount), 0.0) AS guarantee_outstanding_amount,
                        COALESCE(SUM(balance_effect), 0.0) AS finance_balance_effect,
                        COALESCE(SUM(cash_in_amount), 0.0) AS finance_cash_in_amount,
                        COALESCE(SUM(cash_out_amount), 0.0) AS finance_cash_out_amount
                    FROM sc_finance_business_project_summary
                    GROUP BY COALESCE(project_id, 0), project_id
                ),
                interfund AS (
                    SELECT
                        COALESCE(project_id, 0) AS project_key,
                        project_id,
                        MIN(company_id) AS company_id,
                        MIN(currency_id) AS currency_id,
                        COUNT(*)::integer AS interfund_group_count,
                        COALESCE(SUM(source_line_count), 0)::integer AS interfund_source_line_count,
                        COALESCE(SUM(inflow_amount), 0.0) AS interfund_inflow_amount,
                        COALESCE(SUM(outflow_amount), 0.0) AS interfund_outflow_amount,
                        COALESCE(SUM(net_amount), 0.0) AS interfund_net_amount,
                        COALESCE(SUM(internal_transfer_amount), 0.0) AS internal_transfer_amount,
                        COALESCE(SUM(company_borrow_in_amount), 0.0) AS company_borrow_in_amount,
                        COALESCE(SUM(company_repay_out_amount), 0.0) AS company_repay_out_amount,
                        COALESCE(SUM(project_transfer_in_amount), 0.0) AS project_transfer_in_amount,
                        COALESCE(SUM(project_transfer_out_amount), 0.0) AS project_transfer_out_amount,
                        COALESCE(SUM(contractor_borrow_out_amount), 0.0) AS contractor_borrow_out_amount,
                        COALESCE(SUM(contractor_repay_in_amount), 0.0) AS contractor_repay_in_amount
                    FROM sc_interfund_movement_project_summary
                    GROUP BY COALESCE(project_id, 0), project_id
                ),
                combined AS (
                    SELECT
                        COALESCE(f.project_key, i.project_key) AS project_key,
                        COALESCE(f.project_id, i.project_id) AS project_id,
                        COALESCE(f.company_id, i.company_id) AS company_id,
                        COALESCE(f.currency_id, i.currency_id) AS currency_id,
                        COALESCE(f.finance_group_count, 0) AS finance_group_count,
                        COALESCE(i.interfund_group_count, 0) AS interfund_group_count,
                        COALESCE(f.finance_source_line_count, 0) AS finance_source_line_count,
                        COALESCE(i.interfund_source_line_count, 0) AS interfund_source_line_count,
                        COALESCE(f.arrival_amount, 0.0) AS arrival_amount,
                        COALESCE(f.arrival_paid_amount, 0.0) AS arrival_paid_amount,
                        COALESCE(f.deduction_net_amount, 0.0) AS deduction_net_amount,
                        COALESCE(f.tax_deduction_amount, 0.0) AS tax_deduction_amount,
                        COALESCE(f.tax_deduction_tax_amount, 0.0) AS tax_deduction_tax_amount,
                        COALESCE(f.self_funding_balance, 0.0) AS self_funding_balance,
                        COALESCE(f.guarantee_outstanding_amount, 0.0) AS guarantee_outstanding_amount,
                        COALESCE(f.finance_balance_effect, 0.0) AS finance_balance_effect,
                        COALESCE(f.finance_cash_in_amount, 0.0) AS finance_cash_in_amount,
                        COALESCE(f.finance_cash_out_amount, 0.0) AS finance_cash_out_amount,
                        COALESCE(i.interfund_inflow_amount, 0.0) AS interfund_inflow_amount,
                        COALESCE(i.interfund_outflow_amount, 0.0) AS interfund_outflow_amount,
                        COALESCE(i.interfund_net_amount, 0.0) AS interfund_net_amount,
                        COALESCE(i.internal_transfer_amount, 0.0) AS internal_transfer_amount,
                        COALESCE(i.company_borrow_in_amount, 0.0) AS company_borrow_in_amount,
                        COALESCE(i.company_repay_out_amount, 0.0) AS company_repay_out_amount,
                        COALESCE(i.project_transfer_in_amount, 0.0) AS project_transfer_in_amount,
                        COALESCE(i.project_transfer_out_amount, 0.0) AS project_transfer_out_amount,
                        COALESCE(i.contractor_borrow_out_amount, 0.0) AS contractor_borrow_out_amount,
                        COALESCE(i.contractor_repay_in_amount, 0.0) AS contractor_repay_in_amount
                    FROM finance f
                    FULL OUTER JOIN interfund i ON i.project_key = f.project_key
                )
                SELECT
                    ROW_NUMBER() OVER (ORDER BY c.project_key)::integer AS id,
                    CASE
                        WHEN c.project_id IS NULL THEN '未关联项目 / 资金综合口径'
                        ELSE COALESCE(p.name->>'zh_CN', p.name->>'en_US', '项目') || ' / 资金综合口径'
                    END AS display_name,
                    c.project_id,
                    c.company_id,
                    c.currency_id,
                    c.finance_group_count,
                    c.interfund_group_count,
                    c.finance_source_line_count,
                    c.interfund_source_line_count,
                    (c.finance_source_line_count + c.interfund_source_line_count)::integer AS source_line_count,
                    c.arrival_amount,
                    c.arrival_paid_amount,
                    c.deduction_net_amount,
                    c.tax_deduction_amount,
                    c.tax_deduction_tax_amount,
                    c.self_funding_balance,
                    c.guarantee_outstanding_amount,
                    c.finance_balance_effect,
                    c.finance_cash_in_amount,
                    c.finance_cash_out_amount,
                    (c.finance_cash_in_amount - c.finance_cash_out_amount) AS finance_cash_net_amount,
                    c.interfund_inflow_amount,
                    c.interfund_outflow_amount,
                    c.interfund_net_amount,
                    c.internal_transfer_amount,
                    c.company_borrow_in_amount,
                    c.company_repay_out_amount,
                    c.project_transfer_in_amount,
                    c.project_transfer_out_amount,
                    c.contractor_borrow_out_amount,
                    c.contractor_repay_in_amount,
                    (c.finance_balance_effect + c.interfund_net_amount) AS combined_balance_effect,
                    ((c.finance_cash_in_amount - c.finance_cash_out_amount) + c.interfund_net_amount) AS combined_cash_net_amount,
                    '由 sc.finance.business.project.summary 与 sc.interfund.movement.project.summary 汇总；不替代来源业务单据' AS coverage_note
                FROM combined c
                LEFT JOIN project_project p ON p.id = c.project_id
            )
            """
        )
