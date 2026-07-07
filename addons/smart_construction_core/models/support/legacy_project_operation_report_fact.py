# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyProjectOperationReportFact(models.Model):
    _name = "sc.legacy.project.operation.report.fact"
    _description = "历史项目经营统计表事实"
    _order = "legacy_pid desc, legacy_project_name"

    legacy_project_id = fields.Char(string="旧项目ID", required=True, index=True)
    legacy_pid = fields.Char(string="旧项目排序号", index=True)
    legacy_project_name = fields.Char(string="旧项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    import_batch = fields.Char(string="导入批次", index=True)

    current_receipt_amount = fields.Monetary(string="本期收款", currency_field="currency_id")
    current_deduction_registered_amount = fields.Monetary(string="本期扣款登记", currency_field="currency_id")
    current_subcontract_amount = fields.Monetary(string="本期拨付金额", currency_field="currency_id")
    personal_income_tax_amount = fields.Monetary(string="个人所得税", currency_field="currency_id")
    enterprise_income_tax_amount = fields.Monetary(string="企业所得税", currency_field="currency_id")
    interest_amount = fields.Monetary(string="利息", currency_field="currency_id")
    management_fee_refundable_amount = fields.Monetary(string="管理费(可退)", currency_field="currency_id")
    management_fee_nonrefundable_amount = fields.Monetary(string="管理费(不可退)", currency_field="currency_id")
    other_amount = fields.Monetary(string="其他", currency_field="currency_id")
    vat_nonrefundable_amount = fields.Monetary(string="增值税(不可退)", currency_field="currency_id")
    vat_three_percent_amount = fields.Monetary(string="增值税3%", currency_field="currency_id")
    construction_stamp_tax_amount = fields.Monetary(string="建安印花税", currency_field="currency_id")
    prepaid_vat_amount = fields.Monetary(string="预缴增值税", currency_field="currency_id")
    purchase_sale_stamp_tax_amount = fields.Monetary(string="购销合同印花税", currency_field="currency_id")
    risk_reserve_amount = fields.Monetary(string="风险责任金", currency_field="currency_id")
    surcharge_nonrefundable_amount = fields.Monetary(string="增值税附加(不可退)", currency_field="currency_id")
    surcharge_amount = fields.Monetary(string="增值税附加", currency_field="currency_id")
    vat_amount = fields.Monetary(string="增值税", currency_field="currency_id")
    output_tax_amount = fields.Monetary(string="销项金额", currency_field="currency_id")
    input_tax_amount = fields.Monetary(string="进项金额", currency_field="currency_id")
    actual_deduction_vat_amount = fields.Monetary(string="实际抵扣金额(增值税)", currency_field="currency_id")
    deduction_rate = fields.Float(string="抵扣比例", digits=(16, 6))
    deductible_surcharge_amount = fields.Monetary(string="可抵扣金额(附加税)", currency_field="currency_id")
    actual_deduction_surcharge_amount = fields.Monetary(string="实际抵扣金额(附加税)", currency_field="currency_id")
    net_income_amount = fields.Monetary(string="净收入", currency_field="currency_id")
    operation_income_amount = fields.Monetary(string="经营收入", currency_field="currency_id")

    company_id = fields.Many2one(related="project_id.company_id", string="公司", store=True, readonly=True)
    currency_id = fields.Many2one(related="project_id.company_id.currency_id", string="币种", readonly=True)

    _sql_constraints = [
        (
            "legacy_project_operation_report_fact_unique",
            "unique(legacy_project_id)",
            "历史项目经营统计表事实已存在。",
        )
    ]
