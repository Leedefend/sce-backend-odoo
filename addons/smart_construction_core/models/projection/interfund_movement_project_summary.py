# -*- coding: utf-8 -*-
import ast

from odoo import api, fields, models, tools
from odoo.osv import expression
from odoo.exceptions import UserError


class ScInterfundMovementProjectSummary(models.Model):
    _name = "sc.interfund.movement.project.summary"
    _description = "项目借还调拨汇总"
    _auto = False
    _rec_name = "display_name"
    _order = "project_id, movement_type"
    _sc_readonly_navigation_button_methods = {
        "action_open_interfund_facts",
        "action_open_business_entry",
    }

    _BUSINESS_ENTRY_ACTION_BY_MOVEMENT_TYPE = {
        "company_to_project_borrow": "smart_construction_core.action_sc_financing_loan_project_borrow_company",
        "project_to_company_repay": "smart_construction_core.action_sc_expense_claim_project_repay_company",
        "project_to_project_transfer": "smart_construction_core.action_sc_fund_account_between_user",
        "same_project_account_transfer": "smart_construction_core.action_sc_fund_account_between_user",
        "project_to_contractor_borrow": "smart_construction_core.action_sc_financing_loan_contractor_project_borrow",
        "contractor_to_project_repay": "smart_construction_core.action_sc_expense_claim_contractor_project_repay",
        "project_to_company_transfer": "smart_construction_core.action_sc_fund_account_between_user",
        "company_to_project_transfer": "smart_construction_core.action_sc_fund_account_between_user",
        "unclassified_account_transfer": "smart_construction_core.action_sc_fund_account_between_user",
    }

    display_name = fields.Char(string="汇总项", readonly=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    movement_type = fields.Selection(
        [
            ("company_to_project_borrow", "公司借款给项目"),
            ("project_to_company_repay", "项目归还公司款"),
            ("project_to_project_transfer", "项目间账户调拨"),
            ("same_project_account_transfer", "同项目账户调拨"),
            ("project_to_contractor_borrow", "项目借款给承包人"),
            ("contractor_to_project_repay", "承包人归还项目款"),
            ("project_to_company_transfer", "项目账户转公司账户"),
            ("company_to_project_transfer", "公司账户转项目账户"),
            ("unclassified_account_transfer", "未完全分类账户调拨"),
        ],
        string="业务类型",
        readonly=True,
        index=True,
    )
    source_line_count = fields.Integer(string="来源明细数", readonly=True)
    low_confidence_count = fields.Integer(string="低置信度明细数", readonly=True)
    inflow_amount = fields.Monetary(string="项目流入", currency_field="currency_id", readonly=True)
    outflow_amount = fields.Monetary(string="项目流出", currency_field="currency_id", readonly=True)
    net_amount = fields.Monetary(string="项目借还调拨净流入", currency_field="currency_id", readonly=True)
    internal_transfer_amount = fields.Monetary(string="账户调拨", currency_field="currency_id", readonly=True)
    company_borrow_in_amount = fields.Monetary(string="公司借款流入", currency_field="currency_id", readonly=True)
    company_repay_out_amount = fields.Monetary(string="归还公司流出", currency_field="currency_id", readonly=True)
    project_transfer_in_amount = fields.Monetary(string="项目间调入", currency_field="currency_id", readonly=True)
    project_transfer_out_amount = fields.Monetary(string="项目间调出", currency_field="currency_id", readonly=True)
    contractor_borrow_out_amount = fields.Monetary(string="承包人借款流出", currency_field="currency_id", readonly=True)
    contractor_repay_in_amount = fields.Monetary(string="承包人还款流入", currency_field="currency_id", readonly=True)
    coverage_note = fields.Char(string="口径说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("项目借还调拨汇总是只读汇总，请从来源业务单据维护数据。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def _project_fact_domain(self):
        self.ensure_one()
        if not self.project_id:
            return [
                ("source_project_id", "=", False),
                ("target_project_id", "=", False),
                ("project_id", "=", False),
            ]
        project_domain = expression.OR(
            [
                [("source_project_id", "=", self.project_id.id)],
                [("target_project_id", "=", self.project_id.id)],
                [("project_id", "=", self.project_id.id)],
            ]
        )
        if self.movement_type:
            return expression.AND([[("movement_type", "=", self.movement_type)], project_domain])
        return project_domain

    def _fund_account_operation_domain(self):
        self.ensure_one()
        if not self.project_id:
            return [
                ("source_project_id", "=", False),
                ("target_project_id", "=", False),
                ("project_id", "=", False),
            ]
        return expression.OR(
            [
                [("source_project_id", "=", self.project_id.id)],
                [("target_project_id", "=", self.project_id.id)],
                [("project_id", "=", self.project_id.id)],
            ]
        )

    def _action_domain(self, action_result):
        raw_domain = action_result.get("domain") or []
        if isinstance(raw_domain, str):
            try:
                parsed = ast.literal_eval(raw_domain)
            except (SyntaxError, ValueError):
                parsed = []
            return list(parsed) if isinstance(parsed, list) else []
        return list(raw_domain) if isinstance(raw_domain, list) else []

    def _action_context(self, action_result, action_name):
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
        context.setdefault("default_summary", action_name)
        context.setdefault("default_purpose", action_name)
        context.setdefault("default_operation_reason", action_name)
        context.setdefault(
            "default_note",
            "\n".join(
                part
                for part in (
                    "办理来源：项目借还调拨汇总",
                    "办理事项：%s" % action_name,
                    "项目：%s" % self.project_id.display_name if self.project_id else False,
                    "来源明细数：%s" % self.source_line_count,
                    "项目流入：%s" % (self.inflow_amount or 0.0),
                    "项目流出：%s" % (self.outflow_amount or 0.0),
                    "项目净流入：%s" % (self.net_amount or 0.0),
                    self.coverage_note,
                )
                if part
            ),
        )
        return context

    def action_open_interfund_facts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s / 借还调拨明细" % (self.display_name or "项目"),
            "res_model": "sc.interfund.movement.fact",
            "view_mode": "tree,pivot,form",
            "domain": self._project_fact_domain(),
            "context": {"search_default_group_movement_type": 1},
        }

    def action_open_business_entry(self):
        self.ensure_one()
        action_xmlid = self._BUSINESS_ENTRY_ACTION_BY_MOVEMENT_TYPE.get(self.movement_type)
        action = self.env.ref(action_xmlid, raise_if_not_found=False) if action_xmlid else None
        if not action:
            return self.action_open_interfund_facts()
        result = action.sudo().read()[0]
        action_name = result.get("name") or self._fields["movement_type"].convert_to_export(self.movement_type, self)
        domain = self._action_domain(result)
        if self.project_id and result.get("res_model") in {"sc.expense.claim", "sc.financing.loan"}:
            domain.append(("project_id", "=", self.project_id.id))
        if result.get("res_model") == "sc.fund.account.operation":
            domain = expression.AND([domain, self._fund_account_operation_domain()])
        result.update(
            {
                "name": "%s / %s" % (self.project_id.display_name if self.project_id else "项目", action_name),
                "domain": domain,
                "context": self._action_context(result, action_name),
                "target": "current",
            }
        )
        return result

    def init(self):
        self._cr.execute("SELECT to_regclass('sc_interfund_movement_fact'), to_regclass('project_project')")
        if not all(self._cr.fetchone()):
            return

        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH project_perspective AS (
                    SELECT
                        f.target_project_id AS project_id,
                        f.movement_type,
                        f.company_id,
                        f.currency_id,
                        f.classification_confidence,
                        f.amount,
                        f.amount AS inflow_amount,
                        0.0 AS outflow_amount,
                        f.amount AS net_amount,
                        0.0 AS internal_transfer_amount
                    FROM sc_interfund_movement_fact f
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
                        f.movement_type,
                        f.company_id,
                        f.currency_id,
                        f.classification_confidence,
                        f.amount,
                        0.0 AS inflow_amount,
                        f.amount AS outflow_amount,
                        -f.amount AS net_amount,
                        0.0 AS internal_transfer_amount
                    FROM sc_interfund_movement_fact f
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
                        f.movement_type,
                        f.company_id,
                        f.currency_id,
                        f.classification_confidence,
                        f.amount,
                        0.0 AS inflow_amount,
                        0.0 AS outflow_amount,
                        0.0 AS net_amount,
                        f.amount AS internal_transfer_amount
                    FROM sc_interfund_movement_fact f
                    WHERE COALESCE(f.source_project_id, f.target_project_id, f.project_id) IS NOT NULL
                      AND f.movement_type IN ('same_project_account_transfer', 'unclassified_account_transfer')
                ),
                grouped AS (
                    SELECT
                        pp.project_id,
                        pp.movement_type,
                        MIN(pp.company_id) AS company_id,
                        MIN(pp.currency_id) AS currency_id,
                        COUNT(*)::integer AS source_line_count,
                        COUNT(*) FILTER (WHERE pp.classification_confidence = 'low')::integer AS low_confidence_count,
                        COALESCE(SUM(pp.inflow_amount), 0.0) AS inflow_amount,
                        COALESCE(SUM(pp.outflow_amount), 0.0) AS outflow_amount,
                        COALESCE(SUM(pp.net_amount), 0.0) AS net_amount,
                        COALESCE(SUM(pp.internal_transfer_amount), 0.0) AS internal_transfer_amount,
                        COALESCE(SUM(CASE WHEN pp.movement_type = 'company_to_project_borrow' THEN pp.inflow_amount ELSE 0 END), 0.0) AS company_borrow_in_amount,
                        COALESCE(SUM(CASE WHEN pp.movement_type = 'project_to_company_repay' THEN pp.outflow_amount ELSE 0 END), 0.0) AS company_repay_out_amount,
                        COALESCE(SUM(CASE WHEN pp.movement_type = 'project_to_project_transfer' THEN pp.inflow_amount ELSE 0 END), 0.0) AS project_transfer_in_amount,
                        COALESCE(SUM(CASE WHEN pp.movement_type = 'project_to_project_transfer' THEN pp.outflow_amount ELSE 0 END), 0.0) AS project_transfer_out_amount,
                        COALESCE(SUM(CASE WHEN pp.movement_type = 'project_to_contractor_borrow' THEN pp.outflow_amount ELSE 0 END), 0.0) AS contractor_borrow_out_amount,
                        COALESCE(SUM(CASE WHEN pp.movement_type = 'contractor_to_project_repay' THEN pp.inflow_amount ELSE 0 END), 0.0) AS contractor_repay_in_amount
                    FROM project_perspective pp
                    GROUP BY pp.project_id, pp.movement_type
                )
                SELECT
                    ROW_NUMBER() OVER (ORDER BY g.project_id, g.movement_type)::integer AS id,
                    COALESCE(p.name->>'zh_CN', p.name->>'en_US', '项目') || ' / ' || g.movement_type AS display_name,
                    g.project_id,
                    g.company_id,
                    g.currency_id,
                    g.movement_type,
                    g.source_line_count,
                    g.low_confidence_count,
                    g.inflow_amount,
                    g.outflow_amount,
                    g.net_amount,
                    g.internal_transfer_amount,
                    g.company_borrow_in_amount,
                    g.company_repay_out_amount,
                    g.project_transfer_in_amount,
                    g.project_transfer_out_amount,
                    g.contractor_borrow_out_amount,
                    g.contractor_repay_in_amount,
                    CASE
                        WHEN g.movement_type = 'project_to_project_transfer' THEN '项目间调拨按来源项目流出、目标项目流入双向归集'
                        WHEN g.movement_type = 'same_project_account_transfer' THEN '同项目账户调拨只计内部调拨，净流入为 0'
                        ELSE '按 sc.interfund.movement.fact 的项目视角归集'
                    END AS coverage_note
                FROM grouped g
                LEFT JOIN project_project p ON p.id = g.project_id
            )
            """
        )
