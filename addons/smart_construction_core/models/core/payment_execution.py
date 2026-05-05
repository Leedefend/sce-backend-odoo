# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScPaymentExecution(models.Model):
    _name = "sc.payment.execution"
    _description = "付款执行"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
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
            ("outflow_request", "付款申请残余"),
            ("actual_outflow", "实付残余"),
        ],
        string="业务类型",
        default="outflow_request",
        required=True,
        index=True,
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
    contract_id = fields.Many2one("construction.contract", string="合同", index=True)
    payment_request_id = fields.Many2one("payment.request", string="付款申请", index=True, ondelete="set null")
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
        default=lambda self: self.env.company.currency_id.id,
    )
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    legacy_residual_reason = fields.Char(string="残余原因", index=True, readonly=True)
    legacy_attachment_ref = fields.Char(string="历史附件引用", readonly=True)
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

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "Legacy payment execution source must be unique.",
        ),
        ("planned_amount_nonnegative", "CHECK(planned_amount >= 0)", "Planned amount must be non-negative."),
        ("paid_amount_nonnegative", "CHECK(paid_amount >= 0)", "Paid amount must be non-negative."),
        ("invoice_amount_nonnegative", "CHECK(invoice_amount >= 0)", "Invoice amount must be non-negative."),
    ]

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
        return {
            "project_id": request.project_id.id,
            "partner_id": request.partner_id.id,
            "contract_id": request.contract_id.id,
            "payment_request_id": request.id,
            "document_no": request.name,
            "planned_amount": request.amount or 0.0,
            "paid_amount": request.amount or 0.0,
            "currency_id": request.currency_id.id,
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
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.payment.execution") or _("Payment Execution")
        return super().create(vals_list)

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {
                "payment_request_id",
                "partner_id",
                "contract_id",
                "note",
                "active",
                "write_uid",
                "write_date",
            }
            if set(vals) - allowed:
                raise UserError(_("历史迁移付款执行单据已确认，只允许补充业务锚点和备注。"))
        return super().write(vals)

    def action_confirm(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state == "draft":
                if policy.is_approval_required(rec._name, company=rec.company_id):
                    company = rec.company_id or self.env.company
                    rec.with_company(company).with_context(allowed_company_ids=[company.id])._request_document_approval()
                else:
                    rec.write({"state": "confirmed", "reject_reason": False})

    def action_paid(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state in ("draft", "confirmed"):
                if policy.is_approval_required(rec._name, company=rec.company_id) and rec.validation_status != "validated":
                    raise UserError(_("付款执行尚未完成统一审批流程。"))
                rec.state = "paid"

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移付款执行单据不能在新系统取消。"))
            if rec.state != "cancel":
                rec.state = "cancel"

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
