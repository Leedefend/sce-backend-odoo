# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

from ..support.state_guard import raise_guard


class ScExpenseClaim(models.Model):
    _name = "sc.expense.claim"
    _description = "费用与保证金单据"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation", "sc.company.contractor.responsibility.context.mixin"]
    _order = "date_claim desc, id desc"

    name = fields.Char(string="单据号", required=True, default="新建", copy=False)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    claim_type = fields.Selection(
        [
            ("expense", "费用报销"),
            ("deposit_pay", "保证金支付"),
            ("deposit_refund", "保证金退回"),
            ("deposit_receive", "保证金收取"),
            ("deduction_refund", "扣款退回"),
            ("project_company_repay", "项目还公司款"),
        ],
        string="业务类型",
        default="expense",
        required=True,
        index=True,
    )
    direction = fields.Selection(
        [("outflow", "流出"), ("inflow", "流入")],
        string="资金方向",
        compute="_compute_direction",
        store=True,
        index=True,
    )
    handling_kind = fields.Selection(
        [
            ("expense_reimbursement", "费用报销"),
            ("project_expense", "项目费用报销"),
            ("deduction_bill", "扣款单"),
            ("deduction_paid", "扣款实缴"),
            ("deduction_refund", "扣款退回"),
            ("bid_deposit_pay", "投标保证金支付"),
            ("bid_deposit_return", "投标保证金退回"),
            ("contract_deposit_pay", "合同保证金支付"),
            ("contract_deposit_return", "合同保证金退回"),
            ("self_funding_deposit", "自筹保证金"),
            ("self_funding_deposit_return", "自筹保证金退回"),
            ("deposit_receive", "保证金收取"),
            ("repayment_contractor_project", "承包人还项目款"),
            ("repayment_project_company", "项目还公司款"),
            ("repayment_registration", "还款登记"),
            ("other", "其他费用/保证金办理"),
        ],
        string="办理口径",
        compute="_compute_handling_kind",
        store=True,
        index=True,
    )
    business_axis = fields.Selection(
        [
            ("expense", "费用业务"),
            ("deduction", "扣款业务"),
            ("guarantee", "保证金业务"),
            ("interfund", "往来款业务"),
            ("other", "其他业务"),
        ],
        string="业务域",
        compute="_compute_business_and_finance_axes",
        store=True,
        index=True,
    )
    financial_flow = fields.Selection(
        [
            ("cash_in", "现金流入"),
            ("cash_out", "现金流出"),
            ("noncash", "非现金事实"),
            ("interfund", "内部往来资金"),
            ("reference", "追溯参考"),
        ],
        string="财务影响",
        compute="_compute_business_and_finance_axes",
        store=True,
        index=True,
    )
    payment_anchor_policy = fields.Selection(
        [
            ("legacy_optional", "历史事实可不关联申请"),
            ("pay_request_required", "必须关联付款申请"),
            ("receive_request_required", "必须关联收款申请"),
            ("noncash_no_request", "非现金扣款不关联申请"),
            ("interfund_no_request", "往来款不关联申请"),
        ],
        string="申请锚点口径",
        compute="_compute_payment_anchor_policy",
        store=True,
        index=True,
    )
    claim_flow_label = fields.Char(string="办理事项", compute="_compute_claim_flow_label")
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        index=True,
        ondelete="restrict",
        domain="[('target_model', '=', 'sc.expense.claim')]",
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submit", "已提交"),
            ("approved", "已批准"),
            ("done", "已完成"),
            ("legacy_confirmed", "历史已确认"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        required=True,
        index=True,
    )
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
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
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True)
    applicant_name = fields.Char(string="申请人", index=True)
    department_name = fields.Char(string="部门", index=True)
    company_name_text = fields.Char(string="所属公司")
    guarantee_project_name = fields.Char(string="投标项目/合同名称", index=True)
    guarantee_type = fields.Selection(
        [("bid", "投标保证金"), ("contract", "合同保证金"), ("other", "其他保证金")],
        string="保证金类型",
        default="bid",
        index=True,
    )
    payment_method = fields.Char(string="支付方式")
    clearing_method = fields.Char(string="缴纳方式")
    return_reason = fields.Char(string="退回原因")
    is_returned = fields.Boolean(string="是否清退退回")
    fill_date = fields.Date(string="填写日期", default=fields.Date.context_today)
    payee = fields.Char(string="收款人", index=True)
    receipt_account_name = fields.Char(string="收款账户名称", index=True)
    payee_account = fields.Char(string="收款账号")
    payee_bank = fields.Char(string="开户行")
    payment_account_name = fields.Char(string="付款账户名称", index=True)
    payer_account = fields.Char(string="支付账户")
    payer_bank = fields.Char(string="支付账户开户行")
    date_claim = fields.Date(string="单据日期", default=fields.Date.context_today, index=True)
    expense_type = fields.Char(string="费用类型", index=True)
    summary = fields.Char(string="摘要", index=True)
    amount = fields.Monetary(string="申请金额", currency_field="currency_id", required=True)
    approved_amount = fields.Monetary(string="批准金额", currency_field="currency_id")
    paid_amount = fields.Monetary(string="已付款金额", currency_field="currency_id")
    deduction_line_ids = fields.One2many(
        "sc.expense.claim.deduction.line",
        "claim_id",
        string="扣款单明细",
    )
    deduction_line_amount_total = fields.Monetary(
        string="扣款明细合计",
        currency_field="currency_id",
        compute="_compute_deduction_line_amount_total",
        store=True,
    )
    unpaid_amount = fields.Monetary(
        string="未付款金额",
        currency_field="currency_id",
        compute="_compute_unpaid_amount",
        store=True,
    )
    payment_state = fields.Char(string="付款状态", index=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.ref("base.CNY", raise_if_not_found=False).id or self.env.company.currency_id.id,
    )
    payment_request_id = fields.Many2one(
        "payment.request",
        string="付款/收款申请",
        index=True,
        ondelete="set null",
        domain="[('project_id', '=', project_id)]",
    )
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_no = fields.Char(string="历史单据号", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    creator_name = fields.Char(string="历史录入人", index=True, readonly=True)
    created_time = fields.Datetime(string="历史录入时间", index=True, readonly=True)
    reject_reason = fields.Char(string="驳回原因", readonly=True, copy=False)
    note = fields.Text(string="备注")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_expense_claim_attachment_rel",
        "claim_id",
        "attachment_id",
        string="附件",
    )
    active = fields.Boolean("有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "历史费用/保证金来源记录必须唯一。",
        ),
        ("amount_nonnegative", "CHECK(amount >= 0)", "Claim amount must be non-negative."),
        ("paid_amount_nonnegative", "CHECK(paid_amount IS NULL OR paid_amount >= 0)", "Paid amount must be non-negative."),
    ]

    @api.depends("claim_type")
    def _compute_direction(self):
        for rec in self:
            rec.direction = (
                "inflow"
                if rec.claim_type in ("deposit_refund", "deposit_receive", "deduction_refund")
                else "outflow"
            )

    @api.depends("claim_type", "expense_type", "summary", "direction")
    def _compute_claim_flow_label(self):
        for rec in self:
            expense_type = (rec.expense_type or "").strip()
            summary = (rec.summary or "").strip()
            text = f"{expense_type} {summary}"
            if rec.claim_type == "project_company_repay":
                if "项目还公司款" in text:
                    rec.claim_flow_label = _("项目还公司款")
                else:
                    rec.claim_flow_label = _("还款登记")
            elif rec.claim_type == "deposit_receive" and "承包人还项目款" in text:
                rec.claim_flow_label = _("承包人还项目款")
            elif rec.claim_type == "deduction_refund":
                rec.claim_flow_label = _("扣款退回")
            elif rec.claim_type == "deposit_pay":
                rec.claim_flow_label = _("保证金支付")
            elif rec.claim_type == "deposit_refund":
                rec.claim_flow_label = _("保证金退回")
            elif rec.claim_type == "deposit_receive":
                rec.claim_flow_label = _("保证金收取")
            elif "扣款" in text:
                rec.claim_flow_label = expense_type or _("扣款办理")
            elif "报销" in text:
                rec.claim_flow_label = expense_type or _("费用报销")
            elif "备用金" in text:
                rec.claim_flow_label = _("备用金")
            else:
                rec.claim_flow_label = expense_type or _("费用办理")

    @api.depends("business_category_id.code", "claim_type", "expense_type", "summary", "guarantee_type")
    def _compute_handling_kind(self):
        for rec in self:
            code = rec.business_category_id.code or ""
            expense_type = (rec.expense_type or "").strip()
            summary = (rec.summary or "").strip()
            text = "%s %s" % (expense_type, summary)
            if code == "finance.expense.project" or expense_type == "项目费用报销单":
                rec.handling_kind = "project_expense"
            elif code == "finance.expense.reimbursement":
                if rec.claim_type == "deposit_receive":
                    rec.handling_kind = "self_funding_deposit" if expense_type == "自筹保证金" else "deposit_receive"
                else:
                    rec.handling_kind = "expense_reimbursement"
            elif code == "finance.deduction.bill" or rec._is_noncash_deduction_bill():
                rec.handling_kind = "deduction_bill"
            elif code == "finance.deduction.paid" or expense_type == "扣款实缴登记":
                rec.handling_kind = "deduction_paid"
            elif code == "finance.deduction.refund" or rec.claim_type == "deduction_refund" or expense_type == "扣款实缴退回":
                rec.handling_kind = "deduction_refund"
            elif code == "finance.deposit.bid.pay" or (rec.claim_type == "deposit_pay" and rec.guarantee_type != "contract"):
                rec.handling_kind = "bid_deposit_pay"
            elif code == "finance.deposit.self_funding.return" or (
                rec.claim_type == "deposit_refund" and expense_type == "自筹保证金退回"
            ):
                rec.handling_kind = "self_funding_deposit_return"
            elif code == "finance.deposit.bid.return" or (
                rec.claim_type == "deposit_refund"
                and rec.guarantee_type != "contract"
                and expense_type != "自筹保证金退回"
            ):
                rec.handling_kind = "bid_deposit_return"
            elif code == "finance.deposit.contract.pay" or (rec.claim_type == "deposit_pay" and rec.guarantee_type == "contract"):
                rec.handling_kind = "contract_deposit_pay"
            elif code == "finance.deposit.contract.return" or (
                rec.claim_type == "deposit_refund" and rec.guarantee_type == "contract"
            ):
                rec.handling_kind = "contract_deposit_return"
            elif code == "finance.repayment.contractor_project" or (
                rec.claim_type == "deposit_receive" and "承包人还项目款" in text
            ):
                rec.handling_kind = "repayment_contractor_project"
            elif code == "finance.repayment.project_company" or (
                rec.claim_type == "project_company_repay" and "项目还公司款" in text
            ):
                rec.handling_kind = "repayment_project_company"
            elif code == "finance.repayment.registration" or rec.claim_type == "project_company_repay":
                rec.handling_kind = "repayment_registration"
            elif rec.claim_type == "deposit_receive":
                rec.handling_kind = "self_funding_deposit" if expense_type == "自筹保证金" else "deposit_receive"
            else:
                rec.handling_kind = "other"

    @api.depends("handling_kind")
    def _compute_business_and_finance_axes(self):
        expense_kinds = {"expense_reimbursement", "project_expense"}
        deduction_kinds = {"deduction_bill", "deduction_paid", "deduction_refund"}
        guarantee_kinds = {
            "bid_deposit_pay",
            "bid_deposit_return",
            "contract_deposit_pay",
            "contract_deposit_return",
            "self_funding_deposit",
            "self_funding_deposit_return",
            "deposit_receive",
        }
        interfund_kinds = {
            "repayment_contractor_project",
            "repayment_project_company",
            "repayment_registration",
        }
        cash_in_kinds = {
            "deduction_paid",
            "bid_deposit_return",
            "contract_deposit_return",
            "self_funding_deposit",
            "deposit_receive",
        }
        cash_out_kinds = {
            "expense_reimbursement",
            "project_expense",
            "deduction_refund",
            "bid_deposit_pay",
            "contract_deposit_pay",
            "self_funding_deposit_return",
        }
        for rec in self:
            kind = rec.handling_kind
            if kind in expense_kinds:
                rec.business_axis = "expense"
            elif kind in deduction_kinds:
                rec.business_axis = "deduction"
            elif kind in guarantee_kinds:
                rec.business_axis = "guarantee"
            elif kind in interfund_kinds:
                rec.business_axis = "interfund"
            else:
                rec.business_axis = "other"

            if kind == "deduction_bill":
                rec.financial_flow = "noncash"
            elif kind in cash_in_kinds:
                rec.financial_flow = "cash_in"
            elif kind in cash_out_kinds:
                rec.financial_flow = "cash_out"
            elif kind in interfund_kinds:
                rec.financial_flow = "interfund"
            else:
                rec.financial_flow = "reference"

    @api.depends(
        "source_origin",
        "handling_kind",
        "financial_flow",
        "claim_type",
        "expense_type",
        "summary",
        "business_category_id.code",
    )
    def _compute_payment_anchor_policy(self):
        for rec in self:
            if rec.source_origin == "legacy":
                rec.payment_anchor_policy = "legacy_optional"
            elif rec._is_interfund_repayment():
                rec.payment_anchor_policy = "interfund_no_request"
            elif rec._is_noncash_deduction_bill():
                rec.payment_anchor_policy = "noncash_no_request"
            elif rec.financial_flow == "cash_in":
                rec.payment_anchor_policy = "receive_request_required"
            elif rec.financial_flow == "cash_out":
                rec.payment_anchor_policy = "pay_request_required"
            else:
                rec.payment_anchor_policy = "interfund_no_request"

    def _is_interfund_repayment(self):
        self.ensure_one()
        text = "%s %s" % (self.expense_type or "", self.summary or "")
        return self.claim_type == "project_company_repay" or (
            self.claim_type == "deposit_receive" and "承包人还项目款" in text
        )

    def _is_noncash_deduction_bill(self):
        self.ensure_one()
        expense_type = (self.expense_type or "").strip()
        return self.business_category_id.code == "finance.deduction.bill" or (
            self.claim_type == "expense" and expense_type in {"扣款单", "扣款登记"}
        )

    def _expected_payment_request_type(self):
        self.ensure_one()
        if self.financial_flow == "cash_in":
            return "receive"
        if self.financial_flow == "cash_out":
            return "pay"
        return False

    @api.onchange("amount")
    def _onchange_amount(self):
        for rec in self:
            if not rec.approved_amount:
                rec.approved_amount = rec.amount

    @api.onchange("deduction_line_ids")
    def _onchange_deduction_line_ids(self):
        for rec in self:
            if not rec._is_noncash_deduction_bill():
                continue
            total = sum(rec.deduction_line_ids.mapped("amount"))
            rec.amount = total
            if not rec.approved_amount or rec.approved_amount == rec._origin.approved_amount:
                rec.approved_amount = total

    @api.model
    def _deduction_line_commands_amount_total(self, commands):
        total = 0.0
        has_amount = False
        for command in commands or []:
            if not isinstance(command, (list, tuple)) or len(command) < 3:
                continue
            operation = command[0]
            values = command[2] if isinstance(command[2], dict) else {}
            if operation == 0 and "amount" in values:
                total += float(values.get("amount") or 0.0)
                has_amount = True
        return total if has_amount else None

    @api.model
    def _vals_is_noncash_deduction_bill(self, vals):
        if self.env.context.get("default_business_category_code") == "finance.deduction.bill":
            return True
        category_id = vals.get("business_category_id")
        if category_id:
            category = self.env["sc.business.category"].sudo().browse(category_id)
            if category.exists() and category.code == "finance.deduction.bill":
                return True
        expense_type = (vals.get("expense_type") or self.env.context.get("default_expense_type") or "").strip()
        return expense_type in {"扣款登记", "扣款单"}

    @api.model
    def _apply_deduction_line_amount_defaults(self, vals):
        if not self._vals_is_noncash_deduction_bill(vals):
            return vals
        line_total = self._deduction_line_commands_amount_total(vals.get("deduction_line_ids"))
        if line_total is None:
            return vals
        if not vals.get("amount"):
            vals["amount"] = line_total
        if not vals.get("approved_amount"):
            vals["approved_amount"] = vals.get("amount") or line_total
        return vals

    @api.model
    def _context_project_id(self):
        project_id = self.env.context.get("default_project_id") or self.env.context.get("current_project_id")
        try:
            return int(project_id) if project_id else False
        except (TypeError, ValueError):
            return False

    @api.model
    def _context_partner_id(self):
        partner_id = self.env.context.get("default_partner_id") or self.env.context.get("current_partner_id")
        try:
            return int(partner_id) if partner_id else False
        except (TypeError, ValueError):
            return False

    @api.model
    def _resolve_business_category_code(self, vals):
        code = self.env.context.get("default_business_category_code") or self.env.context.get(
            "current_business_category_code"
        )
        if code:
            return code
        claim_type = vals.get("claim_type", self.env.context.get("default_claim_type") or "expense")
        guarantee_type = vals.get("guarantee_type", self.env.context.get("default_guarantee_type") or "bid")
        expense_type = (vals.get("expense_type") or self.env.context.get("default_expense_type") or "").strip()
        summary = (vals.get("summary") or self.env.context.get("default_summary") or "").strip()
        text = "%s %s" % (expense_type, summary)
        if claim_type == "deposit_pay":
            return "finance.deposit.contract.pay" if guarantee_type == "contract" else "finance.deposit.bid.pay"
        if claim_type == "deposit_refund":
            if expense_type == "自筹保证金退回" or "自筹保证金退回" in text:
                return "finance.deposit.self_funding.return"
            return "finance.deposit.contract.return" if guarantee_type == "contract" else "finance.deposit.bid.return"
        if claim_type == "deduction_refund" or expense_type == "扣款实缴退回":
            return "finance.deduction.refund"
        if claim_type == "project_company_repay":
            if expense_type == "项目还公司款登记" or "项目还公司款" in text:
                return "finance.repayment.project_company"
            return "finance.repayment.registration"
        if claim_type == "deposit_receive" and "承包人还项目款" in text:
            return "finance.repayment.contractor_project"
        if expense_type == "扣款实缴登记":
            return "finance.deduction.paid"
        if expense_type in {"扣款登记", "扣款单"} or "扣款登记" in text or "扣款单" in text:
            return "finance.deduction.bill"
        if expense_type == "项目费用报销单":
            return "finance.expense.project"
        return "finance.expense.reimbursement"

    @api.model
    def _resolve_business_category_id(self, vals):
        code = self._resolve_business_category_code(vals)
        category = self.env["sc.business.category"].sudo().search(
            [("code", "=", code), ("target_model", "=", "sc.expense.claim")],
            limit=1,
        )
        return category.id if category else False

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        project_id = res.get("project_id") or self._context_project_id()
        if project_id and "project_id" in fields_list:
            res["project_id"] = project_id
        partner_id = res.get("partner_id") or self._context_partner_id()
        if partner_id and "partner_id" in fields_list:
            res["partner_id"] = partner_id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            project_id = self._context_project_id()
            if project_id:
                vals.setdefault("project_id", project_id)
            partner_id = self._context_partner_id()
            if partner_id:
                vals.setdefault("partner_id", partner_id)
            context_date = self.env.context.get("default_date_claim") or self.env.context.get("current_document_date")
            if context_date:
                vals.setdefault("date_claim", context_date)
            context_amount = self.env.context.get("default_amount") or self.env.context.get("current_business_amount")
            if context_amount:
                vals.setdefault("amount", context_amount)
            context_summary = self.env.context.get("default_summary") or self.env.context.get("default_note")
            if context_summary:
                vals.setdefault("summary", context_summary)
            context_note = self.env.context.get("default_note")
            if context_note:
                vals.setdefault("note", context_note)
            context_payee = self.env.context.get("default_payee") or self.env.context.get("default_partner_name")
            if context_payee:
                vals.setdefault("payee", context_payee)
            context_receipt_account = self.env.context.get("default_receipt_account_name")
            if context_receipt_account:
                vals.setdefault("receipt_account_name", context_receipt_account)
            context_payment_account = self.env.context.get("default_payment_account_name")
            if context_payment_account:
                vals.setdefault("payment_account_name", context_payment_account)
            for field_name in (
                "applicant_name",
                "department_name",
                "company_name_text",
                "guarantee_project_name",
                "payee_account",
                "payee_bank",
                "payer_account",
                "payer_bank",
            ):
                value = self.env.context.get("default_%s" % field_name)
                if value:
                    vals.setdefault(field_name, value)
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.expense.claim") or _("Expense Claim")
            self._apply_deduction_line_amount_defaults(vals)
            vals.setdefault("approved_amount", vals.get("amount", 0.0))
            vals.setdefault("business_category_id", self._resolve_business_category_id(vals))
        return super().create(vals_list)

    def _history_surface_allowed_write_fields(self):
        return {"attachment_ids"}

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {
                "payment_request_id",
                "partner_id",
                "note",
                "department_name",
                "payment_state",
                "paid_amount",
                "active",
                "business_category_id",
                "direction",
                "handling_kind",
                "business_axis",
                "financial_flow",
                "payment_anchor_policy",
                "creator_name",
                "created_time",
                "legacy" + "_visible_" + "attachment",
                "write_uid",
                "write_date",
            } | self._history_surface_allowed_write_fields()
            blocked = set(vals) - allowed
            for field_name in list(blocked):
                if all(rec[field_name] == vals[field_name] for rec in self):
                    blocked.remove(field_name)
            if blocked:
                raise UserError(_("历史迁移费用/保证金单据已确认，只允许补充支付锚点、往来单位、备注和历史录入审计事实。"))
        result = super().write(vals)
        if not self.env.context.get("skip_deduction_amount_sync") and "deduction_line_ids" in vals:
            for rec in self:
                if (
                    rec.source_origin != "legacy"
                    and rec._is_noncash_deduction_bill()
                    and rec.state not in {"approved", "done", "legacy_confirmed", "cancel"}
                ):
                    total = rec.deduction_line_amount_total
                    if (
                        float_compare(rec.amount or 0.0, total, precision_rounding=rec.currency_id.rounding or 0.01) != 0
                        or float_compare(rec.approved_amount or 0.0, total, precision_rounding=rec.currency_id.rounding or 0.01) != 0
                    ):
                        rec.with_context(skip_deduction_amount_sync=True).write(
                            {
                                "amount": total,
                                "approved_amount": total,
                            }
                        )
        return result

    @api.depends("amount", "approved_amount", "paid_amount")
    def _compute_unpaid_amount(self):
        for rec in self:
            expected = rec.approved_amount or rec.amount or 0.0
            rec.unpaid_amount = max(expected - (rec.paid_amount or 0.0), 0.0)

    @api.depends("deduction_line_ids.amount")
    def _compute_deduction_line_amount_total(self):
        for rec in self:
            rec.deduction_line_amount_total = sum(rec.deduction_line_ids.mapped("amount"))

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_expense_claim
               SET payment_state = COALESCE(NULLIF(payment_state, ''), NULLIF(legacy_document_state, ''), state),
                   direction = CASE
                       WHEN claim_type IN ('deposit_refund', 'deposit_receive', 'deduction_refund') THEN 'inflow'
                       ELSE 'outflow'
                   END,
                   paid_amount = COALESCE(paid_amount, approved_amount, amount, 0.0)
             WHERE source_origin = 'legacy'
            """
        )
        self.env.cr.execute(
            """
            UPDATE sc_expense_claim claim
               SET business_category_id = category.id
              FROM sc_business_category category
             WHERE claim.business_category_id IS NULL
               AND category.target_model = 'sc.expense.claim'
               AND category.code = CASE
                   WHEN claim.claim_type = 'deposit_pay' AND claim.guarantee_type = 'contract'
                       THEN 'finance.deposit.contract.pay'
                   WHEN claim.claim_type = 'deposit_pay'
                       THEN 'finance.deposit.bid.pay'
                   WHEN claim.claim_type = 'deposit_refund'
                         AND (
                             COALESCE(claim.expense_type, '') = '自筹保证金退回'
                             OR COALESCE(claim.expense_type, '') || ' ' || COALESCE(claim.summary, '') LIKE '%自筹保证金退回%'
                             OR COALESCE(claim.legacy_source_table, '') = 'C_JFHKLR_TH_ZCDF_CB'
                         )
                       THEN 'finance.deposit.self_funding.return'
                   WHEN claim.claim_type = 'deposit_refund' AND claim.guarantee_type = 'contract'
                       THEN 'finance.deposit.contract.return'
                   WHEN claim.claim_type = 'deposit_refund'
                       THEN 'finance.deposit.bid.return'
                   WHEN claim.claim_type = 'deduction_refund'
                         OR COALESCE(claim.expense_type, '') = '扣款实缴退回'
                       THEN 'finance.deduction.refund'
                   WHEN claim.claim_type = 'project_company_repay'
                         AND (
                             COALESCE(claim.expense_type, '') = '项目还公司款登记'
                             OR COALESCE(claim.expense_type, '') || ' ' || COALESCE(claim.summary, '') LIKE '%项目还公司款%'
                         )
                       THEN 'finance.repayment.project_company'
                   WHEN claim.claim_type = 'project_company_repay'
                       THEN 'finance.repayment.registration'
                   WHEN claim.claim_type = 'deposit_receive'
                         AND COALESCE(claim.expense_type, '') || ' ' || COALESCE(claim.summary, '') LIKE '%承包人还项目款%'
                       THEN 'finance.repayment.contractor_project'
                   WHEN COALESCE(claim.expense_type, '') = '扣款实缴登记'
                       THEN 'finance.deduction.paid'
                   WHEN COALESCE(claim.expense_type, '') IN ('扣款登记', '扣款单')
                         OR COALESCE(claim.expense_type, '') || ' ' || COALESCE(claim.summary, '') LIKE '%扣款登记%'
                         OR COALESCE(claim.expense_type, '') || ' ' || COALESCE(claim.summary, '') LIKE '%扣款单%'
                       THEN 'finance.deduction.bill'
                   WHEN COALESCE(claim.expense_type, '') = '项目费用报销单'
                       THEN 'finance.expense.project'
                   ELSE 'finance.expense.reimbursement'
               END
            """
        )
        self.env.cr.execute(
            """
            UPDATE sc_expense_claim claim
               SET business_category_id = category.id
              FROM sc_business_category category
             WHERE category.target_model = 'sc.expense.claim'
               AND category.code = 'finance.deposit.self_funding.return'
               AND claim.claim_type = 'deposit_refund'
               AND (
                   COALESCE(claim.expense_type, '') = '自筹保证金退回'
                   OR COALESCE(claim.expense_type, '') || ' ' || COALESCE(claim.summary, '') LIKE '%自筹保证金退回%'
                   OR COALESCE(claim.legacy_source_table, '') = 'C_JFHKLR_TH_ZCDF_CB'
               )
               AND (
                   claim.business_category_id IS NULL
                   OR claim.business_category_id <> category.id
               )
            """
        )
        self.env.cr.execute(
            """
            UPDATE sc_expense_claim
               SET direction = 'outflow'
             WHERE claim_type = 'project_company_repay'
               AND direction IS DISTINCT FROM 'outflow'
            """
        )

    @api.model
    def _migrate_self_funding_deposit_return_category(self):
        category = self.env["sc.business.category"].sudo().search(
            [
                ("code", "=", "finance.deposit.self_funding.return"),
                ("target_model", "=", "sc.expense.claim"),
            ],
            limit=1,
        )
        if not category:
            return False
        self.env.cr.execute(
            """
            UPDATE sc_expense_claim claim
               SET business_category_id = %s,
                   handling_kind = 'self_funding_deposit_return',
                   business_axis = 'guarantee',
                   financial_flow = 'cash_out',
                   payment_anchor_policy = CASE
                       WHEN source_origin = 'legacy' THEN 'legacy_optional'
                       ELSE 'pay_request_required'
                   END
             WHERE claim.claim_type = 'deposit_refund'
               AND (
                   COALESCE(claim.expense_type, '') = '自筹保证金退回'
                   OR COALESCE(claim.expense_type, '') || ' ' || COALESCE(claim.summary, '') LIKE '%%自筹保证金退回%%'
                   OR COALESCE(claim.legacy_source_table, '') = 'C_JFHKLR_TH_ZCDF_CB'
               )
               AND (
                   claim.business_category_id IS NULL
                   OR claim.business_category_id <> %s
                   OR claim.handling_kind IS DISTINCT FROM 'self_funding_deposit_return'
                   OR claim.financial_flow IS DISTINCT FROM 'cash_out'
               )
            """,
            (category.id, category.id),
        )
        return True

    def action_submit(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿状态的费用/保证金单据可以提交。"))
            before = rec._snapshot_audit_payload()
            rec._check_business_ready()
            if policy.is_approval_required(rec._name, company=rec.company_id):
                rec.write({"state": "submit", "reject_reason": False})
                company = rec.company_id or self.env.company
                rec.with_company(company).with_context(
                    allowed_company_ids=[company.id],
                ).request_validation()
                rec._audit_transition(
                    "expense_claim_submitted",
                    before,
                    rec._snapshot_audit_payload(),
                    "action_submit",
                )
            else:
                rec.write({"state": "approved", "reject_reason": False})
                rec._audit_transition(
                    "expense_claim_approved",
                    before,
                    rec._snapshot_audit_payload(),
                    "action_submit",
                )

    def action_approve(self):
        self._assert_finance_approve_access()
        policy_model = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state != "submit":
                raise UserError(_("只有已提交的费用/保证金单据可以批准。"))
            before = rec._snapshot_audit_payload()
            rec._check_business_ready()
            if policy_model.is_approval_required(rec._name, company=rec.company_id):
                if rec.validation_status != "validated":
                    raise UserError(_("请先完成统一审批流程后再批准费用/保证金单据。"))
            else:
                policy = policy_model.get_active_policy(rec._name, company=rec.company_id)
                if policy:
                    policy.assert_user_can_approve()
            rec.write({"state": "approved", "reject_reason": False})
            rec._audit_transition(
                "expense_claim_approved",
                before,
                rec._snapshot_audit_payload(),
                "action_approve",
            )

    def _check_state_from_condition(self):
        self.ensure_one()
        parent = getattr(super(), "_check_state_from_condition", None)
        base_ok = parent() if parent else False
        return base_ok or self.state == "submit"

    def _get_tier_reject_reason(self):
        self.ensure_one()
        reviews = self.review_ids.filtered(lambda review: review.status == "rejected" and review.comment)
        if reviews:
            return reviews.sorted(lambda review: review.write_date or review.create_date, reverse=True)[0].comment
        return _("OCA审批驳回（未填写原因）")

    def action_on_tier_approved(self):
        for rec in self:
            if rec.state != "submit":
                raise UserError(_("只有已提交的费用/保证金单据可以完成统一审批回调。"))
            if rec.validation_status != "validated":
                raise UserError(_("费用/保证金单据尚未完成统一审批流程。"))
            before = rec._snapshot_audit_payload()
            rec._check_business_ready()
            rec.write({"state": "approved", "reject_reason": False})
            rec._audit_transition(
                "expense_claim_approved",
                before,
                rec._snapshot_audit_payload(),
                "action_on_tier_approved",
            )

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state != "submit":
                raise UserError(_("只有已提交的费用/保证金单据可以驳回。"))
            before = rec._snapshot_audit_payload()
            rec.write(
                {
                    "state": "draft",
                    "reject_reason": reason or rec._get_tier_reject_reason(),
                }
            )
            rec._audit_transition(
                "expense_claim_rejected",
                before,
                rec._snapshot_audit_payload(),
                "action_on_tier_rejected",
            )

    def action_done(self):
        self._assert_finance_confirm_access()
        for rec in self:
            if rec.state != "approved":
                raise UserError(_("只有已批准的费用/保证金单据可以完成。"))
            before = rec._snapshot_audit_payload()
            rec._check_business_ready()
            rec._sync_payment_request_done()
            rec.write({"state": "done"})
            rec._ensure_interfund_cash_ledger()
            rec._audit_transition(
                "expense_claim_done",
                before,
                rec._snapshot_audit_payload(),
                "action_done",
            )

    def _has_finance_confirm_access(self):
        return self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager")

    def _assert_finance_confirm_access(self):
        if not self._has_finance_confirm_access():
            raise UserError(_("你没有完成费用/保证金单据的财务确认权限。"))

    def _assert_finance_approve_access(self):
        if not self._has_finance_confirm_access():
            raise UserError(_("你没有批准费用/保证金单据的权限。"))

    def _check_business_ready(self):
        for rec in self:
            if rec.source_origin == "legacy":
                continue
            if not rec.project_id:
                raise UserError(_("费用/保证金单据必须关联项目。"))
            if rec._is_interfund_repayment() and rec.payment_request_id:
                raise UserError(_("往来款办理应与经营收付款申请分开，不应关联付款/收款申请。"))
            if rec._is_noncash_deduction_bill() and rec.payment_request_id:
                raise UserError(_("扣款单是扣款登记中的代扣列支明细，表达公司与项目/承包人之间的责任清分事实，不应关联付款/收款申请；扣款实缴或退回请使用对应现金办理入口。"))
            if rec.payment_anchor_policy in ("pay_request_required", "receive_request_required") and not rec.payment_request_id:
                raise UserError(_("新系统费用/扣款/保证金现金办理必须关联付款/收款申请。"))
            if not rec.partner_id:
                raise UserError(_("新系统费用/保证金单据必须选择往来单位。"))
            if (rec.amount or 0.0) <= 0:
                raise UserError(_("费用/保证金申请金额必须大于 0。"))
            if (rec.approved_amount or 0.0) < 0:
                raise UserError(_("费用/保证金批准金额不能为负数。"))
            expected = rec.approved_amount or rec.amount or 0.0
            if (rec.paid_amount or 0.0) < 0:
                raise UserError(_("费用/保证金已付款金额不能为负数。"))
            if (rec.paid_amount or 0.0) > expected:
                raise UserError(_("费用/保证金已付款金额不能超过批准/申请金额。"))
            if rec._is_noncash_deduction_bill():
                rec._check_deduction_bill_lines_or_raise()
            rec._check_attachment_policy_or_raise()
            rec._check_deposit_refund_balance_or_raise()
            if rec._is_noncash_deduction_bill():
                rec._check_company_contractor_deduction_responsibility_or_raise()
                continue
            if rec.financial_flow == "cash_out":
                payee_account = rec.payee_account or rec.receipt_account_name or rec.payee
                payer_account = rec.payer_account or rec.payment_account_name
                if not payee_account:
                    raise UserError(_("新系统现金流出办理必须填写收款账户信息。"))
                if not payer_account:
                    raise UserError(_("新系统现金流出办理必须填写付款账户信息。"))
            elif rec.financial_flow == "cash_in":
                receiving_account = rec.payer_account or rec.payment_account_name
                if not receiving_account:
                    raise UserError(_("新系统现金流入办理必须填写收款账户信息。"))
            rec._check_payment_request_scope_or_raise()

    def _check_deposit_refund_balance_or_raise(self):
        for rec in self:
            if rec.claim_type != "deposit_refund":
                continue
            amount = rec.approved_amount or rec.amount or 0.0
            if amount <= 0:
                continue
            balance = rec._deposit_refund_available_balance()
            rounding = rec.currency_id.rounding if rec.currency_id else 0.01
            if float_compare(amount, balance, precision_rounding=rounding) == 1:
                raise UserError(
                    _("保证金退回金额不能超过同项目、同往来单位、同保证金类型的已缴未退余额。当前可退余额：%s。")
                    % balance
                )

    def _deposit_refund_available_balance(self):
        self.ensure_one()
        if not self.project_id or not self.partner_id:
            return 0.0
        domain_base = [
            ("active", "=", True),
            ("project_id", "=", self.project_id.id),
            ("partner_id", "=", self.partner_id.id),
            ("guarantee_type", "=", self.guarantee_type or "bid"),
            ("state", "in", ["done", "legacy_confirmed"]),
        ]
        if self.id:
            domain_base.append(("id", "!=", self.id))
        Claim = self.env["sc.expense.claim"].sudo()
        Claim.flush_model(["active", "project_id", "partner_id", "guarantee_type", "state", "claim_type", "approved_amount", "amount"])
        paid_rows = Claim.read_group(
            domain_base + [("claim_type", "=", "deposit_pay")],
            ["approved_amount:sum", "amount:sum"],
            [],
        )
        refund_rows = Claim.read_group(
            domain_base + [("claim_type", "=", "deposit_refund")],
            ["approved_amount:sum", "amount:sum"],
            [],
        )

        def total(rows):
            if not rows:
                return 0.0
            row = rows[0]
            return float(
                row.get("approved_amount_sum")
                or row.get("approved_amount")
                or row.get("amount_sum")
                or row.get("amount")
                or 0.0
            )

        return max(total(paid_rows) - total(refund_rows), 0.0)

    def _check_company_contractor_deduction_responsibility_or_raise(self):
        for rec in self:
            if rec.source_origin == "legacy" and rec.state == "legacy_confirmed":
                continue
            if not rec._is_noncash_deduction_bill():
                continue
            summary = rec.company_contractor_responsibility_summary_id
            if not summary:
                continue
            amount = rec.approved_amount or rec.amount or 0.0
            failures = rec._company_contractor_responsibility_balance_failures(summary, amount, _("本次扣款金额"))
            if failures:
                raise_guard(
                        "EXPENSE_CLAIM_DEDUCTION_RESPONSIBILITY_BALANCE_BLOCKED",
                        f"扣款单[{rec.display_name}]",
                        _("办理扣款登记"),
                        reasons=failures,
                        hints=[_("打开公司-承包人责任余额，核对到款确认、已拨付、已扣除税费和已列支明细后再继续办理。")],
                    )

    def _check_deduction_bill_lines_or_raise(self):
        for rec in self:
            if rec.source_origin == "legacy" and rec.state == "legacy_confirmed":
                continue
            if not rec._is_noncash_deduction_bill():
                continue
            lines = rec.deduction_line_ids
            if not lines:
                raise UserError(_("扣款登记必须填写至少一条扣款单明细后才能提交、批准或完成。"))
            for line in lines:
                if not (line.item_name or "").strip():
                    raise UserError(_("扣款单明细必须填写扣款事项。"))
                if (line.amount or 0.0) <= 0:
                    raise UserError(_("扣款单明细金额必须大于 0。"))
            total = sum(lines.mapped("amount"))
            expected = rec.approved_amount or rec.amount or 0.0
            rounding = rec.currency_id.rounding if rec.currency_id else 0.01
            if float_compare(total, expected, precision_rounding=rounding) != 0:
                raise UserError(_("扣款单明细金额合计必须等于本次扣款金额。当前明细合计：%s，本次扣款金额：%s。") % (total, expected))

    def _check_attachment_policy_or_raise(self):
        self.ensure_one()
        category = self.business_category_id
        if category and category.attachment_policy == "required" and not self.attachment_ids:
            raise UserError(_("当前业务分类要求上传附件后才能提交、批准或完成。"))

    def _sync_payment_request_done(self):
        for rec in self:
            request = rec.payment_request_id
            if not request or request.state == "done":
                continue
            rec._check_payment_request_scope_or_raise()
            expected_type = rec._expected_payment_request_type()
            if not expected_type:
                raise UserError(_("非现金或内部往来办理不应自动完成付款/收款申请。"))
            if request.type != expected_type:
                raise UserError(
                    _("费用/保证金资金方向与付款/收款申请类型不一致，不能自动完成申请。")
                )
            rounding = request.currency_id.rounding if request.currency_id else 0.01
            amount = rec.approved_amount or rec.amount or 0.0
            if float_compare(amount, request.amount or 0.0, precision_rounding=rounding) == -1:
                raise UserError(_("费用/保证金批准金额低于付款/收款申请金额，不能自动完成申请。"))
            if request.state == "submit" and request.validation_status == "validated":
                request.with_context(tier_validation_callback=True).action_on_tier_approved()
                request.invalidate_recordset()
            if request.state == "approve" and request.validation_status == "validated":
                request.action_set_approved()
                request.invalidate_recordset()
            if request.state != "approved":
                continue
            if request.type == "receive":
                before = request._snapshot_audit_payload()
                request.with_context(payment_soft_gate=True)._ensure_treasury_ledger(
                    amount=request.amount or 0.0,
                    date=rec.date_claim,
                    note=_("auto:expense_claim_done"),
                )
                request.with_context(allow_transition=True, payment_soft_gate=True).write({"state": "done"})
                after = request._snapshot_audit_payload()
                request._audit_transition("payment_paid", before, after, action_name="expense_claim_done")
            else:
                before = request._snapshot_audit_payload()
                request.with_context(payment_soft_gate=True)._ensure_payment_ledger(
                    amount=request.amount or 0.0,
                    ref=rec.name,
                    note=_("auto:expense_claim_done"),
                )
                request.with_context(allow_transition=True, payment_soft_gate=True).write({"state": "done"})
                after = request._snapshot_audit_payload()
                request._audit_transition("payment_paid", before, after, action_name="expense_claim_done")

    def _ensure_interfund_cash_ledger(self):
        Ledger = self.env["sc.treasury.ledger"]
        for rec in self:
            if not rec._is_interfund_repayment() or (rec.approved_amount or rec.amount or 0.0) <= 0:
                continue
            Ledger._ensure_interfund_ledger(
                rec,
                project=rec.project_id,
                partner=rec.partner_id,
                direction="in" if rec.direction == "inflow" else "out",
                amount=rec.approved_amount or rec.amount or 0.0,
                date=rec.date_claim,
                currency=rec.currency_id,
                note=_("auto:expense_claim_interfund_done"),
            )

    def _check_payment_request_scope_or_raise(self):
        for rec in self:
            request = rec.payment_request_id
            if not request:
                continue
            if rec.source_origin == "legacy" and rec.state == "legacy_confirmed":
                continue
            expected_type = rec._expected_payment_request_type()
            if not expected_type:
                raise UserError(_("非现金或内部往来办理不应关联付款/收款申请。"))
            if request.type != expected_type:
                raise UserError(_("费用/保证金资金方向与付款/收款申请类型不一致。"))
            if rec.project_id and request.project_id and rec.project_id != request.project_id:
                raise UserError(_("费用/保证金项目必须与付款/收款申请项目一致。"))
            if rec.partner_id and request.partner_id and rec.partner_id != request.partner_id:
                raise UserError(_("费用/保证金往来单位必须与付款/收款申请往来单位一致。"))

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移费用/保证金单据不能在新系统取消。"))
            if rec.state not in ("draft", "submit", "approved"):
                raise UserError(_("只有草稿、已提交或已批准的费用/保证金单据可以取消。"))
            before = rec._snapshot_audit_payload()
            rec.write({"state": "cancel"})
            rec._audit_transition(
                "expense_claim_cancelled",
                before,
                rec._snapshot_audit_payload(),
                "action_cancel",
            )

    def _snapshot_audit_payload(self):
        self.ensure_one()
        return {
            "state": self.state,
            "source_origin": self.source_origin,
            "claim_type": self.claim_type,
            "direction": self.direction,
            "business_axis": self.business_axis,
            "handling_kind": self.handling_kind,
            "financial_flow": self.financial_flow,
            "payment_anchor_policy": self.payment_anchor_policy,
            "project_id": self.project_id.id,
            "company_id": self.company_id.id,
            "partner_id": self.partner_id.id,
            "payment_request_id": self.payment_request_id.id,
            "date_claim": fields.Date.to_string(self.date_claim) if self.date_claim else False,
            "expense_type": self.expense_type,
            "summary": self.summary,
            "amount": self.amount,
            "approved_amount": self.approved_amount,
            "paid_amount": self.paid_amount,
            "currency_id": self.currency_id.id,
            "payment_state": self.payment_state,
            "reject_reason": self.reject_reason,
            "validation_status": self.validation_status,
        }

    def _audit_transition(self, event_code, before, after, action_name):
        self.ensure_one()
        return self.env["sc.audit.log"].write_event(
            event_code,
            self._name,
            self.id,
            action=action_name,
            before=before,
            after=after,
            company_id=self.company_id,
            project_id=self.project_id,
        )


class ScExpenseClaimDeductionLine(models.Model):
    _name = "sc.expense.claim.deduction.line"
    _description = "扣款单明细"
    _order = "claim_id, sequence, id"

    claim_id = fields.Many2one(
        "sc.expense.claim",
        string="扣款登记",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(string="序号", default=10)
    item_name = fields.Char(string="明细名称", required=True, index=True)
    deduction_category = fields.Selection(
        [
            ("management_fee", "管理费"),
            ("enterprise_income_tax", "企业所得税"),
            ("vat", "增值税"),
            ("vat_surcharge", "增值税附加"),
            ("construction_stamp_tax", "建安印花税"),
            ("purchase_sale_stamp_tax", "购销合同印花税"),
            ("vat_nonrefundable", "增值税（不可退）"),
            ("individual_income_tax", "个人所得税"),
            ("vat_surcharge_nonrefundable", "增值税附加（不可退）"),
            ("risk_reserve", "风险责任金"),
            ("interest", "利息"),
            ("project_management_fee", "项目管理费"),
            ("labor_tax_fee", "项目劳务税费"),
            ("cost_invoice_withholding", "暂扣成本票"),
            ("archive_deposit", "档案保证金"),
            ("data_fee", "资料费"),
            ("social_security", "社保费"),
            ("tax", "税费（未细分）"),
            ("service_fee", "服务费"),
            ("other", "其他扣款"),
        ],
        string="扣款分类",
        required=True,
        index=True,
    )
    amount = fields.Monetary(string="扣款金额", currency_field="currency_id", required=True)
    currency_id = fields.Many2one(related="claim_id.currency_id", store=True, readonly=True)
    note = fields.Char(string="备注")

    _sql_constraints = [
        ("amount_positive", "CHECK(amount > 0)", "扣款单明细金额必须大于 0。"),
    ]
