# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class ScExpenseClaim(models.Model):
    _name = "sc.expense.claim"
    _description = "费用与保证金单据"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
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
    claim_flow_label = fields.Char(string="办理事项", compute="_compute_claim_flow_label")
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
        default=lambda self: self.env.company.currency_id.id,
    )
    payment_request_id = fields.Many2one("payment.request", string="付款/收款申请", index=True, ondelete="set null")
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_no = fields.Char(string="历史单据号", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    legacy_visible_document_state = fields.Char(string="历史可见单据状态", readonly=True)
    legacy_visible_document_no = fields.Char(string="历史可见单据编号", readonly=True)
    legacy_visible_date = fields.Datetime(string="历史可见日期", readonly=True)
    legacy_visible_push_result = fields.Char(string="历史可见推送结果", readonly=True)
    legacy_visible_payment_time = fields.Char(string="历史可见付款时间", readonly=True)
    legacy_visible_expense_type = fields.Char(string="历史可见成本类别", readonly=True)
    legacy_visible_note = fields.Text(string="历史可见备注", readonly=True)
    legacy_visible_project_name = fields.Char(string="历史可见项目名称", readonly=True)
    legacy_visible_department = fields.Char(string="历史可见部门", readonly=True)
    legacy_visible_summary = fields.Text(string="历史可见事项说明/用途", readonly=True)
    legacy_visible_amount = fields.Char(string="历史可见金额", readonly=True)
    legacy_visible_title = fields.Char(string="历史可见标题", readonly=True)
    legacy_visible_adjustment_item = fields.Char(string="历史可见上缴内容", readonly=True)
    legacy_visible_returned_flag = fields.Char(string="历史可见是否退回", readonly=True)
    legacy_visible_borrower = fields.Char(string="历史可见借款人", readonly=True)
    legacy_visible_loan_amount = fields.Char(string="历史可见借款金额", readonly=True)
    legacy_visible_repayment_amount = fields.Char(string="历史可见还款金额", readonly=True)
    legacy_visible_loan_rate = fields.Char(string="历史可见借款利率", readonly=True)
    legacy_visible_interest = fields.Char(string="历史可见利息", readonly=True)
    legacy_visible_repayment_time = fields.Datetime(string="历史可见还款时间", readonly=True)
    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True, readonly=True)
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
            "Legacy expense/deposit claim source must be unique.",
        ),
        ("amount_nonnegative", "CHECK(amount >= 0)", "Claim amount must be non-negative."),
        ("paid_amount_nonnegative", "CHECK(paid_amount IS NULL OR paid_amount >= 0)", "Paid amount must be non-negative."),
    ]

    @api.depends("claim_type")
    def _compute_direction(self):
        for rec in self:
            rec.direction = (
                "inflow"
                if rec.claim_type in ("deposit_refund", "deposit_receive", "deduction_refund", "project_company_repay")
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

    @api.onchange("amount")
    def _onchange_amount(self):
        for rec in self:
            if not rec.approved_amount:
                rec.approved_amount = rec.amount

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
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.expense.claim") or _("Expense Claim")
            vals.setdefault("approved_amount", vals.get("amount", 0.0))
        return super().create(vals_list)

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
                "creator_legacy_user_id",
                "creator_name",
                "created_time",
                "write_uid",
                "write_date",
            }
            blocked = set(vals) - allowed
            for field_name in list(blocked):
                if all(rec[field_name] == vals[field_name] for rec in self):
                    blocked.remove(field_name)
            if blocked:
                raise UserError(_("历史迁移费用/保证金单据已确认，只允许补充支付锚点、往来单位、备注和历史录入审计事实。"))
        return super().write(vals)

    @api.depends("amount", "approved_amount", "paid_amount")
    def _compute_unpaid_amount(self):
        for rec in self:
            expected = rec.approved_amount or rec.amount or 0.0
            rec.unpaid_amount = max(expected - (rec.paid_amount or 0.0), 0.0)

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_expense_claim
               SET department_name = COALESCE(NULLIF(department_name, ''), NULLIF(legacy_visible_department, '')),
                   payment_state = COALESCE(
                       NULLIF(payment_state, ''),
                       NULLIF(legacy_document_state, ''),
                       NULLIF(legacy_visible_document_state, ''),
                       state
                   ),
                   paid_amount = COALESCE(paid_amount, approved_amount, amount, 0.0)
             WHERE source_origin = 'legacy'
            """
        )

    def action_submit(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿状态的费用/保证金单据可以提交。"))
            rec._check_business_ready()
            if policy.is_approval_required(rec._name, company=rec.company_id):
                rec.write({"state": "submit", "reject_reason": False})
                company = rec.company_id or self.env.company
                rec.with_company(company).with_context(
                    allowed_company_ids=[company.id],
                ).request_validation()
            else:
                rec.write({"state": "approved", "reject_reason": False})

    def action_approve(self):
        policy_model = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state != "submit":
                raise UserError(_("只有已提交的费用/保证金单据可以批准。"))
            rec._check_business_ready()
            if policy_model.is_approval_required(rec._name, company=rec.company_id):
                if rec.validation_status != "validated":
                    raise UserError(_("请先完成统一审批流程后再批准费用/保证金单据。"))
            else:
                policy = policy_model.get_active_policy(rec._name, company=rec.company_id)
                if policy:
                    policy.assert_user_can_approve()
            rec.state = "approved"

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
            rec._check_business_ready()
            rec.write({"state": "approved", "reject_reason": False})

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state != "submit":
                raise UserError(_("只有已提交的费用/保证金单据可以驳回。"))
            rec.write(
                {
                    "state": "draft",
                    "reject_reason": reason or rec._get_tier_reject_reason(),
                }
            )

    def action_done(self):
        for rec in self:
            if rec.state != "approved":
                raise UserError(_("只有已批准的费用/保证金单据可以完成。"))
            rec._check_business_ready()
            rec._sync_payment_request_done()
            rec.state = "done"

    def _check_business_ready(self):
        for rec in self:
            if not rec.project_id:
                raise UserError(_("费用/保证金单据必须关联项目。"))
            if (rec.amount or 0.0) <= 0:
                raise UserError(_("费用/保证金申请金额必须大于 0。"))
            if (rec.approved_amount or 0.0) < 0:
                raise UserError(_("费用/保证金批准金额不能为负数。"))
            expected = rec.approved_amount or rec.amount or 0.0
            if (rec.paid_amount or 0.0) < 0:
                raise UserError(_("费用/保证金已付款金额不能为负数。"))
            if (rec.paid_amount or 0.0) > expected:
                raise UserError(_("费用/保证金已付款金额不能超过批准/申请金额。"))
            rec._check_payment_request_scope_or_raise()

    def _sync_payment_request_done(self):
        for rec in self:
            request = rec.payment_request_id
            if not request or request.state == "done":
                continue
            rec._check_payment_request_scope_or_raise()
            expected_type = "receive" if rec.direction == "inflow" else "pay"
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
                request.with_context(payment_soft_gate=True)._ensure_payment_ledger(
                    amount=request.amount or 0.0,
                    ref=rec.name,
                    note=_("auto:expense_claim_done"),
                )
                request.with_context(allow_transition=True, payment_soft_gate=True).write({"state": "done"})

    def _check_payment_request_scope_or_raise(self):
        for rec in self:
            request = rec.payment_request_id
            if not request:
                continue
            if rec.source_origin == "legacy" and rec.state == "legacy_confirmed":
                continue
            expected_type = "receive" if rec.direction == "inflow" else "pay"
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
            rec.state = "cancel"
