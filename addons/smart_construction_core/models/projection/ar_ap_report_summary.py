# -*- coding: utf-8 -*-
import ast

from odoo import fields, models, tools
from odoo.exceptions import UserError


class ScArApReportSummary(models.Model):
    _name = "sc.ar.ap.report.summary"
    _description = "应收应付报表"
    _auto = False
    _rec_name = "project_name"
    _order = "project_name"
    _sc_readonly_navigation_button_methods = {
        "action_open_project_partner_rows",
        "action_open_income_contracts",
        "action_open_expense_contracts",
        "action_open_receipts",
        "action_open_invoices",
        "action_open_payments",
        "action_open_finance_facts",
    }

    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True, index=True)
    legacy_project_id = fields.Char(string="旧项目ID", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)

    income_contract_amount = fields.Monetary(string="施工合同价", currency_field="currency_id", readonly=True)
    receipt_amount = fields.Monetary(string="已收款", currency_field="currency_id", readonly=True)
    output_invoice_amount = fields.Monetary(string="已开票", currency_field="currency_id", readonly=True)
    received_uninvoiced_amount = fields.Monetary(string="已收款未开票", currency_field="currency_id", readonly=True)
    invoiced_unreceived_amount = fields.Monetary(string="已开票未收款", currency_field="currency_id", readonly=True)
    payable_contract_amount = fields.Monetary(string="供货合同价", currency_field="currency_id", readonly=True)
    paid_amount = fields.Monetary(string="已付款", currency_field="currency_id", readonly=True)
    input_invoice_amount = fields.Monetary(string="已开票(应付)", currency_field="currency_id", readonly=True)
    payable_unpaid_amount = fields.Monetary(string="开票未付款", currency_field="currency_id", readonly=True)
    paid_uninvoiced_amount = fields.Monetary(string="付款未开票", currency_field="currency_id", readonly=True)
    output_tax_amount = fields.Monetary(string="开票登记税额", currency_field="currency_id", readonly=True)
    input_tax_amount = fields.Monetary(string="进项上报税额", currency_field="currency_id", readonly=True)
    deduction_tax_amount = fields.Monetary(string="抵扣总额", currency_field="currency_id", readonly=True)
    tax_burden_rate = fields.Float(string="税负", digits=(16, 6), readonly=True)
    output_surcharge_amount = fields.Monetary(string="销项附加税额", currency_field="currency_id", readonly=True)
    input_surcharge_amount = fields.Monetary(string="进项附加税额", currency_field="currency_id", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

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
                "name": "%s / %s" % (self.project_name or "应收应付报表", name),
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
            "name": "%s / 往来单位明细" % (self.project_name or "项目"),
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
            "name": "%s / 收付款事实" % (self.project_name or "项目"),
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
        self._cr.execute(
            """
            SELECT
                to_regclass('sc_legacy_ar_ap_report_fact'),
                to_regclass('project_project'),
                to_regclass('res_company')
            """
        )
        if not all(self._cr.fetchone()):
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    f.id::integer AS id,
                    f.project_id,
                    COALESCE(
                        NULLIF(p.name->>'zh_CN', ''),
                        NULLIF(p.name->>'en_US', ''),
                        CASE
                            WHEN NULLIF(f.legacy_project_name, '') IS NOT NULL
                             AND f.legacy_project_name NOT LIKE '%?%'
                            THEN f.legacy_project_name
                            ELSE ''
                        END,
                        ''
                    ) AS project_name,
                    f.legacy_project_id,
                    p.company_id,
                    COALESCE(c.currency_id, (SELECT currency_id FROM res_company ORDER BY id LIMIT 1)) AS currency_id,
                    COALESCE(f.income_contract_amount, 0.0) AS income_contract_amount,
                    COALESCE(f.receipt_amount, 0.0) AS receipt_amount,
                    COALESCE(f.output_invoice_amount, 0.0) AS output_invoice_amount,
                    COALESCE(f.received_uninvoiced_amount, 0.0) AS received_uninvoiced_amount,
                    COALESCE(f.invoiced_unreceived_amount, 0.0) AS invoiced_unreceived_amount,
                    COALESCE(f.payable_contract_amount, 0.0) AS payable_contract_amount,
                    COALESCE(f.paid_amount, 0.0) AS paid_amount,
                    COALESCE(f.input_invoice_amount, 0.0) AS input_invoice_amount,
                    COALESCE(f.payable_unpaid_amount, 0.0) AS payable_unpaid_amount,
                    COALESCE(f.paid_uninvoiced_amount, 0.0) AS paid_uninvoiced_amount,
                    COALESCE(f.output_tax_amount, 0.0) AS output_tax_amount,
                    COALESCE(f.input_tax_amount, 0.0) AS input_tax_amount,
                    COALESCE(f.deduction_tax_amount, 0.0) AS deduction_tax_amount,
                    COALESCE(f.tax_burden_rate, 0.0) AS tax_burden_rate,
                    COALESCE(f.output_surcharge_amount, 0.0) AS output_surcharge_amount,
                    COALESCE(f.input_surcharge_amount, 0.0) AS input_surcharge_amount,
                    '按旧存储过程 UP_USP_SELECT_YSYFHZB_XM_ZJ 默认日期口径导入项目汇总行'
                        AS coverage_note
                FROM sc_legacy_ar_ap_report_fact f
                LEFT JOIN project_project p ON p.id = f.project_id
                LEFT JOIN res_company c ON c.id = p.company_id
            )
            """
        )
