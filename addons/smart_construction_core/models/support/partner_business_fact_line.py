# -*- coding: utf-8 -*-
from odoo import fields, models, tools
from odoo.exceptions import UserError


class ScPartnerBusinessFactLine(models.Model):
    _name = "sc.partner.business.fact.line"
    _description = "客户供应商关联业务明细"
    _auto = False
    _rec_name = "display_name"
    _order = "document_date desc, id desc"

    display_name = fields.Char(string="业务摘要", readonly=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", readonly=True, index=True)
    business_role = fields.Selection(
        [("customer", "客户"), ("supplier", "供应商")],
        string="业务方向",
        readonly=True,
        index=True,
    )
    source_label = fields.Char(string="业务类型", readonly=True, index=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True, index=True)
    document_no = fields.Char(string="单据编号", readonly=True, index=True)
    document_date = fields.Date(string="单据日期", readonly=True, index=True)
    amount = fields.Monetary(string="金额", currency_field="currency_id", readonly=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    document_state = fields.Char(string="单据状态", readonly=True, index=True)
    creator_name = fields.Char(string="录入人", readonly=True, index=True)
    created_time = fields.Datetime(string="录入时间", readonly=True, index=True)
    source_model = fields.Char(string="来源模型", readonly=True, index=True)
    source_res_id = fields.Integer(string="来源记录", readonly=True, index=True)
    source_note = fields.Text(string="说明", readonly=True)

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('construction_contract'),
                to_regclass('sc_receipt_income'),
                to_regclass('payment_request'),
                to_regclass('sc_payment_execution'),
                to_regclass('sc_legacy_receipt_residual_fact'),
                to_regclass('sc_legacy_payment_residual_fact'),
                to_regclass('sc_settlement_order'),
                to_regclass('sc_legacy_enterprise_business_fact'),
                to_regclass('sc_legacy_expense_deposit_fact'),
                to_regclass('sc_legacy_supplier_contract_pricing_fact'),
                to_regclass('sc_legacy_invoice_registration_line'),
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
                WITH source_rows AS (
                    SELECT
                        'construction.contract'::varchar AS source_model,
                        c.id::integer AS source_res_id,
                        c.partner_id,
                        CASE WHEN c.type = 'out' THEN 'customer' ELSE 'supplier' END::varchar AS business_role,
                        CASE WHEN c.type = 'out' THEN '收入合同' ELSE '支出合同' END::varchar AS source_label,
                        c.project_id,
                        c.legacy_visible_project_name::varchar AS project_name,
                        COALESCE(NULLIF(c.legacy_visible_document_no, ''), NULLIF(c.legacy_document_no, ''), NULLIF(c.legacy_contract_no, ''), c.name)::varchar AS document_no,
                        COALESCE(c.legacy_visible_contract_date, c.date_contract)::date AS document_date,
                        COALESCE(c.amount_final, c.visible_contract_amount, c.amount_total, 0.0)::numeric AS amount,
                        c.currency_id,
                        COALESCE(NULLIF(c.legacy_visible_document_state, ''), NULLIF(c.legacy_status, ''), c.state)::varchar AS document_state,
                        c.entry_user_text::varchar AS creator_name,
                        c.entry_time AS created_time,
                        c.subject::text AS source_note
                    FROM construction_contract c
                    WHERE c.partner_id IS NOT NULL

                    UNION ALL
                    SELECT
                        'sc.receipt.income', r.id, r.partner_id, 'customer', '收款事实',
                        r.project_id, NULL::varchar, COALESCE(NULLIF(r.document_no, ''), r.name),
                        r.date_receipt, COALESCE(r.amount, 0.0), r.currency_id,
                        COALESCE(NULLIF(r.legacy_document_state, ''), r.state),
                        r.creator_name, r.created_time, r.note
                    FROM sc_receipt_income r
                    WHERE r.partner_id IS NOT NULL

                    UNION ALL
                    SELECT
                        'payment.request', p.id, p.partner_id,
                        CASE WHEN p.type = 'receive' THEN 'customer' ELSE 'supplier' END,
                        CASE WHEN p.type = 'receive' THEN '收款申请' ELSE '付款申请' END,
                        p.project_id, NULL::varchar,
                        p.name,
                        p.date_request, COALESCE(p.amount, 0.0), p.currency_id,
                        COALESCE(NULLIF(p.legacy_document_state, ''), p.state),
                        p.creator_name, p.created_time, p.note
                    FROM payment_request p
                    WHERE p.partner_id IS NOT NULL

                    UNION ALL
                    SELECT
                        'sc.payment.execution', e.id, e.partner_id, 'supplier', '付款执行',
                        e.project_id, NULL::varchar,
                        COALESCE(NULLIF(e.document_no, ''), e.name),
                        e.date_payment, COALESCE(e.paid_amount, e.planned_amount, 0.0), e.currency_id,
                        COALESCE(NULLIF(e.legacy_document_state, ''), e.state),
                        e.creator_name, e.created_time,
                        e.note
                    FROM sc_payment_execution e
                    WHERE e.partner_id IS NOT NULL

                    UNION ALL
                    SELECT
                        'sc.legacy.receipt.residual.fact', f.id, f.partner_id, 'customer', '历史收款事实',
                        f.project_id, f.project_name, f.document_no, f.document_date,
                        COALESCE(f.amount, 0.0), NULL::integer, f.document_state,
                        f.creator_name, f.created_time, f.note
                    FROM sc_legacy_receipt_residual_fact f
                    WHERE f.partner_id IS NOT NULL

                    UNION ALL
                    SELECT
                        'sc.legacy.payment.residual.fact', f.id, f.partner_id, 'supplier', '历史付款事实',
                        f.project_id, f.project_name, f.document_no, f.document_date,
                        COALESCE(f.paid_amount, f.planned_amount, 0.0), NULL::integer, f.document_state,
                        f.creator_name, f.created_time, f.note
                    FROM sc_legacy_payment_residual_fact f
                    WHERE f.partner_id IS NOT NULL

                    UNION ALL
                    SELECT
                        'sc.settlement.order', s.id, s.partner_id, 'supplier', '支出结算',
                        s.project_id, NULL::varchar, s.name, COALESCE(s.date_settlement, s.document_date),
                        COALESCE(s.amount_total, 0.0), s.currency_id, s.state,
                        NULL::varchar, s.create_date, s.note
                    FROM sc_settlement_order s
                    WHERE s.partner_id IS NOT NULL

                    UNION ALL
                    SELECT
                        'sc.legacy.enterprise.business.fact', f.id, f.partner_id, 'supplier', '历史支出事实',
                        NULL::integer, f.legacy_project_name, f.document_no, f.document_date,
                        COALESCE(f.amount_total, 0.0), f.currency_id, f.legacy_document_state,
                        f.creator_name, f.created_time, COALESCE(f.source_note, f.note)
                    FROM sc_legacy_enterprise_business_fact f
                    WHERE f.partner_id IS NOT NULL
                      AND f.fact_family IN ('payment', 'supplier_contract')

                    UNION ALL
                    SELECT
                        'sc.legacy.expense.deposit.fact', f.id, f.partner_id, 'supplier', '历史费用/保证金支出',
                        f.project_id, f.project_display_name, f.document_no, f.document_date,
                        COALESCE(f.source_amount, 0.0), NULL::integer, f.legacy_state,
                        NULL::varchar, NULL::timestamp, f.note
                    FROM sc_legacy_expense_deposit_fact f
                    WHERE f.partner_id IS NOT NULL
                      AND f.direction = 'outflow'

                    UNION ALL
                    SELECT
                        'sc.legacy.supplier.contract.pricing.fact', f.id, f.partner_id, 'supplier', '历史供应商合同',
                        f.project_id, f.project_name, COALESCE(NULLIF(f.document_no, ''), f.contract_no),
                        f.sign_date, COALESCE(f.amount_total, 0.0), NULL::integer, f.document_state,
                        f.creator_name, f.created_time, f.title
                    FROM sc_legacy_supplier_contract_pricing_fact f
                    WHERE f.partner_id IS NOT NULL

                    UNION ALL
                    SELECT
                        'sc.legacy.invoice.registration.line', f.id, f.partner_id, 'supplier', '历史供应商发票',
                        f.project_id, f.project_name, COALESCE(NULLIF(f.document_no, ''), f.invoice_no),
                        COALESCE(f.invoice_date::date, f.document_date::date),
                        COALESCE(f.amount_total, 0.0), NULL::integer, f.header_state,
                        f.creator_name, f.created_time, f.note
                    FROM sc_legacy_invoice_registration_line f
                    WHERE f.partner_id IS NOT NULL
                )
                SELECT
                    row_number() OVER (ORDER BY sr.source_model, sr.source_res_id, sr.partner_id)::integer AS id,
                    CONCAT(sr.source_label, ' / ', COALESCE(NULLIF(sr.document_no, ''), sr.source_res_id::varchar))::varchar AS display_name,
                    sr.partner_id,
                    sr.business_role,
                    sr.source_label,
                    sr.project_id,
                    COALESCE(NULLIF(sr.project_name, ''), pp.name->>'zh_CN', pp.name->>'en_US', '')::varchar AS project_name,
                    sr.document_no,
                    sr.document_date,
                    sr.amount,
                    COALESCE(sr.currency_id, (SELECT currency_id FROM res_company ORDER BY id LIMIT 1)) AS currency_id,
                    sr.document_state,
                    sr.creator_name,
                    sr.created_time,
                    sr.source_model,
                    sr.source_res_id,
                    sr.source_note
                FROM source_rows sr
                LEFT JOIN project_project pp ON pp.id = sr.project_id
            )
            """
        )

    def action_open_source_record(self):
        self.ensure_one()
        if not self.source_model or not self.source_res_id or self.source_model not in self.env:
            raise UserError("没有可打开的来源业务单据。")
        source = self.env[self.source_model].browse(self.source_res_id).exists()
        if not source:
            raise UserError("来源业务单据不存在或已被归档清理。")
        return {
            "type": "ir.actions.act_window",
            "name": self.source_label or source.display_name,
            "res_model": self.source_model,
            "res_id": source.id,
            "view_mode": "form",
            "target": "current",
        }
