# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScInvoiceAnalysisSummary(models.Model):
    _name = "sc.invoice.analysis.summary"
    _description = "发票分析报表"
    _auto = False
    _rec_name = "project_name"
    _order = "project_name"
    _sc_readonly_navigation_button_methods = {
        "action_open_income_contracts",
        "action_open_company_invoices",
        "action_open_individual_invoices",
    }

    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    contract_amount = fields.Monetary(string="施工合同金额", currency_field="currency_id", readonly=True)
    company_invoice_amount = fields.Monetary(string="公司发票金额", currency_field="currency_id", readonly=True)
    individual_invoice_amount = fields.Monetary(string="个体发票金额", currency_field="currency_id", readonly=True)
    company_invoice_ratio = fields.Float(string="公司发票比例", readonly=True, digits=(16, 6))
    individual_invoice_ratio = fields.Float(string="个体发票比例", readonly=True, digits=(16, 6))
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def _project_domain(self):
        self.ensure_one()
        if self.project_id:
            return [("project_id", "=", self.project_id.id)]
        return [("project_id", "=", False)]

    def _project_context(self):
        self.ensure_one()
        return {
            "default_project_id": self.project_id.id if self.project_id else False,
            "current_project_id": self.project_id.id if self.project_id else False,
            "search_default_group_project": 1,
        }

    def _open_action(self, action_xmlid, name, domain, context=None):
        self.ensure_one()
        action = self.env.ref(action_xmlid, raise_if_not_found=False)
        result = action.sudo().read()[0] if action else {"type": "ir.actions.act_window", "view_mode": "tree,form"}
        result.update(
            {
                "name": "%s / %s" % (self.project_name or "项目", name),
                "domain": domain,
                "context": context or self._project_context(),
                "target": "current",
            }
        )
        return result

    def action_open_income_contracts(self):
        return self._open_action(
            "smart_construction_core.action_sc_legacy_invoice_analysis_report_fact",
            "施工合同金额来源",
            self._project_domain() + [("fact_type", "=", "contract_amount")],
        )

    def action_open_company_invoices(self):
        return self._open_action(
            "smart_construction_core.action_sc_legacy_invoice_analysis_report_fact",
            "公司发票金额来源",
            self._project_domain()
            + [
                ("fact_type", "=", "input_invoice_amount"),
                ("invoice_company_type", "=", "公司发票"),
            ],
        )

    def action_open_individual_invoices(self):
        return self._open_action(
            "smart_construction_core.action_sc_legacy_invoice_analysis_report_fact",
            "个体发票金额来源",
            self._project_domain()
            + [
                ("fact_type", "=", "input_invoice_amount"),
                ("invoice_company_type", "=", "个体发票"),
            ],
        )

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('project_project'),
                to_regclass('res_company'),
                to_regclass('sc_legacy_invoice_analysis_report_fact')
            """
        )
        if not all(self._cr.fetchone()):
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH contract_amount AS (
                    SELECT
                        project_id,
                        SUM(COALESCE(source_amount, 0.0)) AS contract_amount
                    FROM sc_legacy_invoice_analysis_report_fact
                    WHERE fact_type = 'contract_amount'
                    GROUP BY project_id
                ),
                input_invoice AS (
                    SELECT
                        project_id,
                        SUM(
                            CASE WHEN invoice_company_type = '公司发票'
                                THEN COALESCE(source_amount, 0.0) ELSE 0.0 END
                        ) AS company_invoice_amount,
                        SUM(
                            CASE WHEN invoice_company_type = '个体发票'
                                THEN COALESCE(source_amount, 0.0) ELSE 0.0 END
                        ) AS individual_invoice_amount
                    FROM sc_legacy_invoice_analysis_report_fact
                    WHERE fact_type = 'input_invoice_amount'
                    GROUP BY project_id
                )
                SELECT
                    p.id::integer AS id,
                    p.id AS project_id,
                    COALESCE(p.name->>'zh_CN', p.name->>'en_US', '') AS project_name,
                    p.company_id,
                    COALESCE(c.currency_id, (SELECT currency_id FROM res_company ORDER BY id LIMIT 1)) AS currency_id,
                    COALESCE(ca.contract_amount, 0.0) AS contract_amount,
                    COALESCE(ii.company_invoice_amount, 0.0) AS company_invoice_amount,
                    COALESCE(ii.individual_invoice_amount, 0.0) AS individual_invoice_amount,
                    CASE
                        WHEN COALESCE(ca.contract_amount, 0.0) <= 0 THEN 0.0
                        ELSE trunc((COALESCE(ii.company_invoice_amount, 0.0)::numeric / ca.contract_amount::numeric), 6)
                    END AS company_invoice_ratio,
                    CASE
                        WHEN COALESCE(ca.contract_amount, 0.0) <= 0 THEN 0.0
                        ELSE trunc((COALESCE(ii.individual_invoice_amount, 0.0)::numeric / ca.contract_amount::numeric), 6)
                    END AS individual_invoice_ratio,
                    '按旧发票分析报表 SQLID 87d7d56f62494c99a0c339f303335813：施工合同金额来自 T_ProjectContract_Out.GCYSZJ，发票比例按 C_JXXP_ZYFPJJD.D_SCBSJS_FPGSLX 分类金额除以施工合同金额'
                        AS coverage_note
                FROM project_project p
                LEFT JOIN res_company c ON c.id = p.company_id
                LEFT JOIN contract_amount ca ON ca.project_id = p.id
                LEFT JOIN input_invoice ii ON ii.project_id = p.id
                WHERE p.active IS TRUE
                  AND (
                    COALESCE(ca.contract_amount, 0.0) <> 0.0
                    OR COALESCE(ii.company_invoice_amount, 0.0) <> 0.0
                    OR COALESCE(ii.individual_invoice_amount, 0.0) <> 0.0
                  )
            )
            """
        )
