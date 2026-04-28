# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyInvoiceSurchargeFact(models.Model):
    _name = "sc.legacy.invoice.surcharge.fact"
    _description = "历史发票附加税事实"
    _order = "document_date desc, legacy_line_id"

    direction = fields.Selection(
        [("output", "销项"), ("input", "进项")],
        string="方向",
        required=True,
        index=True,
    )
    legacy_line_id = fields.Char(string="历史明细ID", required=True, index=True)
    legacy_header_id = fields.Char(string="历史主表ID", index=True)
    source_table = fields.Char(string="来源表", required=True, index=True)
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
    invoice_date = fields.Date(string="发票日期", index=True)
    surcharge_amount = fields.Float(string="附加税")
    import_batch = fields.Char(string="导入批次", default="legacy_invoice_surcharge_v1", required=True, index=True)
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_invoice_surcharge_line_direction_unique",
            "unique(direction, legacy_line_id)",
            "Legacy invoice surcharge line must be unique per direction.",
        ),
    ]
