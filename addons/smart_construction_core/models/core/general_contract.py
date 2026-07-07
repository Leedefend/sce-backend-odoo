# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScGeneralContract(models.Model):
    _name = "sc.general.contract"
    _description = "综合合同"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
    _state_from = ["draft"]
    _state_to = ["confirmed"]
    _cancel_state = "cancel"
    _order = "contract_date desc, id desc"

    name = fields.Char(string="登记单号", required=True, default="新建", copy=False)
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
            ("signed", "已签署"),
            ("legacy_confirmed", "历史已确认"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        required=True,
        index=True,
    )
    project_id = fields.Many2one("project.project", string="关联项目", index=True)
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company.id,
        required=True,
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
    partner_name_text = fields.Char(string="合同方文本", index=True)
    credit_code = fields.Char(string="统一信用代码", index=True)
    contact_name = fields.Char(string="联系人", index=True)
    contact_phone = fields.Char(string="联系电话", index=True)
    engineering_address = fields.Char(string="工程地址", index=True)
    bank_name = fields.Char(string="开户行", index=True)
    bank_account = fields.Char(string="银行账号", index=True)
    document_no = fields.Char(string="审批编号", index=True)
    contract_no = fields.Char(string="合同编号", index=True, readonly=True, copy=False)
    contract_name = fields.Char(string="合同名称", required=True, index=True)
    submitted_time = fields.Datetime(string="提交时间", index=True)
    contract_type = fields.Char(string="合同类型", index=True)
    contract_attribute = fields.Char(string="合同属性", index=True)
    contract_direction = fields.Selection(
        [
            ("income", "收入合同"),
            ("expense", "支出合同"),
            ("neutral", "一般合同"),
            ("unknown", "未判定"),
        ],
        string="合同方向",
        default="neutral",
        required=True,
        index=True,
        tracking=True,
    )
    contract_direction_source = fields.Char(string="合同方向来源", readonly=True, copy=False)
    contract_direction_reason = fields.Char(string="合同方向依据", readonly=True, copy=False)
    template_name = fields.Char(string="合同模板", index=True)
    union_mode = fields.Selection([("none", "非联合体"), ("lead", "联合体牵头"), ("member", "联合体成员")], string="联合体模式", default="none", index=True)
    pricing_mode = fields.Selection([("lump_sum", "总价"), ("unit_price", "单价"), ("mixed", "综合单价"), ("other", "其他")], string="计价模式", index=True)
    subcontract_mode = fields.Selection([("none", "非分包"), ("professional", "专业分包"), ("labor", "劳务分包"), ("material", "材料采购"), ("equipment", "设备租赁")], string="合同分包类型", index=True)
    sign_status = fields.Char(string="签署状态", index=True)
    signing_place = fields.Char(string="合同签订地点", index=True)
    contract_date = fields.Date(string="合同日期", default=fields.Date.context_today, index=True)
    expected_sign_date = fields.Date(string="合同预计签订日期", index=True)
    completion_date = fields.Date(string="计划交货或完工日期", index=True)
    amount_total = fields.Monetary(string="合同金额", currency_field="currency_id", required=True)
    amount_untaxed = fields.Monetary(string="不含税金额", currency_field="currency_id")
    settlement_amount = fields.Monetary(string="结算金额", currency_field="currency_id")
    invoice_amount = fields.Monetary(string="开票金额", currency_field="currency_id")
    uninvoiced_amount = fields.Monetary(string="未开票金额", currency_field="currency_id", compute="_compute_business_amounts", store=True)
    received_amount = fields.Monetary(string="收款金额", currency_field="currency_id")
    unreceived_amount = fields.Monetary(string="未收款金额", currency_field="currency_id", compute="_compute_business_amounts", store=True)
    paid_amount = fields.Monetary(string="付款金额", currency_field="currency_id")
    unpaid_amount = fields.Monetary(string="未付款金额", currency_field="currency_id", compute="_compute_business_amounts", store=True)
    prepayment_amount = fields.Monetary(string="预付款", currency_field="currency_id")
    install_debug_payment = fields.Monetary(string="安装调试款", currency_field="currency_id")
    install_commissioning_payment = fields.Monetary(
        string="安装调试款",
        currency_field="currency_id",
        compute="_compute_business_aliases",
    )
    warranty_deposit = fields.Monetary(string="质保金", currency_field="currency_id")
    tax_id = fields.Many2one(
        "account.tax",
        string="税率",
        domain=[("type_tax_use", "=", "none"), ("amount_type", "=", "percent"), ("price_include", "=", False)],
        help="合同办理使用的税率百分比。历史税率数值会同步保留。",
    )
    tax_rate = fields.Float(string="税率", digits=(16, 4))
    change_amount_total = fields.Monetary(string="累计变更金额", currency_field="currency_id")
    change_rate = fields.Float(string="变更率(%)", compute="_compute_change_rate", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    payment_terms = fields.Text(string="付款条件")
    special_condition = fields.Text(string="特殊条款")
    attachment_ids = fields.Many2many("ir.attachment", "sc_general_contract_attachment_rel", "contract_id", "attachment_id", string="合同附件")
    applicant_name = fields.Char(string="申请人", index=True)
    applicant_department = fields.Char(string="申请部门", index=True)
    purchase_engineer = fields.Char(string="采购工程师", index=True)
    handler_id = fields.Many2one("res.users", string="经办人", index=True)
    entry_user_id = fields.Many2one("res.users", string="录入人", default=lambda self: self.env.user, index=True)
    entry_data = fields.Char(string="录入数据")
    related_contract_no = fields.Char(string="关联合同号", index=True)
    is_supplement_contract = fields.Char(string="是否补充合同", index=True)
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    reject_reason = fields.Char(string="驳回原因", readonly=True, copy=False)
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)
    archived = fields.Boolean(string="是否归档", default=False, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "历史总包合同来源记录必须唯一。",
        ),
        ("amount_total_nonnegative", "CHECK(amount_total >= 0)", "Contract amount must be non-negative."),
    ]

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_general_contract
               SET contract_direction = CASE
                       WHEN evidence LIKE '%%收入%%'
                         OR evidence LIKE '%%销售%%'
                         OR evidence LIKE '%%收款%%'
                         OR evidence LIKE '%%回款%%'
                         OR evidence LIKE '%%应收%%'
                         THEN 'income'
                       WHEN evidence LIKE '%%供应商%%'
                         OR evidence LIKE '%%采购%%'
                         OR evidence LIKE '%%支出%%'
                         OR evidence LIKE '%%付款%%'
                         OR evidence LIKE '%%应付%%'
                         OR evidence LIKE '%%分包%%'
                         OR evidence LIKE '%%劳务%%'
                         OR evidence LIKE '%%材料%%'
                         OR evidence LIKE '%%设备%%'
                         OR evidence LIKE '%%租赁%%'
                         OR evidence LIKE '%%咨询%%'
                         OR evidence LIKE '%%费用%%'
                         THEN 'expense'
                       WHEN trim(evidence) = '' THEN 'unknown'
                       ELSE 'neutral'
                   END,
                   contract_direction_source = 'contract_evidence',
                   contract_direction_reason = CASE
                       WHEN trim(evidence) = '' THEN '缺少合同方向证据'
                       ELSE '历史合同类型/属性/名称=' || evidence
                   END
              FROM (
                    SELECT id, concat_ws(' ', contract_type, contract_attribute, contract_name) AS evidence
                      FROM sc_general_contract
                     WHERE source_origin = 'legacy'
                       AND COALESCE(contract_direction, 'neutral') IN ('neutral', 'unknown')
                   ) classified
             WHERE sc_general_contract.id = classified.id
            """
        )

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.general.contract") or _("一般合同（公司）")
            if not vals.get("contract_no"):
                vals["contract_no"] = seq.next_by_code("sc.general.contract.no") or vals["name"]
            self._sync_company_vals(vals)
            vals.update(self._prepare_contract_direction_vals(vals))
            self._sync_tax_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        if self._needs_contract_direction_refresh(vals):
            vals = dict(vals)
            vals.update(self._prepare_contract_direction_vals(vals))
        if "tax_id" in vals or "tax_rate" in vals:
            vals = dict(vals)
            self._sync_tax_vals(vals)
        if "project_id" in vals and vals.get("project_id") and "company_id" not in vals:
            vals = dict(vals)
            self._sync_company_vals(vals)
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {
                "partner_id",
                "note",
                "active",
                "write_uid",
                "write_date",
                "contract_direction",
                "contract_direction_source",
                "contract_direction_reason",
                "tax_id",
                "tax_rate",
            }
            if set(vals) - allowed:
                raise UserError(_("历史迁移综合合同已确认，只允许补充往来单位和备注。"))
        return super().write(vals)

    @api.model
    def _sync_company_vals(self, vals):
        if vals.get("company_id"):
            return
        project_id = vals.get("project_id")
        if project_id:
            project = self.env["project.project"].browse(int(project_id)).exists()
            if project and project.company_id:
                vals["company_id"] = project.company_id.id
                return
        vals["company_id"] = self.env.company.id

    @api.onchange("tax_id")
    def _onchange_tax_id(self):
        for rec in self:
            rec.tax_rate = rec.tax_id.amount if rec.tax_id else 0.0

    @api.onchange("project_id")
    def _onchange_project_id(self):
        for rec in self:
            if rec.project_id and rec.project_id.company_id:
                rec.company_id = rec.project_id.company_id

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for rec in self:
            if not rec.partner_id:
                continue
            partner_vals = rec._general_contract_partner_defaults(rec.partner_id)
            for field_name, value in partner_vals.items():
                if value and not rec[field_name]:
                    rec[field_name] = value

    @api.model
    def _general_contract_partner_defaults(self, partner):
        partner = partner.exists()
        if not partner:
            return {}
        bank = partner.bank_ids[:1]
        return {
            "partner_name_text": partner.display_name or partner.name,
            "credit_code": partner.vat or getattr(partner, "legacy_credit_code", False),
            "contact_name": partner.name if partner.company_type == "person" else "",
            "contact_phone": partner.mobile or partner.phone,
            "bank_name": getattr(partner, "sc_bank_name", False) or getattr(bank, "sc_bank_name", False) or getattr(bank, "bank_name", False),
            "bank_account": getattr(partner, "sc_bank_account", False) or getattr(bank, "acc_number", False),
        }

    @api.model
    def _contract_tax_for_rate(self, amount):
        try:
            amount = float(amount or 0.0)
        except Exception:
            amount = 0.0
        if amount <= 0:
            return self.env["account.tax"].browse()
        helper = self.env["construction.contract"].sudo().with_company(self.env.company)
        helper._sc_ensure_contract_tax_seeds()
        return (
            self.env["account.tax"]
            .sudo()
            .with_context(active_test=False)
            .search(
                [
                    ("company_id", "=", self.env.company.id),
                    ("type_tax_use", "=", "none"),
                    ("amount_type", "=", "percent"),
                    ("price_include", "=", False),
                    ("amount", "=", amount),
                ],
                order="active desc, id asc",
                limit=1,
            )
        )

    @api.model
    def _sync_tax_vals(self, vals):
        if not isinstance(vals, dict):
            return
        if vals.get("tax_id"):
            tax = self.env["account.tax"].browse(int(vals.get("tax_id") or 0)).exists()
            if tax:
                vals["tax_rate"] = tax.amount
            return
        if vals.get("tax_rate") and not vals.get("tax_id"):
            tax = self._contract_tax_for_rate(vals.get("tax_rate"))
            if tax:
                vals["tax_id"] = tax.id

    @api.model
    def _sync_contract_tax_ids_from_rate(self):
        self.env["construction.contract"].sudo()._sc_ensure_contract_tax_seeds()
        rows = self.sudo().search([("tax_id", "=", False), ("tax_rate", ">", 0)])
        for rec in rows:
            tax = rec._contract_tax_for_rate(rec.tax_rate)
            if tax:
                rec.with_context(skip_validation_check=True, tracking_disable=True).write({"tax_id": tax.id})
        return True

    @api.model
    def _needs_contract_direction_refresh(self, vals):
        evidence_fields = {"contract_type", "contract_attribute", "contract_name"}
        return bool(evidence_fields & set(vals)) and "contract_direction" not in vals

    @api.model
    def _prepare_contract_direction_vals(self, vals):
        if vals.get("contract_direction"):
            return {
                "contract_direction_source": vals.get("contract_direction_source") or "manual",
                "contract_direction_reason": vals.get("contract_direction_reason") or _("人工指定"),
            }
        direction, reason = self._classify_contract_direction(
            vals.get("contract_type"),
            vals.get("contract_attribute"),
            vals.get("contract_name"),
        )
        return {
            "contract_direction": direction,
            "contract_direction_source": "contract_evidence",
            "contract_direction_reason": reason,
        }

    @api.model
    def _classify_contract_direction(self, contract_type=None, contract_attribute=None, contract_name=None):
        evidence = " ".join(
            str(item or "").strip()
            for item in (contract_type, contract_attribute, contract_name)
            if str(item or "").strip()
        )
        if not evidence:
            return "unknown", _("缺少合同方向证据")
        income_keywords = ("收入", "销售", "收款", "回款", "应收", "经营收入", "公司收入")
        expense_keywords = ("供应商", "采购", "支出", "付款", "应付", "分包", "劳务", "材料", "设备", "租赁", "咨询", "费用")
        if any(keyword in evidence for keyword in income_keywords):
            return "income", _("命中收入合同关键字：%s") % evidence
        if any(keyword in evidence for keyword in expense_keywords):
            return "expense", _("命中支出合同关键字：%s") % evidence
        return "neutral", _("未命中收支方向关键字：%s") % evidence

    @api.depends("install_debug_payment")
    def _compute_business_aliases(self):
        for rec in self:
            rec.install_commissioning_payment = rec.install_debug_payment

    @api.depends("amount_total", "change_amount_total")
    def _compute_change_rate(self):
        for rec in self:
            rec.change_rate = (rec.change_amount_total / rec.amount_total * 100.0) if rec.amount_total else 0.0

    @api.depends("amount_total", "invoice_amount", "received_amount", "paid_amount")
    def _compute_business_amounts(self):
        for rec in self:
            rec.uninvoiced_amount = max((rec.amount_total or 0.0) - (rec.invoice_amount or 0.0), 0.0)
            rec.unreceived_amount = max((rec.amount_total or 0.0) - (rec.received_amount or 0.0), 0.0)
            rec.unpaid_amount = max((rec.amount_total or 0.0) - (rec.paid_amount or 0.0), 0.0)

    def action_confirm(self):
        policy_model = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿状态的一般合同（公司）可以确认。"))
            rec._check_business_anchor()
            if policy_model.is_approval_required(rec._name, company=rec.company_id) and rec.validation_status != "validated":
                rec._request_general_contract_validation()
                continue
            policy = policy_model.get_active_policy(rec._name, company=rec.company_id)
            if policy and not policy_model.is_approval_required(rec._name, company=rec.company_id):
                policy.assert_user_can_approve()
            rec.with_context(skip_validation_check=True).write({"state": "confirmed", "reject_reason": False})

    def action_signed(self):
        for rec in self:
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认状态的一般合同（公司）可以签署。"))
            rec._check_business_anchor()
            if rec.state == "draft":
                rec.action_confirm()
                if rec.state != "confirmed":
                    continue
            rec.state = "signed"

    def _check_business_anchor(self):
        for rec in self:
            if not rec.contract_name:
                raise UserError(_("一般合同（公司）必须填写合同名称。"))
            if not rec.partner_id and not rec.partner_name_text:
                raise UserError(_("一般合同（公司）必须填写往来单位或合同方文本。"))
            if rec.amount_total <= 0:
                raise UserError(_("一般合同（公司）合同金额必须大于0。"))
            if rec.contract_direction == "unknown":
                raise UserError(_("一般合同（公司）必须明确合同方向。"))

    def _request_general_contract_validation(self):
        self.ensure_one()
        if self.review_ids and self.validation_status == "rejected":
            self.restart_validation()
        elif not self.review_ids or self.validation_status == "no":
            reviews = self.request_validation()
            if not reviews:
                    raise UserError(_("一般合同（公司）已启用审批，但没有匹配的统一审批规则，请检查业务审批配置。"))
        else:
            raise UserError(_("一般合同（公司）已经在统一审批流程中，请等待审批完成。"))
        self.with_context(skip_validation_check=True).write({"reject_reason": False})

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
                continue
            if rec.validation_status != "validated":
                raise UserError(_("一般合同（公司）尚未完成统一审批流程。"))
            rec.with_context(skip_validation_check=True).write({"reject_reason": False})
        return self.action_confirm()

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state != "draft":
                continue
            rec.with_context(skip_validation_check=True).write(
                {"reject_reason": reason or rec._get_tier_reject_reason()}
            )

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移综合合同不能在新系统取消。"))
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认状态的一般合同（公司）可以取消。"))
            rec.state = "cancel"
