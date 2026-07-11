# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.osv import expression
from odoo.exceptions import UserError


class ScFinanceCounterpartyPositionSummary(models.Model):
    _name = "sc.finance.counterparty.position.summary"
    _description = "往来对象资金总览"
    _auto = False
    _rec_name = "display_name"
    _order = "counterparty_type, counterparty_name"
    _sc_skip_default_list_aggregates = True
    _sc_skip_default_list_total = True
    _sc_readonly_navigation_button_methods = {
        "action_open_project_positions",
        "action_open_finance_facts",
        "action_open_interfund_facts",
    }

    display_name = fields.Char(string="往来对象", readonly=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    counterparty_type = fields.Selection(
        [
            ("company", "公司"),
            ("project", "项目"),
            ("partner", "往来单位/人员"),
            ("internal", "项目内部"),
            ("unknown", "未识别对象"),
        ],
        string="往来对象类型",
        readonly=True,
        index=True,
    )
    counterparty_project_id = fields.Many2one("project.project", string="对方项目", readonly=True, index=True)
    partner_id = fields.Many2one("res.partner", string="对方单位/人员", readonly=True, index=True)
    counterparty_name = fields.Char(string="对方名称", readonly=True, index=True)
    project_count = fields.Integer(string="涉及项目数", readonly=True)
    finance_source_line_count = fields.Integer(string="收付款明细数", readonly=True)
    interfund_source_line_count = fields.Integer(string="借还调拨明细数", readonly=True)
    source_line_count = fields.Integer(string="全部明细数", readonly=True)
    finance_balance_effect = fields.Monetary(string="收付款余额影响", currency_field="currency_id", readonly=True)
    finance_cash_in_amount = fields.Monetary(string="收付款现金流入", currency_field="currency_id", readonly=True)
    finance_cash_out_amount = fields.Monetary(string="收付款现金流出", currency_field="currency_id", readonly=True)
    finance_cash_net_amount = fields.Monetary(string="收付款现金净额", currency_field="currency_id", readonly=True)
    interfund_inflow_amount = fields.Monetary(string="借还调拨流入", currency_field="currency_id", readonly=True)
    interfund_outflow_amount = fields.Monetary(string="借还调拨流出", currency_field="currency_id", readonly=True)
    interfund_net_amount = fields.Monetary(string="借还调拨净流入", currency_field="currency_id", readonly=True)
    internal_transfer_amount = fields.Monetary(string="账户调拨", currency_field="currency_id", readonly=True)
    combined_balance_effect = fields.Monetary(string="资金余额影响", currency_field="currency_id", readonly=True)
    combined_cash_net_amount = fields.Monetary(string="现金净额", currency_field="currency_id", readonly=True)
    position_direction = fields.Selection(
        [
            ("positive", "正向余额"),
            ("negative", "负向余额"),
            ("balanced", "已平衡"),
        ],
        string="余额方向",
        readonly=True,
        index=True,
    )
    coverage_note = fields.Char(string="口径说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("往来对象资金总览是只读汇总，请从来源业务单据维护数据。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def _counterparty_identity_domain(self):
        self.ensure_one()
        domain = [("counterparty_type", "=", self.counterparty_type)]
        if self.counterparty_type == "project":
            domain.append(("counterparty_project_id", "=", self.counterparty_project_id.id or False))
        elif self.counterparty_type == "partner":
            if self.partner_id:
                domain.append(("partner_id", "=", self.partner_id.id))
            else:
                domain.extend([("partner_id", "=", False), ("counterparty_name", "=", self.counterparty_name or False)])
        else:
            domain.extend(
                [
                    ("counterparty_project_id", "=", False),
                    ("partner_id", "=", False),
                    ("counterparty_name", "=", self.counterparty_name or False),
                ]
            )
        return domain

    def action_open_project_positions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "项目与对象资金往来",
            "res_model": "sc.finance.project.counterparty.position",
            "view_mode": "tree,pivot,form",
            "domain": self._counterparty_identity_domain(),
            "context": {"search_default_group_project": 1},
        }

    def _finance_fact_counterparty_domain(self):
        self.ensure_one()
        if self.counterparty_type == "partner":
            if self.partner_id:
                return [("partner_id", "=", self.partner_id.id)]
            return [("partner_id", "=", False), ("partner_name", "=", self.counterparty_name or False)]
        if self.counterparty_type == "unknown":
            return [("partner_id", "=", False), ("partner_name", "=", False)]
        return [("id", "=", 0)]

    def _interfund_fact_counterparty_domain(self):
        self.ensure_one()
        if self.counterparty_type == "project":
            counterparty_project_id = self.counterparty_project_id.id if self.counterparty_project_id else False
            if not counterparty_project_id:
                return [("id", "=", 0)]
            return expression.OR(
                [
                    [("source_project_id", "=", counterparty_project_id)],
                    [("target_project_id", "=", counterparty_project_id)],
                ]
            )
        if self.counterparty_type == "company":
            return [
                ("movement_type", "in", ("company_to_project_borrow", "company_to_project_transfer", "project_to_company_repay", "project_to_company_transfer")),
                ("partner_id", "=", False),
                ("partner_name", "in", (False, "")),
            ]
        if self.counterparty_type == "partner":
            if not self.partner_id and self.counterparty_name == "未识别承包人":
                return [
                    ("movement_type", "in", ("contractor_to_project_repay", "project_to_contractor_borrow")),
                    ("partner_id", "=", False),
                    ("partner_name", "in", (False, "")),
                ]
            if self.partner_id:
                return [("partner_id", "=", self.partner_id.id)]
            return [("partner_id", "=", False), ("partner_name", "=", self.counterparty_name or False)]
        if self.counterparty_type == "internal":
            return [("movement_type", "in", ("same_project_account_transfer", "unclassified_account_transfer"))]
        if self.counterparty_type == "unknown":
            return [("partner_id", "=", False), ("partner_name", "=", False)]
        return [("id", "=", 0)]

    def action_open_finance_facts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s / 收付款来源明细" % (self.display_name or "往来对象"),
            "res_model": "sc.finance.business.fact",
            "view_mode": "tree,pivot,form",
            "domain": self._finance_fact_counterparty_domain(),
            "context": {"search_default_group_project": 1, "search_default_group_business_domain": 1},
        }

    def action_open_interfund_facts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s / 借款还款与调拨明细" % (self.display_name or "往来对象"),
            "res_model": "sc.interfund.movement.fact",
            "view_mode": "tree,pivot,form",
            "domain": self._interfund_fact_counterparty_domain(),
            "context": {"search_default_group_project": 1, "search_default_group_movement_type": 1},
        }

    def init(self):
        self._cr.execute("SELECT to_regclass('sc_finance_project_counterparty_position')")
        if not self._cr.fetchone()[0]:
            return

        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH grouped AS (
                    SELECT
                        counterparty_type,
                        counterparty_project_id,
                        partner_id,
                        counterparty_name,
                        MIN(company_id) AS company_id,
                        MIN(currency_id) AS currency_id,
                        COUNT(DISTINCT COALESCE(project_id, 0))::integer AS project_count,
                        COALESCE(SUM(finance_source_line_count), 0)::integer AS finance_source_line_count,
                        COALESCE(SUM(interfund_source_line_count), 0)::integer AS interfund_source_line_count,
                        COALESCE(SUM(source_line_count), 0)::integer AS source_line_count,
                        COALESCE(SUM(finance_balance_effect), 0.0) AS finance_balance_effect,
                        COALESCE(SUM(finance_cash_in_amount), 0.0) AS finance_cash_in_amount,
                        COALESCE(SUM(finance_cash_out_amount), 0.0) AS finance_cash_out_amount,
                        COALESCE(SUM(finance_cash_net_amount), 0.0) AS finance_cash_net_amount,
                        COALESCE(SUM(interfund_inflow_amount), 0.0) AS interfund_inflow_amount,
                        COALESCE(SUM(interfund_outflow_amount), 0.0) AS interfund_outflow_amount,
                        COALESCE(SUM(interfund_net_amount), 0.0) AS interfund_net_amount,
                        COALESCE(SUM(internal_transfer_amount), 0.0) AS internal_transfer_amount,
                        COALESCE(SUM(combined_balance_effect), 0.0) AS combined_balance_effect,
                        COALESCE(SUM(combined_cash_net_amount), 0.0) AS combined_cash_net_amount
                    FROM sc_finance_project_counterparty_position
                    GROUP BY counterparty_type, counterparty_project_id, partner_id, counterparty_name
                )
                SELECT
                    ROW_NUMBER() OVER (
                        ORDER BY counterparty_type, COALESCE(counterparty_project_id, 0), COALESCE(partner_id, 0), counterparty_name
                    )::integer AS id,
                    counterparty_name AS display_name,
                    company_id,
                    currency_id,
                    counterparty_type,
                    counterparty_project_id,
                    partner_id,
                    counterparty_name,
                    project_count,
                    finance_source_line_count,
                    interfund_source_line_count,
                    source_line_count,
                    finance_balance_effect,
                    finance_cash_in_amount,
                    finance_cash_out_amount,
                    finance_cash_net_amount,
                    interfund_inflow_amount,
                    interfund_outflow_amount,
                    interfund_net_amount,
                    internal_transfer_amount,
                    combined_balance_effect,
                    combined_cash_net_amount,
                    CASE
                        WHEN combined_balance_effect > 0.005 THEN 'positive'
                        WHEN combined_balance_effect < -0.005 THEN 'negative'
                        ELSE 'balanced'
                    END AS position_direction,
                    '由项目与对象资金往来跨项目归集；用于对象层面总余额判断，不替代来源业务单据' AS coverage_note
                FROM grouped
            )
            """
        )
