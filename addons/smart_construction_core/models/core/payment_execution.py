# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

from ..support.state_guard import raise_guard


class ScPaymentExecution(models.Model):
    _name = "sc.payment.execution"
    _description = "付款执行"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation", "sc.company.contractor.responsibility.context.mixin"]
    _order = "date_payment desc, id desc"

    name = fields.Char(string="单据号", required=True, default="新建", copy=False)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    source_kind = fields.Selection(
        [
            ("outflow_request", "付款申请"),
            ("actual_outflow", "实际付款"),
        ],
        string="业务类型",
        default="outflow_request",
        required=True,
        index=True,
    )
    execution_flow_label = fields.Char(string="办理事项", compute="_compute_execution_flow_label")
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        index=True,
        ondelete="restrict",
        domain="[('target_model', '=', 'sc.payment.execution')]",
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("paid", "已付款"),
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
    contract_id = fields.Many2one(
        "construction.contract",
        string="合同",
        index=True,
        domain="[('project_id', '=', project_id)]",
    )
    payment_request_id = fields.Many2one(
        "payment.request",
        string="付款申请",
        index=True,
        ondelete="set null",
        domain="[('project_id', '=', project_id), ('type', '=', 'pay')]",
    )
    payment_request_partner_id = fields.Many2one(
        "res.partner",
        string="申请往来单位",
        related="payment_request_id.partner_id",
        store=True,
        readonly=True,
        index=True,
    )
    actual_payee_partner_id = fields.Many2one(
        "res.partner",
        string="实际收款单位",
        related="partner_id",
        store=True,
        readonly=True,
        index=True,
    )
    payment_request_partner_relation = fields.Selection(
        [
            ("no_request", "未关联付款申请"),
            ("same_partner", "申请方与收款方一致"),
            ("actual_payee_differs", "实际收款方不同"),
            ("missing_request_partner", "申请方为空"),
            ("missing_actual_payee", "实际收款方为空"),
        ],
        string="申请/收款方关系",
        compute="_compute_payment_request_partner_relation",
        store=True,
        readonly=True,
        index=True,
    )
    date_payment = fields.Date(string="单据日期", default=fields.Date.context_today, index=True)
    document_no = fields.Char(string="来源单号", index=True)
    payment_family = fields.Char(string="付款族", index=True)
    payment_method = fields.Char(string="付款方式", index=True)
    bank_account = fields.Char(string="付款账户", index=True)
    payment_account_name = fields.Char(string="付款账户名称", index=True)
    payment_account_no = fields.Char(string="付款账号", index=True)
    payment_bank_name = fields.Char(string="付款开户行", index=True)
    receipt_account_name = fields.Char(string="收款账户名称", index=True)
    receipt_account_no = fields.Char(string="收款账号", index=True)
    receipt_bank_name = fields.Char(string="收款开户行", index=True)
    handler_name = fields.Char(string="经办人", index=True)
    planned_amount = fields.Monetary(string="申请/计划金额", currency_field="currency_id")
    paid_amount = fields.Monetary(string="实付金额", currency_field="currency_id")
    invoice_amount = fields.Monetary(string="发票金额", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: (self.env.ref("base.CNY", raise_if_not_found=False) or self.env.company.currency_id).id,
    )
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    push_result = fields.Char(string="推送结果", index=True, readonly=True)
    kingdee_document_no = fields.Char(string="金蝶单据编号", index=True, readonly=True)
    creator_name = fields.Char(string="历史录入人", index=True, readonly=True)
    created_time = fields.Datetime(string="历史录入时间", index=True, readonly=True)
    reject_reason = fields.Char(string="驳回原因", readonly=True, copy=False)
    note = fields.Text(string="备注")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_payment_execution_attachment_rel",
        "execution_id",
        "attachment_id",
        string="附件",
    )
    active = fields.Boolean(string="有效", default=True, index=True)
    partner_payment_status_display = fields.Char(string="单据状态", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_date_display = fields.Char(string="付款日期", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_payee_unit = fields.Char(string="收款单位", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_actual_payee_unit = fields.Char(string="实际收款单位", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_amount_display = fields.Char(string="付款金额", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_category_display = fields.Char(string="支付类别", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_content_display = fields.Char(string="付款内容", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_method_display = fields.Char(string="付款方式名称", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_cost_type_display = fields.Char(string="类型（成本）", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_account_name_display = fields.Char(string="付款账户名称", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_attachment_text = fields.Char(string="附件", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_voucher_no = fields.Char(string="凭证号", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_writer = fields.Char(string="填写人", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_source_created_by = fields.Char(string="录入人", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_project_name = fields.Char(string="项目名称", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_source_text = fields.Char(string="付款单关联来源", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    partner_payment_document_no = fields.Char(string="单据编号", compute="_compute_partner_payment_visible_fields", store=True, readonly=True)
    company_finance_status_display = fields.Char(string="单据状态", compute="_compute_company_finance_visible_fields", store=True, readonly=True)
    company_finance_push_result = fields.Char(string="推送结果", compute="_compute_company_finance_visible_fields", store=True, readonly=True)
    company_finance_document_no = fields.Char(string="单据编号", compute="_compute_company_finance_visible_fields", store=True, readonly=True)
    company_finance_amount_display = fields.Char(string="付款金额", compute="_compute_company_finance_visible_fields", store=True, readonly=True)
    company_finance_cost_type_display = fields.Char(string="成本类别", compute="_compute_company_finance_visible_fields", store=True, readonly=True)
    company_finance_payee_unit = fields.Char(string="收款单位名称", compute="_compute_company_finance_visible_fields", store=True, readonly=True)
    company_finance_payment_account_name = fields.Char(string="付款账户名称", compute="_compute_company_finance_visible_fields", store=True, readonly=True)
    company_finance_note_display = fields.Char(string="备注", compute="_compute_company_finance_visible_fields", store=True, readonly=True)
    company_finance_source_created_by = fields.Char(string="录入人", compute="_compute_company_finance_visible_fields", store=True, readonly=True)
    company_finance_source_created_at = fields.Char(string="录入时间", compute="_compute_company_finance_visible_fields", store=True, readonly=True)
    company_finance_attachment_text = fields.Char(string="附件", compute="_compute_company_finance_visible_fields", store=True, readonly=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "历史付款执行来源记录必须唯一。",
        ),
        ("planned_amount_nonnegative", "CHECK(planned_amount >= 0)", "Planned amount must be non-negative."),
        ("paid_amount_nonnegative", "CHECK(paid_amount >= 0)", "Paid amount must be non-negative."),
        ("invoice_amount_nonnegative", "CHECK(invoice_amount >= 0)", "Invoice amount must be non-negative."),
    ]

    @api.depends("payment_request_id", "payment_request_partner_id", "actual_payee_partner_id")
    def _compute_payment_request_partner_relation(self):
        for record in self:
            if not record.payment_request_id:
                record.payment_request_partner_relation = "no_request"
            elif not record.payment_request_partner_id:
                record.payment_request_partner_relation = "missing_request_partner"
            elif not record.actual_payee_partner_id:
                record.payment_request_partner_relation = "missing_actual_payee"
            elif record.payment_request_partner_id == record.actual_payee_partner_id:
                record.payment_request_partner_relation = "same_partner"
            else:
                record.payment_request_partner_relation = "actual_payee_differs"

    @api.depends("source_kind", "payment_family", "payment_method")
    def _compute_execution_flow_label(self):
        for record in self:
            family = (record.payment_family or "").strip()
            method = (record.payment_method or "").strip()
            if family:
                record.execution_flow_label = family
            elif record.source_kind == "actual_outflow":
                record.execution_flow_label = _("实际付款登记")
            elif method:
                record.execution_flow_label = _("付款执行：%s") % method
            else:
                record.execution_flow_label = _("付款执行")

    @staticmethod
    def _partner_payment_state_label(value):
        return {
            "-1": "已作废",
            "0": "未审核",
            "1": "审核中",
            "2": "审核通过",
            "3": "已驳回",
            "4": "已作废",
            "draft": "草稿",
            "confirmed": "已确认",
            "paid": "已付款",
            "legacy_confirmed": "历史已确认",
            "cancel": "已取消",
        }.get(str(value or ""), str(value or ""))

    def _partner_payment_attachment_label(self):
        self.ensure_one()
        count = len(self.attachment_ids)
        return "附件(%s)" % count if count else ""

    @api.depends(
        "state",
        "date_payment",
        "partner_id",
        "receipt_account_name",
        "paid_amount",
        "payment_family",
        "source_kind",
        "payment_method",
        "note",
        "business_category_id",
        "payment_account_name",
        "attachment_ids",
        "kingdee_document_no",
        "handler_name",
        "creator_name",
        "project_id",
        "payment_request_id",
        "document_no",
        "name",
    )
    def _compute_partner_payment_visible_fields(self):
        for record in self:
            record.partner_payment_status_display = record._partner_payment_state_label(record.state)
            record.partner_payment_date_display = fields.Date.to_string(record.date_payment) if record.date_payment else ""
            record.partner_payment_payee_unit = record.partner_id.display_name or record.receipt_account_name or ""
            record.partner_payment_actual_payee_unit = record.receipt_account_name or record.partner_id.display_name or ""
            record.partner_payment_amount_display = str(record.paid_amount or "")
            record.partner_payment_category_display = record.payment_family or record.payment_method or ""
            record.partner_payment_content_display = record.note or ""
            record.partner_payment_method_display = record.payment_family or record.payment_method or ""
            record.partner_payment_cost_type_display = record.business_category_id.display_name or record.payment_family or record.payment_method or ""
            record.partner_payment_account_name_display = record.payment_account_name or ""
            record.partner_payment_attachment_text = record._partner_payment_attachment_label()
            record.partner_payment_voucher_no = record.kingdee_document_no or ""
            record.partner_payment_writer = record.handler_name or record.creator_name or ""
            record.partner_payment_source_created_by = record.creator_name or ""
            record.partner_payment_project_name = record.project_id.display_name or ""
            record.partner_payment_source_text = record.payment_request_id.display_name or record.document_no or record.name or ""
            record.partner_payment_document_no = record.document_no or record.name or ""

    @api.depends(
        "state",
        "legacy_document_state",
        "push_result",
        "document_no",
        "name",
        "paid_amount",
        "payment_family",
        "payment_method",
        "business_category_id",
        "receipt_account_name",
        "partner_id",
        "payment_account_name",
        "note",
        "creator_name",
        "created_time",
        "attachment_ids",
    )
    def _compute_company_finance_visible_fields(self):
        for record in self:
            status_value = record.legacy_document_state or record.state
            record.company_finance_status_display = record._partner_payment_state_label(status_value)
            record.company_finance_push_result = record.push_result or ""
            record.company_finance_document_no = record.document_no or record.name or ""
            record.company_finance_amount_display = (
                str(record.paid_amount) if record.paid_amount is not False and record.paid_amount is not None else ""
            )
            record.company_finance_cost_type_display = (
                record.payment_method
                or record.payment_family
                or record.business_category_id.display_name
                or ""
            )
            record.company_finance_payee_unit = record.receipt_account_name or record.partner_id.display_name or ""
            record.company_finance_payment_account_name = record.payment_account_name or ""
            record.company_finance_note_display = record.note or ""
            record.company_finance_source_created_by = record.creator_name or ""
            record.company_finance_source_created_at = (
                fields.Datetime.to_string(record.created_time) if record.created_time else ""
            )
            record.company_finance_attachment_text = record._partner_payment_attachment_label()

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
        return res

    def _payment_request_values(self, request):
        if not request:
            return {}
        receipt_account_name = request.payment_account_name or request.partner_account_name or ""
        receipt_bank_name = request.payment_bank_name or request.partner_bank_name or ""
        receipt_account_no = request.payment_account_no or request.partner_bank_account or ""
        payment_account_name = request.legacy_payment_account_name or request.payer_unit or ""
        payment_account_no = request.legacy_payment_account_no or ""
        return {
            "project_id": request.project_id.id,
            "partner_id": request.partner_id.id,
            "contract_id": request.contract_id.id,
            "payment_request_id": request.id,
            "source_kind": "actual_outflow",
            "payment_family": "往来单位付款",
            "document_no": request.name,
            "planned_amount": request.amount or 0.0,
            "paid_amount": request.amount or 0.0,
            "currency_id": request.currency_id.id,
            "receipt_account_name": receipt_account_name,
            "receipt_bank_name": receipt_bank_name,
            "receipt_account_no": receipt_account_no,
            "payment_account_name": payment_account_name,
            "payment_account_no": payment_account_no,
            "note": request.note or "",
        }

    @api.onchange("payment_request_id")
    def _onchange_payment_request_id(self):
        if not self.payment_request_id:
            return
        for field_name, value in self._payment_request_values(self.payment_request_id).items():
            setattr(self, field_name, value)

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            project_id = self._context_project_id()
            if project_id:
                vals.setdefault("project_id", project_id)
            request_id = vals.get("payment_request_id")
            if request_id:
                request = self.env["payment.request"].browse(request_id).exists()
                for field_name, value in self._payment_request_values(request).items():
                    vals.setdefault(field_name, value)
            vals.setdefault("business_category_id", self._resolve_business_category_id(vals))
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.payment.execution") or _("Payment Execution")
        return super().create(vals_list)

    @api.model
    def _resolve_business_category_code(self, vals):
        code = self.env.context.get("default_business_category_code") or self.env.context.get(
            "current_business_category_code"
        )
        if code:
            return code
        payment_family = vals.get("payment_family") or self.env.context.get("default_payment_family") or ""
        if payment_family in ("公司财务支出", "actual_outflow"):
            return "finance.payment.execution.company"
        return "finance.payment.execution.partner"

    @api.model
    def _resolve_business_category_id(self, vals):
        code = self._resolve_business_category_code(vals)
        category = self.env["sc.business.category"].sudo().search(
            [("code", "=", code), ("target_model", "=", self._name)],
            limit=1,
        )
        return category.id if category else False

    def _history_surface_allowed_write_fields(self):
        return set()

    def write(self, vals):
        if (
            any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self)
            and not self.env.context.get("history_surface_sync")
        ):
            projection_fields = {
                name
                for name in self._fields
                if name.startswith("partner_payment_") or name.startswith("company_finance_")
            }
            allowed = {
                "payment_request_id",
                "partner_id",
                "contract_id",
                "creator_name",
                "created_time",
                "note",
                "active",
                "write_uid",
                "write_date",
            } | projection_fields | self._history_surface_allowed_write_fields()
            if set(vals) - allowed:
                raise UserError(_("历史迁移付款执行单据已确认，只允许补充业务锚点和备注。"))
        return super().write(vals)

    def action_confirm(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state != "draft":
                raise_guard(
                    "PAYMENT_EXECUTION_INVALID_TRANSITION",
                    f"付款执行[{rec.display_name}]",
                    _("确认付款执行"),
                    reasons=[_("只有草稿状态的付款执行可以确认")],
                )
            rec._check_business_anchor_or_raise()
            rec._check_payment_request_scope_or_raise()
            rec._check_company_contractor_payment_responsibility_or_raise()
            if policy.is_approval_required(rec._name, company=rec.company_id):
                company = rec.company_id or self.env.company
                rec.with_company(company).with_context(allowed_company_ids=[company.id])._request_document_approval()
            else:
                rec.write({"state": "confirmed", "reject_reason": False})

    def action_paid(self):
        self._assert_finance_confirm_access()
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state not in ("draft", "confirmed"):
                raise_guard(
                    "PAYMENT_EXECUTION_INVALID_TRANSITION",
                    f"付款执行[{rec.display_name}]",
                    _("登记付款"),
                    reasons=[_("只有草稿或已确认状态的付款执行可以登记付款")],
                )
            rec._check_business_anchor_or_raise()
            rec._check_payment_request_scope_or_raise()
            rec._check_company_contractor_payment_responsibility_or_raise()
            if policy.is_approval_required(rec._name, company=rec.company_id) and rec.validation_status != "validated":
                raise UserError(_("付款执行尚未完成统一审批流程。"))
            rec.state = "paid"
            rec._sync_payment_request_done()

    def _has_finance_confirm_access(self):
        return (
            self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager")
            or self.env.user.has_group("smart_construction_custom.group_sc_role_finance")
        )

    def _assert_finance_confirm_access(self):
        if not self._has_finance_confirm_access():
            raise UserError(_("你没有登记付款的财务确认权限。"))

    def _assert_finance_cancel_access(self):
        if not self._has_finance_confirm_access():
            raise UserError(_("你没有取消或撤销付款执行的财务权限。"))

    def _sync_payment_request_done(self):
        for rec in self:
            request = rec.payment_request_id
            if not request or request.state == "done":
                continue
            rec._check_payment_request_scope_or_raise()
            if request.state == "approve" and request.validation_status == "validated":
                request.action_set_approved()
                request.invalidate_recordset()
            if request.state != "approved":
                continue
            rounding = request.currency_id.rounding if request.currency_id else 0.01
            if float_compare(rec.paid_amount or 0.0, request.amount or 0.0, precision_rounding=rounding) == -1:
                raise UserError(_("实付金额低于付款申请金额，不能自动完成付款申请。"))
            before = request._snapshot_audit_payload()
            request.with_context(payment_soft_gate=True)._ensure_payment_ledger(
                amount=request.amount or 0.0,
                ref=rec.name,
                note=_("auto:payment_execution_paid"),
            )
            request.with_context(allow_transition=True, payment_soft_gate=True).write({"state": "done"})
            after = request._snapshot_audit_payload()
            request._audit_transition("payment_paid", before, after, action_name="payment_execution_paid")

    def action_cancel(self):
        self._assert_finance_cancel_access()
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移付款执行单据不能在新系统取消。"))
            if rec.state == "paid":
                rec._reverse_paid_execution()
                continue
            if rec.state in ("legacy_confirmed", "cancel"):
                raise_guard(
                    "PAYMENT_EXECUTION_INVALID_TRANSITION",
                    f"付款执行[{rec.display_name}]",
                    _("取消付款执行"),
                    reasons=[_("历史已确认或已取消的付款执行不能取消")],
                )
            rec.state = "cancel"

    def _reverse_paid_execution(self):
        for rec in self:
            request = rec.payment_request_id
            if not request:
                raise_guard(
                    "PAYMENT_EXECUTION_MISSING_REQUEST",
                    f"付款执行[{rec.display_name}]",
                    _("撤销已付款"),
                    reasons=[_("已付款执行必须关联付款申请才能撤销")],
                )
            ledger = self.env["payment.ledger"].sudo().search(
                [("payment_request_id", "=", request.id)],
                limit=1,
            )
            if not ledger:
                raise_guard(
                    "PAYMENT_LEDGER_NOT_FOUND",
                    f"付款执行[{rec.display_name}]",
                    _("撤销已付款"),
                    reasons=[_("未找到对应付款台账，不能自动撤销")],
                )
            before = request._snapshot_audit_payload()
            ledger.with_context(allow_payment_reversal=True).unlink()
            if request.state == "done":
                request.with_context(allow_transition=True, payment_soft_gate=True).write({"state": "approved"})
            rec.write({"state": "cancel"})
            after = request._snapshot_audit_payload()
            request._audit_transition("payment_reversed", before, after, action_name="payment_execution_cancel")
            rec.message_post(body=_("已撤销付款登记，并将付款申请退回已批准状态。"))

    def _check_business_anchor_or_raise(self):
        for rec in self:
            if rec.source_origin == "legacy":
                continue
            if not rec.project_id:
                raise_guard(
                    "PAYMENT_EXECUTION_MISSING_PROJECT",
                    f"付款执行[{rec.display_name}]",
                    _("办理付款执行"),
                    reasons=[_("付款执行必须关联项目")],
                )
            if not rec.payment_request_id:
                raise_guard(
                    "PAYMENT_EXECUTION_MISSING_REQUEST",
                    f"付款执行[{rec.display_name}]",
                    _("办理付款执行"),
                    reasons=[_("新系统付款执行必须关联已审批的付款申请")],
                )
            request = rec.payment_request_id
            material_settlement = request.material_settlement_id if request else False
            if not rec.contract_id and not material_settlement and not (request and request._has_payment_basis()):
                raise_guard(
                    "PAYMENT_EXECUTION_MISSING_CONTRACT",
                    f"付款执行[{rec.display_name}]",
                    _("办理付款执行"),
                    reasons=[_("新系统付款执行必须关联合同或结算依据")],
                )
            if not rec.partner_id:
                raise_guard(
                    "PAYMENT_EXECUTION_MISSING_PARTNER",
                    f"付款执行[{rec.display_name}]",
                    _("办理付款执行"),
                    reasons=[_("付款执行必须选择往来单位")],
                )
            if (rec.paid_amount or 0.0) <= 0:
                raise_guard(
                    "PAYMENT_EXECUTION_INVALID_AMOUNT",
                    f"付款执行[{rec.display_name}]",
                    _("办理付款执行"),
                    reasons=[_("实付金额必须大于0")],
                )
            payer_account = rec.payment_account_no or rec.bank_account or rec.payment_account_name
            payee_account = rec.receipt_account_no or rec.receipt_account_name
            if not payer_account:
                raise_guard(
                    "PAYMENT_EXECUTION_MISSING_PAYER_ACCOUNT",
                    f"付款执行[{rec.display_name}]",
                    _("办理付款执行"),
                    reasons=[_("新系统付款执行必须填写付款账户信息")],
                )
            if not payee_account:
                raise_guard(
                    "PAYMENT_EXECUTION_MISSING_PAYEE_ACCOUNT",
                    f"付款执行[{rec.display_name}]",
                    _("办理付款执行"),
                    reasons=[_("新系统付款执行必须填写收款账户信息")],
                )

    def _check_payment_request_scope_or_raise(self):
        for rec in self:
            request = rec.payment_request_id
            if not request:
                continue
            if rec.source_origin == "legacy" and rec.state == "legacy_confirmed":
                continue
            if request.type != "pay":
                raise UserError(_("付款登记只能关联付款类型的付款申请。"))
            if rec.project_id and request.project_id and rec.project_id != request.project_id:
                raise UserError(_("付款登记项目必须与付款申请项目一致。"))
            if rec.partner_id and request.partner_id and rec.partner_id != request.partner_id:
                raise UserError(_("付款登记往来单位必须与付款申请往来单位一致。"))
            if rec.contract_id and request.contract_id and rec.contract_id != request.contract_id:
                raise UserError(_("付款登记合同必须与付款申请合同一致。"))

    def _company_contractor_payment_responsibility_failures(self, summary, paid_amount):
        return self._company_contractor_responsibility_balance_failures(summary, paid_amount, _("本次实付金额"))

    def _check_company_contractor_payment_responsibility_or_raise(self):
        for rec in self:
            if rec.source_origin == "legacy" and rec.state == "legacy_confirmed":
                continue
            summary = rec.company_contractor_responsibility_summary_id
            if not summary:
                continue
            failures = rec._company_contractor_payment_responsibility_failures(summary, rec.paid_amount or 0.0)
            if failures:
                raise_guard(
                    "PAYMENT_EXECUTION_RESPONSIBILITY_BALANCE_BLOCKED",
                    f"付款执行[{rec.display_name}]",
                    _("办理付款执行"),
                    reasons=failures,
                    hints=[_("打开公司-承包人责任余额，核对到款确认、自筹、拨付和扣款明细后再继续办理。")],
                )

    def _request_document_approval(self):
        self.ensure_one()
        if self.review_ids and self.validation_status == "rejected":
            self.restart_validation()
        elif not self.review_ids or self.validation_status == "no":
            reviews = self.request_validation()
            if not reviews:
                raise UserError(_("付款执行已启用审批，但没有匹配的统一审批规则，请检查业务审批配置。"))
        else:
            raise UserError(_("付款执行已经在统一审批流程中，请等待审批完成。"))

    def _check_state_from_condition(self):
        self.ensure_one()
        parent = getattr(super(), "_check_state_from_condition", None)
        base_ok = parent() if parent else False
        return base_ok or self.state == "draft"

    def _get_tier_reject_reason(self):
        self.ensure_one()
        reviews = self.review_ids.filtered(lambda review: review.status == "rejected" and review.comment)
        if reviews:
            return reviews.sorted(lambda review: review.write_date or review.create_date, reverse=True)[0].comment
        return _("OCA审批驳回（未填写原因）")

    def action_on_tier_approved(self):
        for rec in self:
            if rec.state == "draft":
                rec.with_context(skip_validation_check=True).write({"state": "confirmed", "reject_reason": False})

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state == "draft":
                rec.with_context(skip_validation_check=True).write(
                    {"reject_reason": reason or rec._get_tier_reject_reason()}
                )

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_payment_execution execution
               SET business_category_id = category.id
              FROM sc_business_category category
             WHERE execution.business_category_id IS NULL
               AND category.target_model = 'sc.payment.execution'
               AND category.code = CASE
                   WHEN COALESCE(execution.payment_family, '') IN ('公司财务支出', 'actual_outflow')
                       THEN 'finance.payment.execution.company'
                   ELSE 'finance.payment.execution.partner'
               END
            """
        )
