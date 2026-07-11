# -*- coding: utf-8 -*-
import ast

from odoo import api, fields, models, tools
from odoo.osv import expression
from odoo.exceptions import UserError


class ScFinanceProjectCounterpartyPosition(models.Model):
    _name = "sc.finance.project.counterparty.position"
    _description = "项目与对象资金往来"
    _auto = False
    _rec_name = "display_name"
    _order = "project_id, counterparty_type, counterparty_name"
    _sc_skip_default_list_aggregates = True
    _sc_skip_default_list_total = True
    _sc_readonly_navigation_button_methods = {
        "action_open_finance_facts",
        "action_open_interfund_facts",
        "action_open_company_borrow_entry",
        "action_open_company_repay_entry",
        "action_open_contractor_borrow_entry",
        "action_open_contractor_repay_entry",
        "action_open_account_transfer_entry",
    }

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
    coverage_note = fields.Char(string="口径说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("项目与对象资金往来是只读汇总，请从来源业务单据维护数据。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def _project_domain(self):
        self.ensure_one()
        if self.project_id:
            return [("project_id", "=", self.project_id.id)]
        return [("project_id", "=", False)]

    def _action_domain(self, action_result):
        raw_domain = action_result.get("domain") or []
        if isinstance(raw_domain, str):
            try:
                parsed = ast.literal_eval(raw_domain)
            except (SyntaxError, ValueError):
                parsed = []
            return list(parsed) if isinstance(parsed, list) else []
        return list(raw_domain) if isinstance(raw_domain, list) else []

    def _analysis_note(self, action_name):
        self.ensure_one()
        parts = [
            "办理来源：项目与对象资金往来",
            "办理事项：%s" % action_name,
            "项目：%s" % self.project_id.display_name if self.project_id else False,
            "往来对象：%s" % (self.counterparty_name or self.display_name or ""),
            "对象类型：%s" % (dict(self._fields["counterparty_type"].selection).get(self.counterparty_type) or self.counterparty_type or ""),
            "全部明细数：%s" % self.source_line_count,
            "资金余额影响：%s" % (self.combined_balance_effect or 0.0),
            "现金净额：%s" % (self.combined_cash_net_amount or 0.0),
        ]
        return "\n".join(part for part in parts if part)

    def _action_context(self, action_result, action_name=None):
        raw_context = action_result.get("context") or {}
        if isinstance(raw_context, str):
            try:
                parsed = ast.literal_eval(raw_context)
            except (SyntaxError, ValueError):
                parsed = {}
            context = dict(parsed) if isinstance(parsed, dict) else {}
        else:
            context = dict(raw_context) if isinstance(raw_context, dict) else {}
        if self.project_id:
            context.update(
                {
                    "default_project_id": self.project_id.id,
                    "current_project_id": self.project_id.id,
                }
            )
        if self.partner_id:
            context.update(
                {
                    "default_partner_id": self.partner_id.id,
                    "current_partner_id": self.partner_id.id,
                }
            )
        elif self.counterparty_name and self.counterparty_type == "partner":
            context.update(
                {
                    "default_partner_name": self.counterparty_name,
                    "default_payee": self.counterparty_name,
                }
            )
        if self.counterparty_project_id:
            context["current_counterparty_project_id"] = self.counterparty_project_id.id
        if action_name:
            context.setdefault("default_summary", action_name)
            context.setdefault("default_purpose", action_name)
            context.setdefault("default_operation_reason", action_name)
            context.setdefault("default_note", self._analysis_note(action_name))
        return context

    def _formal_entry_action(self, action_xmlid, action_name):
        self.ensure_one()
        action = self.env.ref(action_xmlid, raise_if_not_found=False)
        if not action:
            raise UserError("正式办理入口不存在，请检查业务菜单配置。")
        result = action.sudo().read()[0]
        domain = self._action_domain(result)
        if self.project_id and result.get("res_model") in {"sc.expense.claim", "sc.financing.loan", "sc.tax.deduction.registration"}:
            domain.append(("project_id", "=", self.project_id.id))
        if self.partner_id and result.get("res_model") in {"sc.expense.claim", "sc.financing.loan", "sc.tax.deduction.registration"}:
            domain.append(("partner_id", "=", self.partner_id.id))
        if result.get("res_model") == "sc.fund.account.operation":
            domain = expression.AND([domain, self._fund_account_operation_domain()])
        result.update(
            {
                "name": "%s / %s" % (self.display_name or "项目与对象资金往来", action_name),
                "domain": domain,
                "context": self._action_context(result, action_name=action_name),
                "target": "current",
            }
        )
        return result

    def _fund_account_operation_domain(self):
        self.ensure_one()
        project_id = self.project_id.id if self.project_id else False
        if not project_id:
            return [("id", "=", 0)]
        if self.counterparty_type == "company":
            return expression.OR(
                [
                    [("source_project_id", "=", project_id), ("target_project_id", "=", False)],
                    [("source_project_id", "=", False), ("target_project_id", "=", project_id)],
                    [("project_id", "=", project_id)],
                ]
            )
        if self.counterparty_type == "project":
            counterparty_project_id = self.counterparty_project_id.id if self.counterparty_project_id else False
            if not counterparty_project_id:
                return [("id", "=", 0)]
            return expression.OR(
                [
                    [("source_project_id", "=", project_id), ("target_project_id", "=", counterparty_project_id)],
                    [("source_project_id", "=", counterparty_project_id), ("target_project_id", "=", project_id)],
                ]
            )
        if self.counterparty_type == "internal":
            return expression.OR(
                [
                    [("source_project_id", "=", project_id), ("target_project_id", "=", project_id)],
                    [("project_id", "=", project_id)],
                ]
            )
        return [("id", "=", 0)]

    def _counterparty_identity_domain(self):
        self.ensure_one()
        if self.counterparty_type == "project":
            return [("counterparty_project_id", "=", self.counterparty_project_id.id or False)]
        if self.counterparty_type == "partner":
            if self.partner_id:
                return [("partner_id", "=", self.partner_id.id)]
            return [("partner_id", "=", False), ("counterparty_name", "=", self.counterparty_name or False)]
        if self.counterparty_type in ("company", "internal", "unknown"):
            return [
                ("counterparty_project_id", "=", False),
                ("partner_id", "=", False),
                ("counterparty_name", "=", self.counterparty_name or False),
            ]
        return [("counterparty_name", "=", self.counterparty_name or False)]

    def _finance_fact_counterparty_domain(self):
        self.ensure_one()
        domain = list(self._project_domain())
        if self.counterparty_type == "partner":
            if self.partner_id:
                domain.append(("partner_id", "=", self.partner_id.id))
            else:
                domain.extend([("partner_id", "=", False), ("partner_name", "=", self.counterparty_name or False)])
        elif self.counterparty_type == "unknown":
            domain.extend([("partner_id", "=", False), ("partner_name", "=", False)])
        else:
            domain.append(("id", "=", 0))
        return domain

    def _interfund_fact_counterparty_domain(self):
        self.ensure_one()
        project_id = self.project_id.id if self.project_id else False
        if not project_id:
            return [("id", "=", 0)]
        if self.counterparty_type == "project":
            counterparty_project_id = self.counterparty_project_id.id if self.counterparty_project_id else False
            return expression.OR(
                [
                    [("target_project_id", "=", project_id), ("source_project_id", "=", counterparty_project_id)],
                    [("source_project_id", "=", project_id), ("target_project_id", "=", counterparty_project_id)],
                ]
            )
        if self.counterparty_type == "company":
            return expression.OR(
                [
                    [
                        ("target_project_id", "=", project_id),
                        ("source_project_id", "=", False),
                        ("partner_id", "=", False),
                        ("partner_name", "in", (False, "")),
                        ("movement_type", "in", ("company_to_project_borrow", "company_to_project_transfer")),
                    ],
                    [
                        ("source_project_id", "=", project_id),
                        ("target_project_id", "=", False),
                        ("partner_id", "=", False),
                        ("partner_name", "in", (False, "")),
                        ("movement_type", "in", ("project_to_company_repay", "project_to_company_transfer")),
                    ],
                ]
            )
        if self.counterparty_type == "partner":
            if not self.partner_id and self.counterparty_name == "未识别承包人":
                return expression.OR(
                    [
                        [
                            ("target_project_id", "=", project_id),
                            ("movement_type", "=", "contractor_to_project_repay"),
                            ("partner_id", "=", False),
                            ("partner_name", "in", (False, "")),
                        ],
                        [
                            ("source_project_id", "=", project_id),
                            ("movement_type", "=", "project_to_contractor_borrow"),
                            ("partner_id", "=", False),
                            ("partner_name", "in", (False, "")),
                        ],
                    ]
                )
            identity_domain = [("partner_id", "=", self.partner_id.id)] if self.partner_id else [("partner_id", "=", False), ("partner_name", "=", self.counterparty_name or False)]
            project_domain = expression.OR(
                [[("target_project_id", "=", project_id)], [("source_project_id", "=", project_id)], [("project_id", "=", project_id)]]
            )
            return expression.AND([project_domain, identity_domain])
        if self.counterparty_type == "internal":
            return expression.AND(
                [
                    [("movement_type", "in", ("same_project_account_transfer", "unclassified_account_transfer"))],
                    expression.OR(
                        [
                            [("source_project_id", "=", project_id)],
                            [("source_project_id", "=", False), ("target_project_id", "=", project_id)],
                            [
                                ("source_project_id", "=", False),
                                ("target_project_id", "=", False),
                                ("project_id", "=", project_id),
                            ],
                        ]
                    ),
                ]
            )
        if self.counterparty_type == "unknown":
            project_domain = expression.OR(
                [[("target_project_id", "=", project_id)], [("source_project_id", "=", project_id)], [("project_id", "=", project_id)]]
            )
            return expression.AND([project_domain, [("partner_id", "=", False), ("partner_name", "=", False)]])
        return [("id", "=", 0)]

    def action_open_finance_facts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "项目收付款来源明细",
            "res_model": "sc.finance.business.fact",
            "view_mode": "tree,pivot,form",
            "domain": self._finance_fact_counterparty_domain(),
            "context": {"search_default_group_business_domain": 1},
        }

    def action_open_interfund_facts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "借款还款与调拨明细",
            "res_model": "sc.interfund.movement.fact",
            "view_mode": "tree,pivot,form",
            "domain": self._interfund_fact_counterparty_domain(),
            "context": {"search_default_group_movement_type": 1},
        }

    def action_open_company_borrow_entry(self):
        return self._formal_entry_action(
            "smart_construction_core.action_sc_financing_loan_project_borrow_company",
            "项目借公司款登记",
        )

    def action_open_company_repay_entry(self):
        return self._formal_entry_action(
            "smart_construction_core.action_sc_expense_claim_project_repay_company",
            "项目还公司款登记",
        )

    def action_open_contractor_borrow_entry(self):
        return self._formal_entry_action(
            "smart_construction_core.action_sc_financing_loan_contractor_project_borrow",
            "承包人借项目款",
        )

    def action_open_contractor_repay_entry(self):
        return self._formal_entry_action(
            "smart_construction_core.action_sc_expense_claim_contractor_project_repay",
            "承包人还项目款",
        )

    def action_open_account_transfer_entry(self):
        return self._formal_entry_action(
            "smart_construction_core.action_sc_fund_account_between_user",
            "账户间资金往来",
        )

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
                    '由项目收付款与借款还款调拨数据按项目和对方对象归集；本页只做分析，不替代业务办理单据' AS coverage_note
                FROM grouped g
                LEFT JOIN project_project p ON p.id = g.project_id
            )
            """
        )
