# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ScFinanceProjectCounterpartyPosition(models.Model):
    _name = "sc.finance.project.counterparty.position"
    _description = "项目往来对象资金口径"
    _auto = False
    _rec_name = "display_name"
    _order = "project_id, counterparty_type, counterparty_name"

    display_name = fields.Char(string="往来对象口径", readonly=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
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
    finance_source_line_count = fields.Integer(string="财务事实明细数", readonly=True)
    interfund_source_line_count = fields.Integer(string="资金往来明细数", readonly=True)
    source_line_count = fields.Integer(string="综合明细数", readonly=True)
    finance_balance_effect = fields.Monetary(string="财务余额影响", currency_field="currency_id", readonly=True)
    finance_cash_in_amount = fields.Monetary(string="财务现金流入", currency_field="currency_id", readonly=True)
    finance_cash_out_amount = fields.Monetary(string="财务现金流出", currency_field="currency_id", readonly=True)
    finance_cash_net_amount = fields.Monetary(string="财务现金净额", currency_field="currency_id", readonly=True)
    interfund_inflow_amount = fields.Monetary(string="往来项目流入", currency_field="currency_id", readonly=True)
    interfund_outflow_amount = fields.Monetary(string="往来项目流出", currency_field="currency_id", readonly=True)
    interfund_net_amount = fields.Monetary(string="往来项目净流入", currency_field="currency_id", readonly=True)
    internal_transfer_amount = fields.Monetary(string="项目内调拨", currency_field="currency_id", readonly=True)
    combined_balance_effect = fields.Monetary(string="综合余额影响", currency_field="currency_id", readonly=True)
    combined_cash_net_amount = fields.Monetary(string="综合现金净额", currency_field="currency_id", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("项目往来对象资金口径是只读投影，请从来源业务单据维护数据。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('sc_finance_business_fact'),
                to_regclass('sc_interfund_movement_fact'),
                to_regclass('project_project')
            """
        )
        if not all(self._cr.fetchone()):
            return

        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH project_names AS (
                    SELECT id, COALESCE(name->>'zh_CN', name->>'en_US') AS project_name
                    FROM project_project
                ),
                perspective AS (
                    SELECT
                        f.project_id,
                        f.company_id,
                        f.currency_id,
                        CASE
                            WHEN f.partner_id IS NOT NULL OR NULLIF(f.partner_name, '') IS NOT NULL THEN 'partner'
                            ELSE 'unknown'
                        END AS counterparty_type,
                        NULL::integer AS counterparty_project_id,
                        f.partner_id,
                        COALESCE(NULLIF(f.partner_name, ''), '未识别对象') AS counterparty_name,
                        1 AS finance_source_line_count,
                        0 AS interfund_source_line_count,
                        f.balance_effect AS finance_balance_effect,
                        f.cash_in_amount AS finance_cash_in_amount,
                        f.cash_out_amount AS finance_cash_out_amount,
                        0.0 AS interfund_inflow_amount,
                        0.0 AS interfund_outflow_amount,
                        0.0 AS interfund_net_amount,
                        0.0 AS internal_transfer_amount
                    FROM sc_finance_business_fact f
                    UNION ALL
                    SELECT
                        f.target_project_id AS project_id,
                        f.company_id,
                        f.currency_id,
                        CASE
                            WHEN f.source_project_id IS NOT NULL THEN 'project'
                            WHEN f.partner_id IS NOT NULL OR NULLIF(f.partner_name, '') IS NOT NULL THEN 'partner'
                            WHEN f.movement_type = 'contractor_to_project_repay' THEN 'partner'
                            WHEN f.movement_type IN ('company_to_project_borrow', 'company_to_project_transfer') THEN 'company'
                            ELSE 'unknown'
                        END AS counterparty_type,
                        f.source_project_id AS counterparty_project_id,
                        CASE WHEN f.source_project_id IS NULL THEN f.partner_id ELSE NULL::integer END AS partner_id,
                        COALESCE(
                            sp.project_name,
                            NULLIF(f.partner_name, ''),
                            CASE
                                WHEN f.movement_type = 'contractor_to_project_repay' THEN '未识别承包人'
                                ELSE '公司'
                            END
                        ) AS counterparty_name,
                        0 AS finance_source_line_count,
                        1 AS interfund_source_line_count,
                        0.0 AS finance_balance_effect,
                        0.0 AS finance_cash_in_amount,
                        0.0 AS finance_cash_out_amount,
                        f.amount AS interfund_inflow_amount,
                        0.0 AS interfund_outflow_amount,
                        f.amount AS interfund_net_amount,
                        0.0 AS internal_transfer_amount
                    FROM sc_interfund_movement_fact f
                    LEFT JOIN project_names sp ON sp.id = f.source_project_id
                    WHERE f.target_project_id IS NOT NULL
                      AND f.movement_type IN (
                            'company_to_project_borrow',
                            'company_to_project_transfer',
                            'project_to_project_transfer',
                            'contractor_to_project_repay'
                      )
                    UNION ALL
                    SELECT
                        f.source_project_id AS project_id,
                        f.company_id,
                        f.currency_id,
                        CASE
                            WHEN f.target_project_id IS NOT NULL THEN 'project'
                            WHEN f.partner_id IS NOT NULL OR NULLIF(f.partner_name, '') IS NOT NULL THEN 'partner'
                            WHEN f.movement_type = 'project_to_contractor_borrow' THEN 'partner'
                            WHEN f.movement_type IN ('project_to_company_repay', 'project_to_company_transfer') THEN 'company'
                            ELSE 'unknown'
                        END AS counterparty_type,
                        f.target_project_id AS counterparty_project_id,
                        CASE WHEN f.target_project_id IS NULL THEN f.partner_id ELSE NULL::integer END AS partner_id,
                        COALESCE(
                            tp.project_name,
                            NULLIF(f.partner_name, ''),
                            CASE
                                WHEN f.movement_type = 'project_to_contractor_borrow' THEN '未识别承包人'
                                ELSE '公司'
                            END
                        ) AS counterparty_name,
                        0 AS finance_source_line_count,
                        1 AS interfund_source_line_count,
                        0.0 AS finance_balance_effect,
                        0.0 AS finance_cash_in_amount,
                        0.0 AS finance_cash_out_amount,
                        0.0 AS interfund_inflow_amount,
                        f.amount AS interfund_outflow_amount,
                        -f.amount AS interfund_net_amount,
                        0.0 AS internal_transfer_amount
                    FROM sc_interfund_movement_fact f
                    LEFT JOIN project_names tp ON tp.id = f.target_project_id
                    WHERE f.source_project_id IS NOT NULL
                      AND f.movement_type IN (
                            'project_to_company_repay',
                            'project_to_company_transfer',
                            'project_to_project_transfer',
                            'project_to_contractor_borrow'
                      )
                    UNION ALL
                    SELECT
                        COALESCE(f.source_project_id, f.target_project_id, f.project_id) AS project_id,
                        f.company_id,
                        f.currency_id,
                        'internal' AS counterparty_type,
                        NULL::integer AS counterparty_project_id,
                        NULL::integer AS partner_id,
                        '项目内部账户' AS counterparty_name,
                        0 AS finance_source_line_count,
                        1 AS interfund_source_line_count,
                        0.0 AS finance_balance_effect,
                        0.0 AS finance_cash_in_amount,
                        0.0 AS finance_cash_out_amount,
                        0.0 AS interfund_inflow_amount,
                        0.0 AS interfund_outflow_amount,
                        0.0 AS interfund_net_amount,
                        f.amount AS internal_transfer_amount
                    FROM sc_interfund_movement_fact f
                    WHERE COALESCE(f.source_project_id, f.target_project_id, f.project_id) IS NOT NULL
                      AND f.movement_type IN ('same_project_account_transfer', 'unclassified_account_transfer')
                ),
                grouped AS (
                    SELECT
                        project_id,
                        counterparty_type,
                        counterparty_project_id,
                        partner_id,
                        counterparty_name,
                        MIN(company_id) AS company_id,
                        MIN(currency_id) AS currency_id,
                        COALESCE(SUM(finance_source_line_count), 0)::integer AS finance_source_line_count,
                        COALESCE(SUM(interfund_source_line_count), 0)::integer AS interfund_source_line_count,
                        COALESCE(SUM(finance_balance_effect), 0.0) AS finance_balance_effect,
                        COALESCE(SUM(finance_cash_in_amount), 0.0) AS finance_cash_in_amount,
                        COALESCE(SUM(finance_cash_out_amount), 0.0) AS finance_cash_out_amount,
                        COALESCE(SUM(interfund_inflow_amount), 0.0) AS interfund_inflow_amount,
                        COALESCE(SUM(interfund_outflow_amount), 0.0) AS interfund_outflow_amount,
                        COALESCE(SUM(interfund_net_amount), 0.0) AS interfund_net_amount,
                        COALESCE(SUM(internal_transfer_amount), 0.0) AS internal_transfer_amount
                    FROM perspective
                    GROUP BY project_id, counterparty_type, counterparty_project_id, partner_id, counterparty_name
                )
                SELECT
                    ROW_NUMBER() OVER (
                        ORDER BY g.project_id, g.counterparty_type, COALESCE(g.counterparty_project_id, 0), COALESCE(g.partner_id, 0), g.counterparty_name
                    )::integer AS id,
                    COALESCE(p.name->>'zh_CN', p.name->>'en_US', '未关联项目') || ' / ' || g.counterparty_name AS display_name,
                    g.project_id,
                    g.company_id,
                    g.currency_id,
                    g.counterparty_type,
                    g.counterparty_project_id,
                    g.partner_id,
                    g.counterparty_name,
                    g.finance_source_line_count,
                    g.interfund_source_line_count,
                    (g.finance_source_line_count + g.interfund_source_line_count)::integer AS source_line_count,
                    g.finance_balance_effect,
                    g.finance_cash_in_amount,
                    g.finance_cash_out_amount,
                    (g.finance_cash_in_amount - g.finance_cash_out_amount) AS finance_cash_net_amount,
                    g.interfund_inflow_amount,
                    g.interfund_outflow_amount,
                    g.interfund_net_amount,
                    g.internal_transfer_amount,
                    (g.finance_balance_effect + g.interfund_net_amount) AS combined_balance_effect,
                    ((g.finance_cash_in_amount - g.finance_cash_out_amount) + g.interfund_net_amount) AS combined_cash_net_amount,
                    '由财务事实与资金往来事实按项目及对方对象归集；不替代来源业务单据' AS coverage_note
                FROM grouped g
                LEFT JOIN project_project p ON p.id = g.project_id
            )
            """
        )
