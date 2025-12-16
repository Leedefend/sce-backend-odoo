# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..support import operating_metrics as opm


class ScSettlementOrder(models.Model):
    _name = "sc.settlement.order"
    _description = "Settlement Order"
    _order = "id desc"

    name = fields.Char(string="结算单号", required=True, default="新建", copy=False)
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
    )
    contract_id = fields.Many2one(
        "construction.contract",
        string="合同",
        index=True,
    )
    partner_id = fields.Many2one("res.partner", string="往来单位", required=True)
    settlement_type = fields.Selection(
        [("out", "支出结算"), ("in", "收入结算")],
        string="结算类型",
        default="out",
    )
    date_settlement = fields.Date(string="结算日期", default=fields.Date.context_today)
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    amount_total = fields.Monetary(
        string="金额合计",
        currency_field="currency_id",
        compute="_compute_amount_total",
        store=True,
    )
    note = fields.Text(string="备注")

    line_ids = fields.One2many(
        "sc.settlement.order.line",
        "settlement_id",
        string="结算行",
    )
    payment_request_ids = fields.One2many(
        "payment.request",
        "settlement_id",
        string="付款申请",
        readonly=True,
    )
    paid_amount = fields.Monetary(
        string="已付款金额",
        currency_field="currency_id",
        compute="_compute_paid_amounts",
        store=True,
        compute_sudo=True,
    )
    remaining_amount = fields.Monetary(
        string="待付款金额",
        currency_field="currency_id",
        compute="_compute_paid_amounts",
        store=True,
        compute_sudo=True,
    )
    amount_paid = fields.Monetary(
        string="已付累计",
        currency_field="currency_id",
        compute="_compute_paid_amounts",
        store=True,
        compute_sudo=True,
        help="按付款申请的已付口径汇总的金额（状态见 _get_paid_payment_states）。",
    )
    amount_payable = fields.Monetary(
        string="可付余额",
        currency_field="currency_id",
        compute="_compute_paid_amounts",
        store=True,
        compute_sudo=True,
        help="可付余额 = 结算金额 - 已付累计；为负时代表存在超付风险。",
    )
    purchase_order_ids = fields.Many2many(
        comodel_name="purchase.order",
        relation="sc_settlement_order_purchase_rel",
        column1="settlement_id",
        column2="purchase_id",
        string="采购订单",
        help="与本结算单关联的采购订单（Phase-3 三单匹配基础版）。",
    )
    invoice_ref = fields.Char(string="发票号/票据号")
    invoice_amount = fields.Monetary(string="发票金额", currency_field="currency_id")
    invoice_date = fields.Date(string="发票日期")

    compliance_contract_ok = fields.Boolean(string="合同一致", compute="_compute_compliance_summary", store=False)
    compliance_state = fields.Selection(
        [("ok", "通过"), ("warn", "警告"), ("block", "阻断")],
        string="匹配状态",
        compute="_compute_compliance_summary",
        store=False,
    )
    compliance_message = fields.Text(string="匹配提示", compute="_compute_compliance_summary", store=False)

    @api.depends(
        "line_ids.amount",
        "payment_request_ids",
        "payment_request_ids.state",
        "payment_request_ids.amount",
    )
    def _compute_paid_amounts(self):
        """Phase7-1: 结算单的已付/可付口径，统一由 operating_metrics 提供。"""
        paid_map = opm.settlement_paid_map(self.env, self.ids)
        for order in self:
            total = order.amount_total or 0.0
            paid = paid_map.get(order.id, 0.0)
            remaining = total - paid
            order.paid_amount = paid
            order.remaining_amount = remaining
            order.amount_paid = paid
            order.amount_payable = remaining

    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submit", "提交"),
            ("approve", "批准"),
            ("done", "完成"),
            ("cancel", "取消"),
        ],
        string="状态",
        default="draft",
    )

    @api.depends("line_ids.amount")
    def _compute_amount_total(self):
        for order in self:
            order.amount_total = sum(order.line_ids.mapped("amount"))

    @api.constrains("purchase_order_ids", "partner_id")
    def _check_po_vendor_consistency(self):
        for rec in self:
            if not rec.purchase_order_ids or not rec.partner_id:
                continue
            wrong = rec.purchase_order_ids.filtered(lambda po: po.partner_id.id != rec.partner_id.id)
            if wrong:
                raise ValidationError(
                    _("采购订单供应商与结算单往来单位不一致：%s")
                    % ", ".join(wrong.mapped("name")[:10])
                )

    @api.depends(
        "contract_id",
        "payment_request_ids.contract_id",
        "purchase_order_ids",
        "purchase_order_ids.state",
        "purchase_order_ids.partner_id",
        "partner_id",
        "invoice_ref",
        "invoice_amount",
        "invoice_date",
        "amount_total",
    )
    def _compute_compliance_summary(self):
        for rec in self:
            missing = []
            mismatch = []
            warnings = []

            # 合同一致性
            if rec.contract_id and rec.payment_request_ids:
                wrong = rec.payment_request_ids.filtered(
                    lambda r: r.contract_id and r.contract_id.id != rec.contract_id.id
                )
                if wrong:
                    mismatch.append(_("付款申请合同与结算单不一致"))

            # 采购来源
            if not rec.purchase_order_ids:
                missing.append(_("采购订单"))
            else:
                bad_state = rec.purchase_order_ids.filtered(lambda po: po.state not in ("purchase", "done"))
                if bad_state:
                    mismatch.append(_("采购订单状态不合规"))
                # 供应商不一致由 constrains 硬拦，这里不重复

            # 发票占位（软提示）
            if not rec.invoice_ref:
                warnings.append(_("缺少发票信息（占位）"))
            else:
                if rec.invoice_amount and rec.amount_total and rec.invoice_amount < rec.amount_total:
                    warnings.append(_("发票金额小于结算金额"))

            # 汇总状态：block > warn > ok
            if mismatch:
                rec.compliance_state = "block"
            elif missing or warnings:
                rec.compliance_state = "warn"
            else:
                rec.compliance_state = "ok"

            lines = []
            if mismatch:
                lines.append(_("【阻断】") + "；".join(mismatch))
            if missing:
                lines.append(_("【缺失】") + "；".join(missing))
            if warnings:
                lines.append(_("【提示】") + "；".join(warnings))
            rec.compliance_message = "\n".join(lines) if lines else _("匹配正常")
            rec.compliance_contract_ok = not bool(mismatch)

    def _get_bool_param(self, key, default=True):
        val = self.env["ir.config_parameter"].sudo().get_param(key)
        if val is None:
            return default
        return str(val).strip().lower() in ("1", "true", "yes", "y", "on")

    def _check_contract_consistency_or_raise(self, strict=True):
        """
        strict=True 用于 approve 时强制校验；strict=False 受参数控制。
        """
        self.ensure_one()
        hard_block = self._get_bool_param("sc.settlement.check_contract.hard_block", True)
        if not hard_block and not strict:
            return
        if self.contract_id and self.payment_request_ids:
            wrong = self.payment_request_ids.filtered(
                lambda r: r.contract_id and r.contract_id.id != self.contract_id.id
            )
            if wrong:
                raise UserError(
                    _("合同不一致，禁止继续操作。请检查结算单合同与关联付款申请合同。")
                )

    def _check_purchase_orders_or_raise(self, strict=True):
        """
        strict=True 用于 approve 时强制校验；strict=False 受参数控制。
        """
        self.ensure_one()
        hard_block = self._get_bool_param("sc.settlement.check_purchase.hard_block", True)
        if not hard_block and not strict:
            return

        if not self.purchase_order_ids:
            if strict:
                raise UserError(_("缺少采购订单来源，无法批准结算单。"))
            return

        bad_state = self.purchase_order_ids.filtered(lambda po: po.state not in ("purchase", "done"))
        if bad_state:
            raise UserError(
                _("采购订单状态不合规（需为 已采购/完成），问题订单：%s")
                % ", ".join(bad_state.mapped("name")[:10])
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "新建") in (False, "新建"):
                seq = self.env["ir.sequence"].next_by_code("sc.settlement.order")
                vals["name"] = seq or _("Settlement")
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            rec._check_contract_consistency_or_raise(strict=False)
            rec._check_purchase_orders_or_raise(strict=False)
        self.env["sc.data.validator"].validate_or_raise()
        self.write({"state": "submit"})

    def action_approve(self):
        for rec in self:
            rec._check_contract_consistency_or_raise(strict=True)
            rec._check_purchase_orders_or_raise(strict=True)
        self.env["sc.data.validator"].validate_or_raise()
        self.write({"state": "approve"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancel"})


class ScSettlementOrderLine(models.Model):
    _name = "sc.settlement.order.line"
    _description = "Settlement Order Line"
    _order = "id"

    settlement_id = fields.Many2one(
        "sc.settlement.order",
        string="结算单",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(string="名称", required=True)
    qty = fields.Float(string="数量", default=1.0, digits="Product Unit of Measure")
    price_unit = fields.Monetary(string="单价", currency_field="currency_id", default=0.0)
    amount = fields.Monetary(string="金额", currency_field="currency_id", compute="_compute_amount", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="settlement_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.depends("qty", "price_unit")
    def _compute_amount(self):
        for line in self:
            line.amount = (line.qty or 0.0) * (line.price_unit or 0.0)
