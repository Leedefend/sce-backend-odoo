# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ScLegacyPurchaseContractFact(models.Model):
    _name = "sc.legacy.purchase.contract.fact"
    _description = "采购/一般合同"
    _order = "submitted_time desc, legacy_record_id"

    legacy_record_id = fields.Char(string="记录编号", required=True, index=True, default=lambda self: self._default_record_id())
    legacy_pid = fields.Char(string="附件编号", index=True)
    source_dataset = fields.Char(string="数据来源", index=True)
    document_no = fields.Char(string="单号", index=True)
    document_state = fields.Char(string="单据状态", index=True)
    submitted_time = fields.Datetime(string="提交时间", index=True)
    applicant_name = fields.Char(string="申请人", index=True)
    applicant_department_legacy_id = fields.Char(string="申请部门原编号", index=True)
    applicant_department = fields.Char(string="申请部门", index=True)
    project_legacy_id = fields.Char(string="项目原编号", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    contract_name = fields.Char(string="合同名称", index=True)
    contract_no = fields.Char(string="合同编号", index=True)
    signing_place = fields.Char(string="签署地点", index=True)
    contract_type_legacy_id = fields.Char(string="合同类型原编号", index=True)
    contract_type = fields.Char(string="合同类型", index=True)
    completion_date = fields.Datetime(string="完成时间", index=True)
    expected_sign_date = fields.Datetime(string="预计签署时间", index=True)
    total_amount = fields.Float(string="合同金额")
    currency_legacy_id = fields.Char(string="币种原编号", index=True)
    currency_name = fields.Char(string="币种", index=True)
    prepayment_amount = fields.Float(string="预付款")
    install_debug_payment = fields.Float(string="安装调试款")
    install_commissioning_payment = fields.Float(string="安装调试款", compute="_compute_business_aliases")
    warranty_deposit = fields.Float(string="质保金")
    payment_terms = fields.Text(string="付款条件")
    partner_legacy_id = fields.Char(string="往来方原编号", index=True)
    partner_name = fields.Char(string="往来方", index=True)
    contact_name = fields.Char(string="联系人", index=True)
    contact_phone = fields.Char(string="联系电话", index=True)
    bank_name = fields.Char(string="开户行", index=True)
    bank_account = fields.Char(string="银行账号", index=True)
    sign_status = fields.Char(string="签署状态", index=True)
    purchase_engineer = fields.Char(string="采购工程师", index=True)
    special_condition = fields.Text(string="特殊条款")
    attachment_ref = fields.Char(string="附件")
    person_legacy_id = fields.Char(string="人员原编号", index=True)
    creator_legacy_user_id = fields.Char(string="创建人原编号", index=True)
    creator_name = fields.Char(string="创建人", index=True)
    created_time = fields.Datetime(string="创建时间", index=True)
    modifier_legacy_user_id = fields.Char(string="修改人原编号", index=True)
    modifier_name = fields.Char(string="修改人", index=True)
    modified_time = fields.Datetime(string="修改时间", index=True)
    is_supplement_contract = fields.Char(string="是否补充合同", index=True)
    related_contract_legacy_id = fields.Char(string="关联合同原编号", index=True)
    related_contract_no = fields.Char(string="关联合同编号", index=True)
    contract_attribute = fields.Char(string="合同属性", index=True)
    credit_code = fields.Char(string="统一信用代码", index=True)
    tax_rate = fields.Float(string="税率")
    note = fields.Text(string="备注")
    source_table = fields.Char(string="来源表", default="T_CGHT_INFO", required=True, index=True)
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        ("legacy_purchase_contract_unique", "unique(legacy_record_id)", "Legacy purchase contract id must be unique."),
    ]

    @api.depends("install_debug_payment")
    def _compute_business_aliases(self):
        for record in self:
            record.install_commissioning_payment = record.install_debug_payment

    @api.model
    def _default_record_id(self):
        return self.env["ir.sequence"].next_by_code("sc.legacy.purchase.contract.fact") or "新系统采购一般合同"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("legacy_record_id"):
                vals["legacy_record_id"] = self._default_record_id()
        return super().create(vals_list)
