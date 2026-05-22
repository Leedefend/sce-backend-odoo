# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScIncomeContractLedger(models.Model):
    _name = "sc.income.contract.ledger"
    _description = "统一收入合同台账"
    _auto = False
    _order = "contract_date desc, id desc"

    source_model = fields.Selection(
        [
            ("construction.contract.income", "项目收入合同"),
            ("sc.general.contract", "一般合同（公司）"),
        ],
        string="来源模型",
        readonly=True,
        index=True,
    )
    source_record_id = fields.Integer(string="来源记录ID", readonly=True, index=True)
    contract_family = fields.Selection(
        [
            ("project_income", "项目收入合同"),
            ("company_general_income", "公司一般收入合同"),
        ],
        string="合同来源",
        readonly=True,
        index=True,
    )
    name = fields.Char(string="单据编号", readonly=True)
    contract_no = fields.Char(string="合同编号", readonly=True)
    contract_name = fields.Char(string="合同名称", readonly=True)
    project_id = fields.Many2one("project.project", string="项目名称", readonly=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True)
    operation_strategy = fields.Selection(
        [
            ("direct", "公司直营"),
            ("joint", "联营项目"),
        ],
        string="经营方式",
        readonly=True,
    )
    partner_id = fields.Many2one("res.partner", string="合同方", readonly=True)
    partner_name_text = fields.Char(string="合同方文本", readonly=True)
    contract_date = fields.Date(string="合同日期", readonly=True)
    contract_payment_method_text = fields.Text(string="合同约定付款方式", readonly=True)
    amount_total = fields.Monetary(string="合同金额", currency_field="currency_id", readonly=True)
    settlement_amount = fields.Monetary(string="结算金额", currency_field="currency_id", readonly=True)
    invoice_amount = fields.Monetary(string="开票金额", currency_field="currency_id", readonly=True)
    received_amount = fields.Monetary(string="收款金额", currency_field="currency_id", readonly=True)
    unreceived_amount = fields.Monetary(string="未收款金额", currency_field="currency_id", readonly=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    state = fields.Char(string="状态", readonly=True)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        readonly=True,
    )
    legacy_source_model = fields.Char(string="历史来源模型", readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", readonly=True)
    handler_id = fields.Many2one("res.users", string="经办人", readonly=True)
    entry_user_id = fields.Many2one("res.users", string="录入人", readonly=True)
    entry_time = fields.Datetime(string="录入时间", readonly=True)
    active = fields.Boolean(string="有效", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    (i.id * 2)::integer AS id,
                    'construction.contract.income'::varchar AS source_model,
                    i.id::integer AS source_record_id,
                    'project_income'::varchar AS contract_family,
                    c.name::varchar AS name,
                    COALESCE(NULLIF(c.legacy_contract_no, ''), NULLIF(c.legacy_external_contract_no, ''), c.name)::varchar AS contract_no,
                    c.subject::varchar AS contract_name,
                    c.project_id,
                    c.company_id,
                    c.operation_strategy::varchar AS operation_strategy,
                    c.partner_id,
                    COALESCE(rp.name, NULLIF(c.legacy_counterparty_text, ''))::varchar AS partner_name_text,
                    c.date_contract::date AS contract_date,
                    c.contract_payment_method_text::text AS contract_payment_method_text,
                    COALESCE(c.visible_contract_amount, c.amount_final, c.amount_total, 0.0)::numeric AS amount_total,
                    0.0::numeric AS settlement_amount,
                    COALESCE(c.visible_invoice_amount, 0.0)::numeric AS invoice_amount,
                    COALESCE(c.visible_received_amount, 0.0)::numeric AS received_amount,
                    COALESCE(c.visible_unreceived_amount, 0.0)::numeric AS unreceived_amount,
                    c.currency_id,
                    c.state::varchar AS state,
                    CASE WHEN COALESCE(c.legacy_contract_id, '') <> '' THEN 'legacy' ELSE 'manual' END::varchar AS source_origin,
                    CASE WHEN COALESCE(c.legacy_contract_id, '') <> '' THEN 'construction.contract.legacy' ELSE NULL END::varchar AS legacy_source_model,
                    NULL::varchar AS legacy_source_table,
                    NULLIF(c.legacy_contract_id, '')::varchar AS legacy_record_id,
                    c.handler_id,
                    c.entry_user_id,
                    c.entry_time,
                    c.active
                FROM construction_contract_income i
                JOIN construction_contract c ON c.id = i.contract_id
                LEFT JOIN res_partner rp ON rp.id = c.partner_id
                WHERE c.type = 'out'
                  AND c.active
                  AND (COALESCE(c.legacy_contract_id, '') = '' OR c.legacy_income_surface_visible)

                UNION ALL

                SELECT
                    (g.id * 2 + 1)::integer AS id,
                    'sc.general.contract'::varchar AS source_model,
                    g.id::integer AS source_record_id,
                    'company_general_income'::varchar AS contract_family,
                    g.name::varchar AS name,
                    COALESCE(NULLIF(g.contract_no, ''), g.name)::varchar AS contract_no,
                    g.contract_name::varchar AS contract_name,
                    g.project_id,
                    g.company_id,
                    g.operation_strategy::varchar AS operation_strategy,
                    g.partner_id,
                    COALESCE(rp.name, NULLIF(g.partner_name_text, ''))::varchar AS partner_name_text,
                    g.contract_date::date AS contract_date,
                    g.payment_terms::text AS contract_payment_method_text,
                    COALESCE(g.amount_total, 0.0)::numeric AS amount_total,
                    COALESCE(g.settlement_amount, 0.0)::numeric AS settlement_amount,
                    COALESCE(g.invoice_amount, 0.0)::numeric AS invoice_amount,
                    COALESCE(g.received_amount, 0.0)::numeric AS received_amount,
                    COALESCE(g.unreceived_amount, 0.0)::numeric AS unreceived_amount,
                    g.currency_id,
                    g.state::varchar AS state,
                    g.source_origin::varchar AS source_origin,
                    g.legacy_source_model,
                    g.legacy_source_table,
                    g.legacy_record_id,
                    g.handler_id,
                    g.entry_user_id,
                    g.create_date AS entry_time,
                    g.active
                FROM sc_general_contract g
                LEFT JOIN res_partner rp ON rp.id = g.partner_id
                WHERE g.active
                  AND g.contract_direction = 'income'
            )
            """
        )

    def action_open_source_record(self):
        self.ensure_one()
        if self.source_model == "construction.contract.income":
            xmlid = "smart_construction_core.action_construction_contract_income"
        else:
            xmlid = "smart_construction_core.action_sc_general_contract"
        action = self.env.ref(xmlid).sudo().read()[0]
        action.update({"res_id": self.source_record_id, "views": [(False, "form")], "view_mode": "form"})
        return action
