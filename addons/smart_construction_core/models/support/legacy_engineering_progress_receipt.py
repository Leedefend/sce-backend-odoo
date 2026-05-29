# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScLegacyEngineeringProgressReceipt(models.Model):
    _name = "sc.legacy.engineering.progress.receipt"
    _description = "工程进度收款"
    _auto = False
    _order = "document_date desc, id desc"

    source_model = fields.Char(string="新系统承载模型", readonly=True)
    legacy_source_table = fields.Char(string="旧库来源表", readonly=True)
    legacy_record_id = fields.Char(string="旧库记录", readonly=True)
    document_no = fields.Char(string="单据编号", readonly=True)
    document_date = fields.Date(string="申请日期", readonly=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True)
    project_name = fields.Char(string="历史项目名称", readonly=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", readonly=True)
    partner_name = fields.Char(string="历史往来单位", readonly=True)
    amount = fields.Float(string="收款金额", readonly=True)
    receipt_type = fields.Char(string="收款类型", readonly=True)
    income_category = fields.Char(string="收入类别", readonly=True)
    state_label = fields.Char(string="状态", readonly=True)
    creator_name = fields.Char(string="历史录入人", readonly=True)
    created_time = fields.Datetime(string="历史录入时间", readonly=True)
    note = fields.Text(string="备注", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    100000000 + r.id AS id,
                    'sc.receipt.income'::varchar AS source_model,
                    r.legacy_source_table::varchar AS legacy_source_table,
                    r.legacy_record_id::varchar AS legacy_record_id,
                    COALESCE(NULLIF(r.document_no, ''), r.name)::varchar AS document_no,
                    r.date_receipt::date AS document_date,
                    r.project_id AS project_id,
                    COALESCE(rp.name->>'zh_CN', rp.name->>'en_US')::varchar AS project_name,
                    r.partner_id AS partner_id,
                    rpartner.name::varchar AS partner_name,
                    r.amount::double precision AS amount,
                    COALESCE(NULLIF(r.legacy_receipt_type, ''), r.receipt_type)::varchar AS receipt_type,
                    r.income_category::varchar AS income_category,
                    r.state::varchar AS state_label,
                    r.creator_name::varchar AS creator_name,
                    r.created_time AS created_time,
                    r.note::text AS note
                FROM sc_receipt_income r
                LEFT JOIN project_project rp ON rp.id = r.project_id
                LEFT JOIN res_partner rpartner ON rpartner.id = r.partner_id
                WHERE r.legacy_source_table = 'C_JFHKLR'

                UNION ALL

                SELECT
                    200000000 + p.id AS id,
                    'payment.request'::varchar AS source_model,
                    p.legacy_source_table::varchar AS legacy_source_table,
                    substring(COALESCE(p.note, '') from 'legacy_receipt_id=([^;\\s]+)')::varchar AS legacy_record_id,
                    p.name::varchar AS document_no,
                    p.date_request::date AS document_date,
                    p.project_id AS project_id,
                    COALESCE(pp.name->>'zh_CN', pp.name->>'en_US')::varchar AS project_name,
                    p.partner_id AS partner_id,
                    ppartner.name::varchar AS partner_name,
                    p.amount::double precision AS amount,
                    p.receipt_type::varchar AS receipt_type,
                    NULL::varchar AS income_category,
                    p.state::varchar AS state_label,
                    p.creator_name::varchar AS creator_name,
                    p.created_time AS created_time,
                    p.note::text AS note
                FROM payment_request p
                LEFT JOIN project_project pp ON pp.id = p.project_id
                LEFT JOIN res_partner ppartner ON ppartner.id = p.partner_id
                WHERE p.legacy_source_table = 'C_JFHKLR_ROUTED_OUT'

                UNION ALL

                SELECT
                    300000000 + f.id AS id,
                    'sc.legacy.receipt.income.fact'::varchar AS source_model,
                    f.legacy_source_table::varchar AS legacy_source_table,
                    f.legacy_record_id::varchar AS legacy_record_id,
                    f.document_no::varchar AS document_no,
                    f.document_date::date AS document_date,
                    f.project_id AS project_id,
                    f.legacy_project_name::varchar AS project_name,
                    f.partner_id AS partner_id,
                    f.legacy_partner_name::varchar AS partner_name,
                    f.source_amount::double precision AS amount,
                    f.receipt_type::varchar AS receipt_type,
                    f.income_category::varchar AS income_category,
                    f.legacy_state::varchar AS state_label,
                    f.creator_name::varchar AS creator_name,
                    f.created_time AS created_time,
                    f.note::text AS note
                FROM sc_legacy_receipt_income_fact f
                WHERE f.legacy_source_table = 'C_JFHKLR'
            )
            """
        )
