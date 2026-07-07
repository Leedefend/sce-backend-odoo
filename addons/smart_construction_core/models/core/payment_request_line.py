# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class PaymentRequestLine(models.Model):
    _name = "payment.request.line"
    _description = "Payment Request Line"
    _inherit = ["sc.delete.guard.mixin"]
    _order = "request_id desc, sequence asc, id asc"

    request_id = fields.Many2one(
        "payment.request",
        string="付款申请",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(string="序号", default=10, index=True)
    legacy_line_id = fields.Char(string="历史明细ID", required=True, copy=False, index=True)
    legacy_parent_id = fields.Char(string="历史父单ID", required=True, copy=False, index=True)
    legacy_supplier_contract_id = fields.Char(string="历史供应合同ID", copy=False)
    source_document_no = fields.Char(string="来源单号")
    source_line_type = fields.Char(string="来源类型")
    source_counterparty_text = fields.Char(string="来源往来方")
    source_contract_no = fields.Char(string="来源合同号")
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
        string="供应合同",
        index=True,
    )
    settlement_id = fields.Many2one(
        "sc.settlement.order",
        string="结算单",
        index=True,
        ondelete="set null",
        help="历史付款申请明细关联的结算单；用于保留一张付款申请对应多张结算单的历史事实。",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="request_id.currency_id",
        store=True,
        readonly=True,
    )
    amount = fields.Monetary(string="明细金额", currency_field="currency_id", required=True)
    paid_before_amount = fields.Monetary(string="历史已付", currency_field="currency_id")
    remaining_amount = fields.Monetary(string="历史未付", currency_field="currency_id")
    current_pay_amount = fields.Monetary(string="本次申请", currency_field="currency_id")
    note = fields.Text(string="备注")
    import_batch = fields.Char(string="导入批次", copy=False)
    active = fields.Boolean(default=True)
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

    def unlink(self):
        locked = self.filtered(lambda rec: rec.request_id and rec.request_id.state not in ("draft", "cancel"))
        if locked:
            raise UserError("仅草稿或已取消付款申请的明细允许删除。")
        self._sc_raise_delete_blockers(action_label="删除付款申请明细")
        return super().unlink()
