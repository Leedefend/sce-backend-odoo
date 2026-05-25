# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScLegacyFundConfirmationDocument(models.Model):
    _name = "sc.legacy.fund.confirmation.document"
    _description = "Legacy Arrival Confirmation Document"
    _auto = False
    _order = "receipt_time desc, document_no desc"

    sequence_no = fields.Integer(string="序号", readonly=True)
    document_state = fields.Char(string="单据状态", readonly=True)
    document_no = fields.Char(string="单据编号", readonly=True, index=True)
    receipt_time = fields.Datetime(string="时间", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True, index=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True)
    period_no = fields.Char(string="期数", readonly=True)
    actual_fund_amount = fields.Float(string="本期收款", readonly=True)
    deducted_amount_total = fields.Float(string="本期代扣代缴合计", readonly=True)
    paid_amount_total = fields.Float(string="本期拨付金额合计", readonly=True)
    construction_unit_name = fields.Char(string="施工单位", readonly=True, index=True)
    contract_amount = fields.Float(string="合同金额", readonly=True)
    current_project_stage = fields.Char(string="目前形象进度", readonly=True)
    accumulated_invoice_amount = fields.Float(string="累计开票金额", readonly=True)
    previous_retained_balance = fields.Float(string="上期留存余额", readonly=True)
    creator_name = fields.Char(string="录入人", readonly=True)
    created_time = fields.Datetime(string="录入时间", readonly=True, index=True)
    attachment_links = fields.Char(string="附件", readonly=True)
    attachment_ref = fields.Char(string="历史附件引用", readonly=True)
    legacy_header_id = fields.Char(string="历史主表ID", readonly=True, index=True)
    active = fields.Boolean(string="有效", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH document_rows AS (
                    SELECT
                        COALESCE(NULLIF(l.legacy_header_id, ''), NULLIF(l.document_no, ''), l.legacy_line_id) AS document_key,
                        MIN(l.id) AS id,
                        MIN(NULLIF(l.legacy_header_id, '')) AS legacy_header_id,
                        MIN(NULLIF(l.document_no, '')) AS document_no,
                        MIN(l.receipt_time) AS receipt_time,
                        COALESCE(MAX(NULLIF(l.project_name, '')), MAX(COALESCE(p.name->>'zh_CN', p.name->>'en_US'))) AS project_name,
                        MIN(l.project_id) AS project_id,
                        MAX(NULLIF(l.period_no, '')) AS period_no,
                        MAX(COALESCE(l.actual_fund_amount, 0.0)) AS actual_fund_amount,
                        SUM(GREATEST(COALESCE(l.current_actual_amount, 0.0), 0.0)) AS deducted_amount_total,
                        GREATEST(MAX(COALESCE(l.actual_fund_amount, 0.0)) - SUM(GREATEST(COALESCE(l.current_actual_amount, 0.0), 0.0)), 0.0) AS paid_amount_total,
                        MAX(NULLIF(l.contract_name, '')) AS construction_unit_name,
                        MAX(COALESCE(l.contract_amount, 0.0)) AS contract_amount,
                        MAX(NULLIF(l.current_project_stage, '')) AS current_project_stage,
                        MAX(COALESCE(l.accumulated_invoice_amount, 0.0)) AS accumulated_invoice_amount,
                        0.0::double precision AS previous_retained_balance,
                        MAX(NULLIF(l.creator_name, '')) AS creator_name,
                        MIN(l.created_time) AS created_time,
                        MIN(NULLIF(l.attachment_ref, '')) AS attachment_ref,
                        BOOL_OR(COALESCE(l.active, false)) AS active,
                        CASE MAX(NULLIF(l.document_state, ''))
                            WHEN '-1' THEN '已驳回'
                            WHEN '0' THEN '草稿'
                            WHEN '1' THEN '审核中'
                            WHEN '2' THEN '审核通过'
                            ELSE COALESCE(MAX(NULLIF(l.document_state, '')), '')
                        END AS document_state
                    FROM sc_legacy_fund_confirmation_line l
                    LEFT JOIN project_project p ON p.id = l.project_id
                    WHERE COALESCE(l.active, false)
                    GROUP BY COALESCE(NULLIF(l.legacy_header_id, ''), NULLIF(l.document_no, ''), l.legacy_line_id)
                ), attachment_rows AS (
                    SELECT
                        d.document_key,
                        STRING_AGG(
                            DISTINCT fi.file_name || ' | legacy-file://' || ltrim(COALESCE(NULLIF(fi.preview_path, ''), fi.file_path), '/'),
                            ' '
                        ) AS attachment_links
                    FROM document_rows d
                    JOIN sc_legacy_file_index fi
                      ON fi.active
                     AND fi.bill_id = d.attachment_ref
                     AND COALESCE(NULLIF(fi.file_name, ''), '') <> ''
                     AND COALESCE(NULLIF(fi.preview_path, ''), NULLIF(fi.file_path, '')) IS NOT NULL
                    GROUP BY d.document_key
                )
                SELECT
                    ROW_NUMBER() OVER (ORDER BY d.receipt_time DESC NULLS LAST, d.document_no DESC NULLS LAST, d.id DESC)::integer AS sequence_no,
                    d.id,
                    d.document_state,
                    d.document_no,
                    d.receipt_time,
                    d.project_name,
                    d.project_id,
                    d.period_no,
                    d.actual_fund_amount,
                    d.deducted_amount_total,
                    d.paid_amount_total,
                    d.construction_unit_name,
                    d.contract_amount,
                    d.current_project_stage,
                    d.accumulated_invoice_amount,
                    d.previous_retained_balance,
                    d.creator_name,
                    d.created_time,
                    COALESCE(a.attachment_links, d.attachment_ref) AS attachment_links,
                    d.attachment_ref,
                    d.legacy_header_id,
                    d.active
                FROM document_rows d
                LEFT JOIN attachment_rows a ON a.document_key = d.document_key
            )
            """
        )
