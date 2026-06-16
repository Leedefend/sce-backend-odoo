# -*- coding: utf-8 -*-
import calendar

from odoo import fields, models, tools


class ProjectProfitCompare(models.Model):
    """Project-level profit summary aggregating revenue and cost by period/structure."""

    _name = "project.profit.compare"
    _description = "项目经营利润对比"
    _auto = False
    _rec_name = "project_id"
    _order = "project_id, period, wbs_id"
    _sc_readonly_navigation_button_methods = {
        "action_open_actual_revenue_lines",
        "action_open_budget_revenue_lines",
        "action_open_actual_cost_ledger",
        "action_open_budget_cost_allocations",
    }

    project_id = fields.Many2one("project.project", string="项目", readonly=True)
    period = fields.Char("期间", readonly=True)
    wbs_id = fields.Many2one("construction.work.breakdown", string="工程结构", readonly=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)

    revenue_budget_amount = fields.Monetary("预算收入", currency_field="currency_id", readonly=True)
    revenue_actual_amount = fields.Monetary("实际收入", currency_field="currency_id", readonly=True)
    cost_budget_amount = fields.Monetary("预算成本", currency_field="currency_id", readonly=True)
    cost_actual_amount = fields.Monetary("实际成本", currency_field="currency_id", readonly=True)

    gross_profit_actual = fields.Monetary(
        "实际毛利", currency_field="currency_id", readonly=True
    )
    gross_profit_budget = fields.Monetary(
        "预算毛利", currency_field="currency_id", readonly=True
    )
    gross_margin_rate = fields.Float(
        "毛利率(%)", readonly=True,
        help="实际毛利 / 实际收入，当实际收入为 0 时显示 0%。",
    )

    def _dimension_domain(self, include_period=True):
        self.ensure_one()
        domain = [("project_id", "=", self.project_id.id)]
        if self.wbs_id:
            domain.append(("wbs_id", "=", self.wbs_id.id))
        if include_period and self.period and self.period != "TOTAL":
            domain.extend(self._period_domain())
        return domain

    def _period_domain(self):
        if not self.period or self.period == "TOTAL":
            return []
        try:
            year, month = (int(part) for part in self.period.split("-", 1))
            last_day = calendar.monthrange(year, month)[1]
        except (TypeError, ValueError):
            return [("period", "=", self.period)]
        return [
            ("date", ">=", "%04d-%02d-01" % (year, month)),
            ("date", "<=", "%04d-%02d-%02d" % (year, month, last_day)),
        ]

    def _action_context(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        context.update(
            {
                "default_project_id": self.project_id.id,
                "search_default_project_id": self.project_id.id,
            }
        )
        if self.wbs_id:
            context.update(
                {
                    "default_wbs_id": self.wbs_id.id,
                    "search_default_wbs_id": self.wbs_id.id,
                }
            )
        return context

    def action_open_actual_cost_ledger(self):
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_project_cost_ledger").sudo().read()[0]
        action.update(
            {
                "name": "实际成本来源 / %s" % (self.project_id.display_name or "项目"),
                "domain": self._dimension_domain(include_period=True),
                "context": self._action_context(),
                "target": "current",
            }
        )
        return action

    def action_open_budget_cost_allocations(self):
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_project_budget_cost_alloc").sudo().read()[0]
        domain = [("project_id", "=", self.project_id.id)]
        if self.wbs_id:
            domain.append(("budget_boq_line_id.wbs_id", "=", self.wbs_id.id))
        action.update(
            {
                "name": "预算成本来源 / %s" % (self.project_id.display_name or "项目"),
                "domain": domain,
                "context": self._action_context(),
                "target": "current",
            }
        )
        return action

    def action_open_budget_revenue_lines(self):
        self.ensure_one()
        domain = self._dimension_domain(include_period=False)
        domain.append(("budget_id.is_active", "=", True))
        return {
            "type": "ir.actions.act_window",
            "name": "预算收入来源 / %s" % (self.project_id.display_name or "项目"),
            "res_model": "project.budget.boq.line",
            "view_mode": "tree,form",
            "domain": domain,
            "context": self._action_context(),
            "target": "current",
        }

    def action_open_actual_revenue_lines(self):
        self.ensure_one()
        domain = self._dimension_domain(include_period=True)
        domain.extend(
            [
                ("move_id.state", "=", "posted"),
                ("move_id.move_type", "in", ["out_invoice", "out_refund"]),
                ("account_id.internal_group", "=", "income"),
            ]
        )
        return {
            "type": "ir.actions.act_window",
            "name": "实际收入来源 / %s" % (self.project_id.display_name or "项目"),
            "res_model": "account.move.line",
            "view_mode": "tree,form",
            "domain": domain,
            "context": self._action_context(),
            "target": "current",
        }

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH cost_actual AS (
                    SELECT
                        project_id,
                        COALESCE(wbs_id, -1) AS wbs_key,
                        COALESCE(to_char(date, 'YYYY-MM'), 'TOTAL') AS period,
                        currency_id,
                        SUM(amount) AS cost_actual_amount
                    FROM project_cost_ledger
                    GROUP BY project_id, COALESCE(wbs_id, -1), COALESCE(to_char(date, 'YYYY-MM'), 'TOTAL'), currency_id
                ),
                cost_budget AS (
                    SELECT
                        alloc.project_id,
                        COALESCE(line.wbs_id, -1) AS wbs_key,
                        'TOTAL' AS period,
                        line.currency_id AS currency_id,
                        SUM(alloc.amount_budget) AS cost_budget_amount
                    FROM project_budget_cost_alloc alloc
                    JOIN project_budget_boq_line line ON alloc.budget_boq_line_id = line.id
                    JOIN project_budget bud ON line.budget_id = bud.id
                    WHERE bud.is_active = TRUE
                    GROUP BY alloc.project_id, COALESCE(line.wbs_id, -1), line.currency_id
                ),
                revenue_budget AS (
                    SELECT
                        line.project_id,
                        COALESCE(line.wbs_id, -1) AS wbs_key,
                        'TOTAL' AS period,
                        line.currency_id,
                        SUM(line.amount_bidded) AS revenue_budget_amount
                    FROM project_budget_boq_line line
                    JOIN project_budget bud ON line.budget_id = bud.id
                    WHERE bud.is_active = TRUE
                    GROUP BY line.project_id, COALESCE(line.wbs_id, -1), line.currency_id
                ),
                revenue_actual AS (
                    SELECT
                        aml.project_id,
                        COALESCE(aml.wbs_id, -1) AS wbs_key,
                        COALESCE(to_char(aml.date, 'YYYY-MM'), 'TOTAL') AS period,
                        COALESCE(aml.currency_id, am.currency_id) AS currency_id,
                        SUM(-aml.balance) AS revenue_actual_amount
                    FROM account_move_line aml
                    JOIN account_move am ON aml.move_id = am.id
                    JOIN account_account acc ON aml.account_id = acc.id
                    WHERE am.state = 'posted'
                      AND am.move_type IN ('out_invoice', 'out_refund')
                      AND aml.project_id IS NOT NULL
                      AND acc.internal_group = 'income'
                    GROUP BY aml.project_id,
                             COALESCE(aml.wbs_id, -1),
                             COALESCE(to_char(aml.date, 'YYYY-MM'), 'TOTAL'),
                             COALESCE(aml.currency_id, am.currency_id)
                )
                SELECT
                    row_number() OVER () AS id,
                    COALESCE(cb.project_id, ca.project_id, rb.project_id, ra.project_id) AS project_id,
                    COALESCE(ca.period, ra.period, cb.period, rb.period) AS period,
                    NULLIF(COALESCE(ca.wbs_key, cb.wbs_key, ra.wbs_key, rb.wbs_key), -1) AS wbs_id,
                    COALESCE(ca.currency_id, cb.currency_id, ra.currency_id, rb.currency_id) AS currency_id,
                    COALESCE(rb.revenue_budget_amount, 0.0) AS revenue_budget_amount,
                    COALESCE(ra.revenue_actual_amount, 0.0) AS revenue_actual_amount,
                    COALESCE(cb.cost_budget_amount, 0.0) AS cost_budget_amount,
                    COALESCE(ca.cost_actual_amount, 0.0) AS cost_actual_amount,
                    COALESCE(ra.revenue_actual_amount, 0.0) - COALESCE(ca.cost_actual_amount, 0.0) AS gross_profit_actual,
                    COALESCE(rb.revenue_budget_amount, 0.0) - COALESCE(cb.cost_budget_amount, 0.0) AS gross_profit_budget,
                    CASE
                        WHEN COALESCE(ra.revenue_actual_amount, 0.0) = 0.0 THEN 0.0
                        ELSE (COALESCE(ra.revenue_actual_amount, 0.0) - COALESCE(ca.cost_actual_amount, 0.0))
                             / COALESCE(ra.revenue_actual_amount, 0.0) * 100.0
                    END AS gross_margin_rate
                FROM cost_actual ca
                FULL OUTER JOIN cost_budget cb
                    ON ca.project_id = cb.project_id
                   AND ca.wbs_key = cb.wbs_key
                   AND ca.currency_id = cb.currency_id
                FULL OUTER JOIN revenue_actual ra
                    ON COALESCE(ca.project_id, cb.project_id) = ra.project_id
                   AND COALESCE(ca.wbs_key, cb.wbs_key) = ra.wbs_key
                   AND ra.currency_id = COALESCE(ca.currency_id, cb.currency_id, ra.currency_id)
                   AND ra.period = COALESCE(ca.period, ra.period)
                FULL OUTER JOIN revenue_budget rb
                    ON COALESCE(ca.project_id, cb.project_id, ra.project_id) = rb.project_id
                   AND COALESCE(ca.wbs_key, cb.wbs_key, ra.wbs_key) = rb.wbs_key
                   AND rb.currency_id = COALESCE(ca.currency_id, cb.currency_id, ra.currency_id, rb.currency_id)
                ORDER BY project_id, period, wbs_id
            )
        """)
