# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyIncomeInvoiceFact(models.Model):
    _name = "sc.legacy.income.invoice.fact"
    _description = "历史收入票据事实"
    _order = "document_date desc, source_table, legacy_record_id"

    legacy_record_id = fields.Char(string="记录编号", required=True, index=True)
    legacy_parent_id = fields.Char(string="父单编号", index=True)
    legacy_pid = fields.Char(string="附件编号", index=True)
    source_table = fields.Char(string="来源表", required=True, index=True)
    source_dataset = fields.Char(string="数据来源", index=True)
    fact_type = fields.Selection(
        [
            ("invoice_application", "开票申请"),
            ("invoice_application_line", "开票申请明细"),
            ("invoice_config", "税控开票配置"),
            ("invoice_contract_link", "开票合同关联"),
            ("prepaid_tax", "预缴税款"),
            ("prepaid_tax_line", "预缴税款明细"),
            ("invoice_issue", "发票开具"),
            ("invoice_issue_line", "发票开具明细"),
            ("tax_deduction", "抵扣登记"),
            ("tax_transfer_line", "进项转出明细"),
        ],
        string="事实类型",
        required=True,
        index=True,
    )
    document_no = fields.Char(string="单号", index=True)
    document_state = fields.Char(string="单据状态", index=True)
    state = fields.Selection(
        [("legacy_confirmed", "历史已确认"), ("cancel", "历史作废")],
        string="承载状态",
        default="legacy_confirmed",
        required=True,
        index=True,
    )

    project_legacy_id = fields.Char(string="项目原编号", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目锚点", index=True, ondelete="set null")
    company_id = fields.Many2one("res.company", string="公司", related="project_id.company_id", store=True, readonly=True, index=True)
    partner_legacy_id = fields.Char(string="客户/购方原编号", index=True)
    partner_name = fields.Char(string="客户/购方", index=True)
    partner_tax_no = fields.Char(string="税号", index=True)
    contract_legacy_id = fields.Char(string="合同原编号", index=True)
    contract_no = fields.Char(string="合同编号", index=True)
    contract_name = fields.Char(string="合同名称", index=True)
    invoice_no = fields.Char(string="发票号码", index=True)
    invoice_code = fields.Char(string="发票代码", index=True)
    invoice_type = fields.Char(string="发票类型", index=True)
    invoice_content = fields.Char(string="开票内容", index=True)
    tax_method = fields.Char(string="计税方法", index=True)
    tax_type = fields.Char(string="交税类型", index=True)
    tax_certificate_no = fields.Char(string="完税凭证号码", index=True)

    document_date = fields.Datetime(string="单据日期", index=True)
    invoice_date = fields.Datetime(string="开票/缴纳日期", index=True)
    expected_receipt_date = fields.Datetime(string="预计回款日期", index=True)
    created_time = fields.Datetime(string="创建时间", index=True)
    creator_name = fields.Char(string="创建人", index=True)
    creator_legacy_user_id = fields.Char(string="创建人原编号", index=True)

    qty = fields.Float(string="数量/比例")
    unit_price = fields.Float(string="单价")
    amount_total = fields.Float(string="价税合计/金额")
    amount_no_tax = fields.Float(string="不含税金额")
    tax_amount = fields.Float(string="税额")
    tax_rate = fields.Float(string="税率")
    amount_contract = fields.Float(string="合同金额")
    amount_received = fields.Float(string="收款/抵扣金额")

    bank_name = fields.Char(string="开户行")
    bank_account = fields.Char(string="银行账号")
    attachment_ref = fields.Char(string="附件")
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_income_invoice_unique",
            "unique(source_table, legacy_record_id)",
            "同一历史收入票据事实只能导入一次。",
        ),
    ]
