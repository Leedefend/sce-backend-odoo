# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScLegacyFundConfirmationDocument(models.Model):
    _name = "sc.legacy.fund.confirmation.document"
    _description = "历史到账确认单据"
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
                WITH header_available AS (
                    SELECT EXISTS (
                        SELECT 1
                        FROM sc_legacy_fund_confirmation_header
                        WHERE COALESCE(active, false)
                        LIMIT 1
                    ) AS has_headers
                ), header_rows AS (
                    SELECT
                        h.id,
                        h.legacy_header_id,
                        NULLIF(h.document_no, '') AS document_no,
                        h.receipt_time,
                        COALESCE(NULLIF(h.project_name, ''), COALESCE(p.name->>'zh_CN', p.name->>'en_US')) AS project_name,
                        h.project_id,
                        NULLIF(h.period_no, '') AS period_no,
                        COALESCE(h.actual_fund_amount, 0.0) AS actual_fund_amount,
                        COALESCE(line_totals.deducted_amount_total, 0.0) AS deducted_amount_total,
                        GREATEST(COALESCE(h.actual_fund_amount, 0.0) - COALESCE(line_totals.deducted_amount_total, 0.0), 0.0) AS paid_amount_total,
                        NULLIF(h.contract_name, '') AS construction_unit_name,
                        COALESCE(h.contract_amount, 0.0) AS contract_amount,
                        NULLIF(h.current_project_stage, '') AS current_project_stage,
                        COALESCE(h.accumulated_invoice_amount, 0.0) AS accumulated_invoice_amount,
                        0.0::double precision AS previous_retained_balance,
                        NULLIF(h.creator_name, '') AS creator_name,
                        h.created_time,
                        NULLIF(h.attachment_ref, '') AS attachment_ref,
                        COALESCE(h.active, false) AS active,
                        CASE NULLIF(h.document_state, '')
                            WHEN '-1' THEN '已驳回'
                            WHEN '0' THEN '草稿'
                            WHEN '1' THEN '审核中'
                            WHEN '2' THEN '审核通过'
                            ELSE COALESCE(NULLIF(h.document_state, ''), '')
                        END AS document_state
                    FROM sc_legacy_fund_confirmation_header h
                    LEFT JOIN project_project p ON p.id = h.project_id
                    LEFT JOIN (
                        SELECT
                            legacy_header_id,
                            SUM(GREATEST(COALESCE(current_actual_amount, 0.0), 0.0)) AS deducted_amount_total
                        FROM sc_legacy_fund_confirmation_line
                        WHERE COALESCE(active, false)
                          AND COALESCE(NULLIF(legacy_header_id, ''), '') <> ''
                        GROUP BY legacy_header_id
                    ) line_totals ON line_totals.legacy_header_id = h.legacy_header_id
                    WHERE COALESCE(h.active, false)
                ), fallback_document_rows AS (
                    SELECT
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
                ), document_rows AS (
                    SELECT *
                    FROM header_rows
                    UNION ALL
                    SELECT *
                    FROM fallback_document_rows
                    WHERE NOT (SELECT has_headers FROM header_available)
                ), attachment_rows AS (
                    SELECT
                        d.id AS document_id,
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
                    GROUP BY d.id
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
                    COALESCE(
                        a.attachment_links,
                        CASE
                            WHEN COALESCE(NULLIF(d.attachment_ref, ''), '') <> ''
                            THEN '历史附件 | legacy-file-id://' || d.attachment_ref
                            ELSE NULL
                        END
                    ) AS attachment_links,
                    d.attachment_ref,
                    d.legacy_header_id,
                    d.active
                FROM document_rows d
                LEFT JOIN attachment_rows a ON a.document_id = d.id
            )
            """
        )
