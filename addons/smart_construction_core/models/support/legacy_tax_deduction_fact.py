# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyTaxDeductionFact(models.Model):
    _name = "sc.legacy.tax.deduction.fact"
    _description = "历史抵扣税额事实"
    _order = "document_date desc, legacy_line_id"

    legacy_line_id = fields.Char(string="历史明细ID", required=True, index=True)
    legacy_header_id = fields.Char(string="历史主表ID", index=True)
    legacy_pid = fields.Char(string="历史PID", index=True)
    source_table = fields.Char(string="来源表", default="C_JXXP_DKDJ_CB", required=True, index=True)
    document_no = fields.Char(string="单据编号", index=True)
    document_date = fields.Date(string="单据日期", index=True)
    document_state = fields.Char(string="历史状态", index=True)
    deleted_flag = fields.Char(string="删除标记", index=True)
    project_legacy_id = fields.Char(string="历史项目ID", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    partner_legacy_id = fields.Char(string="历史往来单位ID", index=True)
    partner_name = fields.Char(string="往来单位", index=True)
    partner_credit_code = fields.Char(string="统一信用代码", index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位记录", index=True, ondelete="set null")
    invoice_no = fields.Char(string="发票号码", index=True)
    invoice_code = fields.Char(string="发票代码", index=True)
    invoice_date = fields.Date(string="开票日期", index=True)
    invoice_amount_untaxed = fields.Float(string="发票不含税金额")
    invoice_tax_amount = fields.Float(string="发票税额")
    invoice_amount_total = fields.Float(string="发票价税合计")
    deduction_amount = fields.Float(string="抵扣金额")
    deduction_tax_amount = fields.Float(string="抵扣税额")
    deduction_surcharge_amount = fields.Float(string="抵扣附加税")
    deduction_confirm_date = fields.Date(string="认证抵扣日期", index=True)
    import_batch = fields.Char(string="导入批次", default="legacy_tax_deduction_v1", required=True, index=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_tax_deduction_line_unique",
            "unique(legacy_line_id)",
            "Legacy tax deduction line id must be unique.",
        ),
    ]
