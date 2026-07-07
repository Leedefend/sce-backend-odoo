# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyInvoiceCostProgressReportFact(models.Model):
    _name = "sc.legacy.invoice.cost.progress.report.fact"
    _description = "历史发票成本进度报表事实"
    _order = "legacy_project_name"

    legacy_project_id = fields.Char(string="旧项目ID", required=True, index=True)
    legacy_project_name = fields.Char(string="旧项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    import_batch = fields.Char(string="导入批次", index=True)

    progress_receipt_amount = fields.Monetary(string="工程进度收款", currency_field="currency_id")
    output_invoice_amount = fields.Monetary(string="开票登记金额", currency_field="currency_id")
    input_invoice_amount = fields.Monetary(string="进项上报金额", currency_field="currency_id")
    cost_difference_amount = fields.Monetary(string="成本差额", currency_field="currency_id")

    company_id = fields.Many2one(related="project_id.company_id", string="公司", store=True, readonly=True)
    currency_id = fields.Many2one(related="project_id.company_id.currency_id", string="币种", readonly=True)

    _sql_constraints = [
        (
            "legacy_invoice_cost_progress_report_fact_unique",
            "unique(legacy_project_id)",
            "历史发票成本进度报表事实已存在。",
        )
    ]
