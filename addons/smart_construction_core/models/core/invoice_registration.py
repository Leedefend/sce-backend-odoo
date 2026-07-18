# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class ScInvoiceRegistration(models.Model):
    _name = "sc.invoice.registration"
    _description = "发票登记"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
    _order = "invoice_date desc, id desc"

    name = fields.Char(string="登记单号", required=True, default="新建", copy=False)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    source_kind = fields.Selection(
        [
            ("invoice_registration", "发票登记"),
            ("input_invoice_tax", "进项税额"),
            ("output_invoice_tax", "销项税额"),
            ("prepaid_tax", "预缴税"),
        ],
        string="业务类型",
        default="invoice_registration",
        required=True,
        index=True,
    )
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        index=True,
        ondelete="restrict",
        domain="[('target_model', '=', 'sc.invoice.registration')]",
    )
    direction = fields.Selection(
        [
            ("input", "进项"),
            ("output", "销项"),
            ("prepaid", "预缴"),
            ("unknown", "未识别"),
        ],
        string="方向",
        default="input",
        required=True,
        index=True,
    )
    invoice_flow_label = fields.Char(string="办理事项", compute="_compute_invoice_flow_label")
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("registered", "已登记"),
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
    settlement_id = fields.Many2one(
        "sc.settlement.order",
        string="结算单",
        index=True,
        domain="[('project_id', '=', project_id)]",
    )
    document_no = fields.Char(string="来源单号", index=True)
    document_date = fields.Date(string="单据日期", default=fields.Date.context_today, index=True)
    application_date = fields.Date(string="申请日期", index=True)
    invoice_date = fields.Date(string="发票日期", default=fields.Date.context_today, index=True)
    invoice_state = fields.Char(string="开票状态", index=True)
    recognition_date = fields.Date(string="认票日期", index=True)
    invoice_no = fields.Char(string="发票号码", index=True)
    invoice_code = fields.Char(string="发票代码", index=True)
    invoice_type = fields.Char(string="发票类型", index=True)
    tax_rate = fields.Char(string="税率", index=True)
    tax_type = fields.Char(string="交税类型", index=True)
    prepaid_tax_date = fields.Date(string="预缴税款日期", index=True)
    tax_certificate_no = fields.Char(string="完税凭证号码", index=True)
    invoice_content = fields.Char(string="开票内容", index=True)
    cost_category_name = fields.Char(string="成本类别", index=True)
    recipient_unit_name = fields.Char(string="受票单位", index=True)
    caliber = fields.Char(string="口径", index=True)
    invoice_company_type = fields.Char(string="发票公司类型", index=True)
    invoice_issue_company = fields.Char(string="开票单位", index=True)
    actual_invoice_issue_company = fields.Char(string="实际开票单位", index=True)
    invoice_provider_name = fields.Char(string="发票提供人/单位", index=True)
    push_result = fields.Char(string="推送结果", index=True)
    kingdee_document_no = fields.Char(string="金蝶单据编号", index=True)
    expected_receipt_date = fields.Date(string="预计回款日期", index=True)
    applicant_name = fields.Char(string="申请人", index=True)
    invoice_count = fields.Integer(string="开票张数", default=0)
    contract_amount = fields.Monetary(string="合同额", currency_field="currency_id")
    amount_no_tax = fields.Monetary(string="不含税金额", currency_field="currency_id")
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id")
    amount_total = fields.Monetary(string="价税合计", currency_field="currency_id")
    actual_invoice_amount = fields.Monetary(string="实开总金额", currency_field="currency_id")
    surcharge_amount = fields.Monetary(string="附加税", currency_field="currency_id")
    related_receipt_amount = fields.Monetary(string="关联回款金额", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: (self.env.ref("base.CNY", raise_if_not_found=False) or self.env.company.currency_id).id,
    )
    handler_name = fields.Char(string="经办人", index=True)
    invoice_holder = fields.Char(string="持票人", index=True)
    accounting_state = fields.Char(string="核算状态", index=True)
    voucher_no = fields.Char(string="凭证号", index=True)
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    legacy_partner_id = fields.Char(string="历史往来单位ID", index=True, readonly=True)
    legacy_partner_name = fields.Char(string="历史往来单位", index=True, readonly=True)
    legacy_partner_tax_no = fields.Char(string="历史税号", index=True, readonly=True)
    creator_name = fields.Char(string="历史录入人", index=True, readonly=True)
    created_time = fields.Datetime(string="历史录入时间", index=True, readonly=True)
    red_flush_adjustment_id = fields.Many2one(
        "sc.output.invoice.adjustment",
        string="红冲变更登记",
        readonly=True,
        copy=False,
        index=True,
        ondelete="restrict",
    )
    red_flush_origin_source_model = fields.Char(string="红冲原票来源模型", readonly=True, copy=False, index=True)
    red_flush_origin_source_record_id = fields.Integer(string="红冲原票来源ID", readonly=True, copy=False, index=True)
    red_flush_origin_invoice_no = fields.Char(string="红冲原发票号码", readonly=True, copy=False, index=True)
    reject_reason = fields.Char(string="驳回原因", readonly=True, copy=False)
    note = fields.Text(string="备注")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_invoice_registration_attachment_rel",
        "invoice_id",
        "attachment_id",
        string="附件",
    )
    active = fields.Boolean(string="有效", default=True, index=True)
    document_status_display = fields.Char(
        string="单据状态",
        compute="_compute_formal_list_visible_fields",
        store=True,
        readonly=True,
    )
    project_name_display = fields.Char(
        string="项目名称",
        compute="_compute_formal_list_visible_fields",
        store=True,
        readonly=True,
    )
    recipient_unit_display = fields.Char(
        string="受票单位",
        compute="_compute_formal_list_visible_fields",
        store=True,
        readonly=True,
    )
    invoice_issue_company_display = fields.Char(
        string="开票单位",
        compute="_compute_formal_list_visible_fields",
        store=True,
        readonly=True,
    )
    actual_invoice_issue_company_display = fields.Char(
        string="实际开票单位",
        compute="_compute_formal_list_visible_fields",
        store=True,
        readonly=True,
    )
    invoice_quantity_display = fields.Char(
        string="数量/开票张数",
        compute="_compute_formal_list_visible_fields",
        store=True,
        readonly=True,
    )
    note_display = fields.Char(
        string="备注",
        compute="_compute_formal_list_visible_fields",
        store=True,
        readonly=True,
    )
    invoice_attachment_text = fields.Char(
        string="附件",
        compute="_compute_formal_list_visible_fields",
        store=True,
        readonly=True,
    )
    source_created_by = fields.Char(
        string="录入人",
        compute="_compute_formal_list_visible_fields",
        store=True,
        readonly=True,
    )
    source_created_at = fields.Datetime(
        string="录入时间",
        compute="_compute_formal_list_visible_fields",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "历史发票登记来源记录必须唯一。",
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
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        project_id = res.get("project_id") or self._context_project_id()
        if project_id and "project_id" in fields_list:
            res["project_id"] = project_id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            project_id = self._context_project_id()
            if project_id:
                vals.setdefault("project_id", project_id)
            vals.setdefault("business_category_id", self._resolve_business_category_id(vals))
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.invoice.registration") or _("Invoice Registration")
        return super().create(vals_list)

    def _resolve_business_category_id(self, vals):
        Category = self.env["sc.business.category"].sudo()
        code = self.env.context.get("default_business_category_code") or self.env.context.get(
            "current_business_category_code"
        )
        source_kind = vals.get("source_kind") or self.env.context.get("default_source_kind") or "invoice_registration"
        direction = vals.get("direction") or self.env.context.get("default_direction") or "input"
        invoice_content = vals.get("invoice_content") or self.env.context.get("default_invoice_content") or ""
        if not code:
            if source_kind == "prepaid_tax" or direction == "prepaid":
                code = "invoice.prepaid_tax"
            elif source_kind == "input_invoice_tax" or direction == "input":
                code = "invoice.input.report"
            elif invoice_content == "销项开票申请":
                code = "invoice.output.application"
            elif source_kind == "output_invoice_tax" or direction == "output":
                code = "invoice.output.registration"
        category = Category.search(
            [("code", "=", code), ("target_model", "=", "sc.invoice.registration")],
            limit=1,
        )
        return category.id if category else False

    @api.depends("source_kind", "direction", "invoice_content", "tax_type")
    def _compute_invoice_flow_label(self):
        for rec in self:
            if rec.invoice_content:
                rec.invoice_flow_label = rec.invoice_content
            elif rec.source_kind == "prepaid_tax" or rec.direction == "prepaid":
                rec.invoice_flow_label = _("预缴税款")
            elif rec.source_kind == "output_invoice_tax" or rec.direction == "output":
                rec.invoice_flow_label = _("销项开票")
            elif rec.source_kind == "input_invoice_tax" or rec.direction == "input":
                rec.invoice_flow_label = _("进项发票")
            elif rec.tax_type:
                rec.invoice_flow_label = rec.tax_type
            else:
                rec.invoice_flow_label = _("发票登记")

    @api.depends(
        "state",
        "project_id",
        "recipient_unit_name",
        "legacy_partner_name",
        "partner_id",
        "invoice_issue_company",
        "actual_invoice_issue_company",
        "invoice_count",
        "note",
        "attachment_ids",
        "creator_name",
        "created_time",
    )
    def _compute_formal_list_visible_fields(self):
        state_labels = dict(self._fields["state"].selection)
        for record in self:
            record.document_status_display = state_labels.get(record.state) or ""
            record.project_name_display = record.project_id.display_name or ""
            record.recipient_unit_display = (
                record.recipient_unit_name
                or record.legacy_partner_name
                or record.partner_id.display_name
                or ""
            )
            record.invoice_issue_company_display = record.invoice_issue_company or ""
            record.actual_invoice_issue_company_display = (
                record.actual_invoice_issue_company
                or record.invoice_issue_company
                or ""
            )
            record.invoice_quantity_display = str(record.invoice_count) if record.invoice_count else ""
            record.note_display = record.note or ""
            record.invoice_attachment_text = (
                record._invoice_attachment_ref_label()
                or ("附件(%s)" % len(record.attachment_ids) if record.attachment_ids else "")
            )
            record.source_created_by = record.creator_name or ""
            record.source_created_at = record.created_time or False

    def _invoice_attachment_ref_label(self):
        self.ensure_one()
        text = str(self._invoice_attachment_ref_value() or "").strip()
        if not text:
            return ""
        if text.startswith("附件("):
            return text
        tokens = [item.strip() for item in text.replace(";", ",").split(",") if item.strip()]
        if tokens and all(len(item) == 32 and all(char in "0123456789abcdefABCDEF" for char in item) for item in tokens):
            return "附件(%s)" % len(tokens)
        return text

    def _invoice_attachment_ref_value(self):
        return ""

    def _history_surface_allowed_write_fields(self):
        return set()

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {
                "partner_id",
                "contract_id",
                "settlement_id",
                "note",
                "active",
                "creator_name",
                "created_time",
                "tax_type",
                "prepaid_tax_date",
                "tax_certificate_no",
                "invoice_company_type",
                "application_date",
                "invoice_state",
                "recipient_unit_name",
                "caliber",
                "actual_invoice_issue_company",
                "actual_invoice_amount",
                "invoice_provider_name",
                "legacy_acceptance_label",
                "legacy_acceptance_sort_id",
                "write_uid",
                "write_date",
            } | self._history_surface_allowed_write_fields()
            if set(vals) - allowed:
                raise UserError(_("历史迁移发票登记已确认，只允许补充业务锚点和备注。"))
        return super().write(vals)

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_invoice_registration
               SET business_category_id = CASE
                   WHEN source_kind = 'prepaid_tax' OR direction = 'prepaid' THEN (
                       SELECT id FROM sc_business_category WHERE code = 'invoice.prepaid_tax' LIMIT 1
                   )
                   WHEN source_kind = 'input_invoice_tax' OR direction = 'input' THEN (
                       SELECT id FROM sc_business_category WHERE code = 'invoice.input.report' LIMIT 1
                   )
                   WHEN source_kind = 'output_invoice_tax' AND invoice_content = '销项开票申请' THEN (
                       SELECT id FROM sc_business_category WHERE code = 'invoice.output.application' LIMIT 1
                   )
                   WHEN source_kind = 'output_invoice_tax' OR direction = 'output' THEN (
                       SELECT id FROM sc_business_category WHERE code = 'invoice.output.registration' LIMIT 1
                   )
                   ELSE NULL
               END
             WHERE business_category_id IS NULL
            """
        )

    def action_confirm(self):
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿发票登记可以确认。"))
            rec._check_business_anchor()
            before = rec._snapshot_audit_payload()
            if policy.is_approval_required(rec._name, company=rec.company_id):
                company = rec.company_id or self.env.company
                rec.with_company(company).with_context(allowed_company_ids=[company.id])._request_document_approval()
                rec.invalidate_recordset()
                rec._audit_transition("invoice_submitted", before, rec._snapshot_audit_payload(), action_name="action_confirm")
            else:
                rec.write({"state": "confirmed", "reject_reason": False})
                rec._audit_transition("invoice_confirmed", before, rec._snapshot_audit_payload(), action_name="action_confirm")

    def action_register(self):
        self._assert_finance_register_access()
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state != "confirmed":
                raise UserError(_("只有已确认发票登记可以登记。"))
            rec._check_business_anchor()
            if policy.is_approval_required(rec._name, company=rec.company_id) and rec.validation_status != "validated":
                raise UserError(_("发票登记尚未完成统一审批流程。"))
            before = rec._snapshot_audit_payload()
            rec.write({"state": "registered"})
            rec._audit_transition("invoice_registered", before, rec._snapshot_audit_payload(), action_name="action_register")

    def _has_finance_register_access(self):
        return self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager")

    def _assert_finance_register_access(self):
        if not self._has_finance_register_access():
            raise UserError(_("你没有完成发票登记的财务确认权限。"))

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移发票登记不能在新系统取消。"))
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认发票登记可以取消。"))
            before = rec._snapshot_audit_payload()
            rec.write({"state": "cancel"})
            rec._audit_transition("invoice_cancelled", before, rec._snapshot_audit_payload(), action_name="action_cancel")

    def _snapshot_audit_payload(self):
        self.ensure_one()
        return {
            "state": self.state,
            "validation_status": self.validation_status,
            "source_kind": self.source_kind,
            "business_category_code": self.business_category_id.code,
            "direction": self.direction,
            "invoice_content": self.invoice_content,
            "project_id": self.project_id.id,
            "partner_id": self.partner_id.id,
            "contract_id": self.contract_id.id,
            "settlement_id": self.settlement_id.id,
            "invoice_no": self.invoice_no,
            "tax_certificate_no": self.tax_certificate_no,
            "amount_no_tax": self.amount_no_tax,
            "tax_amount": self.tax_amount,
            "amount_total": self.amount_total,
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

    def _check_business_anchor(self):
        for rec in self:
            if not rec.invoice_date:
                raise UserError(_("发票登记必须填写发票日期。"))
            if (rec.amount_total or 0.0) <= 0 and (rec.tax_amount or 0.0) <= 0 and (rec.surcharge_amount or 0.0) <= 0:
                raise UserError(_("发票登记必须填写有效金额。"))
            if rec.source_kind == "prepaid_tax" or rec.direction == "prepaid":
                if not rec.tax_certificate_no:
                    raise UserError(_("预缴税登记必须填写完税凭证号码。"))
            elif not rec.invoice_no:
                raise UserError(_("发票登记必须填写发票号码。"))
            if rec.contract_id:
                if rec.contract_id.project_id != rec.project_id:
                    raise UserError(_("发票登记合同必须属于当前项目。"))
                if rec.contract_id.partner_id and rec.partner_id and rec.contract_id.partner_id != rec.partner_id:
                    raise UserError(_("发票登记往来单位必须与合同相对方一致。"))
            if rec.settlement_id:
                if rec.settlement_id.project_id != rec.project_id:
                    raise UserError(_("发票登记结算单必须属于当前项目。"))
                if rec.settlement_id.contract_id and rec.contract_id and rec.settlement_id.contract_id != rec.contract_id:
                    raise UserError(_("发票登记合同必须与结算单合同一致。"))
                if rec.settlement_id.partner_id and rec.partner_id and rec.settlement_id.partner_id != rec.partner_id:
                    raise UserError(_("发票登记往来单位必须与结算单往来单位一致。"))
            rec._check_output_invoice_contract_balance()

    def _check_output_invoice_contract_balance(self):
        for rec in self:
            if rec.source_origin == "legacy":
                continue
            if rec.direction != "output" or not rec.contract_id:
                continue
            if rec.red_flush_adjustment_id or (rec.amount_total or 0.0) <= 0.0:
                continue
            contract_total = rec.contract_id.amount_final or rec.contract_id.amount_total or 0.0
            if contract_total <= 0.0:
                continue
            rounding = rec.currency_id.rounding if rec.currency_id else 0.01
            rows = self.sudo().read_group(
                [
                    ("contract_id", "=", rec.contract_id.id),
                    ("direction", "=", "output"),
                    ("state", "in", ["confirmed", "registered", "legacy_confirmed"]),
                    ("amount_total", ">", 0.0),
                    ("id", "!=", rec.id),
                ],
                ["amount_total:sum"],
                [],
            )
            invoiced = rows[0].get("amount_total_sum", rows[0].get("amount_total", 0.0)) if rows else 0.0
            requested = (invoiced or 0.0) + (rec.amount_total or 0.0)
            if float_compare(requested, contract_total, precision_rounding=rounding) == 1:
                raise UserError(
                    _("销项开票金额不能超过合同剩余开票余额。合同金额：%(total)s，已开票：%(invoiced)s，本次：%(current)s。")
                    % {
                        "total": contract_total,
                        "invoiced": invoiced or 0.0,
                        "current": rec.amount_total or 0.0,
                    }
                )

    def _request_document_approval(self):
        self.ensure_one()
        if self.review_ids and self.validation_status == "rejected":
            self.restart_validation()
        elif not self.review_ids or self.validation_status == "no":
            reviews = self.request_validation()
            if not reviews:
                raise UserError(_("发票登记已启用审批，但没有匹配的统一审批规则，请检查业务审批配置。"))
        else:
            raise UserError(_("发票登记已经在统一审批流程中，请等待审批完成。"))

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
            if rec.state != "draft":
                raise UserError(_("只有草稿发票登记可以完成统一审批回调。"))
            rec._check_business_anchor()
            before = rec._snapshot_audit_payload()
            rec.with_context(skip_validation_check=True).write({"state": "confirmed", "reject_reason": False})
            rec._audit_transition("invoice_confirmed", before, rec._snapshot_audit_payload(), action_name="action_on_tier_approved")

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿发票登记可以驳回。"))
            before = rec._snapshot_audit_payload()
            rec.with_context(skip_validation_check=True).write(
                {"reject_reason": reason or rec._get_tier_reject_reason()}
            )
            rec._audit_transition(
                "invoice_rejected",
                before,
                rec._snapshot_audit_payload(),
                reason=reason or rec.reject_reason,
                action_name="action_on_tier_rejected",
            )
