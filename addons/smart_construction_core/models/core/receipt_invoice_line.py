# -*- coding: utf-8 -*-
from odoo import fields, models


class ReceiptInvoiceLine(models.Model):
    _name = "sc.receipt.invoice.line"
    _description = "收款发票明细"
    _order = "request_id desc, sequence asc, id asc"

    request_id = fields.Many2one(
        "payment.request",
        string="收款申请",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(string="序号", default=10, index=True)
    legacy_invoice_line_id = fields.Char(string="历史发票明细ID", required=True, copy=False, index=True)
    legacy_receipt_id = fields.Char(string="历史收款单ID", required=True, copy=False, index=True)
    legacy_invoice_id = fields.Char(string="历史发票ID", copy=False)
    legacy_invoice_child_id = fields.Char(string="历史发票子表ID", copy=False)
    legacy_pid = fields.Char(string="历史附件PID", copy=False)
    legacy_file_bill_id = fields.Char(string="历史票据文件ID", copy=False)
    invoice_no = fields.Char(string="发票号码")
    invoice_party_name = fields.Char(string="开票抬头")
    invoice_issue_company = fields.Char(string="开票方")
    source_document_no = fields.Char(string="来源单号")
    source_table_name = fields.Char(string="来源表名")
    amount_source = fields.Char(string="金额来源")
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        related="request_id.project_id",
        store=True,
        readonly=True,
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="往来单位",
        related="request_id.partner_id",
        store=True,
        readonly=True,
        index=True,
    )
    contract_id = fields.Many2one(
        "construction.contract",
        string="合同",
        related="request_id.contract_id",
        store=True,
        readonly=True,
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="request_id.currency_id",
        store=True,
        readonly=True,
    )
    invoice_amount = fields.Monetary(string="发票金额", currency_field="currency_id", required=True)
    current_receipt_amount = fields.Monetary(string="本次收款", currency_field="currency_id")
    invoiced_before_amount = fields.Monetary(string="历史已开票", currency_field="currency_id")
    note = fields.Text(string="备注")
    import_batch = fields.Char(string="导入批次", copy=False)
    active = fields.Boolean("有效", default=True)
    attachment_count = fields.Integer(string="附件数量", compute="_compute_attachment_count")

    def _compute_attachment_count(self):
        grouped = {}
        if self.ids:
            data = self.env["ir.attachment"].sudo().read_group(
                [("res_model", "=", self._name), ("res_id", "in", self.ids)],
                ["res_id"],
                ["res_id"],
            )
            grouped = {int(row["res_id"]): int(row.get("__count", row.get("res_id_count", 0))) for row in data}
        for rec in self:
            rec.attachment_count = grouped.get(rec.id, 0)

    def action_open_attachments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "附件",
            "res_model": "ir.attachment",
            "view_mode": "tree,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "context": {"default_res_model": self._name, "default_res_id": self.id, "create": False},
            "target": "current",
        }
