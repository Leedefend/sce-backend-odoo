# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class OutflowRequestLine(models.Model):
    _name = "payment.request.line"
    _description = "Payment Request Line"
    _order = "request_id, sequence, id"
    _rec_name = "display_name"

    request_id = fields.Many2one(
        "payment.request",
        string="付款申请",
        required=True,
        index=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    legacy_line_id = fields.Char(
        string="旧系统明细ID",
        required=True,
        index=True,
        copy=False,
        help="旧系统 C_ZFSQGL_CB.Id，用于迁移幂等、审计和回滚。",
    )
    legacy_parent_id = fields.Char(
        string="旧系统付款申请ID",
        required=True,
        index=True,
        copy=False,
        help="旧系统 C_ZFSQGL_CB.ZFSQID；正式关联仍以 request_id 为准。",
    )
    legacy_supplier_contract_id = fields.Char(
        string="旧系统供应商合同ID",
        index=True,
        copy=False,
        help="旧系统 C_ZFSQGL_CB.GLYWID，仅作为来源追踪；正式合同关联使用 contract_id。",
    )
    source_document_no = fields.Char(string="旧系统单据编号", copy=False)
    source_line_type = fields.Char(string="旧系统明细类型", copy=False)
    source_counterparty_text = fields.Char(string="旧系统相对方文本", copy=False)
    source_contract_no = fields.Char(string="旧系统合同编号文本", copy=False)
    request_type = fields.Selection(
        related="request_id.type",
        string="申请类型",
        store=True,
        readonly=True,
    )
    project_id = fields.Many2one(
        related="request_id.project_id",
        string="项目",
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="明细往来单位",
        index=True,
        help="旧系统明细可指向不同相对方；缺失或无法确认时可为空。",
    )
    contract_id = fields.Many2one(
        "construction.contract",
        string="明细关联合同",
        index=True,
        domain="[('project_id', '=', project_id)]",
        help="可选合同锚；不得由此推导付款、结算或台账状态。",
    )
    currency_id = fields.Many2one(
        related="request_id.currency_id",
        string="币种",
        store=True,
        readonly=True,
    )
    amount = fields.Monetary(
        string="明细金额",
        currency_field="currency_id",
        required=True,
        help="旧系统 C_ZFSQGL_CB 的正金额事实，首轮不代表已付款或结算完成。",
    )
    paid_before_amount = fields.Monetary(
        string="旧系统已累计支付",
        currency_field="currency_id",
        help="旧系统 YGLZF 追踪值；不作为新系统台账事实。",
    )
    remaining_amount = fields.Monetary(
        string="旧系统剩余金额",
        currency_field="currency_id",
        help="旧系统 SY 追踪值；不作为新系统结算事实。",
    )
    current_pay_amount = fields.Monetary(
        string="旧系统本次支付金额",
        currency_field="currency_id",
        help="旧系统 CCZFJE 追踪值；不作为新系统付款完成事实。",
    )
    note = fields.Text(string="备注")
    import_batch = fields.Char(
        string="导入批次",
        default="legacy_outflow_request_line_asset_v1",
        required=True,
        index=True,
        copy=False,
    )
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "legacy_line_import_batch_unique",
            "unique(legacy_line_id, import_batch)",
            "同一批次中旧系统付款申请明细ID不可重复。",
        )
    ]

    @api.constrains("amount")
    def _check_amount_positive(self):
        for line in self:
            currency = line.currency_id or line.request_id.currency_id
            rounding = currency.rounding if currency else 0.01
            if float_compare(line.amount or 0.0, 0.0, precision_rounding=rounding) <= 0:
                raise ValidationError("付款申请明细金额必须大于 0。")

    @api.constrains("request_id", "contract_id")
    def _check_contract_project(self):
        for line in self:
            if line.contract_id and line.contract_id.project_id != line.request_id.project_id:
                raise ValidationError("付款申请明细合同必须属于同一项目。")
