# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class ProjectCostCompare(models.Model):
    """Readonly SQL view aggregating project budget vs actual cost."""

    _name = "project.cost.compare"
    _description = "项目成本预算 vs 实际"
    _auto = False
    _rec_name = "project_id"
    _order = "project_id, period, wbs_id, cost_code_id"

    project_id = fields.Many2one("project.project", string="项目", readonly=True)
    cost_code_id = fields.Many2one("project.cost.code", string="成本科目", readonly=True)
    wbs_id = fields.Many2one("construction.work.breakdown", string="工程结构(WBS)", readonly=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    period = fields.Char("期间(YYYY-MM)", readonly=True)

    budget_amount = fields.Monetary("预算成本", currency_field="currency_id", readonly=True)
    actual_amount = fields.Monetary("实际成本", currency_field="currency_id", readonly=True)

    diff_amount = fields.Monetary(
        "差额(实际-预算)", currency_field="currency_id",
        readonly=True,
    )
    diff_rate = fields.Float(
        "偏差率(%)", readonly=True,
        help="预算为 0 时偏差率显示为 0。",
    )

    def action_open_ledger(self):
        """Open cost ledger filtered by this record's project and cost code."""
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_project_cost_ledger").read()[0]
        domain = [("project_id", "=", self.project_id.id)]
        if self.cost_code_id:
            domain.append(("cost_code_id", "=", self.cost_code_id.id))
        if self.wbs_id:
            domain.append(("wbs_id", "=", self.wbs_id.id))
        if self.period and self.period != "TOTAL":
            domain.append(("period", "=", self.period))
        action["domain"] = domain
        action["context"] = dict(
            self.env.context,
            search_default_project_id=self.project_id.id,
            search_default_cost_code_id=self.cost_code_id.id if self.cost_code_id else False,
            search_default_wbs_id=self.wbs_id.id if self.wbs_id else False,
            search_default_period=self.period if self.period and self.period != "TOTAL" else False,
            default_project_id=self.project_id.id,
        )
        return action

    def init(self):
        """SQL view combining budget allocations and actual ledger costs."""
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    row_number() OVER () AS id,
                    COALESCE(b.project_id, a.project_id) AS project_id,
                    COALESCE(b.cost_code_id, a.cost_code_id) AS cost_code_id,
                    COALESCE(b.wbs_id, a.wbs_id) AS wbs_id,
                    COALESCE(b.currency_id, a.currency_id) AS currency_id,
                    COALESCE(a.period, 'TOTAL') AS period,
                    COALESCE(b.budget_amount, 0.0) AS budget_amount,
                    COALESCE(a.actual_amount, 0.0) AS actual_amount,
                    COALESCE(a.actual_amount, 0.0) - COALESCE(b.budget_amount, 0.0) AS diff_amount,
                    CASE
                        WHEN COALESCE(b.budget_amount, 0.0) = 0.0 THEN 0.0
                        ELSE (COALESCE(a.actual_amount, 0.0) - COALESCE(b.budget_amount, 0.0))
                             / COALESCE(b.budget_amount, 0.0) * 100.0
                    END AS diff_rate
                FROM (
                    SELECT
                        l.project_id,
                        l.cost_code_id,
                        l.wbs_id,
                        l.currency_id,
                        COALESCE(to_char(l.date, 'YYYY-MM'), 'TOTAL') AS period,
                        SUM(l.amount) AS actual_amount
                    FROM project_cost_ledger l
                    GROUP BY l.project_id, l.cost_code_id, l.wbs_id, l.currency_id, to_char(l.date, 'YYYY-MM')
                ) a
                FULL OUTER JOIN (
                    SELECT
                        alloc.project_id,
                        alloc.cost_code_id,
                        line.wbs_id,
                        bud.currency_id,
                        'TOTAL' AS period,
                        SUM(alloc.amount_budget) AS budget_amount
                    FROM project_budget_cost_alloc alloc
                    JOIN project_budget_boq_line line
                        ON alloc.budget_boq_line_id = line.id
                    JOIN project_budget bud
                        ON line.budget_id = bud.id
                    WHERE bud.is_active = TRUE
                    GROUP BY alloc.project_id, alloc.cost_code_id, line.wbs_id, bud.currency_id
                ) b
                ON  a.project_id = b.project_id
                AND a.cost_code_id = b.cost_code_id
                AND COALESCE(a.wbs_id, 0) = COALESCE(b.wbs_id, 0)
                AND a.currency_id = b.currency_id
                ORDER BY COALESCE(b.project_id, a.project_id),
                         COALESCE(b.period, a.period),
                         COALESCE(b.wbs_id, a.wbs_id),
                         COALESCE(b.cost_code_id, a.cost_code_id)
            )
        """)
