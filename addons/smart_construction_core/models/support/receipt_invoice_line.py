# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class ScReceiptInvoiceLine(models.Model):
    _name = "sc.receipt.invoice.line"
    _description = "Receipt Invoice Line"
    _order = "request_id, sequence, id"

    request_id = fields.Many2one(
        "payment.request",
        string="收款申请",
        required=True,
        index=True,
        ondelete="cascade",
        domain="[('type', '=', 'receive')]",
        help="收款发票明细所属收款申请；仅承载票据辅助事实，不代表会计凭证。",
    )
    sequence = fields.Integer(default=10, index=True)
    legacy_invoice_line_id = fields.Char(
        string="旧系统发票明细ID",
        required=True,
        index=True,
        copy=False,
    )
    legacy_receipt_id = fields.Char(
        string="旧系统收款ID",
        required=True,
        index=True,
        copy=False,
    )
    legacy_invoice_id = fields.Char(string="旧系统发票ID", index=True, copy=False)
    legacy_invoice_child_id = fields.Char(string="旧系统发票从表ID", index=True, copy=False)
    legacy_pid = fields.Char(string="旧系统PID", index=True, copy=False)
    legacy_file_bill_id = fields.Char(
        string="旧系统附件BILLID",
        index=True,
        copy=False,
        help="后续附件资产包用于匹配 BASE_SYSTEM_FILE.BILLID 的锚点；本批次不导入附件二进制。",
    )

    request_type = fields.Selection(related="request_id.type", string="申请类型", readonly=True, store=True)
    project_id = fields.Many2one(related="request_id.project_id", string="项目", readonly=True, store=True)
    partner_id = fields.Many2one(related="request_id.partner_id", string="往来单位", readonly=True, store=True)
    contract_id = fields.Many2one(related="request_id.contract_id", string="合同", readonly=True, store=True)
    currency_id = fields.Many2one(related="request_id.currency_id", string="币种", readonly=True, store=True)

    invoice_no = fields.Char(string="发票号", index=True)
    invoice_party_name = fields.Char(string="开票对方")
    invoice_issue_company = fields.Char(string="开票单位")
    source_document_no = fields.Char(string="旧系统单据号", index=True)
    source_table_name = fields.Char(string="旧系统来源表")
    amount_source = fields.Char(string="金额来源字段")
    invoice_amount = fields.Monetary(
        string="发票金额",
        currency_field="currency_id",
        required=True,
        help="旧系统 KPJE/CCSKJE/YKPJE 的正金额事实；不代表 account.move 发票。",
    )
    current_receipt_amount = fields.Monetary(
        string="本次收款金额",
        currency_field="currency_id",
        help="旧系统 CCSKJE 追踪值；不作为新系统收款完成事实。",
    )
    invoiced_before_amount = fields.Monetary(
        string="已开票金额",
        currency_field="currency_id",
        help="旧系统 YKPJE 追踪值；不作为新系统会计事实。",
    )

    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_receipt_invoice_line_attachment_rel",
        "invoice_line_id",
        "attachment_id",
        string="附件",
        help="对接 Odoo 原生附件；附件资产包应在本记录外部 ID 存在后再绑定。",
    )
    attachment_count = fields.Integer(string="附件数", compute="_compute_attachment_count", store=False)
    note = fields.Text(string="备注")
    import_batch = fields.Char(
        string="导入批次",
        default="legacy_receipt_invoice_line_asset_v1",
        required=True,
        index=True,
        copy=False,
    )
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "uniq_legacy_line_batch",
            "unique(legacy_invoice_line_id, import_batch)",
            "同一批次中旧系统收款发票明细ID不可重复。",
        )
    ]

    @api.depends("attachment_ids")
    def _compute_attachment_count(self):
        for line in self:
            line.attachment_count = len(line.attachment_ids)

    @api.constrains("request_id")
    def _check_request_is_receive(self):
        for line in self:
            if line.request_id and line.request_id.type != "receive":
                raise ValidationError("收款发票明细只能关联收款申请。")

    @api.constrains("invoice_amount")
    def _check_invoice_amount_positive(self):
        for line in self:
            currency = line.currency_id or line.request_id.currency_id
            rounding = currency.rounding if currency else 0.01
            if float_compare(line.invoice_amount or 0.0, 0.0, precision_rounding=rounding) <= 0:
                raise ValidationError("收款发票明细金额必须大于 0。")
