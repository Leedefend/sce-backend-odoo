# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScLegacyEngineeringProgressReceipt(models.Model):
    _name = "sc.legacy.engineering.progress.receipt"
    _description = "工程进度收款"
    _auto = False
    _order = "document_date desc, id desc"

    source_model = fields.Char(string="新系统承载模型", readonly=True)
    legacy_source_table = fields.Char(string="旧库来源表", readonly=True)
    source_family = fields.Char(string="来源类别", readonly=True)
    operation_strategy = fields.Char(string="经营方式", readonly=True)
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
                    300000000 + f.id AS id,
                    'sc.legacy.receipt.income.fact'::varchar AS source_model,
                    f.legacy_source_table::varchar AS legacy_source_table,
                    f.source_family::varchar AS source_family,
                    f.operation_strategy::varchar AS operation_strategy,
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
                  AND f.source_family = 'engineering_progress_receipt_visible'
                  AND f.operation_strategy IN ('joint', 'direct')
            )
            """
        )
