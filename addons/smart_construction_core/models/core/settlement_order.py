# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..support import operating_metrics as opm
from ..support.state_guard import raise_guard
from ..support.state_machine import ScStateMachine


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
        ScStateMachine.selection(ScStateMachine.SETTLEMENT_ORDER),
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
            rec._check_line_contracts_or_raise()
            rec._check_contract_consistency_or_raise(strict=False)
            rec._check_purchase_orders_or_raise(strict=False)
        self.env["sc.data.validator"].validate_or_raise()
        self.write({"state": "submit"})

    def action_approve(self):
        for rec in self:
            rec._check_line_contracts_or_raise()
            rec._check_contract_consistency_or_raise(strict=True)
            rec._check_purchase_orders_or_raise(strict=True)
        self.env["sc.data.validator"].validate_or_raise()
        self.write({"state": "approve"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self._check_payments_before_cancel()
        self.write({"state": "cancel"})

    def _check_payments_before_cancel(self):
        Payment = self.env["payment.request"]
        for rec in self:
            count = Payment.search_count(
                [
                    ("settlement_id", "=", rec.id),
                    ("state", "in", ["approve", "approved", "done"]),
                ]
            )
            if count:
                raise_guard(
                    "P0_SETTLEMENT_CANCEL_BLOCKED",
                    f"结算单[{rec.display_name}]",
                    _("作废结算单"),
                    reasons=[_("已关联付款申请：%s 条") % count],
                    hints=[_("请先取消/完成关联付款申请后再作废结算单")],
                )

    def write(self, vals):
        if vals.get("state") == "cancel":
            self._check_payments_before_cancel()
        return super().write(vals)

    # ------------------------------------------------------------------
    # 合同联动：选合同后自动带出项目/公司/币种/往来单位/结算类型
    # ------------------------------------------------------------------
    @api.onchange("contract_id")
    def _onchange_contract_id_fill_header(self):
        for rec in self:
            c = rec.contract_id
            if not c:
                continue
            # 项目/公司/币种
            if not rec.project_id and getattr(c, "project_id", False):
                rec.project_id = c.project_id.id
            if not rec.company_id and getattr(c, "company_id", False):
                rec.company_id = c.company_id.id
            if not rec.currency_id:
                cur = getattr(c, "currency_id", False) or (rec.company_id.currency_id if rec.company_id else False)
                if cur:
                    rec.currency_id = cur.id
            # 往来单位（合同相对方）
            partner = getattr(c, "partner_id", False)
            if partner and not rec.partner_id:
                rec.partner_id = partner.id
            # 结算类型：收入合同->收入结算(in)，支出合同->支出结算(out)
            if getattr(c, "type", False) and not rec.settlement_type:
                rec.settlement_type = "in" if c.type == "out" else "out"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "新建") in (False, "新建"):
                seq = self.env["ir.sequence"].next_by_code("sc.settlement.order")
                vals["name"] = seq or _("Settlement")
        records = super().create(vals_list)
        records._apply_contract_defaults_if_needed()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "contract_id" in vals:
            self._apply_contract_defaults_if_needed()
        return res

    def _apply_contract_defaults_if_needed(self):
        """兜底：导入/批量写入绕过 onchange 时也能带出合同信息。"""
        for rec in self:
            c = rec.contract_id
            if not c:
                continue
            updates = {}
            if not rec.project_id and getattr(c, "project_id", False):
                updates["project_id"] = c.project_id.id
            if not rec.company_id and getattr(c, "company_id", False):
                updates["company_id"] = c.company_id.id
            if not rec.currency_id:
                cur = getattr(c, "currency_id", False) or (updates.get("company_id") and self.env["res.company"].browse(updates["company_id"]).currency_id)
                if cur:
                    updates["currency_id"] = cur.id
            partner = getattr(c, "partner_id", False)
            if partner and not rec.partner_id:
                updates["partner_id"] = partner.id
            if not rec.settlement_type and getattr(c, "type", False):
                updates["settlement_type"] = "in" if c.type == "out" else "out"
            if updates:
                rec.with_context(skip_onchange=True).sudo().write(updates)

    def _check_line_contracts_or_raise(self):
        for rec in self:
            for line in rec.line_ids:
                if not line.contract_id:
                    raise_guard(
                        "SETTLEMENT_CONTRACT_REQUIRED",
                        f"结算单[{rec.display_name}]",
                        _("校验结算行合同"),
                        reasons=[_("结算行未绑定合同")],
                    )
                if line.contract_id and rec.project_id:
                    if line.contract_id.project_id.id != rec.project_id.id:
                        raise_guard(
                            "SETTLEMENT_CONTRACT_MISMATCH",
                            f"结算单[{rec.display_name}]",
                            _("校验结算行合同"),
                            reasons=[_("合同项目与结算单项目不一致")],
                        )


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
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        related="settlement_id.project_id",
        store=True,
        readonly=True,
    )
    contract_id = fields.Many2one(
        "construction.contract",
        string="合同",
        index=True,
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

    def _ensure_manager_role(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_project_manager"):
            raise_guard(
                "SETTLEMENT_CONTRACT_REQUIRED",
                "Settlement Line",
                "Change Contract",
                reasons=["manager role required"],
            )

    def _ensure_contract_required(self, contract_id=None):
        if not contract_id:
            raise_guard(
                "SETTLEMENT_CONTRACT_REQUIRED",
                "Settlement Line",
                "Bind Contract",
                reasons=["contract_id is required"],
            )

    def _ensure_contract_match(self, contract_id, project_id):
        if not contract_id or not project_id:
            return
        contract = self.env["construction.contract"].browse(contract_id)
        if contract.project_id and contract.project_id.id != project_id:
            raise_guard(
                "SETTLEMENT_CONTRACT_MISMATCH",
                "Settlement Line",
                "Bind Contract",
                reasons=["contract project mismatch"],
            )

    def _audit_contract(self, event_code, before_id, after_id, reason=None, require_reason=False):
        Audit = self.env["sc.audit.log"]
        for rec in self:
            Audit.write_event(
                event_code=event_code,
                model=rec._name,
                res_id=rec.id,
                action=event_code,
                before={"contract_id": before_id},
                after={"contract_id": after_id},
                reason=reason,
                require_reason=require_reason,
                project_id=rec.project_id.id if rec.project_id else False,
                company_id=rec.settlement_id.company_id.id if rec.settlement_id else False,
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("contract_id") and vals.get("settlement_id"):
                settlement = self.env["sc.settlement.order"].browse(vals.get("settlement_id"))
                if settlement.contract_id:
                    vals["contract_id"] = settlement.contract_id.id
            self._ensure_contract_required(vals.get("contract_id"))
            if vals.get("settlement_id"):
                settlement = self.env["sc.settlement.order"].browse(vals.get("settlement_id"))
                self._ensure_contract_match(vals.get("contract_id"), settlement.project_id.id)
        return super().create(vals_list)

    def write(self, vals):
        if "contract_id" in vals and not self.env.context.get("allow_contract_change"):
            raise_guard(
                "SETTLEMENT_CONTRACT_REQUIRED",
                "Settlement Line",
                "Change Contract",
                reasons=["use action_bind_contract/action_unbind_contract"],
            )
        if "contract_id" in vals:
            if not vals.get("contract_id") and not self.env.context.get("allow_contract_change"):
                self._ensure_contract_required(False)
        res = super().write(vals)
        if "contract_id" in vals:
            for rec in self:
                if rec.contract_id:
                    rec._ensure_contract_required(rec.contract_id.id)
                    rec._ensure_contract_match(rec.contract_id.id, rec.project_id.id)
                elif not self.env.context.get("allow_contract_change"):
                    rec._ensure_contract_required(False)
        return res

    def action_bind_contract(self, contract_id, reason=None):
        self.ensure_one()
        self._ensure_contract_required(contract_id)
        self._ensure_contract_match(contract_id, self.project_id.id)
        before_id = self.contract_id.id if self.contract_id else False
        require_reason = False
        if before_id and before_id != contract_id:
            self._ensure_manager_role()
            require_reason = True
        if require_reason and not reason:
            raise_guard(
                "AUDIT_REASON_REQUIRED",
                "Audit",
                "Write",
                reasons=["reason is required"],
            )
        self.with_context(allow_contract_change=True).write({"contract_id": contract_id})
        self._audit_contract(
            "contract_bound",
            before_id=before_id,
            after_id=contract_id,
            reason=reason,
            require_reason=require_reason,
        )
        return True

    def action_unbind_contract(self, reason=None):
        self.ensure_one()
        self._ensure_manager_role()
        if not reason:
            raise_guard(
                "AUDIT_REASON_REQUIRED",
                "Audit",
                "Write",
                reasons=["reason is required"],
            )
        before_id = self.contract_id.id if self.contract_id else False
        self.with_context(allow_contract_change=True).write({"contract_id": False})
        self._audit_contract(
            "contract_unbound",
            before_id=before_id,
            after_id=False,
            reason=reason,
            require_reason=True,
        )
        return True
