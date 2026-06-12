# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class ScSelfFundingRegistration(models.Model):
    _name = "sc.self.funding.registration"
    _description = "自筹垫付/退回办理"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation", "sc.company.contractor.responsibility.context.mixin"]
    _order = "document_date desc, id desc"

    name = fields.Char(string="单据号", required=True, default="新建", copy=False)
    source_origin = fields.Selection(
        [("manual", "新系统办理"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    funding_type = fields.Selection(
        [("income", "自筹垫付"), ("refund", "自筹退回")],
        string="办理类型",
        default="income",
        required=True,
        index=True,
        tracking=True,
    )
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        domain="[('target_model', '=', 'sc.self.funding.registration'), ('active', '=', True)]",
        index=True,
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("done", "已完成"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        required=True,
        index=True,
        tracking=True,
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
    partner_id = fields.Many2one("res.partner", string="承包人", required=True, index=True)
    document_no = fields.Char(string="来源编号", index=True)
    document_date = fields.Date(string="发生日期", default=fields.Date.context_today, required=True, index=True)
    amount = fields.Monetary(string="金额", currency_field="currency_id", required=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: (self.env.ref("base.CNY", raise_if_not_found=False) or self.env.company.currency_id).id,
    )
    payment_account_name = fields.Char(string="公司账户/户名")
    partner_account_name = fields.Char(string="承包人账户/户名")
    bank_name = fields.Char(string="开户行")
    bank_account = fields.Char(string="账号")
    summary = fields.Char(string="摘要")
    note = fields.Text(string="备注")
    reject_reason = fields.Char(string="驳回原因", readonly=True, copy=False)
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_self_funding_registration_attachment_rel",
        "registration_id",
        "attachment_id",
        string="附件",
    )
    active = fields.Boolean(default=True, index=True, string="有效")

    _sql_constraints = [
        ("amount_positive", "CHECK(amount > 0)", "自筹办理金额必须大于 0。"),
    ]

    @api.model
    def _category_code_for_type(self, funding_type):
        if funding_type == "refund":
            return "finance.self_funding.refund"
        return "finance.self_funding.income"

    @api.model
    def _resolve_business_category_id(self, vals):
        code = (
            vals.get("business_category_code")
            or self.env.context.get("default_business_category_code")
            or self.env.context.get("business_category_code")
            or self._category_code_for_type(vals.get("funding_type") or self.env.context.get("default_funding_type"))
        )
        category = self.env["sc.business.category"].sudo().search(
            [("code", "=", code), ("target_model", "=", self._name), ("active", "=", True)],
            limit=1,
        )
        return category.id if category else False

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            vals.setdefault("business_category_id", self._resolve_business_category_id(vals))
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.self.funding.registration") or _("Self Funding")
        return super().create(vals_list)

    def write(self, vals):
        if any(rec.state == "done" for rec in self) and not self.env.context.get("allow_done_self_funding_write"):
            allowed = {"note", "active", "attachment_ids", "write_uid", "write_date"}
            blocked = set(vals) - allowed
            if blocked:
                raise UserError(_("已完成的自筹办理只允许补充备注、附件或归档。"))
        return super().write(vals)

    def action_confirm(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿状态的自筹办理可以提交。"))
            before = rec._snapshot_audit_payload()
            rec._check_done_ready()
            if policy.is_approval_required(rec._name, company=rec.company_id):
                company = rec.company_id or self.env.company
                rec.with_company(company).with_context(allowed_company_ids=[company.id])._request_document_approval()
                event_code = "self_funding_submitted"
            else:
                rec.write({"state": "confirmed", "reject_reason": False})
                event_code = "self_funding_confirmed"
            rec._audit_transition(event_code, before, rec._snapshot_audit_payload(), "action_confirm")

    def action_done(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认状态的自筹办理可以完成。"))
            if policy.is_approval_required(rec._name, company=rec.company_id) and rec.validation_status != "validated":
                raise UserError(_("自筹办理尚未完成统一审批流程。"))
            before = rec._snapshot_audit_payload()
            rec._check_done_ready()
            rec.write({"state": "done"})
            rec._ensure_self_funding_treasury_ledger()
            rec._audit_transition("self_funding_done", before, rec._snapshot_audit_payload(), "action_done")

    def action_cancel(self):
        for rec in self:
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认状态的自筹办理可以取消。"))
            before = rec._snapshot_audit_payload()
            rec.write({"state": "cancel"})
            rec._audit_transition("self_funding_cancelled", before, rec._snapshot_audit_payload(), "action_cancel")

    def _check_done_ready(self):
        self.ensure_one()
        if not self.project_id:
            raise UserError(_("请先选择项目。"))
        if not self.partner_id:
            raise UserError(_("请先选择承包人。"))
        if not self.document_date:
            raise UserError(_("请先填写发生日期。"))
        if self.amount <= 0:
            raise UserError(_("自筹办理金额必须大于 0。"))
        self._check_evidence_ready()
        if self.funding_type == "refund":
            self._check_refund_not_exceed_self_funding_balance()

    def _check_evidence_ready(self):
        self.ensure_one()
        if self.source_origin != "manual":
            return
        if not self.attachment_ids:
            raise UserError(_("请上传自筹办理附件，作为公司与承包人资金责任的办理依据。"))
        if not self.payment_account_name:
            raise UserError(_("请填写公司账户/户名。"))
        if not self.partner_account_name:
            raise UserError(_("请填写承包人账户/户名。"))

    def _check_refund_not_exceed_self_funding_balance(self):
        self.ensure_one()
        summary = self.company_contractor_responsibility_summary_id
        available = summary.self_funding_balance if summary else 0.0
        rounding = self.currency_id.rounding or 0.01
        if float_compare(self.amount, available, precision_rounding=rounding) == 1:
            raise UserError(_("自筹退回金额 %.2f 超过自筹未退余额 %.2f。") % (self.amount, available))

    def _ensure_self_funding_treasury_ledger(self):
        Ledger = self.env["sc.treasury.ledger"].sudo()
        for rec in self:
            direction = "out" if rec.funding_type == "refund" else "in"
            domain = [
                ("source_model", "=", rec._name),
                ("source_res_id", "=", rec.id),
                ("project_id", "=", rec.project_id.id),
                ("direction", "=", direction),
                ("source_kind", "=", "self_funding"),
            ]
            values = {
                "date": rec.document_date,
                "project_id": rec.project_id.id,
                "partner_id": rec.partner_id.id,
                "direction": direction,
                "amount": rec.amount,
                "currency_id": rec.currency_id.id,
                "source_kind": "self_funding",
                "source_model": rec._name,
                "source_res_id": rec.id,
                "state": "posted",
                "note": rec.summary or rec.note or _("auto:self_funding_done"),
            }
            existing = Ledger.search(domain, limit=1)
            if existing:
                existing.write(values)
            else:
                Ledger.with_context(allow_ledger_auto=True).create(values)

    def _request_document_approval(self):
        self.ensure_one()
        if self.review_ids and self.validation_status == "rejected":
            self.restart_validation()
        elif not self.review_ids or self.validation_status == "no":
            reviews = self.request_validation()
            if not reviews:
                raise UserError(_("自筹办理已启用审批，但没有匹配的统一审批规则，请检查业务审批配置。"))
        else:
            raise UserError(_("自筹办理已经在统一审批流程中，请等待审批完成。"))

    def _check_state_from_condition(self):
        self.ensure_one()
        parent = getattr(super(), "_check_state_from_condition", None)
        base_ok = parent() if parent else False
        return base_ok or self.state == "draft"

    def action_on_tier_approved(self):
        for rec in self:
            if rec.state == "draft":
                before = rec._snapshot_audit_payload()
                rec.with_context(skip_validation_check=True).write({"state": "confirmed", "reject_reason": False})
                rec._audit_transition("self_funding_confirmed", before, rec._snapshot_audit_payload(), "action_on_tier_approved")

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state == "draft":
                before = rec._snapshot_audit_payload()
                rec.with_context(skip_validation_check=True).write({"reject_reason": reason or _("统一审批驳回")})
                rec._audit_transition("self_funding_rejected", before, rec._snapshot_audit_payload(), "action_on_tier_rejected")

    def _snapshot_audit_payload(self):
        self.ensure_one()
        return {
            "state": self.state,
            "funding_type": self.funding_type,
            "business_category_code": self.business_category_id.code,
            "project_id": self.project_id.id,
            "company_id": self.company_id.id,
            "partner_id": self.partner_id.id,
            "document_no": self.document_no,
            "document_date": fields.Date.to_string(self.document_date) if self.document_date else False,
            "amount": self.amount,
            "currency_id": self.currency_id.id,
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
