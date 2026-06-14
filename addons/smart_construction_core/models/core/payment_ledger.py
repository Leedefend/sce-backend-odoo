# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class PaymentLedger(models.Model):
    _name = "payment.ledger"
    _description = "Payment Ledger"
    _order = "paid_at desc, id desc"
    _sc_readonly_navigation_button_methods = {
        "action_open_payment_request",
        "action_open_settlement",
    }

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
        if self.env.context.get("allow_payment_reversal"):
            return
        if not request or request.state != "approved":
            raise UserError("付款申请未处于已批准状态，不能登记付款。")
        if request.material_settlement_id:
            if request.material_settlement_id.state == "confirmed":
                return
            raise UserError("材料结算单未确认，不能登记付款。")
        line_settlements = request._linked_settlement_orders()
        if not request.settlement_id:
            if line_settlements and all(settlement.state in ("approve", "done") for settlement in line_settlements):
                return
            raise UserError("付款申请未关联结算单，不能登记付款。")
        if request.settlement_id.state not in ("approve", "done"):
            ICP = self.env["ir.config_parameter"].sudo()
            soft_gate = bool(self.env.context.get("payment_soft_gate"))
            force_block = str(
                ICP.get_param("sc.payment.force_block.p0_payment_settlement_not_ready", "False") or ""
            ).strip().lower() in ("1", "true", "yes", "on")
            if soft_gate and not force_block:
                return
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

    def action_open_payment_request(self):
        self.ensure_one()
        if not self.payment_request_id:
            raise UserError(_("当前付款台账没有关联付款申请。"))
        return {
            "type": "ir.actions.act_window",
            "name": _("付款申请"),
            "res_model": "payment.request",
            "res_id": self.payment_request_id.id,
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_project_id": self.project_id.id,
                "default_partner_id": self.partner_id.id,
            },
        }

    def action_open_settlement(self):
        self.ensure_one()
        material_settlement = self.payment_request_id.material_settlement_id
        if material_settlement:
            return {
                "type": "ir.actions.act_window",
                "name": _("材料结算"),
                "res_model": "sc.material.settlement",
                "res_id": material_settlement.id,
                "view_mode": "form",
                "target": "current",
                "context": {"default_project_id": self.project_id.id},
            }
        settlement = self.payment_request_id.settlement_id
        if not settlement:
            settlements = self.payment_request_id._linked_settlement_orders()
            if len(settlements) == 1:
                settlement = settlements
            elif settlements:
                raise UserError(_("当前付款申请关联多张结算单，请在付款申请明细中查看。"))
            else:
                raise UserError(_("当前付款台账没有关联结算单或材料结算单。"))
        return {
            "type": "ir.actions.act_window",
            "name": _("结算单"),
            "res_model": "sc.settlement.order",
            "res_id": settlement.id,
            "view_mode": "form",
            "target": "current",
            "context": {"default_project_id": self.project_id.id},
        }
