# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyInvoiceRegistrationLine(models.Model):
    _name = "sc.legacy.invoice.registration.line"
    _description = "历史发票登记行事实"
    _order = "invoice_date desc, legacy_line_id"

    legacy_line_id = fields.Char(string="旧系统行ID", required=True, index=True)
    legacy_header_id = fields.Char(string="旧系统主表ID", index=True)
    legacy_pid = fields.Char(string="旧系统行PID", index=True)
    legacy_header_pid = fields.Char(string="旧系统主表PID", index=True)
    project_legacy_id = fields.Char(string="项目旧系统ID", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    fee_project_legacy_id = fields.Char(string="费用项目旧系统ID", index=True)
    fee_project_name = fields.Char(string="费用项目名称", index=True)
    document_no = fields.Char(string="单据编号", index=True)
    document_date = fields.Datetime(string="单据日期", index=True)
    invoice_date = fields.Datetime(string="发票日期", index=True)
    recognition_date = fields.Datetime(string="确认日期", index=True)
    invoice_no = fields.Char(string="发票号码", index=True)
    invoice_code = fields.Char(string="发票代码", index=True)
    invoice_type = fields.Char(string="发票类型", index=True)
    invoice_type_id = fields.Char(string="发票类型旧系统ID", index=True)
    supplier_legacy_id = fields.Char(string="供应商旧系统ID", index=True)
    supplier_name = fields.Char(string="供应商", index=True)
    supplier_tax_no = fields.Char(string="供应商税号", index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True, ondelete="set null")
    amount_no_tax = fields.Float(string="不含税金额")
    tax_amount = fields.Float(string="税额")
    amount_total = fields.Float(string="价税合计")
    tax_rate = fields.Char(string="税率", index=True)
    tax_rate_id = fields.Char(string="税率旧系统ID", index=True)
    quantity = fields.Float(string="数量")
    invoice_content = fields.Char(string="开票内容", index=True)
    cost_category_id = fields.Char(string="成本类别ID", index=True)
    cost_category_name = fields.Char(string="成本类别", index=True)
    contract_legacy_id = fields.Char(string="合同旧系统ID", index=True)
    settlement_legacy_id = fields.Char(string="结算旧系统ID", index=True)
    related_invoice_line_id = fields.Char(string="关联发票行ID", index=True)
    related_invoice_line_no = fields.Char(string="关联发票行号", index=True)
    handler_name = fields.Char(string="经办人", index=True)
    header_state = fields.Char(string="单据状态", index=True)
    creator_legacy_user_id = fields.Char(string="创建人旧系统ID", index=True)
    creator_name = fields.Char(string="创建人", index=True)
    created_time = fields.Datetime(string="创建时间", index=True)
    modified_time = fields.Datetime(string="修改时间", index=True)
    invoice_holder = fields.Char(string="持票人", index=True)
    accounting_state = fields.Char(string="核算状态", index=True)
    checksum = fields.Char(string="校验码", index=True)
    voucher_no = fields.Char(string="凭证号", index=True)
    invoice_source = fields.Char(string="发票来源", index=True)
    project_cost_amount = fields.Float(string="项目成本金额")
    billing_unit = fields.Char(string="开票单位", index=True)
    attachment_ref = fields.Char(string="附件引用")
    attachment_name = fields.Char(string="附件名称")
    attachment_path = fields.Char(string="附件路径")
    note = fields.Text(string="备注")
    source_table = fields.Char(string="来源表", default="C_JXXP_ZYFPJJD_CB", required=True, index=True)
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        ("legacy_invoice_registration_line_unique", "unique(legacy_line_id)", "历史发票登记行记录必须唯一。"),
    ]
