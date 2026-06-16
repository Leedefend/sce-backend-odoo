# -*- coding: utf-8 -*-
import ast

from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ScFinanceBusinessProjectSummary(models.Model):
    _name = "sc.finance.business.project.summary"
    _description = "项目收付款汇总"
    _auto = False
    _rec_name = "display_name"
    _order = "project_id, business_domain"
    _sc_readonly_navigation_button_methods = {
        "action_open_finance_facts",
        "action_open_business_entry",
    }

    _BUSINESS_ENTRY_ACTION_BY_DOMAIN = {
        "deduction_clearing": "smart_construction_core.action_sc_expense_claim_deduction_paid",
        "tax_deduction": "smart_construction_core.action_sc_tax_deduction_registration_user",
        "guarantee_deposit": "smart_construction_core.action_sc_expense_claim_deposit",
    }

    display_name = fields.Char(string="汇总项", readonly=True)
    business_domain = fields.Selection(
        [
            ("arrival_settlement", "到款确认"),
            ("deduction_clearing", "扣款实缴/退回"),
            ("tax_deduction", "抵扣登记"),
            ("self_funding", "自筹收入/退回"),
            ("guarantee_deposit", "保证金收退"),
        ],
        string="收付款类型",
        readonly=True,
        index=True,
    )
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    source_line_count = fields.Integer(string="来源明细数", readonly=True)
    canonical_line_count = fields.Integer(string="正式余额明细数", readonly=True)
    visible_reference_line_count = fields.Integer(string="可见参考明细数", readonly=True)
    amount = fields.Monetary(string="业务金额", currency_field="currency_id", readonly=True)
    balance_effect = fields.Monetary(string="余额影响", currency_field="currency_id", readonly=True)
    cash_in_amount = fields.Monetary(string="现金流入", currency_field="currency_id", readonly=True)
    cash_out_amount = fields.Monetary(string="现金流出", currency_field="currency_id", readonly=True)
    deduction_amount = fields.Monetary(string="扣款/清分金额", currency_field="currency_id", readonly=True)
    paid_amount = fields.Monetary(string="拨付/实付金额", currency_field="currency_id", readonly=True)
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id", readonly=True)
    arrival_amount = fields.Monetary(string="到款金额", currency_field="currency_id", readonly=True)
    arrival_deduction_amount = fields.Monetary(string="到款代扣代缴", currency_field="currency_id", readonly=True)
    arrival_paid_amount = fields.Monetary(string="到款拨付金额", currency_field="currency_id", readonly=True)
    deduction_paid_amount = fields.Monetary(string="扣款实缴", currency_field="currency_id", readonly=True)
    deduction_refund_amount = fields.Monetary(string="扣款退回", currency_field="currency_id", readonly=True)
    deduction_net_amount = fields.Monetary(string="扣款净额", currency_field="currency_id", readonly=True)
    tax_deduction_amount = fields.Monetary(string="抵扣金额", currency_field="currency_id", readonly=True)
    tax_deduction_tax_amount = fields.Monetary(string="抵扣税额", currency_field="currency_id", readonly=True)
    self_funding_income_amount = fields.Monetary(string="自筹收入", currency_field="currency_id", readonly=True)
    self_funding_refund_amount = fields.Monetary(string="自筹退回", currency_field="currency_id", readonly=True)
    self_funding_balance = fields.Monetary(string="自筹正式余额", currency_field="currency_id", readonly=True)
    self_funding_visible_reference_amount = fields.Monetary(string="自筹可见参考金额", currency_field="currency_id", readonly=True)
    guarantee_out_amount = fields.Monetary(string="保证金支出", currency_field="currency_id", readonly=True)
    guarantee_return_amount = fields.Monetary(string="保证金退回", currency_field="currency_id", readonly=True)
    guarantee_outstanding_amount = fields.Monetary(string="保证金在外余额", currency_field="currency_id", readonly=True)
    coverage_note = fields.Char(string="口径说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("项目收付款汇总是只读汇总，请从来源业务单据维护数据。")

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
        context.setdefault(
            "default_note",
            "\n".join(
                part
                for part in (
                    "办理来源：项目收付款汇总",
                    "办理事项：%s" % action_name,
                    "项目：%s" % self.project_id.display_name if self.project_id else False,
                    "来源明细数：%s" % self.source_line_count,
                    "余额影响：%s" % (self.balance_effect or 0.0),
                    "现金流入：%s" % (self.cash_in_amount or 0.0),
                    "现金流出：%s" % (self.cash_out_amount or 0.0),
                    self.coverage_note,
                )
                if part
            ),
        )
        return context

    def action_open_finance_facts(self):
        self.ensure_one()
        domain = self._project_domain()
        if self.business_domain:
            domain.append(("business_domain", "=", self.business_domain))
        return {
            "type": "ir.actions.act_window",
            "name": "%s / 收付款来源明细" % (self.display_name or "项目"),
            "res_model": "sc.finance.business.fact",
            "view_mode": "tree,pivot,form",
            "domain": domain,
            "context": {"search_default_group_business_domain": 1},
        }

    def action_open_business_entry(self):
        self.ensure_one()
        action_xmlid = self._BUSINESS_ENTRY_ACTION_BY_DOMAIN.get(self.business_domain)
        action = self.env.ref(action_xmlid, raise_if_not_found=False) if action_xmlid else None
        if not action:
            return self.action_open_finance_facts()
        result = action.sudo().read()[0]
        action_name = result.get("name") or self._fields["business_domain"].convert_to_export(self.business_domain, self)
        domain = self._action_domain(result)
        if self.project_id and result.get("res_model") in {"sc.expense.claim", "sc.tax.deduction.registration"}:
            domain.append(("project_id", "=", self.project_id.id))
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
        self._cr.execute("SELECT to_regclass('sc_finance_business_fact'), to_regclass('project_project')")
        if not all(self._cr.fetchone()):
            return

        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH grouped AS (
                    SELECT
                        COALESCE(f.project_id, 0) AS project_key,
                        f.project_id,
                        f.business_domain,
                        MIN(f.company_id) AS company_id,
                        MIN(f.currency_id) AS currency_id,
                        COUNT(*)::integer AS source_line_count,
                        COUNT(*) FILTER (WHERE f.balance_policy = 'canonical')::integer AS canonical_line_count,
                        COUNT(*) FILTER (WHERE f.balance_policy = 'visible_reference')::integer AS visible_reference_line_count,
                        COALESCE(SUM(f.amount), 0.0) AS amount,
                        COALESCE(SUM(f.balance_effect), 0.0) AS balance_effect,
                        COALESCE(SUM(f.cash_in_amount), 0.0) AS cash_in_amount,
                        COALESCE(SUM(f.cash_out_amount), 0.0) AS cash_out_amount,
                        COALESCE(SUM(f.deduction_amount), 0.0) AS deduction_amount,
                        COALESCE(SUM(f.paid_amount), 0.0) AS paid_amount,
                        COALESCE(SUM(f.tax_amount), 0.0) AS tax_amount,
                        COALESCE(SUM(CASE WHEN f.fact_type = 'arrival_gross' THEN f.amount ELSE 0 END), 0.0) AS arrival_amount,
                        COALESCE(SUM(CASE WHEN f.fact_type = 'arrival_gross' THEN f.deduction_amount ELSE 0 END), 0.0) AS arrival_deduction_amount,
                        COALESCE(SUM(CASE WHEN f.fact_type = 'arrival_gross' THEN f.paid_amount ELSE 0 END), 0.0) AS arrival_paid_amount,
                        COALESCE(SUM(CASE WHEN f.fact_type = 'deduction_paid' THEN f.amount ELSE 0 END), 0.0) AS deduction_paid_amount,
                        COALESCE(SUM(CASE WHEN f.fact_type = 'deduction_refund' THEN f.amount ELSE 0 END), 0.0) AS deduction_refund_amount,
                        COALESCE(SUM(CASE WHEN f.fact_type IN ('deduction_paid', 'deduction_refund') THEN f.balance_effect ELSE 0 END), 0.0) AS deduction_net_amount,
                        COALESCE(SUM(CASE WHEN f.fact_type = 'tax_deducted' THEN f.amount ELSE 0 END), 0.0) AS tax_deduction_amount,
                        COALESCE(SUM(CASE WHEN f.fact_type = 'tax_deducted' THEN f.tax_amount ELSE 0 END), 0.0) AS tax_deduction_tax_amount,
                        COALESCE(SUM(CASE WHEN f.fact_type = 'self_funding_income' THEN f.amount ELSE 0 END), 0.0) AS self_funding_income_amount,
                        COALESCE(SUM(CASE WHEN f.fact_type = 'self_funding_refund' THEN f.amount ELSE 0 END), 0.0) AS self_funding_refund_amount,
                        COALESCE(SUM(CASE WHEN f.business_domain = 'self_funding' AND f.balance_policy = 'canonical' THEN f.balance_effect ELSE 0 END), 0.0) AS self_funding_balance,
                        COALESCE(SUM(CASE WHEN f.fact_type = 'self_funding_visible_reference' THEN f.amount ELSE 0 END), 0.0) AS self_funding_visible_reference_amount,
                        COALESCE(SUM(CASE WHEN f.fact_type = 'guarantee_out' THEN f.amount ELSE 0 END), 0.0) AS guarantee_out_amount,
                        COALESCE(SUM(CASE WHEN f.fact_type = 'guarantee_return' THEN f.amount ELSE 0 END), 0.0) AS guarantee_return_amount,
                        COALESCE(SUM(CASE WHEN f.business_domain = 'guarantee_deposit' THEN f.balance_effect ELSE 0 END), 0.0) AS guarantee_outstanding_amount
                    FROM sc_finance_business_fact f
                    GROUP BY COALESCE(f.project_id, 0), f.project_id, f.business_domain
                )
                SELECT
                    ROW_NUMBER() OVER (ORDER BY g.project_key, g.business_domain)::integer AS id,
                    CASE
                        WHEN g.project_id IS NULL THEN '未关联项目 / ' || g.business_domain
                        ELSE COALESCE(p.name->>'zh_CN', p.name->>'en_US', '项目') || ' / ' || g.business_domain
                    END AS display_name,
                    g.business_domain,
                    g.project_id,
                    g.company_id,
                    g.currency_id,
                    g.source_line_count,
                    g.canonical_line_count,
                    g.visible_reference_line_count,
                    g.amount,
                    g.balance_effect,
                    g.cash_in_amount,
                    g.cash_out_amount,
                    g.deduction_amount,
                    g.paid_amount,
                    g.tax_amount,
                    g.arrival_amount,
                    g.arrival_deduction_amount,
                    g.arrival_paid_amount,
                    g.deduction_paid_amount,
                    g.deduction_refund_amount,
                    g.deduction_net_amount,
                    g.tax_deduction_amount,
                    g.tax_deduction_tax_amount,
                    g.self_funding_income_amount,
                    g.self_funding_refund_amount,
                    g.self_funding_balance,
                    g.self_funding_visible_reference_amount,
                    g.guarantee_out_amount,
                    g.guarantee_return_amount,
                    g.guarantee_outstanding_amount,
                    CASE
                        WHEN g.business_domain = 'tax_deduction' THEN '税务抵扣保留税务事实，余额影响为 0'
                        WHEN g.business_domain = 'self_funding' THEN '自筹余额只取 income/refund 正式族；visible 族仅作追溯参考'
                        ELSE '按 sc.finance.business.fact 的余额策略汇总'
                    END AS coverage_note
                FROM grouped g
                LEFT JOIN project_project p ON p.id = g.project_id
            )
            """
        )
