# -*- coding: utf-8 -*-
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScFinancingLoan(models.Model):
    _name = "sc.financing.loan"
    _description = "融资与借款登记"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
    _order = "document_date desc, id desc"

    name = fields.Char(string="单据号", required=True, default="新建", copy=False)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    loan_type = fields.Selection(
        [
            ("loan_registration", "贷款登记"),
            ("borrowing_request", "借款申请"),
        ],
        string="业务类型",
        default="loan_registration",
        required=True,
        index=True,
    )
    direction = fields.Selection(
        [("financing_in", "融资流入"), ("borrowed_fund", "借入资金")],
        string="资金方向",
        default="financing_in",
        required=True,
        index=True,
    )
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        domain="[('target_model', '=', 'sc.financing.loan'), ('active', '=', True)]",
        index=True,
        tracking=True,
    )
    loan_flow_label = fields.Char(string="借款方向", compute="_compute_loan_flow_label")
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
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
    document_no = fields.Char(string="来源单号", index=True)
    document_date = fields.Date(string="单据日期", default=fields.Date.context_today, index=True)
    due_date = fields.Date(string="到期日", index=True)
    amount = fields.Monetary(string="金额", currency_field="currency_id", required=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    purpose = fields.Text(string="用途说明")
    rate_label = fields.Char(string="利率/类型", index=True)
    extra_ref = fields.Char(string="扩展引用", index=True)
    extra_label = fields.Char(string="扩展标签", index=True)
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    legacy_counterparty_id = fields.Char(string="历史往来方ID", index=True, readonly=True)
    legacy_counterparty_name = fields.Char(string="历史往来方", index=True, readonly=True)
    legacy_amount_field = fields.Char(string="历史金额字段", index=True, readonly=True)
    legacy_attachment_ref = fields.Char(string="历史附件引用", index=True, readonly=True)
    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True, readonly=True)
    creator_name = fields.Char(string="历史录入人", index=True, readonly=True)
    created_time = fields.Datetime(string="历史录入时间", index=True, readonly=True)
    legacy_visible_project_name = fields.Char(string="历史可见项目名称", readonly=True)
    legacy_visible_request_department = fields.Char(string="历史可见申请部门", readonly=True)
    legacy_visible_request_time = fields.Datetime(string="历史可见申请时间", readonly=True)
    legacy_visible_applicant = fields.Char(string="历史可见申请人", readonly=True)
    legacy_visible_budget_included = fields.Char(string="历史可见是否预算内", readonly=True)
    legacy_visible_actual_loan_amount = fields.Char(string="历史可见实际借款金额", readonly=True)
    legacy_visible_fund_usage_plan = fields.Text(string="历史可见主要资金使用安排", readonly=True)
    legacy_visible_payee = fields.Char(string="历史可见收款人", readonly=True)
    legacy_visible_receipt_account = fields.Char(string="历史可见收款账户", readonly=True)
    legacy_visible_bank_name = fields.Char(string="历史可见开户银行", readonly=True)
    legacy_visible_company_name = fields.Char(string="历史可见公司名称", readonly=True)
    legacy_visible_note = fields.Text(string="历史可见备注", readonly=True)
    legacy_visible_payer_unit = fields.Char(string="历史可见付款单位", readonly=True)
    legacy_visible_receiver_unit = fields.Char(string="历史可见收款单位", readonly=True)
    legacy_visible_counterparty_name = fields.Char(string="历史可见往来单位名称", readonly=True)
    legacy_visible_counterparty_account = fields.Char(string="历史可见往来单位账户", readonly=True)
    legacy_visible_loan_account = fields.Char(string="历史可见借款账号/贷款账户", readonly=True)
    legacy_visible_approved_amount = fields.Char(string="历史可见实际批复金额", readonly=True)
    legacy_visible_request_amount = fields.Char(string="历史可见申请金额", readonly=True)
    legacy_visible_expected_return_time = fields.Datetime(string="历史可见预计归还时间", readonly=True)
    legacy_visible_loan_type = fields.Char(string="历史可见借款类型", readonly=True)
    legacy_visible_loan_bank = fields.Char(string="历史可见贷款银行", readonly=True)
    legacy_visible_due_interest = fields.Char(string="历史可见到期利息", readonly=True)
    legacy_visible_repayment_amount = fields.Char(string="历史可见还款金额", readonly=True)
    legacy_visible_unpaid_amount = fields.Char(string="历史可见未还款金额", readonly=True)
    legacy_visible_loan_date = fields.Datetime(string="历史可见贷款日期", readonly=True)
    legacy_visible_repayment_date = fields.Datetime(string="历史可见还款日期", readonly=True)
    legacy_visible_loan_days = fields.Char(string="历史可见贷款天数", readonly=True)
    legacy_visible_annual_rate = fields.Char(string="历史可见年利率", readonly=True)
    legacy_visible_repayment_account = fields.Char(string="历史可见还款账户", readonly=True)
    legacy_visible_writer = fields.Char(string="历史可见填写人", readonly=True)
    legacy_visible_actual_repayment_days = fields.Char(string="历史可见实际还款天数", readonly=True)
    legacy_visible_actual_annual_rate = fields.Char(string="历史可见实际年利率", readonly=True)
    legacy_visible_loan_interest = fields.Char(string="历史可见贷款利息", readonly=True)
    reject_reason = fields.Char(string="驳回原因", readonly=True, copy=False)
    note = fields.Text(string="备注")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_financing_loan_attachment_rel",
        "loan_id",
        "attachment_id",
        string="附件",
    )
    active = fields.Boolean("有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "Legacy financing loan source must be unique.",
        ),
        ("amount_nonnegative", "CHECK(amount >= 0)", "Financing loan amount must be non-negative."),
    ]

    @api.depends("loan_type", "direction", "purpose", "business_category_id.code")
    def _compute_loan_flow_label(self):
        for record in self:
            category_code = record.business_category_id.code
            purpose = (record.purpose or "").strip()
            if category_code == "finance.loan.contractor_project_borrow" or re.search(r"借.*项目.*款", purpose):
                record.loan_flow_label = _("项目借款给承包人")
            elif category_code == "finance.loan.project_borrow_company" or "项目借公司款" in purpose:
                record.loan_flow_label = _("公司借款给项目")
            elif record.loan_type == "borrowing_request" and record.direction == "borrowed_fund":
                record.loan_flow_label = _("项目借入资金")
            elif record.direction == "financing_in":
                record.loan_flow_label = _("融资流入项目")
            else:
                record.loan_flow_label = _("借款办理")

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
        code = (
            vals.get("business_category_code")
            or self.env.context.get("default_business_category_code")
            or self.env.context.get("business_category_code")
            or self.env.context.get("current_business_category_code")
        )
        if code:
            return code
        loan_type = vals.get("loan_type", self.env.context.get("default_loan_type") or "loan_registration")
        direction = vals.get("direction", self.env.context.get("default_direction") or "financing_in")
        purpose = (vals.get("purpose") or self.env.context.get("default_purpose") or "").strip()
        if loan_type == "borrowing_request" and direction == "borrowed_fund":
            if re.search(r"借.*项目.*款", purpose):
                return "finance.loan.contractor_project_borrow"
            if "项目借公司款" in purpose:
                return "finance.loan.project_borrow_company"
            return "finance.loan.borrowing"
        return False

    @api.model
    def _resolve_business_category_id(self, vals):
        code = self._resolve_business_category_code(vals)
        if not code:
            return False
        category = self.env["sc.business.category"].sudo().search(
            [("code", "=", code), ("target_model", "=", "sc.financing.loan")],
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
            context_date = self.env.context.get("default_document_date") or self.env.context.get("current_document_date")
            if context_date:
                vals.setdefault("document_date", context_date)
            context_amount = self.env.context.get("default_amount") or self.env.context.get("current_business_amount")
            if context_amount:
                vals.setdefault("amount", context_amount)
            context_purpose = self.env.context.get("default_purpose") or self.env.context.get("default_note")
            if context_purpose:
                vals.setdefault("purpose", context_purpose)
            vals.setdefault("business_category_id", self._resolve_business_category_id(vals))
            context_document_no = self.env.context.get("default_document_no") or self.env.context.get("current_source_document_no")
            if context_document_no:
                vals.setdefault("document_no", context_document_no)
            context_note = self.env.context.get("default_note")
            if context_note:
                vals.setdefault("note", context_note)
            for field_name in ("due_date", "rate_label", "extra_ref", "extra_label"):
                value = self.env.context.get("default_%s" % field_name)
                if value:
                    vals.setdefault(field_name, value)
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.financing.loan") or _("Financing Loan")
        return super().create(vals_list)

    def write(self, vals):
        if (
            not self.env.context.get("legacy_visible_surface_sync")
            and any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self)
        ):
            allowed = {
                "partner_id",
                "business_category_id",
                "note",
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
                raise UserError(_("历史迁移融资/借款单据已确认，只允许补充往来单位、备注和历史录入审计事实。"))
        return super().write(vals)

    def action_confirm(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿状态的融资借款可以确认。"))
            before = rec._snapshot_audit_payload()
            rec._check_done_ready()
            if policy.is_approval_required(rec._name, company=rec.company_id):
                company = rec.company_id or self.env.company
                rec.with_company(company).with_context(allowed_company_ids=[company.id])._request_document_approval()
                rec._audit_transition(
                    "financing_loan_submitted",
                    before,
                    rec._snapshot_audit_payload(),
                    "action_confirm",
                )
            else:
                rec.write({"state": "confirmed", "reject_reason": False})
                rec._audit_transition(
                    "financing_loan_confirmed",
                    before,
                    rec._snapshot_audit_payload(),
                    "action_confirm",
                )

    def action_done(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认状态的融资借款可以完成。"))
            if policy.is_approval_required(rec._name, company=rec.company_id) and rec.validation_status != "validated":
                raise UserError(_("融资借款尚未完成统一审批流程。"))
            before = rec._snapshot_audit_payload()
            rec._check_done_ready()
            rec.write({"state": "done"})
            rec._ensure_interfund_cash_ledger()
            rec._audit_transition(
                "financing_loan_done",
                before,
                rec._snapshot_audit_payload(),
                "action_done",
            )

    def _check_done_ready(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("请先选择往来单位后再完成融资借款。"))
        if not self.document_date:
            raise UserError(_("请先填写单据日期后再完成融资借款。"))
        if self.amount <= 0:
            raise UserError(_("融资借款金额必须大于 0。"))
        if self.loan_type == "borrowing_request" and self.direction == "borrowed_fund":
            allowed_codes = {
                "finance.loan.contractor_project_borrow",
                "finance.loan.project_borrow_company",
            }
            if self.business_category_id.code not in allowed_codes:
                raise UserError(_("借款办理必须选择“承包人借项目款”或“项目借公司款登记”业务分类后才能完成。"))

    def _ensure_interfund_cash_ledger(self):
        Ledger = self.env["sc.treasury.ledger"]
        for rec in self:
            if rec.loan_type != "borrowing_request" or rec.direction != "borrowed_fund" or (rec.amount or 0.0) <= 0:
                continue
            if rec.business_category_id.code == "finance.loan.contractor_project_borrow":
                direction = "out"
            elif rec.business_category_id.code == "finance.loan.project_borrow_company":
                direction = "in"
            else:
                continue
            Ledger._ensure_interfund_ledger(
                rec,
                project=rec.project_id,
                partner=rec.partner_id,
                direction=direction,
                amount=rec.amount,
                date=rec.document_date,
                currency=rec.currency_id,
                note=_("auto:financing_loan_done"),
            )

    @api.model
    def _backfill_business_categories(self):
        """Bootstrap legacy borrowing categories without overwriting customer-maintained values."""
        self.env.cr.execute(
            """
            UPDATE sc_business_category
               SET domain_json = %s,
                   default_values_json = %s,
                   ledger_policy_json = %s
             WHERE code = 'finance.loan.contractor_project_borrow'
               AND target_model = 'sc.financing.loan'
               AND domain_json IN (
                   '["&", ["loan_type", "=", "borrowing_request"], ["purpose", "ilike", "项目"]]',
                   '["&", ["loan_type", "=", "borrowing_request"], ["purpose", "ilike", "借%%项目%%款"]]'
               )
            """,
            [
                '["&", "&", ["loan_type", "=", "borrowing_request"], ["direction", "=", "borrowed_fund"], ["business_category_id.code", "=", "finance.loan.contractor_project_borrow"]]',
                '{"loan_type": "borrowing_request", "direction": "borrowed_fund", "business_category_code": "finance.loan.contractor_project_borrow", "purpose": "承包人借项目款"}',
                '{"facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"], "terminal_action": "action_done", "payment_request_policy": "not_applicable"}',
            ],
        )
        self.env.cr.execute(
            """
            UPDATE sc_business_category
               SET domain_json = %s,
                   default_values_json = %s,
                   ledger_policy_json = %s
             WHERE code = 'finance.loan.project_borrow_company'
               AND target_model = 'sc.financing.loan'
               AND domain_json IN (
                   '["&", ["loan_type", "=", "borrowing_request"], ["direction", "=", "borrowed_fund"]]',
                   '["&", "&", ["loan_type", "=", "borrowing_request"], ["direction", "=", "borrowed_fund"], "|", ["purpose", "=", false], ["purpose", "not ilike", "借%%项目%%款"]]'
               )
            """,
            [
                '["&", "&", ["loan_type", "=", "borrowing_request"], ["direction", "=", "borrowed_fund"], ["business_category_id.code", "=", "finance.loan.project_borrow_company"]]',
                '{"loan_type": "borrowing_request", "direction": "borrowed_fund", "business_category_code": "finance.loan.project_borrow_company", "purpose": "项目借公司款登记"}',
                '{"facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"], "terminal_action": "action_done", "payment_request_policy": "not_applicable"}',
            ],
        )
        self.env.cr.execute(
            """
            WITH categories AS (
                SELECT
                    MAX(id) FILTER (WHERE code = 'finance.loan.contractor_project_borrow') AS contractor_project_id,
                    MAX(id) FILTER (WHERE code = 'finance.loan.project_borrow_company') AS project_company_id
                  FROM sc_business_category
                 WHERE target_model = 'sc.financing.loan'
                   AND active IS TRUE
            )
            UPDATE sc_financing_loan loan
               SET business_category_id = CASE
                       WHEN COALESCE(loan.purpose, '') ILIKE '%%借%%项目%%款%%'
                            THEN categories.contractor_project_id
                       ELSE categories.project_company_id
                   END
              FROM categories
             WHERE loan.business_category_id IS NULL
               AND loan.loan_type = 'borrowing_request'
               AND loan.direction = 'borrowed_fund'
               AND (
                   (COALESCE(loan.purpose, '') ILIKE '%%借%%项目%%款%%' AND categories.contractor_project_id IS NOT NULL)
                   OR (COALESCE(loan.purpose, '') NOT ILIKE '%%借%%项目%%款%%' AND categories.project_company_id IS NOT NULL)
               )
            """
        )
        return True

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移融资/借款单据不能在新系统取消。"))
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认状态的融资借款可以取消。"))
            before = rec._snapshot_audit_payload()
            rec.write({"state": "cancel"})
            rec._audit_transition(
                "financing_loan_cancelled",
                before,
                rec._snapshot_audit_payload(),
                "action_cancel",
            )

    def _request_document_approval(self):
        self.ensure_one()
        if self.review_ids and self.validation_status == "rejected":
            self.restart_validation()
        elif not self.review_ids or self.validation_status == "no":
            reviews = self.request_validation()
            if not reviews:
                raise UserError(_("融资借款已启用审批，但没有匹配的统一审批规则，请检查业务审批配置。"))
        else:
            raise UserError(_("融资借款已经在统一审批流程中，请等待审批完成。"))

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
                before = rec._snapshot_audit_payload()
                rec.with_context(skip_validation_check=True).write({"state": "confirmed", "reject_reason": False})
                rec._audit_transition(
                    "financing_loan_confirmed",
                    before,
                    rec._snapshot_audit_payload(),
                    "action_on_tier_approved",
                )

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state == "draft":
                before = rec._snapshot_audit_payload()
                rec.with_context(skip_validation_check=True).write(
                    {"reject_reason": reason or rec._get_tier_reject_reason()}
                )
                rec._audit_transition(
                    "financing_loan_rejected",
                    before,
                    rec._snapshot_audit_payload(),
                    "action_on_tier_rejected",
                )

    def _snapshot_audit_payload(self):
        self.ensure_one()
        return {
            "state": self.state,
            "source_origin": self.source_origin,
            "loan_type": self.loan_type,
            "direction": self.direction,
            "business_category_id": self.business_category_id.id,
            "business_category_code": self.business_category_id.code,
            "project_id": self.project_id.id,
            "company_id": self.company_id.id,
            "partner_id": self.partner_id.id,
            "document_no": self.document_no,
            "document_date": fields.Date.to_string(self.document_date) if self.document_date else False,
            "due_date": fields.Date.to_string(self.due_date) if self.due_date else False,
            "amount": self.amount,
            "currency_id": self.currency_id.id,
            "purpose": self.purpose,
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
