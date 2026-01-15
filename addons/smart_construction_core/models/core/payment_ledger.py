# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class PaymentLedger(models.Model):
    _name = "payment.ledger"
    _description = "Payment Ledger"
    _order = "paid_at desc, id desc"

    _sql_constraints = [
        (
            "uniq_payment_request_id",
            "unique(payment_request_id)",
            "同一付款申请只能生成一条付款台账。",
        ),
    ]

    payment_request_id = fields.Many2one(
        "payment.request",
        string="付款申请",
        required=True,
        ondelete="cascade",
        index=True,
    )
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        related="payment_request_id.project_id",
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="往来单位",
        related="payment_request_id.partner_id",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="payment_request_id.currency_id",
        store=True,
        readonly=True,
    )
    amount = fields.Monetary(
        string="付款金额",
        currency_field="currency_id",
        required=True,
    )
    paid_at = fields.Datetime(
        string="付款时间",
        default=fields.Datetime.now,
        required=True,
    )
    ref = fields.Char(string="外部参考")
    note = fields.Text(string="备注")

    def _check_request_state(self, request):
        if not request or request.state != "approved":
            raise UserError("付款申请未处于已批准状态，不能登记付款。")
        if not request.settlement_id:
            raise UserError("付款申请未关联结算单，不能登记付款。")
        if request.settlement_id.state not in ("approve", "done"):
            raise UserError("结算单未处于已审批状态，不能登记付款。")

    def _check_amount(self):
        for rec in self:
            if (rec.amount or 0.0) <= 0.0:
                raise ValidationError(_("付款金额必须大于 0。"))

    def _check_overpay(self, exclude_ids=None):
        for rec in self:
            req = rec.payment_request_id
            if not req:
                continue
            rounding = req.currency_id.rounding if req.currency_id else 0.01
            domain = [("payment_request_id", "=", req.id)]
            if exclude_ids:
                domain.append(("id", "not in", exclude_ids))
            data = self.env["payment.ledger"].read_group(
                domain,
                ["amount:sum"],
                [],
            )
            paid_total = data[0].get("amount_sum", data[0].get("amount", 0.0)) if data else 0.0
            if float_compare(paid_total, req.amount or 0.0, precision_rounding=rounding) == 1:
                raise UserError("付款累计金额超过申请金额，禁止登记。")

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get("allow_payment_ledger_create"):
            raise UserError("请通过付款申请登记付款记录。")
        request_ids = []
        for vals in vals_list:
            req_id = vals.get("payment_request_id")
            if req_id:
                request_ids.append(req_id)
            request = self.env["payment.request"].browse(req_id)
            self._check_request_state(request)
        if request_ids:
            if len(request_ids) != len(set(request_ids)):
                raise UserError("同一付款申请不能生成多条付款台账。")
            existing = self.search([("payment_request_id", "in", request_ids)], limit=1)
            if existing:
                raise UserError("付款申请已存在付款台账，禁止重复生成。")
        records = super().create(vals_list)
        records._check_amount()
        records._check_overpay()
        return records

    def write(self, vals):
        for rec in self:
            request_id = vals.get("payment_request_id", rec.payment_request_id.id)
            request = self.env["payment.request"].browse(request_id)
            self._check_request_state(request)
        res = super().write(vals)
        self._check_amount()
        self._check_overpay(exclude_ids=self.ids)
        return res

    def unlink(self):
        for rec in self:
            self._check_request_state(rec.payment_request_id)
        return super().unlink()
