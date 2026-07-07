# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyTenderGuaranteeReportFact(models.Model):
    _name = "sc.legacy.tender.guarantee.report.fact"
    _description = "历史投标保证金报表原始事实"
    _order = "legacy_source_table, legacy_record_id"

    legacy_source_table = fields.Char(string="历史来源表", required=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", required=True, index=True)
    legacy_tender_project_name = fields.Char(string="历史投标项目名称", index=True)
    source_amount = fields.Float(string="金额")
    source_amount_field = fields.Char(string="金额来源字段", index=True)
    import_batch = fields.Char(string="导入批次", required=True, default="legacy_tender_guarantee_report_v1", index=True)

    _sql_constraints = [
        (
            "legacy_tender_guarantee_report_fact_unique",
            "unique(legacy_source_table, legacy_record_id)",
            "同一旧投标保证金报表事实只能导入一次。",
        ),
    ]
