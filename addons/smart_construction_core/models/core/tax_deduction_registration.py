# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

from ..support.state_guard import raise_guard


class ScTaxDeductionRegistration(models.Model):
    _name = "sc.tax.deduction.registration"
    _description = "抵扣登记"
    _inherit = ["mail.thread", "mail.activity.mixin", "sc.company.contractor.responsibility.context.mixin"]
    _order = "deduction_confirm_date desc, document_date desc, id desc"

    name = fields.Char(string="登记单号", required=True, default="新建", copy=False, index=True)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("deducted", "已抵扣"),
            ("legacy_confirmed", "历史已确认"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        required=True,
        index=True,
    )
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        index=True,
        ondelete="restrict",
        domain="[('target_model', '=', 'sc.tax.deduction.registration')]",
    )
    deduction_flow_label = fields.Char(string="办理事项", compute="_compute_deduction_flow_label")
    document_no = fields.Char(string="单据编号", index=True)
    document_date = fields.Date(string="单据日期", default=fields.Date.context_today, index=True)
    deduction_confirm_date = fields.Date(string="认证抵扣日期", index=True)
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
    partner_name = fields.Char(string="历史往来单位", index=True)
    invoice_no = fields.Char(string="发票号码", index=True)
    invoice_code = fields.Char(string="发票代码", index=True)
    invoice_date = fields.Date(string="开票日期", index=True)
    invoice_amount_untaxed = fields.Monetary(string="发票不含税金额", currency_field="currency_id")
    invoice_tax_amount = fields.Monetary(string="发票税额", currency_field="currency_id")
    invoice_amount_total = fields.Monetary(string="发票价税合计", currency_field="currency_id")
    tax_rate_text = fields.Char(
        string="税率",
        compute="_compute_tax_rate_text",
        store=True,
        readonly=True,
        index=True,
    )
    deduction_amount = fields.Monetary(string="抵扣金额", currency_field="currency_id")
    deduction_tax_amount = fields.Monetary(string="抵扣税额", currency_field="currency_id")
    deduction_surcharge_amount = fields.Monetary(string="抵扣附加税", currency_field="currency_id")
    is_transfer_out = fields.Boolean(string="是否转出", default=False, index=True)
    deduction_unit_name = fields.Char(string="扣款单位", index=True)
    withholding_amount = fields.Monetary(string="扣款金额", currency_field="currency_id")
    deduction_reason = fields.Text(string="扣款事由")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_tax_deduction_registration_attachment_rel",
        "registration_id",
        "attachment_id",
        string="附件",
    )
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
    creator_name = fields.Char(string="历史录入人", index=True, readonly=True)
    created_time = fields.Datetime(string="历史录入时间", index=True, readonly=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)
    deduction_bill_status_display = fields.Char(
        string="单据状态",
        compute="_compute_deduction_bill_visible_fields",
        store=True,
        readonly=True,
    )
    deduction_bill_document_no = fields.Char(
        string="单据编号",
        compute="_compute_deduction_bill_visible_fields",
        store=True,
        readonly=True,
    )
    deduction_bill_project_name = fields.Char(
        string="项目名称",
        compute="_compute_deduction_bill_visible_fields",
        store=True,
        readonly=True,
    )
    deduction_bill_unit_name = fields.Char(
        string="扣款单位",
        compute="_compute_deduction_bill_visible_fields",
        store=True,
        readonly=True,
    )
    deduction_bill_amount_display = fields.Char(
        string="扣款金额",
        compute="_compute_deduction_bill_visible_fields",
        store=True,
        readonly=True,
    )
    deduction_bill_reason_display = fields.Char(
        string="扣款事由",
        compute="_compute_deduction_bill_visible_fields",
        store=True,
        readonly=True,
    )
    deduction_bill_date_display = fields.Char(
        string="单据日期",
        compute="_compute_deduction_bill_visible_fields",
        store=True,
        readonly=True,
    )
    deduction_bill_attachment_text = fields.Char(
        string="附件",
        compute="_compute_deduction_bill_visible_fields",
        store=True,
        readonly=True,
    )
    deduction_bill_source_created_by = fields.Char(
        string="录入人",
        compute="_compute_deduction_bill_visible_fields",
        store=True,
        readonly=True,
    )
    deduction_bill_source_created_at = fields.Char(
        string="录入时间",
        compute="_compute_deduction_bill_visible_fields",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "历史扣税登记来源记录必须唯一。",
        ),
    ]

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
            vals.setdefault("business_category_id", self._resolve_business_category_id(vals))
            context_date = self.env.context.get("default_document_date") or self.env.context.get("current_document_date")
            if context_date:
                vals.setdefault("document_date", context_date)
            context_deduction_amount = self.env.context.get("default_deduction_amount") or self.env.context.get("default_amount")
            if context_deduction_amount:
                vals.setdefault("deduction_amount", context_deduction_amount)
            context_tax_amount = self.env.context.get("default_deduction_tax_amount")
            if context_tax_amount:
                vals.setdefault("deduction_tax_amount", context_tax_amount)
            context_note = self.env.context.get("default_note")
            if context_note:
                vals.setdefault("note", context_note)
            context_document_no = self.env.context.get("default_document_no") or self.env.context.get("current_source_document_no")
            if context_document_no:
                vals.setdefault("document_no", context_document_no)
            context_partner_name = self.env.context.get("default_partner_name")
            if context_partner_name:
                vals.setdefault("partner_name", context_partner_name)
                vals.setdefault("deduction_unit_name", context_partner_name)
            for field_name in (
                "invoice_no",
                "invoice_code",
                "invoice_date",
                "invoice_amount_untaxed",
                "invoice_tax_amount",
                "invoice_amount_total",
                "deduction_confirm_date",
                "withholding_amount",
                "deduction_reason",
            ):
                value = self.env.context.get("default_%s" % field_name)
                if value:
                    vals.setdefault(field_name, value)
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.tax.deduction.registration") or _("Tax Deduction")
        return super().create(vals_list)

    def _resolve_business_category_id(self, vals):
        code = self.env.context.get("default_business_category_code") or self.env.context.get(
            "current_business_category_code"
        )
        is_transfer_out = vals.get("is_transfer_out", self.env.context.get("default_is_transfer_out", False))
        if not code and not is_transfer_out:
            code = "tax.deduction.registration"
        category = self.env["sc.business.category"].sudo().search(
            [("code", "=", code), ("target_model", "=", "sc.tax.deduction.registration")],
            limit=1,
        )
        return category.id if category else False

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_tax_deduction_registration
               SET business_category_id = (
                   SELECT id FROM sc_business_category WHERE code = 'tax.deduction.registration' LIMIT 1
               )
             WHERE business_category_id IS NULL
               AND COALESCE(is_transfer_out, false) = false
            """
        )

    @api.depends("invoice_amount_untaxed", "invoice_tax_amount")
    def _compute_tax_rate_text(self):
        for record in self:
            untaxed = record.invoice_amount_untaxed or 0.0
            tax = record.invoice_tax_amount or 0.0
            if not untaxed or not tax:
                record.tax_rate_text = False
                continue
            rate = tax / untaxed * 100
            record.tax_rate_text = f"{rate:.2f}".rstrip("0").rstrip(".") + "%"

    @staticmethod
    def _deduction_bill_state_label(value):
        return {
            "-1": "已作废",
            "0": "未审核",
            "1": "审核中",
            "2": "审核通过",
            "3": "已驳回",
            "4": "已作废",
            "draft": "草稿",
            "confirmed": "已确认",
            "deducted": "已抵扣",
            "legacy_confirmed": "历史已确认",
            "cancel": "已取消",
        }.get(str(value or ""), str(value or ""))

    def _deduction_bill_attachment_label(self):
        self.ensure_one()
        count = len(self.attachment_ids)
        return "附件(%s)" % count if count else ""

    @api.depends(
        "state",
        "legacy_document_state",
        "document_no",
        "name",
        "project_id",
        "deduction_unit_name",
        "partner_id",
        "partner_name",
        "withholding_amount",
        "deduction_reason",
        "note",
        "document_date",
        "attachment_ids",
        "creator_name",
        "created_time",
    )
    def _compute_deduction_bill_visible_fields(self):
        for record in self:
            status_value = record.legacy_document_state or record.state
            reason = record.deduction_reason or record.note or ""
            if reason:
                lines = [
                    line.strip()
                    for line in reason.splitlines()
                    if line.strip()
                    and line.strip() != "not_promoted_to_runtime_payment_request"
                    and line.strip() != "missing_partner_anchor"
                    and not line.strip().startswith("[migration:")
                ]
                reason = " ".join(lines)
            record.deduction_bill_status_display = record._deduction_bill_state_label(status_value)
            record.deduction_bill_document_no = record.document_no or record.name or ""
            record.deduction_bill_project_name = record.project_id.display_name or ""
            record.deduction_bill_unit_name = (
                record.deduction_unit_name
                or record.partner_id.display_name
                or record.partner_name
                or ""
            )
            record.deduction_bill_amount_display = str(record.withholding_amount or "")
            record.deduction_bill_reason_display = reason
            record.deduction_bill_date_display = fields.Date.to_string(record.document_date) if record.document_date else ""
            record.deduction_bill_attachment_text = record._deduction_bill_attachment_label()
            record.deduction_bill_source_created_by = record.creator_name or ""
            record.deduction_bill_source_created_at = (
                fields.Datetime.to_string(record.created_time) if record.created_time else ""
            )

    @api.depends("is_transfer_out", "withholding_amount", "deduction_tax_amount", "deduction_amount")
    def _compute_deduction_flow_label(self):
        for rec in self:
            if rec.is_transfer_out:
                rec.deduction_flow_label = _("进项税额转出")
            elif rec.withholding_amount:
                rec.deduction_flow_label = _("扣款抵扣")
            elif rec.deduction_tax_amount or rec.deduction_amount:
                rec.deduction_flow_label = _("进项税额抵扣")
            else:
                rec.deduction_flow_label = _("抵扣登记")

    def _history_surface_allowed_write_fields(self):
        return set()

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {
                "partner_id",
                "note",
                "active",
                "creator_name",
                "created_time",
                "deduction_unit_name",
                "withholding_amount",
                "deduction_reason",
                "attachment_ids",
                "write_uid",
                "write_date",
            } | self._history_surface_allowed_write_fields()
            if set(vals) - allowed:
                raise UserError(_("历史迁移抵扣登记已确认，只允许补充往来单位和备注。"))
        return super().write(vals)

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿状态的抵扣登记可以确认。"))
            before = rec._snapshot_audit_payload()
            rec.write({"state": "confirmed"})
            rec._audit_transition(
                "tax_deduction_confirmed",
                before,
                rec._snapshot_audit_payload(),
                action_name="action_confirm",
            )

    def action_deduct(self):
        self._assert_finance_deduct_access()
        for rec in self:
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认状态的抵扣登记可以确认抵扣。"))
            before = rec._snapshot_audit_payload()
            vals = {}
            if not rec.deduction_confirm_date:
                vals["deduction_confirm_date"] = fields.Date.context_today(rec)
            if not rec.deduction_amount and rec.invoice_amount_untaxed:
                vals["deduction_amount"] = rec.invoice_amount_untaxed
            if not rec.deduction_tax_amount and rec.invoice_tax_amount:
                vals["deduction_tax_amount"] = rec.invoice_tax_amount
            if vals:
                rec.write(vals)
            rec._check_deduct_ready()
            rec._check_company_contractor_deduction_responsibility_or_raise()
            rec.write({"state": "deducted"})
            rec._audit_transition(
                "tax_deduction_deducted",
                before,
                rec._snapshot_audit_payload(),
                action_name="action_deduct",
            )

    def _has_finance_deduct_access(self):
        return self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager")

    def _assert_finance_deduct_access(self):
        if not self._has_finance_deduct_access():
            raise UserError(_("你没有确认抵扣的财务确认权限。"))

    def _check_deduct_ready(self):
        for rec in self:
            if not rec.invoice_no:
                raise UserError(_("请先填写发票号码后再确认抵扣。"))
            if not rec.deduction_confirm_date:
                raise UserError(_("请先填写认证抵扣日期后再确认抵扣。"))
            rounding = rec.currency_id.rounding if rec.currency_id else 0.01
            if float_compare(rec.deduction_tax_amount or 0.0, 0.0, precision_rounding=rounding) <= 0:
                raise UserError(_("抵扣税额必须大于 0。"))
            if rec.invoice_tax_amount and float_compare(
                rec.deduction_tax_amount or 0.0,
                rec.invoice_tax_amount or 0.0,
                precision_rounding=rounding,
            ) == 1:
                raise UserError(_("抵扣税额不能超过发票税额。"))
            if rec.invoice_amount_untaxed and rec.deduction_amount and float_compare(
                rec.deduction_amount or 0.0,
                rec.invoice_amount_untaxed or 0.0,
                precision_rounding=rounding,
            ) == 1:
                raise UserError(_("抵扣金额不能超过发票不含税金额。"))

    def _company_contractor_tax_deduction_responsibility_failures(self, summary, withholding_amount):
        return self._company_contractor_responsibility_balance_failures(summary, withholding_amount, _("本次扣款金额"))

    def _check_company_contractor_deduction_responsibility_or_raise(self):
        for rec in self:
            if rec.source_origin == "legacy" and rec.state == "legacy_confirmed":
                continue
            amount = rec.withholding_amount or 0.0
            if amount <= 0:
                continue
            summary = rec.company_contractor_responsibility_summary_id
            if not summary:
                continue
            failures = rec._company_contractor_tax_deduction_responsibility_failures(summary, amount)
            if failures:
                raise_guard(
                    "TAX_DEDUCTION_RESPONSIBILITY_BALANCE_BLOCKED",
                    f"抵扣登记[{rec.display_name}]",
                    _("办理扣款抵扣"),
                    reasons=failures,
                    hints=[_("打开公司-承包人责任余额，核对到款确认、已拨付和已扣款明细后再继续办理。")],
                )

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移抵扣登记不能在新系统取消。"))
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认状态的抵扣登记可以取消。"))
            before = rec._snapshot_audit_payload()
            rec.write({"state": "cancel"})
            rec._audit_transition(
                "tax_deduction_cancelled",
                before,
                rec._snapshot_audit_payload(),
                action_name="action_cancel",
            )

    def _snapshot_audit_payload(self):
        self.ensure_one()
        return {
            "state": self.state,
            "source_origin": self.source_origin,
            "business_category_code": self.business_category_id.code,
            "project_id": self.project_id.id,
            "partner_id": self.partner_id.id,
            "partner_name": self.partner_name,
            "invoice_no": self.invoice_no,
            "invoice_code": self.invoice_code,
            "invoice_amount_untaxed": self.invoice_amount_untaxed,
            "invoice_tax_amount": self.invoice_tax_amount,
            "invoice_amount_total": self.invoice_amount_total,
            "deduction_amount": self.deduction_amount,
            "deduction_tax_amount": self.deduction_tax_amount,
            "withholding_amount": self.withholding_amount,
            "is_transfer_out": self.is_transfer_out,
            "deduction_reason": self.deduction_reason,
        }

    def _audit_transition(self, event_code, before, after, reason=None, action_name=None):
        self.ensure_one()
        return self.env["sc.audit.log"].write_event(
            event_code=event_code,
            model=self._name,
            res_id=self.id,
            action=action_name or event_code,
            before=before,
            after=after,
            reason=reason,
            company_id=self.company_id or self.env.company,
            project_id=self.project_id,
        )
