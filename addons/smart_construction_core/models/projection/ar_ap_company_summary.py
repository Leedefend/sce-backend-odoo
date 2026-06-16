# -*- coding: utf-8 -*-
import ast

from odoo import api, fields, models
from odoo.exceptions import UserError


class ScArApCompanySummary(models.Model):
    _name = "sc.ar.ap.company.summary"
    _description = "应收应付报表"
    _auto = False
    _rec_name = "display_name"
    _order = "project_id"
    _sc_readonly_navigation_button_methods = {
        "action_open_project_partner_rows",
        "action_open_income_contracts",
        "action_open_expense_contracts",
        "action_open_receipts",
        "action_open_invoices",
        "action_open_payments",
        "action_open_finance_facts",
    }

    display_name = fields.Char(string="汇总项", readonly=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True, index=True)
    partner_count = fields.Integer(string="往来单位数", readonly=True)
    income_contract_amount = fields.Float(string="收入合同金额", readonly=True)
    output_invoice_amount = fields.Float(string="已开票", readonly=True)
    receipt_amount = fields.Float(string="已收款", readonly=True)
    receivable_unpaid_amount = fields.Float(string="未收款", readonly=True)
    invoiced_unreceived_amount = fields.Float(string="已开票未收款", readonly=True)
    received_uninvoiced_amount = fields.Float(string="已收款未开票", readonly=True)
    payable_contract_amount = fields.Float(string="应付合同金额", readonly=True)
    payable_pricing_method_text = fields.Char(string="历史计价方式", readonly=True)
    input_invoice_amount = fields.Float(string="已收供应商发票", readonly=True)
    paid_amount = fields.Float(string="已付款", readonly=True)
    payable_unpaid_amount = fields.Float(string="未付款", readonly=True)
    paid_uninvoiced_amount = fields.Float(string="付款超票", readonly=True)
    output_tax_amount = fields.Float(string="销项税额", readonly=True)
    input_tax_amount = fields.Float(string="进项税额", readonly=True)
    deduction_tax_amount = fields.Float(string="抵扣税额", readonly=True)
    tax_deduction_rate = fields.Float(
        string="抵扣比例",
        readonly=True,
        help="项目级指标：按项目抵扣税额合计 / 项目销项税额合计计算。"
        "本报表每个项目只展示一次，导出或透视时不应跨项目简单平均。",
    )
    output_surcharge_amount = fields.Float(string="销项附加税", readonly=True)
    input_surcharge_amount = fields.Float(string="进项附加税", readonly=True)
    deduction_surcharge_amount = fields.Float(string="抵扣附加税", readonly=True)
    self_funding_income_amount = fields.Float(string="自筹收入金额", readonly=True)
    self_funding_refund_amount = fields.Float(string="自筹退回金额", readonly=True)
    self_funding_unreturned_amount = fields.Float(string="自筹未退金额", readonly=True)
    actual_available_balance = fields.Float(
        string="实际可用余额",
        readonly=True,
        help="项目级指标：来自旧库项目资金余额。本报表每个项目只展示一次。",
    )

    def _raise_readonly_projection(self):
        raise UserError("应收应付报表是历史事实汇总结果，请从来源业务单据维护数据。")

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

    def _action_context(self, action_result):
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
        return context

    def _open_action(self, action_xmlid, name, extra_domain=None, use_action_domain=True):
        self.ensure_one()
        action = self.env.ref(action_xmlid, raise_if_not_found=False)
        if not action:
            raise UserError("来源入口不存在，请检查业务菜单配置。")
        result = action.sudo().read()[0]
        domain = self._action_domain(result) if use_action_domain else []
        domain.extend(self._project_domain())
        if extra_domain:
            domain.extend(extra_domain)
        result.update(
            {
                "name": "%s / %s" % (self.display_name or "应收应付", name),
                "domain": domain,
                "context": self._action_context(result),
                "target": "current",
            }
        )
        return result

    def action_open_project_partner_rows(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s / 往来单位明细" % (self.display_name or "项目"),
            "res_model": "sc.ar.ap.project.summary",
            "view_mode": "tree,form,pivot,graph",
            "domain": self._project_domain(),
            "context": {"search_default_group_partner": 1},
            "target": "current",
        }

    def action_open_income_contracts(self):
        return self._open_action(
            "smart_construction_core.action_construction_contract_income_execution",
            "收入合同",
            [("type", "=", "out")],
            use_action_domain=False,
        )

    def action_open_expense_contracts(self):
        return self._open_action(
            "smart_construction_core.action_construction_contract_expense_execution",
            "支出合同",
            [("type", "=", "in")],
            use_action_domain=False,
        )

    def action_open_receipts(self):
        return self._open_action(
            "smart_construction_core.action_sc_receipt_income",
            "收款登记",
            [("active", "=", True)],
        )

    def action_open_invoices(self):
        return self._open_action(
            "smart_construction_core.action_sc_invoice_registration",
            "发票登记",
            [("active", "=", True)],
        )

    def action_open_payments(self):
        return self._open_action(
            "smart_construction_core.action_sc_treasury_ledger_payment",
            "付款台账",
            [("direction", "=", "out"), ("state", "=", "posted")],
        )

    def action_open_finance_facts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s / 收付款事实" % (self.display_name or "项目"),
            "res_model": "sc.finance.business.fact",
            "view_mode": "tree,pivot,form",
            "domain": self._project_domain(),
            "context": {
                "search_default_group_business_domain": 1,
                "search_default_group_partner": 1,
            },
            "target": "current",
        }

    def init(self):
        self._cr.execute("SELECT to_regclass('sc_ar_ap_project_summary')")
        if not self._cr.fetchone()[0]:
            return
        self._cr.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_class
                    WHERE oid = to_regclass('{self._table}')
                      AND relkind = 'v'
                ) THEN
                    EXECUTE 'DROP VIEW IF EXISTS {self._table} CASCADE';
                ELSIF EXISTS (
                    SELECT 1 FROM pg_class
                    WHERE oid = to_regclass('{self._table}')
                      AND relkind = 'm'
                ) THEN
                    EXECUTE 'DROP MATERIALIZED VIEW IF EXISTS {self._table} CASCADE';
                ELSE
                    EXECUTE 'DROP TABLE IF EXISTS {self._table} CASCADE';
                END IF;
            END $$;
            """
        )
        self._cr.execute(
            f"""
            CREATE TABLE {self._table} AS (
                WITH pricing AS (
                    SELECT
                        project_id,
                        string_agg(DISTINCT pricing_method, ', ' ORDER BY pricing_method)
                            AS payable_pricing_method_text
                    FROM (
                        SELECT
                            summary.project_id,
                            trim(split_value.value) AS pricing_method
                        FROM sc_ar_ap_project_summary summary
                        CROSS JOIN LATERAL regexp_split_to_table(
                            summary.payable_pricing_method_text,
                            ','
                        ) AS split_value(value)
                        WHERE NULLIF(trim(split_value.value), '') IS NOT NULL
                    ) split_pricing
                    GROUP BY project_id
                )
                SELECT
                    row_number() OVER (ORDER BY s.project_id) AS id,
                    COALESCE(MAX(s.project_name), '未匹配项目') AS display_name,
                    s.project_id,
                    COALESCE(MAX(s.project_name), '未匹配项目') AS project_name,
                    COUNT(DISTINCT NULLIF(s.partner_key, '')) AS partner_count,
                    SUM(COALESCE(s.income_contract_amount, 0.0)) AS income_contract_amount,
                    SUM(COALESCE(s.output_invoice_amount, 0.0)) AS output_invoice_amount,
                    SUM(COALESCE(s.receipt_amount, 0.0)) AS receipt_amount,
                    SUM(COALESCE(s.receivable_unpaid_amount, 0.0)) AS receivable_unpaid_amount,
                    SUM(COALESCE(s.invoiced_unreceived_amount, 0.0)) AS invoiced_unreceived_amount,
                    SUM(COALESCE(s.received_uninvoiced_amount, 0.0)) AS received_uninvoiced_amount,
                    SUM(COALESCE(s.payable_contract_amount, 0.0)) AS payable_contract_amount,
                    COALESCE(MAX(p.payable_pricing_method_text), '') AS payable_pricing_method_text,
                    SUM(COALESCE(s.input_invoice_amount, 0.0)) AS input_invoice_amount,
                    SUM(COALESCE(s.paid_amount, 0.0)) AS paid_amount,
                    SUM(COALESCE(s.payable_unpaid_amount, 0.0)) AS payable_unpaid_amount,
                    SUM(COALESCE(s.paid_uninvoiced_amount, 0.0)) AS paid_uninvoiced_amount,
                    SUM(COALESCE(s.output_tax_amount, 0.0)) AS output_tax_amount,
                    SUM(COALESCE(s.input_tax_amount, 0.0)) AS input_tax_amount,
                    SUM(COALESCE(s.deduction_tax_amount, 0.0)) AS deduction_tax_amount,
                    MAX(COALESCE(s.tax_deduction_rate, 0.0)) AS tax_deduction_rate,
                    SUM(COALESCE(s.output_surcharge_amount, 0.0)) AS output_surcharge_amount,
                    SUM(COALESCE(s.input_surcharge_amount, 0.0)) AS input_surcharge_amount,
                    SUM(COALESCE(s.deduction_surcharge_amount, 0.0)) AS deduction_surcharge_amount,
                    SUM(COALESCE(s.self_funding_income_amount, 0.0)) AS self_funding_income_amount,
                    SUM(COALESCE(s.self_funding_refund_amount, 0.0)) AS self_funding_refund_amount,
                    SUM(COALESCE(s.self_funding_unreturned_amount, 0.0)) AS self_funding_unreturned_amount,
                    MAX(COALESCE(s.actual_available_balance, 0.0)) AS actual_available_balance
                FROM sc_ar_ap_project_summary s
                LEFT JOIN pricing p ON p.project_id IS NOT DISTINCT FROM s.project_id
                GROUP BY s.project_id
            )
            """
        )
        self._cr.execute(f"ALTER TABLE {self._table} ADD PRIMARY KEY (id)")
        self._cr.execute(f"CREATE INDEX {self._table}_project_id_idx ON {self._table} (project_id)")
        self._cr.execute(f"CREATE INDEX {self._table}_project_name_idx ON {self._table} (project_name)")
