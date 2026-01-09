# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare

from ..support import operating_metrics as opm
from ..support.state_guard import raise_guard
from ..support.state_machine import ScStateMachine


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
    # 兼容部分搜索条件（有时被带入 account.move 的 move_type 过滤）
    move_type = fields.Selection(
        [("pay", "付款"), ("receive", "收款")],
        string="单据类型(兼容)",
        compute="_compute_move_type",
        store=False,
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
    settlement_amount_payable = fields.Monetary(
        string="可付余额",
        currency_field="settlement_currency_id",
        related="settlement_id.amount_payable",
        store=True,
        readonly=True,
    )
    is_overpay_risk = fields.Boolean(
        string="超付风险",
        compute="_compute_is_overpay_risk",
        store=False,
        help="用于列表高亮：当申请金额超过结算可付余额时为 True。",
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
    ledger_line_ids = fields.One2many(
        "payment.ledger",
        "payment_request_id",
        string="付款记录",
    )
    paid_amount_total = fields.Monetary(
        string="已付款金额",
        currency_field="currency_id",
        compute="_compute_payment_totals",
        store=False,
    )
    unpaid_amount = fields.Monetary(
        string="未付款金额",
        currency_field="currency_id",
        compute="_compute_payment_totals",
        store=False,
    )
    is_fully_paid = fields.Boolean(
        string="已结清",
        compute="_compute_payment_totals",
        store=False,
    )

    state = fields.Selection(
        ScStateMachine.selection(ScStateMachine.PAYMENT_REQUEST),
        string="状态",
        default="draft",
        tracking=True,
    )

    def _get_active_funding_baseline(self, project):
        baseline = self.env["project.funding.baseline"].search(
            [
                ("project_id", "=", project.id),
                ("state", "=", "active"),
            ],
            limit=2,
        )
        if len(baseline) != 1:
            raise UserError("项目必须且只能有一个生效中的资金基准。")
        return baseline

    def _get_reserved_amount(self, project, exclude_ids=None):
        domain = [
            ("project_id", "=", project.id),
            ("type", "=", "pay"),
            ("state", "in", ["submit", "approve", "approved"]),
        ]
        if exclude_ids:
            domain.append(("id", "not in", exclude_ids))
        data = self.read_group(domain, ["amount:sum"], [])
        return data[0].get("amount_sum", data[0].get("amount", 0.0)) if data else 0.0

    def _check_project_funding_gate(self, project, amount, exclude_ids=None):
        if not project or not project.is_funding_ready():
            raise UserError("项目未满足资金承载条件，不能提交付款申请。")
        baseline = self._get_active_funding_baseline(project)
        cap = baseline.total_amount or 0.0
        if cap <= 0.0:
            raise UserError("项目资金基准上限必须大于 0。")
        if (amount or 0.0) <= 0.0:
            raise UserError("申请金额必须大于 0。")
        used = self._get_reserved_amount(project, exclude_ids=exclude_ids)
        rounding = project.company_currency_id.rounding if project.company_currency_id else 0.01
        if float_compare((used or 0.0) + (amount or 0.0), cap, precision_rounding=rounding) == 1:
            raise UserError(
                _("付款申请金额累计超出资金基准上限：\n- 已提交/审批金额：%(used)s\n- 本次申请：%(amount)s\n- 资金上限：%(cap)s")
                % {"used": used, "amount": amount, "cap": cap}
            )

    def _enforce_funding_gate(self, vals=None):
        vals = vals or {}
        for rec in self:
            req_type = vals.get("type", rec.type)
            project_id = vals.get("project_id", rec.project_id.id)
            project = self.env["project.project"].browse(project_id) if project_id else rec.project_id
            amount = vals.get("amount", rec.amount)
            state = vals.get("state", rec.state)
            if req_type == "pay" and state in ("submit", "approve", "approved"):
                self._check_project_funding_gate(project, amount, exclude_ids=rec.ids)

    def _check_project_lifecycle(self, project, target_state):
        if not project:
            return
        if target_state in ("submit", "approve", "approved", "done"):
            if project.lifecycle_state in ("warranty", "closed"):
                raise_guard(
                    "P0_PROJECT_TERMINAL_BLOCKED",
                    f"项目[{project.display_name}]",
                    "提交/审批付款申请",
                    reasons=[f"当前项目状态为 {project.lifecycle_state}"],
                    hints=["请先调整项目状态或完成保修/关闭流程"],
                )

    def _check_settlement_state(self, settlement):
        if not settlement:
            return
        if settlement.state not in ("approve", "done"):
            raise_guard(
                "P0_PAYMENT_SETTLEMENT_NOT_READY",
                f"结算单[{settlement.display_name}]",
                "提交/审批付款申请",
                reasons=[f"结算单状态为 {settlement.state}"],
                hints=["请先完成结算单审批后再提交付款申请"],
            )

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = seq.next_by_code("payment.request") or _("Payment Request")
        records = super().create(vals_list)
        records.filtered(
            lambda r: r.type == "pay" and r.state in ("submit", "approve", "approved")
        )._enforce_funding_gate()
        return records

    def write(self, vals):
        if vals.get("state") == "done":
            self._check_can_done()
        if vals.get("state") in ("approved", "done"):
            for rec in self:
                if rec.validation_status != "validated":
                    raise_guard(
                        "P0_PAYMENT_STATE_BYPASS_BLOCKED",
                        f"付款申请[{rec.display_name}]",
                        "状态变更",
                        reasons=["未完成审批流程"],
                        hints=["请先完成审批后再进入已批准/已完成状态"],
                    )
        res = super().write(vals)
        if any(key in vals for key in ("state", "type", "project_id", "amount")):
            self._enforce_funding_gate(vals)
        return res

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

    def _compute_move_type(self):
        for rec in self:
            rec.move_type = rec.type

    @api.depends("ledger_line_ids.amount", "ledger_line_ids.currency_id", "amount", "currency_id")
    def _compute_payment_totals(self):
        paid_map = {}
        if self.ids:
            data = self.env["payment.ledger"].read_group(
                [("payment_request_id", "in", self.ids)],
                ["amount:sum"],
                ["payment_request_id"],
            )
            for rec in data:
                req_id = rec["payment_request_id"][0]
                paid_map[req_id] = rec.get("amount_sum", rec.get("amount", 0.0)) or 0.0
        for req in self:
            paid_total = paid_map.get(req.id, 0.0)
            req.paid_amount_total = paid_total
            unpaid = (req.amount or 0.0) - paid_total
            req.unpaid_amount = unpaid
            rounding = req.currency_id.rounding if req.currency_id else 0.01
            req.is_fully_paid = float_compare(unpaid, 0.0, precision_rounding=rounding) <= 0

    def _check_can_done(self):
        for rec in self:
            if rec.state != "approved":
                raise ValidationError(_("仅已批准的付款申请可以完成。"))
            rounding = rec.currency_id.rounding if rec.currency_id else 0.01
            data = self.env["payment.ledger"].read_group(
                [("payment_request_id", "=", rec.id)],
                ["amount:sum"],
                [],
            )
            paid_total = data[0].get("amount_sum", data[0].get("amount", 0.0)) if data else 0.0
            unpaid = (rec.amount or 0.0) - paid_total
            if float_compare(unpaid, 0.0, precision_rounding=rounding) == 1:
                raise ValidationError(_("付款未结清，无法完成。"))

    @api.onchange("type", "project_id")
    def _onchange_type_set_contract_domain(self):
        domain = {}
        expected_contract_type = "in" if self.type == "pay" else "out"
        domain["contract_id"] = [
            ("project_id", "=", self.project_id.id),
            ("type", "=", expected_contract_type),
        ]
        if self.contract_id and self.contract_id.type != expected_contract_type:
            self.contract_id = False
        return {"domain": domain}

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
            # 已进入流程的记录在字段更改时仍要守住额度
            if rec.state in ("submit", "approve", "approved", "done"):
                rec._check_settlement_remaining_amount()

    @api.constrains("contract_id", "type")
    def _check_contract_direction(self):
        for rec in self:
            if not rec.contract_id:
                continue
            expected = "in" if rec.type == "pay" else "out"
            if rec.contract_id.type != expected:
                raise ValidationError(_("合同类型必须与申请类型一致。"))

    def _check_settlement_remaining_amount(self):
        """防超付额度硬校验：提交/审批前必须满足结算额度（排除本申请）。"""
        for rec in self:
            settle = rec.settlement_id
            if rec.type != "pay" or not settle:
                continue
            metrics = opm.compute_payment_payable_excluding_self(rec)
            payable = metrics["payable"]
            precision = metrics["precision"]
            amount = rec.amount or 0.0
            if float_compare(payable, 0.0, precision_rounding=precision) <= 0:
                raise_guard(
                    "P0_PAYMENT_OVER_BALANCE",
                    f"付款申请[{rec.display_name}]",
                    "提交/审批付款申请",
                    reasons=[f"结算单剩余额度不足（剩余额度：{payable}）"],
                    hints=["请先调整结算金额或降低付款金额"],
                )
            if float_compare(amount, payable, precision_rounding=precision) == 1:
                raise_guard(
                    "P0_PAYMENT_OVER_BALANCE",
                    f"付款申请[{rec.display_name}]",
                    "提交/审批付款申请",
                    reasons=[f"申请金额 {amount} 超过结算单剩余额度 {payable}"],
                    hints=["请降低付款金额或拆分付款申请"],
                )

    def _check_not_overpay_settlement(self):
        """
        防超付硬校验：付款金额不得超过结算单可付余额。
        """
        for rec in self:
            if rec.type != "pay" or not rec.settlement_id:
                continue
            metrics = opm.compute_payment_payable_excluding_self(rec)
            payable = metrics["payable"]
            precision = metrics["precision"]
            amount = rec.amount or 0.0
            if float_compare(amount, payable, precision_rounding=precision) == 1:
                raise_guard(
                    "P0_PAYMENT_OVER_BALANCE",
                    f"付款申请[{rec.display_name}]",
                    "提交/审批付款申请",
                    reasons=[f"付款金额 {amount} 超出结算单可付余额 {payable}"],
                    hints=["请降低付款金额或先调整结算单余额"],
                )

    def _compute_is_overpay_risk(self):
        """用于 UI 高亮：金额 > 可付余额 时标记风险。"""
        for rec in self:
            if rec.type != "pay" or not rec.settlement_id:
                rec.is_overpay_risk = False
                continue
            metrics = opm.compute_payment_payable_excluding_self(rec)
            payable = metrics["payable"]
            precision = metrics["precision"]
            rec.is_overpay_risk = float_compare(rec.amount or 0.0, payable, precision_rounding=precision) == 1

    def action_submit(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_finance_user"):
            raise ValidationError(_("你没有提交付款/收款申请的权限。"))
        for rec in self:
            if not rec.contract_id:
                raise UserError("请先选择关联合同后再提交付款/收款申请。")
            if rec.contract_id.state == "cancel":
                raise UserError("关联合同已取消，不能提交付款/收款申请。")
            rec._check_project_lifecycle(rec.project_id, "submit")
            rec._check_settlement_state(rec.settlement_id)
        self._enforce_funding_gate({"state": "submit"})
        self._check_settlement_remaining_amount()
        self._check_not_overpay_settlement()
        scope = {
            "res_model": self._name,
            "res_ids": self.ids,
            "project_id": self[:1].project_id.id if self[:1].project_id else False,
            "company_id": self[:1].company_id.id if self[:1].company_id else False,
        }
        self.env["sc.data.validator"].validate_or_raise(scope=scope)
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
            rec.with_company(company).with_context(
                allowed_company_ids=[company.id],
            ).request_validation()
        self.message_post(body=_("付款/收款申请已提交，进入审批流程。"))

    def action_approve(self):
        for rec in self:
            rec._check_project_lifecycle(rec.project_id, "approve")
            rec._check_settlement_state(rec.settlement_id)
        self._enforce_funding_gate({"state": "approve"})
        self._check_settlement_remaining_amount()
        self._check_not_overpay_settlement()
        scope = {
            "res_model": self._name,
            "res_ids": self.ids,
            "project_id": self[:1].project_id.id if self[:1].project_id else False,
            "company_id": self[:1].company_id.id if self[:1].company_id else False,
        }
        self.env["sc.data.validator"].validate_or_raise(scope=scope)
        result = None
        for rec in self:
            if rec.state != "submit":
                continue
            rec.write({"state": "approve"})
            action = rec.validate_tier()
            if action:
                result = action
        return result

    def action_set_approved(self):
        self._enforce_funding_gate({"state": "approved"})
        result = None
        for rec in self:
            action = rec.validate_tier()
            if action:
                result = action
        return result

    def action_done(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager"):
            raise ValidationError(_("你没有完成付款/收款申请的权限。"))
        self._check_can_done()
        for rec in self:
            rec.write({"state": "done"})

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
            rec._check_project_lifecycle(rec.project_id, "approved")
            rec._check_settlement_state(rec.settlement_id)
            rec._enforce_funding_gate({"state": "approved"})
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
                    "state": "rejected",
                }
            )
            rec.message_post(body=_("付款/收款申请审批驳回：%s") % (reason or _("未填写原因")))
