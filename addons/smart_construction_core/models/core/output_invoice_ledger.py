# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScOutputInvoiceLedger(models.Model):
    _name = "sc.output.invoice.ledger"
    _description = "销项发票总台账"
    _auto = False
    _order = "invoice_date desc, id desc"

    source_model = fields.Selection(
        [
            ("sc.receipt.invoice.line", "收款发票明细"),
            ("sc.invoice.registration", "销项冲抵/红冲"),
        ],
        string="来源模型",
        readonly=True,
        index=True,
    )
    source_record_id = fields.Integer(string="来源记录ID", readonly=True, index=True)
    source_kind = fields.Char(string="来源类型", readonly=True, index=True)
    adjustment_kind = fields.Selection(
        [("normal", "正常开票"), ("signed_adjustment", "冲抵/红冲")],
        string="登记类型",
        readonly=True,
        index=True,
    )
    project_id = fields.Many2one("project.project", string="项目", readonly=True)
    operation_strategy = fields.Selection(
        [("direct", "公司直营"), ("joint", "联营项目")],
        string="经营方式",
        readonly=True,
    )
    partner_id = fields.Many2one("res.partner", string="往来单位", readonly=True)
    contract_id = fields.Many2one("construction.contract", string="合同", readonly=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    invoice_date = fields.Date(string="开票日期", readonly=True, index=True)
    invoice_no = fields.Char(string="发票号码", readonly=True, index=True)
    invoice_party_name = fields.Char(string="开票抬头", readonly=True)
    invoice_issue_company = fields.Char(string="开票单位", readonly=True, index=True)
    invoice_document_no = fields.Char(string="开票登记单号", readonly=True, index=True)
    invoice_document_state = fields.Char(string="开票登记状态", readonly=True, index=True)
    source_document_no = fields.Char(string="来源单号", readonly=True)
    source_table_name = fields.Char(string="来源表名", readonly=True)
    amount_source = fields.Char(string="金额来源", readonly=True)
    receipt_line_count = fields.Integer(string="关联收款笔数", readonly=True)
    invoice_amount = fields.Monetary(string="发票金额", currency_field="currency_id", readonly=True)
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id", readonly=True)
    amount_no_tax = fields.Monetary(string="不含税金额", currency_field="currency_id", readonly=True)
    surcharge_amount = fields.Monetary(string="附加税", currency_field="currency_id", readonly=True)
    current_receipt_amount = fields.Monetary(string="本次收款", currency_field="currency_id", readonly=True)
    invoiced_before_amount = fields.Monetary(string="历史已开票", currency_field="currency_id", readonly=True)
    note = fields.Text(string="备注", readonly=True)
    active = fields.Boolean(string="有效", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH receipt_invoice_dedup AS (
                    SELECT
                        ril.*,
                        NULLIF(TRIM(ril.invoice_no), '') AS normalized_invoice_no,
                        COUNT(*) OVER (PARTITION BY NULLIF(TRIM(ril.invoice_no), '')) AS receipt_line_count,
                        SUM(COALESCE(ril.current_receipt_amount, 0.0)) OVER (
                            PARTITION BY NULLIF(TRIM(ril.invoice_no), '')
                        ) AS receipt_amount_sum,
                        ROW_NUMBER() OVER (
                            PARTITION BY NULLIF(TRIM(ril.invoice_no), '')
                            ORDER BY ril.invoice_date DESC NULLS LAST, ril.id DESC
                        ) AS receipt_rank
                    FROM sc_receipt_invoice_line ril
                    WHERE ril.active
                      AND NULLIF(TRIM(ril.invoice_no), '') IS NOT NULL
                      AND TRIM(ril.invoice_no) <> '0'
                )
                SELECT
                    (ril.id * 2)::integer AS id,
                    'sc.receipt.invoice.line'::varchar AS source_model,
                    ril.id::integer AS source_record_id,
                    'receipt_invoice_line_dedup'::varchar AS source_kind,
                    'normal'::varchar AS adjustment_kind,
                    ril.project_id,
                    p.operation_strategy::varchar AS operation_strategy,
                    ril.partner_id,
                    ril.contract_id,
                    ril.currency_id,
                    ril.invoice_date,
                    ril.normalized_invoice_no::varchar AS invoice_no,
                    ril.invoice_party_name::varchar AS invoice_party_name,
                    ril.invoice_issue_company::varchar AS invoice_issue_company,
                    ril.invoice_document_no::varchar AS invoice_document_no,
                    ril.invoice_document_state::varchar AS invoice_document_state,
                    ril.source_document_no::varchar AS source_document_no,
                    ril.source_table_name::varchar AS source_table_name,
                    CASE
                        WHEN ril.receipt_line_count > 1 THEN 'receipt_invoice_line_dedup_by_invoice_no'
                        ELSE ril.amount_source
                    END::varchar AS amount_source,
                    ril.receipt_line_count::integer AS receipt_line_count,
                    ril.invoice_amount::numeric AS invoice_amount,
                    0.0::numeric AS tax_amount,
                    ril.invoice_amount::numeric AS amount_no_tax,
                    ril.surcharge_amount::numeric AS surcharge_amount,
                    ril.receipt_amount_sum::numeric AS current_receipt_amount,
                    ril.invoiced_before_amount::numeric AS invoiced_before_amount,
                    CASE
                        WHEN ril.receipt_line_count > 1 THEN CONCAT_WS(
                            E'\n',
                            NULLIF(ril.note, ''),
                            FORMAT(
                                '同一发票号关联%s笔收款记录，销项发票总台账按发票号去重展示；本次收款为关联收款合计。',
                                ril.receipt_line_count
                            )
                        )
                        ELSE ril.note
                    END::text AS note,
                    ril.active
                FROM receipt_invoice_dedup ril
                LEFT JOIN project_project p ON p.id = ril.project_id
                WHERE ril.receipt_rank = 1

                UNION ALL

                SELECT
                    (ir.id * 2 + 1)::integer AS id,
                    'sc.invoice.registration'::varchar AS source_model,
                    ir.id::integer AS source_record_id,
                    ir.source_kind::varchar AS source_kind,
                    'signed_adjustment'::varchar AS adjustment_kind,
                    ir.project_id,
                    p.operation_strategy::varchar AS operation_strategy,
                    ir.partner_id,
                    ir.contract_id,
                    ir.currency_id,
                    ir.invoice_date,
                    ir.invoice_no::varchar AS invoice_no,
                    COALESCE(rp.name, NULLIF(ir.legacy_partner_name, ''))::varchar AS invoice_party_name,
                    ir.invoice_issue_company::varchar AS invoice_issue_company,
                    ir.document_no::varchar AS invoice_document_no,
                    ir.legacy_document_state::varchar AS invoice_document_state,
                    ir.document_no::varchar AS source_document_no,
                    ir.legacy_source_table::varchar AS source_table_name,
                    'invoice_registration_signed_amount'::varchar AS amount_source,
                    0::integer AS receipt_line_count,
                    ir.amount_total::numeric AS invoice_amount,
                    ir.tax_amount::numeric AS tax_amount,
                    ir.amount_no_tax::numeric AS amount_no_tax,
                    ir.surcharge_amount::numeric AS surcharge_amount,
                    ir.related_receipt_amount::numeric AS current_receipt_amount,
                    0.0::numeric AS invoiced_before_amount,
                    ir.note::text AS note,
                    ir.active
                FROM sc_invoice_registration ir
                LEFT JOIN project_project p ON p.id = ir.project_id
                LEFT JOIN res_partner rp ON rp.id = ir.partner_id
                WHERE ir.active
                  AND ir.direction = 'output'
                  AND ir.legacy_source_model = 'sc.legacy.invoice.tax.fact'
                  AND ir.legacy_source_table = 'C_JXXP_XXKPDJ'
                  AND (
                    COALESCE(ir.amount_total, 0) < 0
                    OR COALESCE(ir.amount_no_tax, 0) < 0
                    OR COALESCE(ir.tax_amount, 0) < 0
                    OR COALESCE(ir.surcharge_amount, 0) < 0
                  )
            )
            """
        )
