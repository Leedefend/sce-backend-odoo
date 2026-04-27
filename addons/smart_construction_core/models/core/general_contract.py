# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScGeneralContract(models.Model):
    _name = "sc.general.contract"
    _description = "综合合同"
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
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True)
    partner_name_text = fields.Char(string="合同方文本", index=True)
    credit_code = fields.Char(string="统一信用代码", index=True)
    contact_name = fields.Char(string="联系人", index=True)
    contact_phone = fields.Char(string="联系电话", index=True)
    bank_name = fields.Char(string="开户行", index=True)
    bank_account = fields.Char(string="银行账号", index=True)
    document_no = fields.Char(string="来源单号", index=True)
    contract_no = fields.Char(string="合同编号", index=True)
    contract_name = fields.Char(string="合同名称", required=True, index=True)
    contract_type = fields.Char(string="合同类型", index=True)
    contract_attribute = fields.Char(string="合同属性", index=True)
    signing_place = fields.Char(string="签署地点", index=True)
    contract_date = fields.Date(string="合同日期", default=fields.Date.context_today, index=True)
    expected_sign_date = fields.Date(string="预计签署日期", index=True)
    completion_date = fields.Date(string="完成日期", index=True)
    amount_total = fields.Monetary(string="合同金额", currency_field="currency_id", required=True)
    prepayment_amount = fields.Monetary(string="预付款", currency_field="currency_id")
    install_debug_payment = fields.Monetary(string="安装调试款", currency_field="currency_id")
    install_commissioning_payment = fields.Monetary(
        string="安装调试款",
        currency_field="currency_id",
        compute="_compute_business_aliases",
    )
    warranty_deposit = fields.Monetary(string="质保金", currency_field="currency_id")
    tax_rate = fields.Float(string="税率", digits=(16, 4))
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    payment_terms = fields.Text(string="付款条件")
    special_condition = fields.Text(string="特殊条款")
    applicant_name = fields.Char(string="申请人", index=True)
    applicant_department = fields.Char(string="申请部门", index=True)
    purchase_engineer = fields.Char(string="采购工程师", index=True)
    related_contract_no = fields.Char(string="关联合同号", index=True)
    is_supplement_contract = fields.Char(string="是否补充合同", index=True)
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    legacy_attachment_ref = fields.Char(string="历史附件引用", readonly=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "Legacy general contract source must be unique.",
        ),
        ("amount_total_nonnegative", "CHECK(amount_total >= 0)", "Contract amount must be non-negative."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.general.contract") or _("General Contract")
        return super().create(vals_list)

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {"partner_id", "note", "active", "write_uid", "write_date"}
            if set(vals) - allowed:
                raise UserError(_("历史迁移综合合同已确认，只允许补充往来单位和备注。"))
        return super().write(vals)

    @api.depends("install_debug_payment")
    def _compute_business_aliases(self):
        for rec in self:
            rec.install_commissioning_payment = rec.install_debug_payment

    def action_confirm(self):
        for rec in self:
            if rec.state == "draft":
                policy = self.env["sc.approval.policy"].get_active_policy(rec._name)
                if policy:
                    policy.assert_user_can_approve()
                rec.state = "confirmed"

    def action_signed(self):
        for rec in self:
            if rec.state in ("draft", "confirmed"):
                if rec.state == "draft":
                    policy = self.env["sc.approval.policy"].get_active_policy(rec._name)
                    if policy:
                        policy.assert_user_can_approve()
                rec.state = "signed"

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移综合合同不能在新系统取消。"))
            if rec.state != "cancel":
                rec.state = "cancel"
