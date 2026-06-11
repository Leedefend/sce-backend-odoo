# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ScCompanyContractorResponsibilityFact(models.Model):
    _name = "sc.company.contractor.responsibility.fact"
    _description = "公司-承包人资金责任明细"
    _auto = False
    _rec_name = "display_name"
    _order = "document_date desc, id desc"
    _sc_readonly_navigation_button_methods = {
        "action_open_finance_fact",
        "action_open_source_record",
    }

    display_name = fields.Char(string="责任摘要", readonly=True)
    responsibility_type = fields.Selection(
        [
            ("arrival_confirmation", "到款确认"),
            ("self_funding_income", "自筹垫付"),
            ("self_funding_refund", "自筹退回"),
        ],
        string="责任类型",
        readonly=True,
        index=True,
    )
    responsibility_scope = fields.Selection(
        [
            ("company_contractor", "公司-承包人"),
        ],
        string="责任范围",
        readonly=True,
        index=True,
    )
    balance_policy = fields.Selection(
        [
            ("canonical", "正式责任"),
        ],
        string="责任口径",
        readonly=True,
        index=True,
    )
    source_model = fields.Char(string="来源模型", readonly=True, index=True)
    source_res_id = fields.Integer(string="来源记录ID", readonly=True, index=True)
    source_document_no = fields.Char(string="来源编号", readonly=True, index=True)
    source_menu_hint = fields.Char(string="来源业务入口", readonly=True, index=True)
    document_date = fields.Date(string="发生日期", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    partner_id = fields.Many2one("res.partner", string="承包人", readonly=True, index=True)
    partner_name = fields.Char(string="承包人名称", readonly=True, index=True)
    amount = fields.Monetary(string="责任金额", currency_field="currency_id", readonly=True)
    arrival_amount = fields.Monetary(string="到款金额", currency_field="currency_id", readonly=True)
    paid_amount = fields.Monetary(string="拨付金额", currency_field="currency_id", readonly=True)
    deducted_amount = fields.Monetary(string="扣款金额", currency_field="currency_id", readonly=True)
    self_funding_income_amount = fields.Monetary(string="自筹垫付", currency_field="currency_id", readonly=True)
    self_funding_refund_amount = fields.Monetary(string="自筹退回", currency_field="currency_id", readonly=True)
    self_funding_balance_effect = fields.Monetary(string="自筹未退影响", currency_field="currency_id", readonly=True)
    project_fund_status_effect = fields.Monetary(string="项目资金状态影响", currency_field="currency_id", readonly=True)
    contractor_responsibility_effect = fields.Monetary(string="承包人责任影响", currency_field="currency_id", readonly=True)
    source_fact_id = fields.Many2one("sc.finance.business.fact", string="收付款事实", readonly=True, index=True)
    coverage_note = fields.Char(string="口径说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("公司-承包人资金责任明细是只读归集，请从到款确认或自筹业务单据维护数据。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def action_open_finance_fact(self):
        self.ensure_one()
        if not self.source_fact_id:
            raise UserError("没有可打开的收付款事实。")
        return {
            "type": "ir.actions.act_window",
            "name": "项目收付款来源明细",
            "res_model": "sc.finance.business.fact",
            "res_id": self.source_fact_id.id,
            "views": [(False, "form")],
            "view_mode": "form",
            "target": "current",
        }

    def action_open_source_record(self):
        self.ensure_one()
        if not self.source_model or not self.source_res_id or self.source_model not in self.env:
            return self.action_open_finance_fact()
        source = self.env[self.source_model].browse(self.source_res_id).exists()
        if not source:
            return self.action_open_finance_fact()
        return {
            "type": "ir.actions.act_window",
            "name": self.source_menu_hint or source.display_name,
            "res_model": self.source_model,
            "res_id": source.id,
            "views": [(False, "form")],
            "view_mode": "form",
            "target": "current",
        }

    def init(self):
        self._cr.execute("SELECT to_regclass('sc_finance_business_fact')")
        if not self._cr.fetchone()[0]:
            return

        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    (600000000 + f.id)::integer AS id,
                    f.display_name,
                    CASE
                        WHEN f.fact_type = 'arrival_gross' THEN 'arrival_confirmation'
                        WHEN f.fact_type = 'self_funding_income' THEN 'self_funding_income'
                        WHEN f.fact_type = 'self_funding_refund' THEN 'self_funding_refund'
                    END AS responsibility_type,
                    'company_contractor' AS responsibility_scope,
                    'canonical' AS balance_policy,
                    f.source_model,
                    f.source_res_id,
                    f.source_document_no,
                    f.source_menu_hint,
                    f.document_date,
                    f.company_id,
                    f.currency_id,
                    f.project_id,
                    f.partner_id,
                    f.partner_name,
                    f.amount,
                    CASE WHEN f.fact_type = 'arrival_gross' THEN f.amount ELSE 0.0 END AS arrival_amount,
                    CASE WHEN f.fact_type = 'arrival_gross' THEN f.paid_amount ELSE 0.0 END AS paid_amount,
                    CASE WHEN f.fact_type = 'arrival_gross' THEN f.deduction_amount ELSE 0.0 END AS deducted_amount,
                    CASE WHEN f.fact_type = 'self_funding_income' THEN f.amount ELSE 0.0 END AS self_funding_income_amount,
                    CASE WHEN f.fact_type = 'self_funding_refund' THEN f.amount ELSE 0.0 END AS self_funding_refund_amount,
                    CASE
                        WHEN f.fact_type = 'self_funding_income' THEN f.amount
                        WHEN f.fact_type = 'self_funding_refund' THEN -f.amount
                        ELSE 0.0
                    END AS self_funding_balance_effect,
                    CASE WHEN f.fact_type = 'arrival_gross' THEN f.amount ELSE 0.0 END AS project_fund_status_effect,
                    CASE
                        WHEN f.fact_type = 'arrival_gross' THEN COALESCE(f.paid_amount, 0.0) + COALESCE(f.deduction_amount, 0.0)
                        WHEN f.fact_type = 'self_funding_income' THEN f.amount
                        WHEN f.fact_type = 'self_funding_refund' THEN -f.amount
                        ELSE 0.0
                    END AS contractor_responsibility_effect,
                    f.id AS source_fact_id,
                    CASE
                        WHEN f.fact_type = 'arrival_gross' THEN '到款确认反映项目收款状态，并约束公司对承包人的拨付、扣款和后续办理'
                        WHEN f.fact_type = 'self_funding_income' THEN '自筹垫付反映承包人与公司的资金占用关系，项目用于归属和办理约束'
                        WHEN f.fact_type = 'self_funding_refund' THEN '自筹退回冲减承包人与公司的自筹占用关系'
                    END AS coverage_note
                FROM sc_finance_business_fact f
                WHERE f.business_domain IN ('arrival_settlement', 'self_funding')
                  AND f.fact_type IN ('arrival_gross', 'self_funding_income', 'self_funding_refund')
                  AND f.balance_policy = 'canonical'
            )
            """
        )
