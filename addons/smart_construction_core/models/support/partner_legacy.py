# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    sc_supplier_type = fields.Selection(
        [
            ("material", "材料供应商"),
            ("labor", "劳务供应商"),
            ("subcontract", "分包单位"),
            ("service", "服务供应商"),
            ("equipment", "设备供应商"),
            ("other", "其他"),
        ],
        string="供应商类型",
        index=True,
    )
    sc_account_name = fields.Char(string="账户名称")
    sc_bank_name = fields.Char(string="开户银行")
    sc_bank_account = fields.Char(string="账号")
    sc_region = fields.Char(string="所属地区", index=True)
    sc_registered_capital = fields.Char(string="注册资本")
    sc_business_scope = fields.Text(string="经营范围")
    sc_default_tax_rate = fields.Float(string="默认税率%", digits=(16, 4))
    sc_default_tax_rate_text = fields.Char(string="历史税率文本")
    sc_source_partner_code = fields.Char(string="单位编号", index=True)
    sc_source_document_state = fields.Char(string="单据状态", index=True)
    sc_source_push_result = fields.Char(string="推送结果", index=True)
    sc_source_project_name = fields.Text(string="项目名称")
    sc_source_cooperation_type = fields.Char(string="合作类型", index=True)
    sc_source_fact_count = fields.Integer(string="业务事实数")
    sc_source_fact_source = fields.Char(string="业务事实来源")
    sc_source_receipt_amount = fields.Float(string="收款金额", digits=(16, 2))
    sc_source_payment_amount = fields.Float(string="付款金额", digits=(16, 2))
    sc_source_created_by = fields.Char(string="录入人")
    sc_source_created_at = fields.Char(string="录入时间")
    sc_supplier_note = fields.Text(string="供应商备注")
    sc_business_role_label = fields.Char(string="业务身份", compute="_compute_sc_business_display", store=True, readonly=True)
    sc_business_fact_basis = fields.Char(string="业务依据", compute="_compute_sc_business_display", store=True, readonly=True)
    sc_legacy_source_label = fields.Char(string="来源类型", compute="_compute_sc_business_display", store=True, readonly=True)
    sc_attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_res_partner_supplier_attachment_rel",
        "partner_id",
        "attachment_id",
        string="供应商附件",
    )

    # Legacy identity carrier fields for idempotent migration replay.
    legacy_partner_id = fields.Char(string="历史供应商编号", index=True)
    legacy_partner_source = fields.Char(string="历史来源", index=True)
    legacy_partner_name = fields.Char(string="历史供应商名称")
    legacy_credit_code = fields.Char(string="历史统一信用代码")
    legacy_tax_no = fields.Char(string="历史税号", index=True)
    legacy_deleted_flag = fields.Char(string="历史删除标识")
    legacy_source_evidence = fields.Char(string="历史来源证据")

    @api.depends("customer_rank", "supplier_rank", "legacy_partner_source")
    def _compute_sc_business_display(self):
        for partner in self:
            customer = bool(partner.customer_rank)
            supplier = bool(partner.supplier_rank)
            if customer and supplier:
                partner.sc_business_role_label = "客户/供应商"
            elif customer:
                partner.sc_business_role_label = "客户"
            elif supplier:
                partner.sc_business_role_label = "供应商"
            else:
                partner.sc_business_role_label = "后台留存"

            source = partner.legacy_partner_source or ""
            if customer and supplier:
                partner.sc_business_fact_basis = "收款/收入与供应商业务事实"
            elif customer:
                partner.sc_business_fact_basis = "收款合同/收款/收入业务事实"
            elif supplier:
                partner.sc_business_fact_basis = "供应商合同/付款业务事实"
            else:
                partner.sc_business_fact_basis = "无用户要求展示业务事实"

            if source == "legacy_mssql_customer_business_fact":
                partner.sc_legacy_source_label = "旧业务库客户事实"
            elif source == "xlsx_business_aligned_partner":
                partner.sc_legacy_source_label = "客户供应商整理数据"
            elif source:
                partner.sc_legacy_source_label = source
            else:
                partner.sc_legacy_source_label = ""


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    sc_legacy_external_id = fields.Char(string="历史账户外部键", index=True, copy=False)
    sc_legacy_partner_id = fields.Char(string="历史往来单位编号", index=True)
    sc_legacy_partner_source = fields.Char(string="历史往来单位来源", index=True)
    sc_legacy_partner_name = fields.Char(string="历史往来单位名称")
    sc_account_holder_name = fields.Char(string="账户名称")
    sc_bank_name = fields.Char(string="开户银行", index=True)
    sc_source_evidence = fields.Char(string="历史来源证据")
    sc_import_batch = fields.Char(string="导入批次", index=True)

    _sql_constraints = [
        (
            "sc_legacy_external_id_unique",
            "unique(sc_legacy_external_id)",
            "历史账户外部键必须唯一。",
        ),
    ]


class ScPartnerImportReview(models.Model):
    _name = "sc.partner.import.review"
    _description = "客户供应商导入复核"
    _order = "review_state, review_reason, partner_name"
    _rec_name = "partner_name"

    import_batch = fields.Char(string="导入批次", required=True, default="partner_business_fit_v1", index=True)
    legacy_partner_source = fields.Char(string="历史来源", required=True, index=True)
    legacy_partner_id = fields.Char(string="历史身份键", required=True, index=True)
    partner_name = fields.Char(string="往来单位名称", required=True, index=True)
    company_type = fields.Selection([("company", "企业/组织"), ("person", "个人")], string="类型", default="company", index=True)
    review_reason = fields.Selection(
        [
            ("background_only_no_user_requested_business_fact", "后台留存"),
            ("unknown_business_role", "角色不明确"),
            ("personal_fragment_review", "个人片段复核"),
            ("invalid_bank_account_review", "银行账户异常"),
            ("invalid_or_placeholder_credit", "信用代码异常"),
            ("multiple_current_payload_matches", "多目标匹配"),
            ("update_only_not_found", "仅更新目标未命中"),
            ("update_only_ambiguous", "仅更新目标歧义"),
            ("mixed_blocker", "多重阻断"),
        ],
        string="复核原因",
        required=True,
        default="mixed_blocker",
        index=True,
    )
    review_state = fields.Selection(
        [
            ("candidate", "待复核"),
            ("resolved", "已处理"),
            ("ignored", "忽略"),
        ],
        string="复核状态",
        required=True,
        default="candidate",
        index=True,
    )
    suggested_customer_rank = fields.Integer(string="建议客户标识")
    suggested_supplier_rank = fields.Integer(string="建议供应商标识")
    confirmed_customer_rank = fields.Integer(string="确认客户标识")
    confirmed_supplier_rank = fields.Integer(string="确认供应商标识")
    target_partner_id = fields.Many2one("res.partner", string="目标往来单位", index=True, ondelete="set null")
    sc_supplier_type = fields.Char(string="供应商类型")
    sc_region = fields.Char(string="所属地区", index=True)
    street = fields.Char(string="地址")
    sc_registered_capital = fields.Char(string="注册资本")
    sc_business_scope = fields.Text(string="经营范围")
    sc_default_tax_rate = fields.Float(string="默认税率%", digits=(16, 4))
    sc_default_tax_rate_text = fields.Char(string="历史税率文本")
    vat = fields.Char(string="统一社会信用代码", index=True)
    sc_account_name = fields.Char(string="账户名称")
    sc_bank_name = fields.Char(string="开户银行")
    sc_bank_account = fields.Char(string="账号")
    source_created_by = fields.Char(string="来源创建人")
    source_created_at = fields.Char(string="来源创建时间")
    source_document_state = fields.Char(string="来源单据状态")
    source_push_result = fields.Char(string="来源推送结果")
    source_project_name = fields.Text(string="来源项目")
    source_files = fields.Text(string="来源文件")
    review_flags = fields.Char(string="复核标记")
    gate_reason = fields.Char(string="阻断原因")
    evidence = fields.Text(string="证据")
    reviewer_id = fields.Many2one("res.users", string="处理人", readonly=True, ondelete="set null")
    reviewed_at = fields.Datetime(string="处理时间", readonly=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "sc_partner_import_review_identity_unique",
            "unique(import_batch, legacy_partner_source, legacy_partner_id)",
            "同一导入批次的客户供应商复核身份必须唯一。",
        ),
    ]

    def _mark_resolved(self, customer_rank: int, supplier_rank: int) -> None:
        self.write(
            {
                "review_state": "resolved",
                "confirmed_customer_rank": customer_rank,
                "confirmed_supplier_rank": supplier_rank,
                "reviewer_id": self.env.user.id,
                "reviewed_at": fields.Datetime.now(),
            }
        )

    def action_resolve_customer(self):
        self._mark_resolved(1, 0)

    def action_resolve_supplier(self):
        self._mark_resolved(0, 1)

    def action_resolve_customer_supplier(self):
        self._mark_resolved(1, 1)

    def action_ignore(self):
        self.write(
            {
                "review_state": "ignored",
                "reviewer_id": self.env.user.id,
                "reviewed_at": fields.Datetime.now(),
            }
        )
