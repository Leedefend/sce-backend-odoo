# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PaymentRequest(models.Model):
    _name = "payment.request"
    _description = "Payment Request"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
    _order = "id desc"

    name = fields.Char(string="申请单号", required=True, default="New", copy=False, tracking=True)
    type = fields.Selection(
        [("pay", "付款"), ("receive", "收款")],
        string="类型",
        default="pay",
        required=True,
        tracking=True,
    )
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="project_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    contract_id = fields.Many2one(
        "construction.contract",
        string="合同",
        domain="[('project_id', '=', project_id)]",
        tracking=True,
    )
    settlement_id = fields.Many2one(
        "sc.settlement.order",
        string="结算单",
        domain="[('project_id', '=', project_id), ('state', '=', 'approve')]",
        tracking=True,
    )
    settlement_currency_id = fields.Many2one(
        "res.currency",
        string="结算币种",
        related="settlement_id.currency_id",
        store=True,
        readonly=True,
    )
    settlement_amount_total = fields.Monetary(
        string="结算总额",
        currency_field="settlement_currency_id",
        related="settlement_id.amount_total",
        store=True,
        readonly=True,
    )
    settlement_paid_amount = fields.Monetary(
        string="已付款金额",
        currency_field="settlement_currency_id",
        related="settlement_id.paid_amount",
        store=True,
        readonly=True,
    )
    settlement_remaining_amount = fields.Monetary(
        string="剩余额度",
        currency_field="settlement_currency_id",
        related="settlement_id.remaining_amount",
        store=True,
        readonly=True,
    )
    settlement_compliance_state = fields.Selection(
        related="settlement_id.compliance_state",
        string="匹配状态",
        readonly=True,
        store=True,
    )
    settlement_compliance_message = fields.Text(
        related="settlement_id.compliance_message",
        string="匹配提示",
        readonly=True,
        store=True,
    )
    settlement_match_blocked = fields.Boolean(
        string="匹配阻断",
        compute="_compute_settlement_match_flags",
        store=False,
    )
    settlement_match_warn = fields.Boolean(
        string="匹配警告",
        compute="_compute_settlement_match_flags",
        store=False,
    )
    settlement_amount_insufficient = fields.Boolean(
        string="结算额度不足",
        compute="_compute_settlement_amount_insufficient",
        store=False,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="往来单位",
        required=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    amount = fields.Monetary(
        string="申请金额",
        currency_field="currency_id",
        required=True,
        tracking=True,
    )
    date_request = fields.Date(
        string="申请日期",
        default=fields.Date.context_today,
    )
    note = fields.Text(string="备注")

    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submit", "提交"),
            ("approve", "审批中"),
            ("approved", "已批准"),
            ("done", "已完成"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = seq.next_by_code("payment.request") or _("Payment Request")
        return super().create(vals_list)

    @api.depends("settlement_id", "settlement_remaining_amount", "amount")
    def _compute_settlement_amount_insufficient(self):
        for rec in self:
            if not rec.settlement_id:
                rec.settlement_amount_insufficient = False
                continue
            remaining = rec.settlement_remaining_amount or 0.0
            request_amount = rec.amount or 0.0
            rec.settlement_amount_insufficient = remaining <= 0 or request_amount > remaining

    @api.depends("settlement_id", "settlement_id.compliance_state")
    def _compute_settlement_match_flags(self):
        for rec in self:
            state = rec.settlement_id.compliance_state if rec.settlement_id else False
            rec.settlement_match_blocked = state == "block"
            rec.settlement_match_warn = state == "warn"

    def _get_bool_param(self, key, default=True):
        val = self.env["ir.config_parameter"].sudo().get_param(key)
        if val is None:
            return default
        return str(val).strip().lower() in ("1", "true", "yes", "y", "on")

    def _check_settlement_compliance_or_raise(self, strict=True):
        self.ensure_one()
        if not self.settlement_id:
            return
        block_on_block = self._get_bool_param("sc.payment.block_on_settlement_block", True)
        block_on_warn = self._get_bool_param("sc.payment.block_on_settlement_warn", False)
        state = self.settlement_id.compliance_state
        msg = self.settlement_id.compliance_message or ""
        if state == "block" and block_on_block:
            raise ValidationError(_("结算单来源匹配未通过，禁止继续：\n%s") % msg)
        if state == "warn" and strict and block_on_warn:
            raise ValidationError(_("结算单来源匹配存在缺失/提示，按策略禁止继续：\n%s") % msg)

    @api.constrains("settlement_id", "type", "project_id", "partner_id", "contract_id")
    def _check_settlement_consistency(self):
        for rec in self:
            settle = rec.settlement_id
            if not settle:
                continue
            if settle.settlement_type == "out" and rec.type != "pay":
                raise ValidationError(_("结算单类型必须与付款申请类型一致。"))
            if settle.settlement_type == "in" and rec.type != "receive":
                raise ValidationError(_("结算单类型必须与付款申请类型一致。"))
            if settle.project_id and rec.project_id and settle.project_id != rec.project_id:
                raise ValidationError(_("结算单项目必须与付款申请项目一致。"))
            if settle.partner_id and rec.partner_id and settle.partner_id != rec.partner_id:
                raise ValidationError(_("结算单往来单位必须与付款申请一致。"))
            if settle.contract_id and rec.contract_id and settle.contract_id != rec.contract_id:
                raise ValidationError(_("结算单合同必须与付款申请一致。"))
            # 额度校验
            if settle.remaining_amount is not None:
                if settle.remaining_amount <= 0:
                    raise ValidationError(
                        _("结算单剩余额度不足，无法提交付款申请（剩余额度：%s）。") % settle.remaining_amount
                    )
                if rec.amount and rec.amount > settle.remaining_amount:
                    raise ValidationError(
                        _("申请金额超过结算单剩余额度，无法提交。（申请金额：%s，剩余额度：%s）")
                        % (rec.amount, settle.remaining_amount)
                    )

    def action_submit(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_finance_user"):
            raise ValidationError(_("你没有提交付款/收款申请的权限。"))
        # 额度校验
        self._check_settlement_consistency()
        for rec in self:
            rec._check_settlement_compliance_or_raise(strict=False)
        self.write(
            {
                "state": "submit",
            }
        )
        self.invalidate_recordset()
        for rec in self:
            company = rec.company_id or self.env.company
            rec.with_context(
                allowed_company_ids=[company.id],
                force_company=company.id,
            ).request_validation()
        self.message_post(body=_("付款/收款申请已提交，进入审批流程。"))

    def action_approve(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager"):
            raise ValidationError(_("你没有审批付款/收款申请的权限。"))
        self.write({"state": "approve"})

    def action_set_approved(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager"):
            raise ValidationError(_("你没有批准付款/收款申请的权限。"))
        self.write({"state": "approved"})

    def action_done(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager"):
            raise ValidationError(_("你没有完成付款/收款申请的权限。"))
        for rec in self:
            if not rec.settlement_id:
                raise ValidationError(_("请先关联已批准的结算单，再完成付款申请。"))
            # 额度校验（再次防守）
            rec._check_settlement_consistency()
            rec._check_settlement_compliance_or_raise(strict=True)
            # 幂等：同一付款申请只允许一条资金流水
            ledger = self.env["sc.treasury.ledger"].sudo().search([("payment_request_id", "=", rec.id)], limit=1)
            if ledger:
                raise ValidationError(_("该付款申请已生成资金流水，不能重复入账。"))
            rec.write({"state": "done"})
            self.env["sc.treasury.ledger"].sudo().with_context(allow_ledger_auto=True).create(
                {
                    "project_id": rec.project_id.id,
                    "partner_id": rec.partner_id.id,
                    "settlement_id": rec.settlement_id.id,
                    "payment_request_id": rec.id,
                    "direction": "out" if rec.type == "pay" else "in",
                    "amount": rec.amount,
                    "currency_id": rec.currency_id.id,
                    "note": _("由付款申请 %s 自动生成") % rec.name,
                }
            )
            # 更新结算单状态（可选：额度打完自动完成）
            settle = rec.settlement_id.sudo()
            settle._compute_paid_amount()
            if settle.remaining_amount <= 0 and settle.state not in ("done", "cancel"):
                settle.write({"state": "done"})

    def action_cancel(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager"):
            raise ValidationError(_("你没有取消付款/收款申请的权限。"))
        self.write({"state": "cancel"})

    def _check_state_from_condition(self):
        self.ensure_one()
        parent = getattr(super(), "_check_state_from_condition", None)
        base_ok = parent() if parent else False
        return base_ok or self.state == "submit"

    def action_on_tier_approved(self):
        for rec in self:
            if rec.state != "submit":
                continue
            rec.write(
                {
                    "state": "approved",
                }
            )
            rec.message_post(body=_("付款/收款申请审批通过。"))

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state != "submit":
                continue
            rec.write(
                {
                    "state": "draft",
                }
            )
            rec.message_post(body=_("付款/收款申请审批驳回：%s") % (reason or _("未填写原因")))
