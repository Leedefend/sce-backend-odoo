# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


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
    invoice_date = fields.Date(string="开票日期", index=True)
    invoice_party_name = fields.Char(string="开票抬头")
    invoice_issue_company = fields.Char(string="开票单位", index=True)
    invoice_document_no = fields.Char(string="开票登记单号", index=True)
    invoice_document_state = fields.Char(string="开票登记状态", index=True)
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
    operation_strategy = fields.Selection(
        related="project_id.operation_strategy",
        string="经营方式",
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
    surcharge_amount = fields.Monetary(string="附加税", currency_field="currency_id")
    current_receipt_amount = fields.Monetary(string="本次收款", currency_field="currency_id")
    invoiced_before_amount = fields.Monetary(string="历史已开票", currency_field="currency_id")
    note = fields.Text(string="备注")
    import_batch = fields.Char(string="导入批次", copy=False)
    active = fields.Boolean("有效", default=True)
    attachment_count = fields.Integer(string="附件数量", compute="_compute_attachment_count")
    visible_attachment_count = fields.Integer(
        string="附件",
        compute="_compute_visible_attachment_count",
        store=True,
        readonly=True,
    )

    @api.constrains("request_id", "invoice_amount", "current_receipt_amount", "active", "import_batch")
    def _check_manual_receipt_invoice_amounts(self):
        for rec in self:
            if rec.import_batch or not rec.active or (rec.current_receipt_amount or 0.0) <= 0.0:
                continue
            rounding = rec.currency_id.rounding if rec.currency_id else 0.01
            if rec.invoice_amount and float_compare(
                rec.current_receipt_amount or 0.0,
                rec.invoice_amount or 0.0,
                precision_rounding=rounding,
            ) == 1:
                raise UserError("本次收款金额不能超过发票金额。")
            if not rec.request_id:
                continue
            rows = self.sudo().read_group(
                [
                    ("request_id", "=", rec.request_id.id),
                    ("active", "=", True),
                    ("current_receipt_amount", ">", 0.0),
                ],
                ["current_receipt_amount:sum"],
                [],
            )
            current_total = rows[0].get("current_receipt_amount_sum", rows[0].get("current_receipt_amount", 0.0)) if rows else 0.0
            if float_compare(current_total or 0.0, rec.request_id.amount or 0.0, precision_rounding=rounding) == 1:
                raise UserError("收款发票明细的本次收款合计不能超过收款申请金额。")

    def _attachment_counts_by_id(self):
        grouped = {}
        if self.ids:
            data = self.env["ir.attachment"].sudo().read_group(
                [("res_model", "=", self._name), ("res_id", "in", self.ids)],
                ["res_id"],
                ["res_id"],
            )
            grouped = {int(row["res_id"]): int(row.get("__count", row.get("res_id_count", 0))) for row in data}
        return grouped

    def _compute_attachment_count(self):
        grouped = self._attachment_counts_by_id()
        for rec in self:
            rec.attachment_count = grouped.get(rec.id, 0)

    @api.depends("legacy_invoice_line_id", "legacy_receipt_id", "legacy_pid", "legacy_file_bill_id")
    def _compute_visible_attachment_count(self):
        grouped = self._attachment_counts_by_id()
        for rec in self:
            rec.visible_attachment_count = grouped.get(rec.id, 0)

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
