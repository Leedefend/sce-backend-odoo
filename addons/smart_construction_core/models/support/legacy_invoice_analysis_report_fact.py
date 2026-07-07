# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyInvoiceAnalysisReportFact(models.Model):
    _name = "sc.legacy.invoice.analysis.report.fact"
    _description = "历史发票分析报表原始事实"
    _order = "legacy_source_table, legacy_record_id"

    legacy_source_table = fields.Char(string="历史来源表", required=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", required=True, index=True)
    fact_type = fields.Selection(
        [
            ("contract_amount", "施工合同金额"),
            ("input_invoice_amount", "进项发票金额"),
        ],
        string="事实类型",
        required=True,
        index=True,
    )
    legacy_project_id = fields.Char(string="历史项目ID", required=True, index=True)
    legacy_project_name = fields.Char(string="历史项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, ondelete="cascade")
    invoice_company_type = fields.Char(string="发票公司类型", index=True)
    source_amount = fields.Float(string="金额")
    source_amount_field = fields.Char(string="金额来源字段", index=True)
    import_batch = fields.Char(string="导入批次", required=True, default="legacy_invoice_analysis_report_v1", index=True)

    _sql_constraints = [
        (
            "legacy_invoice_analysis_fact_unique",
            "unique(legacy_source_table, legacy_record_id, fact_type)",
            "同一旧发票分析报表事实只能导入一次。",
        ),
    ]
