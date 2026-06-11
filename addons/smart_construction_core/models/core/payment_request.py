# -*- coding: utf-8 -*-
import logging
import re
from decimal import Decimal, ROUND_HALF_UP

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare

from ..support import operating_metrics as opm
from ..support.state_guard import raise_guard
from ..support.state_machine import ScStateMachine

_logger = logging.getLogger(__name__)


def _amount_to_chinese_upper(value):
    amount = Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount == 0:
        return "零元整"
    prefix = "负" if amount < 0 else ""
    cents = int(abs(amount) * 100)
    integer = cents // 100
    jiao = cents // 10 % 10
    fen = cents % 10
    digits = "零壹贰叁肆伍陆柒捌玖"
    units = ["", "拾", "佰", "仟"]
    section_units = ["", "万", "亿", "兆"]

    def section_to_text(section):
        text = ""
        zero = False
        for index, char in enumerate(f"{section:04d}"):
            digit = int(char)
            if digit:
                if zero:
                    text += digits[0]
                    zero = False
                text += digits[digit] + units[3 - index]
            elif text:
                zero = True
        return text

    parts = []
    section_index = 0
    need_zero = False
    while integer:
        section = integer % 10000
        if section:
            text = section_to_text(section) + section_units[section_index]
            if need_zero:
                parts.insert(0, digits[0])
            parts.insert(0, text)
            need_zero = section < 1000
        elif parts:
            need_zero = True
        integer //= 10000
        section_index += 1

    result = prefix + "".join(parts).rstrip(digits[0]) + "元"
    if jiao:
        result += digits[jiao] + "角"
    if fen:
        result += digits[fen] + "分"
    if not jiao and not fen:
        result += "整"
    return result


class PaymentRequest(models.Model):
    _name = "payment.request"
    _description = "Payment Request"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "tier.validation",
        "sc.delete.guard.mixin",
        "sc.company.contractor.responsibility.context.mixin",
    ]
    _order = "id desc"
    _sc_delete_guard_blocker_models = (
        "sc.material.rental.order",
    )

    name = fields.Char(string="申请单号", required=True, default="New", copy=False, tracking=True)
    type = fields.Selection(
        [("pay", "付款"), ("receive", "收款")],
        string="类型",
        default="pay",
        required=True,
        tracking=True,
    )
    payment_flow_label = fields.Char(string="办理事项", compute="_compute_payment_flow_label")
    receipt_type = fields.Char(
        string="登记类型",
        index=True,
        tracking=True,
        help="收款申请来源登记类型，历史数据来自 C_JFHKLR.type。",
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
    operation_strategy = fields.Selection(
        related="project_id.operation_strategy",
        string="经营方式",
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
    material_settlement_id = fields.Many2one(
        "sc.material.settlement",
        string="材料结算单",
        domain="[('project_id', '=', project_id), ('state', '=', 'confirmed')]",
        index=True,
        tracking=True,
        ondelete="set null",
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
        string="结算已付款",
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
    amount_uppercase = fields.Char(
        string="金额大写",
        compute="_compute_amount_uppercase",
        store=True,
        readonly=True,
        index=True,
    )
    accepted_amount_uppercase = fields.Char(
        string="金额大写",
        index=True,
        tracking=True,
        help="用户确认验收口径的金额大写；用于历史数据延续和后续业务办理。",
    )
    legacy_visible_document_no = fields.Char(
        string="历史可见单据编号",
        readonly=True,
        index=True,
    )
    legacy_visible_project_name = fields.Char(
        string="历史可见项目名称",
        readonly=True,
        index=True,
    )
    legacy_visible_request_date = fields.Char(
        string="历史可见申请日期",
        readonly=True,
    )
    legacy_visible_payee_unit = fields.Char(
        string="历史可见收款单位",
        readonly=True,
        index=True,
    )
    legacy_visible_actual_payee_unit = fields.Char(
        string="历史可见实际收款单位",
        readonly=True,
        index=True,
    )
    legacy_visible_payer_unit = fields.Char(
        string="历史可见付款单位",
        readonly=True,
        index=True,
    )
    legacy_visible_request_amount = fields.Char(
        string="历史申请付款金额",
        readonly=True,
    )
    cost_category_name = fields.Char(
        string="成本分类名称",
        compute="_compute_reconciliation_summary",
        store=True,
        readonly=True,
        index=True,
    )
    legacy_visible_cost_category_name = fields.Char(
        string="历史成本分类名称",
        readonly=True,
        index=True,
    )
    legacy_visible_cost_type = fields.Char(
        string="历史类型（成本）",
        readonly=True,
        index=True,
    )
    legacy_visible_remark = fields.Text(
        string="历史备注",
        readonly=True,
    )
    legacy_visible_amount_uppercase = fields.Char(
        string="历史金额大写",
        readonly=True,
    )
    legacy_visible_actual_paid_amount = fields.Char(
        string="历史实际付款金额",
        readonly=True,
    )
    legacy_visible_available_balance = fields.Char(
        string="历史可用余额",
        readonly=True,
    )
    legacy_payment_account_name = fields.Char(
        string="历史付款户名",
        readonly=True,
        index=True,
    )
    legacy_payment_account_no = fields.Char(
        string="历史付款账号",
        readonly=True,
        index=True,
    )
    legacy_payee_account_name = fields.Char(
        string="历史收款户名",
        readonly=True,
        index=True,
    )
    legacy_payee_bank_name = fields.Char(
        string="历史收款开户行",
        readonly=True,
        index=True,
    )
    legacy_payee_account_no = fields.Char(
        string="历史收款账号",
        readonly=True,
        index=True,
    )
    actual_payee_unit = fields.Char(
        string="实际收款单位",
        index=True,
        tracking=True,
        help="付款申请自身确认的实际收款单位；历史迁移数据来自用户验收面。",
    )
    payer_unit = fields.Char(
        string="付款单位",
        index=True,
        tracking=True,
        help="付款申请自身确认的付款单位；历史迁移数据来自用户验收面。",
    )
    payment_account_name = fields.Char(
        string="户名",
        index=True,
        tracking=True,
        help="付款申请自身确认的收款户名；不覆盖往来单位主数据。",
    )
    payment_bank_name = fields.Char(
        string="开户行",
        index=True,
        tracking=True,
        help="付款申请自身确认的收款开户行；不覆盖往来单位主数据。",
    )
    payment_account_no = fields.Char(
        string="账号",
        index=True,
        tracking=True,
        help="付款申请自身确认的收款账号；不覆盖往来单位主数据。",
    )
    legacy_visible_writer = fields.Char(
        string="历史填写人",
        readonly=True,
        index=True,
    )
    legacy_visible_attachment = fields.Char(
        string="历史可见附件",
        readonly=True,
    )
    partner_account_name = fields.Char(
        string="户名",
        related="partner_id.sc_account_name",
        store=True,
        readonly=True,
        index=True,
    )
    partner_bank_name = fields.Char(
        string="开户行",
        related="partner_id.sc_bank_name",
        store=True,
        readonly=True,
        index=True,
    )
    partner_bank_account = fields.Char(
        string="账号",
        related="partner_id.sc_bank_account",
        store=True,
        readonly=True,
        index=True,
    )
    date_request = fields.Date(
        string="单据日期",
        default=fields.Date.context_today,
    )
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史单据状态", index=True, readonly=True)
    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True, readonly=True)
    creator_name = fields.Char(string="历史录入人", index=True, readonly=True)
    created_time = fields.Datetime(string="历史录入时间", index=True, readonly=True)
    note = fields.Text(string="备注")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "payment_request_attachment_rel",
        "request_id",
        "attachment_id",
        string="附件",
    )
    ledger_line_ids = fields.One2many(
        "payment.ledger",
        "payment_request_id",
        string="付款记录",
    )
    outflow_line_ids = fields.One2many(
        "payment.request.line",
        "request_id",
        string="付款申请明细",
    )
    receipt_invoice_line_ids = fields.One2many(
        "sc.receipt.invoice.line",
        "request_id",
        string="收款发票明细",
    )
    paid_amount_total = fields.Monetary(
        string="已付款合计",
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

    @api.depends("type", "receipt_type", "legacy_source_table", "cost_category_name", "material_settlement_id")
    def _compute_payment_flow_label(self):
        for record in self:
            if record.type == "receive":
                record.payment_flow_label = record.receipt_type or _("收款申请")
            elif record.material_settlement_id:
                record.payment_flow_label = _("材料结算付款申请")
            elif record.legacy_source_table == "T_FK_Supplier":
                record.payment_flow_label = _("往来单位付款申请")
            elif record.legacy_source_table == "SCBSLY_DIRECT_PAYMENT_APPLY_ACCEPTED":
                record.payment_flow_label = _("支付申请")
            elif record.cost_category_name:
                record.payment_flow_label = _("付款申请：%s") % record.cost_category_name
            else:
                record.payment_flow_label = _("付款申请")

    @api.depends("outflow_line_ids.source_line_type", "legacy_visible_cost_category_name")
    def _compute_reconciliation_summary(self):
        for record in self:
            line_types = [
                line_type
                for line_type in record.outflow_line_ids.mapped("source_line_type")
                if line_type
            ]
            unique_types = sorted(set(line_types))
            record.cost_category_name = " / ".join(unique_types[:5]) or record.legacy_visible_cost_category_name

    @api.depends("amount")
    def _compute_amount_uppercase(self):
        for record in self:
            record.amount_uppercase = _amount_to_chinese_upper(record.amount)

    @api.model
    def _context_project_id(self):
        project_id = self.env.context.get("default_project_id") or self.env.context.get("current_project_id")
        try:
            return int(project_id) if project_id else False
        except (TypeError, ValueError):
            return False

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        project_id = res.get("project_id") or self._context_project_id()
        if project_id and "project_id" in fields_list:
            res["project_id"] = project_id
        if project_id and "operation_strategy" in fields_list and not res.get("operation_strategy"):
            project = self.env["project.project"].browse(project_id).exists()
            if project:
                res["operation_strategy"] = project.operation_strategy
        return res

    def _message_post_non_blocking(self, body):
        for rec in self:
            try:
                rec.message_post(body=body)
            except Exception as exc:
                _logger.warning(
                    "Skip payment.request chatter message for %s: %s",
                    rec.display_name,
                    exc,
                )

    def action_create_payment_execution(self):
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_sc_payment_execution").read()[0]
        action["view_mode"] = "form"
        action["views"] = [(False, "form")]
        action["context"] = {
            **dict(self.env.context or {}),
            "default_payment_request_id": self.id,
            "default_project_id": self.project_id.id,
            "default_partner_id": self.partner_id.id,
            "default_contract_id": self.contract_id.id,
            "default_document_no": self.name,
            "default_planned_amount": self.amount or 0.0,
            "default_paid_amount": self.amount or 0.0,
            "default_currency_id": self.currency_id.id,
        }
        return action

    def unlink(self):
        locked = self.filtered(lambda rec: rec.state not in ("draft", "cancel"))
        if locked:
            raise UserError("仅草稿或已取消的付款申请允许删除。")
        self._sc_raise_delete_blockers(action_label="删除付款申请")
        return super().unlink()

    def _get_active_funding_baseline(self, project):
        baseline = self.env["project.funding.baseline"].sudo().search(
            [
                ("project_id", "=", project.id),
                ("state", "=", "active"),
            ],
            limit=2,
        )
        if len(baseline) != 1:
            raise_guard(
                "P0_PAYMENT_FUNDING_BASELINE_INVALID",
                f"项目[{project.display_name}]",
                "提交付款申请",
                reasons=["项目必须且只能有一个生效中的资金基准"],
                hints=["请先修正项目资金基准后再提交付款申请"],
            )
        return baseline

    def _get_reserved_amount(self, project, exclude_ids=None):
        domain = [
            ("project_id", "=", project.id),
            ("type", "=", "pay"),
            ("state", "in", ["submit", "approve", "approved"]),
        ]
        if exclude_ids:
            domain.append(("id", "not in", exclude_ids))
        data = self.sudo().read_group(domain, ["amount:sum"], [])
        return data[0].get("amount_sum", data[0].get("amount", 0.0)) if data else 0.0

    def _check_project_funding_gate(self, project, amount, exclude_ids=None):
        if not project or not project.is_funding_ready():
            raise_guard(
                "P0_PAYMENT_FUNDING_NOT_READY",
                f"项目[{project.display_name if project else '-'}]",
                "提交付款申请",
                reasons=["项目未满足资金承载条件"],
                hints=["请先完成项目资金承载设置后再提交付款申请"],
            )
        baseline = self._get_active_funding_baseline(project)
        cap = baseline.total_amount or 0.0
        if cap <= 0.0:
            raise_guard(
                "P0_PAYMENT_FUNDING_BASELINE_INVALID",
                f"项目[{project.display_name}]",
                "提交付款申请",
                reasons=["项目资金基准上限必须大于 0"],
                hints=["请先修正项目资金基准后再提交付款申请"],
            )
        if (amount or 0.0) <= 0.0:
            raise UserError("申请金额必须大于 0。")
        used = self._get_reserved_amount(project, exclude_ids=exclude_ids)
        rounding = project.company_currency_id.rounding if project.company_currency_id else 0.01
        if float_compare((used or 0.0) + (amount or 0.0), cap, precision_rounding=rounding) == 1:
            raise_guard(
                "P0_PAYMENT_FUNDING_CAP_EXCEEDED",
                f"项目[{project.display_name}]",
                "提交付款申请",
                reasons=[
                    _("付款申请金额累计超出资金基准上限"),
                    _("已提交/审批金额：%(used)s") % {"used": used},
                    _("本次申请：%(amount)s") % {"amount": amount},
                    _("资金上限：%(cap)s") % {"cap": cap},
                ],
                hints=["请调整付款金额或项目资金基准后再提交付款申请"],
            )

    def _enforce_funding_gate(self, vals=None):
        if self.env.context.get("payment_soft_gate") and not (
            self._payment_force_block_enabled("P0_PAYMENT_FUNDING_NOT_READY")
            or self._payment_force_block_enabled("P0_PAYMENT_FUNDING_BASELINE_INVALID")
            or self._payment_force_block_enabled("P0_PAYMENT_FUNDING_CAP_EXCEEDED")
        ):
            return
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
            project_id = self._context_project_id()
            if project_id:
                vals.setdefault("project_id", project_id)
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = seq.next_by_code("payment.request") or _("Payment Request")
        records = super().create(vals_list)
        records.filtered(
            lambda r: r.type == "pay" and r.state in ("submit", "approve", "approved")
        )._enforce_funding_gate()
        return records

    def write(self, vals):
        if "state" in vals and not self.env.context.get("allow_transition"):
            sample = self[:1]
            raise_guard(
                "PAYMENT_GUARD_DIRECT_STATE_WRITE",
                f"付款申请[{sample.display_name if sample else ''}]",
                "状态变更",
                reasons=["state change must use transition methods"],
            )
        if vals.get("state") == "done":
            self._check_can_done()
        tier_validation_callback = self.env.context.get("tier_validation_callback")
        if vals.get("state") in ("approved", "done") and not tier_validation_callback:
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

    def _get_attachment_count(self):
        self.ensure_one()
        if "message_attachment_count" in self._fields:
            return self.message_attachment_count or 0
        if "attachment_ids" in self._fields:
            return len(self.attachment_ids)
        return self.env["ir.attachment"].search_count(
            [("res_model", "=", self._name), ("res_id", "=", self.id)]
        )

    def _snapshot_audit_payload(self):
        self.ensure_one()
        return {
            "state": self.state,
            "amount": self.amount,
            "partner_id": self.partner_id.id if self.partner_id else False,
            "attachment_count": self._get_attachment_count(),
            "validation_status": self.validation_status,
        }

    def _audit_transition(self, event_code, before, after, reason=None, require_reason=False, action_name=None):
        self.ensure_one()
        return self.env["sc.audit.log"].write_event(
            event_code=event_code,
            model=self._name,
            res_id=self.id,
            action=action_name or event_code,
            before=before,
            after=after,
            reason=reason,
            require_reason=require_reason,
            company_id=self.company_id,
            project_id=self.project_id,
        )

    def _has_submit_access(self):
        return (
            self.env.user.has_group("smart_construction_core.group_sc_cap_business_initiator")
            or self.env.user.has_group("smart_construction_core.group_sc_cap_finance_user")
            or self.env.user.has_group("smart_construction_custom.group_sc_role_finance")
        )

    def _has_finance_approve_access(self):
        return (
            self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager")
            or self.env.user.has_group("smart_construction_custom.group_sc_role_finance")
        )

    def _assert_finance_approve_access(self):
        if not self._has_finance_approve_access():
            raise ValidationError(_("你没有审批付款/收款申请的权限。"))

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

    def _payment_force_block_enabled(self, reason_code):
        code = str(reason_code or "").strip().upper()
        if not code:
            return False
        if self._get_bool_param("sc.payment.force_block_all", False):
            return True
        return self._get_bool_param("sc.payment.force_block.%s" % code.lower(), False)

    def _payment_advisory(self, reason_code, message, suggested_action="", reasons=None, hints=None):
        code = str(reason_code or "BUSINESS_RULE_FAILED").strip().upper()
        return {
            "reason_code": code,
            "message": str(message or code),
            "suggested_action": str(suggested_action or ""),
            "reasons": [str(item) for item in (reasons or []) if str(item or "").strip()],
            "hints": [str(item) for item in (hints or []) if str(item or "").strip()],
            "force_block_enabled": self._payment_force_block_enabled(code),
        }

    def _payment_advisory_from_exception(self, exc, fallback_code="BUSINESS_RULE_FAILED"):
        text = str(exc or "").strip()
        match = re.search(r"\[SC_GUARD:([A-Z0-9_]+)\]", text)
        code = str(match.group(1) if match else fallback_code).strip().upper()
        suggested = {
            "PAYMENT_ATTACHMENTS_REQUIRED": "upload_attachment",
            "P0_PAYMENT_SETTLEMENT_NOT_READY": "complete_settlement_approval",
            "P0_PAYMENT_FUNDING_NOT_READY": "setup_project_funding",
            "P0_PAYMENT_FUNDING_BASELINE_INVALID": "fix_project_funding_baseline",
            "P0_PAYMENT_FUNDING_CAP_EXCEEDED": "adjust_payment_amount_or_funding",
            "P0_PAYMENT_NOT_FULLY_PAID": "complete_payment_execution",
        }.get(code, "")
        return self._payment_advisory(code, text or code, suggested_action=suggested)

    def _collect_payment_advisories(self, action_name):
        self.ensure_one()
        action_key = str(action_name or "").strip().lower()
        advisories = []
        if action_key == "submit" and self._get_attachment_count() <= 0:
            advisories.append(
                self._payment_advisory(
                    "PAYMENT_ATTACHMENTS_REQUIRED",
                    _("付款申请未上传附件，建议补充附件后再提交。"),
                    suggested_action="upload_attachment",
                    reasons=["attachments are missing"],
                    hints=["请补充合同、结算或付款依据附件"],
                )
            )
        if action_key == "done" and not self.is_fully_paid:
            advisories.append(
                self._payment_advisory(
                    "P0_PAYMENT_NOT_FULLY_PAID",
                    _("付款申请尚未登记足额付款，完成时将自动生成付款记录。"),
                    suggested_action="complete_payment_execution",
                    reasons=["payment ledger is not fully paid"],
                    hints=["请确认审批风险后完成付款办理"],
                )
            )
        for check in (
            lambda: self._check_project_lifecycle(self.project_id, action_key),
            lambda: self._check_settlement_state(self.settlement_id),
            lambda: self._check_project_funding_gate(self.project_id, self.amount, exclude_ids=self.ids),
            self._check_settlement_remaining_amount,
            self._check_material_settlement_remaining_amount,
            self._check_not_overpay_settlement,
            self._check_settlement_consistency,
            lambda: self._check_settlement_compliance_or_raise(strict=False),
        ):
            try:
                check()
            except Exception as exc:
                advisories.append(self._payment_advisory_from_exception(exc))
        return advisories

    def _handle_payment_advisories(self, action_name, advisories):
        blocking = [item for item in (advisories or []) if item.get("force_block_enabled")]
        if blocking:
            first = blocking[0]
            raise_guard(
                first.get("reason_code") or "BUSINESS_RULE_FAILED",
                f"付款申请[{self.display_name}]",
                str(action_name or "办理付款申请"),
                reasons=first.get("reasons") or [first.get("message") or ""],
                hints=first.get("hints") or [],
            )
        if advisories:
            lines = [
                "- %s" % str(item.get("message") or item.get("reason_code") or "").strip()
                for item in advisories
                if str(item.get("message") or item.get("reason_code") or "").strip()
            ]
            if lines:
                self._message_post_non_blocking(_("付款申请风险提示：\n%s") % "\n".join(lines))
        return advisories

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
            ledger_model = "sc.treasury.ledger" if rec.type == "receive" else "payment.ledger"
            data = self.env[ledger_model].read_group([("payment_request_id", "=", rec.id)], ["amount:sum"], [])
            paid_total = data[0].get("amount_sum", data[0].get("amount", 0.0)) if data else 0.0
            unpaid = (rec.amount or 0.0) - paid_total
            if float_compare(unpaid, 0.0, precision_rounding=rounding) == 1:
                raise ValidationError(_("付款/收款未结清，无法完成。"))

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

    @api.constrains("material_settlement_id", "type", "project_id", "partner_id", "amount", "state")
    def _check_material_settlement_consistency(self):
        for rec in self:
            settlement = rec.material_settlement_id
            if not settlement:
                continue
            if rec.type != "pay":
                raise ValidationError(_("材料结算只能生成付款申请。"))
            if settlement.project_id and rec.project_id and settlement.project_id != rec.project_id:
                raise ValidationError(_("材料结算项目必须与付款申请项目一致。"))
            if settlement.supplier_id and rec.partner_id and settlement.supplier_id != rec.partner_id:
                raise ValidationError(_("材料结算供应商必须与付款申请往来单位一致。"))
            if rec.state in ("submit", "approve", "approved", "done"):
                rec._check_material_settlement_remaining_amount()

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

    def _material_settlement_requested_amount_excluding_self(self):
        self.ensure_one()
        settlement = self.material_settlement_id
        if not settlement:
            return 0.0
        domain = [
            ("material_settlement_id", "=", settlement.id),
            ("type", "=", "pay"),
            ("state", "not in", ("draft", "cancel")),
            ("id", "!=", self.id),
        ]
        data = self.sudo().read_group(domain, ["amount:sum"], [])
        return data[0].get("amount_sum", data[0].get("amount", 0.0)) if data else 0.0

    def _check_material_settlement_remaining_amount(self):
        for rec in self:
            settlement = rec.material_settlement_id
            if rec.type != "pay" or not settlement:
                continue
            if settlement.state != "confirmed":
                raise_guard(
                    "P0_MATERIAL_SETTLEMENT_NOT_CONFIRMED",
                    f"付款申请[{rec.display_name}]",
                    "提交/审批材料付款申请",
                    reasons=[_("材料结算单未确认")],
                    hints=[_("请先确认材料结算单")],
                )
            precision = rec.currency_id.rounding if rec.currency_id else 0.01
            requested = rec._material_settlement_requested_amount_excluding_self()
            payable = (settlement.amount_total or 0.0) - (requested or 0.0)
            amount = rec.amount or 0.0
            if float_compare(payable, 0.0, precision_rounding=precision) <= 0:
                raise_guard(
                    "P0_MATERIAL_PAYMENT_OVER_BALANCE",
                    f"付款申请[{rec.display_name}]",
                    "提交/审批材料付款申请",
                    reasons=[f"材料结算剩余可申请金额不足（剩余：{payable}）"],
                    hints=[_("请先撤销多余付款申请或调整本次申请金额")],
                )
            if float_compare(amount, payable, precision_rounding=precision) == 1:
                raise_guard(
                    "P0_MATERIAL_PAYMENT_OVER_BALANCE",
                    f"付款申请[{rec.display_name}]",
                    "提交/审批材料付款申请",
                    reasons=[f"本次申请金额 {amount} 超过材料结算剩余可申请金额 {payable}"],
                    hints=[_("请降低付款金额或拆分到后续付款申请")],
                )

    def _compute_is_overpay_risk(self):
        """用于 UI 高亮：金额 > 可付余额 时标记风险。"""
        for rec in self:
            if rec.type != "pay":
                rec.is_overpay_risk = False
                continue
            if rec.material_settlement_id:
                precision = rec.currency_id.rounding if rec.currency_id else 0.01
                payable = (rec.material_settlement_id.amount_total or 0.0) - (
                    rec._material_settlement_requested_amount_excluding_self() or 0.0
                )
                rec.is_overpay_risk = float_compare(rec.amount or 0.0, payable, precision_rounding=precision) == 1
                continue
            if not rec.settlement_id:
                rec.is_overpay_risk = False
                continue
            metrics = opm.compute_payment_payable_excluding_self(rec)
            payable = metrics["payable"]
            precision = metrics["precision"]
            rec.is_overpay_risk = float_compare(rec.amount or 0.0, payable, precision_rounding=precision) == 1

    def action_submit(self):
        if not self._has_submit_access():
            raise ValidationError(_("你没有提交付款/收款申请的权限。"))
        advisory_result = {}
        for rec in self:
            if not rec.contract_id and not rec.material_settlement_id:
                raise UserError("请先选择关联合同后再提交付款/收款申请。")
            if rec.contract_id and rec.contract_id.state == "cancel":
                raise UserError("关联合同已取消，不能提交付款/收款申请。")
            rec._check_material_settlement_remaining_amount()
            advisory_result[rec.id] = rec._handle_payment_advisories(
                "提交付款申请",
                rec._collect_payment_advisories("submit"),
            )
        for rec in self:
            before = rec._snapshot_audit_payload()
            rec.with_context(allow_transition=True, payment_soft_gate=True).write({"state": "submit"})
            after = rec._snapshot_audit_payload()
            rec._audit_transition("payment_submitted", before, after, action_name="action_submit")
        self.invalidate_recordset()
        for rec in self:
            company = rec.company_id or self.env.company
            rec.with_company(company).with_context(
                allowed_company_ids=[company.id],
            ).request_validation()
        self._message_post_non_blocking(_("付款/收款申请已提交，进入审批流程。"))
        return {"warnings": advisory_result}

    def action_approve(self):
        self._assert_finance_approve_access()
        advisory_result = {}
        for rec in self:
            if rec.state != "submit":
                continue
            if rec.validation_status != "validated" and not rec.env.context.get("tier_validation_callback"):
                raise_guard(
                    "PAYMENT_TIER_INCOMPLETE",
                    f"付款申请[{rec.display_name}]",
                    "审批付款申请",
                    reasons=["tier validation not complete"],
                )
            rec._check_material_settlement_remaining_amount()
            advisory_result[rec.id] = rec._handle_payment_advisories(
                "审批付款申请",
                rec._collect_payment_advisories("approve"),
            )
        result = None
        for rec in self:
            if rec.state != "submit":
                continue
            rec.with_context(allow_transition=True, payment_soft_gate=True).write({"state": "approve"})
            action = rec.validate_tier()
            if action:
                result = action
        return result or {"warnings": advisory_result}

    def action_approval_decision(self):
        """Execute the current approval step without forcing the frontend to know tier state."""
        self._assert_finance_approve_access()
        result = None
        advisory_result = {}
        for rec in self:
            if rec.state != "submit":
                continue
            if rec.validation_status in ("waiting", "pending"):
                rec._check_material_settlement_remaining_amount()
                advisory_result[rec.id] = rec._handle_payment_advisories(
                    "审批付款申请",
                    rec._collect_payment_advisories("approve"),
                )
                action = rec.validate_tier()
                if action:
                    result = action
                continue
            if rec.validation_status == "validated":
                return rec.action_approve()
            if rec.validation_status in ("no", False) and not rec.review_ids:
                rec._check_material_settlement_remaining_amount()
                advisory_result[rec.id] = rec._handle_payment_advisories(
                    "审批付款申请",
                    rec._collect_payment_advisories("approve"),
                )
                before = rec._snapshot_audit_payload()
                rec.write({"validation_status": "validated"})
                rec.with_context(allow_transition=True, payment_soft_gate=True).write({"state": "approved"})
                after = rec._snapshot_audit_payload()
                rec._audit_transition("payment_approved", before, after, action_name="action_approval_decision")
                continue
            raise_guard(
                "PAYMENT_TIER_INCOMPLETE",
                f"付款申请[{rec.display_name}]",
                "审批付款申请",
                reasons=[f"validation_status={rec.validation_status}"],
            )
        return result or {"warnings": advisory_result}

    def action_set_approved(self):
        self._assert_finance_approve_access()
        advisory_result = {}
        result = None
        for rec in self:
            rec._check_material_settlement_remaining_amount()
            advisory_result[rec.id] = rec._handle_payment_advisories(
                "批准付款申请",
                rec._collect_payment_advisories("approve"),
            )
            if rec.state == "approve" and rec.validation_status == "validated":
                before = rec._snapshot_audit_payload()
                rec.with_context(allow_transition=True, payment_soft_gate=True).write({"state": "approved"})
                after = rec._snapshot_audit_payload()
                rec._audit_transition("payment_approved", before, after, action_name="action_set_approved")
                continue
            action = rec.validate_tier()
            if action:
                result = action
                continue
        return result or {"warnings": advisory_result}

    def action_done(self):
        has_finance_done_access = (
            self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager")
            or self.env.user.has_group("smart_construction_custom.group_sc_role_finance")
        )
        if not has_finance_done_access:
            raise ValidationError(_("你没有完成付款/收款申请的权限。"))
        advisory_result = {}
        for rec in self:
            approved_reviews = rec.review_ids.filtered(lambda review: review.status == "approved")
            open_reviews = rec.review_ids.filtered(
                lambda review: review.status not in ("approved", "rejected")
            )
            tier_callback_complete = bool(approved_reviews) and not open_reviews
            if rec.validation_status != "validated" and not tier_callback_complete:
                raise_guard(
                    "PAYMENT_TIER_INCOMPLETE",
                    f"付款申请[{rec.display_name}]",
                    "完成付款申请",
                    reasons=["tier validation not complete"],
                )
            if rec.state != "approved":
                raise_guard(
                    "PAYMENT_GUARD_NOT_READY",
                    f"付款申请[{rec.display_name}]",
                    "完成付款申请",
                    reasons=[f"当前状态为 {rec.state}"],
                )
            advisory_result[rec.id] = rec._handle_payment_advisories(
                "完成付款申请",
                rec._collect_payment_advisories("done"),
            )
        for rec in self:
            before = rec._snapshot_audit_payload()
            if rec.type == "receive":
                rec.with_context(payment_soft_gate=True)._ensure_treasury_ledger(note="auto:payment_request_done")
            elif not rec.is_fully_paid:
                rec.with_context(payment_soft_gate=True)._ensure_payment_ledger(note="auto:payment_request_done")
            rec.with_context(allow_transition=True, payment_soft_gate=True).write({"state": "done"})
            after = rec._snapshot_audit_payload()
            rec._audit_transition("payment_paid", before, after, action_name="action_done")
        return {"warnings": advisory_result}

    def _ensure_payment_ledger(self, amount=None, paid_at=None, ref=None, note=None):
        self.ensure_one()
        Ledger = self.env["payment.ledger"].with_context(
            allow_payment_ledger_create=True,
            payment_soft_gate=bool(self.env.context.get("payment_soft_gate")),
        )
        existing = Ledger.search([("payment_request_id", "=", self.id)], limit=1)
        if existing:
            return existing
        vals = {
            "payment_request_id": self.id,
            "amount": amount if amount is not None else (self.amount or 0.0),
            "paid_at": paid_at or fields.Datetime.now(),
        }
        if ref:
            vals["ref"] = ref
        if note:
            vals["note"] = note
        return Ledger.create(vals)

    def _ensure_treasury_ledger(self, amount=None, date=None, note=None):
        self.ensure_one()
        if self.type != "receive":
            raise UserError(_("只有收款申请可以生成收入资金台账。"))
        Ledger = self.env["sc.treasury.ledger"].with_context(allow_ledger_auto=True)
        existing = Ledger.search([("payment_request_id", "=", self.id)], limit=1)
        if existing:
            return existing
        partner = self.partner_id
        if not partner:
            raise UserError(_("收款申请未选择往来单位，不能生成资金台账。"))
        vals = {
            "date": date or fields.Date.context_today(self),
            "project_id": self.project_id.id,
            "partner_id": partner.id,
            "settlement_id": self.settlement_id.id or False,
            "payment_request_id": self.id,
            "direction": "in",
            "amount": amount if amount is not None else (self.amount or 0.0),
            "currency_id": self.currency_id.id,
            "note": note,
        }
        return Ledger.create(vals)

    def action_cancel(self):
        has_finance_cancel_access = (
            self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager")
            or self.env.user.has_group("smart_construction_custom.group_sc_role_finance")
        )
        if not has_finance_cancel_access:
            raise ValidationError(_("你没有取消付款/收款申请的权限。"))
        self.with_context(allow_transition=True).write({"state": "cancel"})

    def _check_state_from_condition(self):
        self.ensure_one()
        parent = getattr(super(), "_check_state_from_condition", None)
        base_ok = parent() if parent else False
        return base_ok or self.state == "submit"

    def action_on_tier_approved(self):
        for rec in self:
            if rec.state != "submit":
                continue
            advisories = rec._collect_payment_advisories("approve")
            if advisories:
                lines = [
                    "- %s" % str(item.get("message") or item.get("reason_code") or "").strip()
                    for item in advisories
                    if str(item.get("message") or item.get("reason_code") or "").strip()
                ]
                if lines:
                    rec._message_post_non_blocking(_("付款申请审批风险提示：\n%s") % "\n".join(lines))
            before = rec._snapshot_audit_payload()
            rec.with_context(
                allow_transition=True,
                payment_soft_gate=True,
                tier_validation_callback=True,
            ).write({"state": "approved"})
            after = rec._snapshot_audit_payload()
            rec._audit_transition("payment_approved", before, after, action_name="action_on_tier_approved")
            rec._message_post_non_blocking(_("付款/收款申请审批通过。"))

    def _get_tier_reject_reason(self):
        self.ensure_one()
        reviews = self.review_ids.filtered(lambda review: review.status == "rejected" and review.comment)
        if reviews:
            return reviews.sorted(lambda review: review.write_date or review.create_date, reverse=True)[0].comment
        return _("OCA审批驳回（未填写原因）")

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state != "submit":
                continue
            reason = reason or rec._get_tier_reject_reason()
            if not reason:
                raise_guard(
                    "AUDIT_REASON_REQUIRED",
                    f"付款申请[{rec.display_name}]",
                    "审批驳回",
                    reasons=["reason is required"],
                )
            before = rec._snapshot_audit_payload()
            rec.with_context(allow_transition=True).write({"state": "rejected"})
            after = rec._snapshot_audit_payload()
            rec._audit_transition(
                "payment_rejected",
                before,
                after,
                reason=reason,
                require_reason=True,
                action_name="action_on_tier_rejected",
            )
            rec._message_post_non_blocking(_("付款/收款申请审批驳回：%s") % (reason or _("未填写原因")))
