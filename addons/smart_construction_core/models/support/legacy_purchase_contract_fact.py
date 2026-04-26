# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyPurchaseContractFact(models.Model):
    _name = "sc.legacy.purchase.contract.fact"
    _description = "Legacy Purchase and General Contract Fact"
    _order = "submitted_time desc, legacy_record_id"

    legacy_record_id = fields.Char(required=True, index=True)
    legacy_pid = fields.Char(index=True)
    source_dataset = fields.Char(index=True)
    document_no = fields.Char(index=True)
    document_state = fields.Char(index=True)
    submitted_time = fields.Datetime(index=True)
    applicant_name = fields.Char(index=True)
    applicant_department_legacy_id = fields.Char(index=True)
    applicant_department = fields.Char(index=True)
    project_legacy_id = fields.Char(index=True)
    project_name = fields.Char(index=True)
    project_id = fields.Many2one("project.project", index=True, ondelete="set null")
    contract_name = fields.Char(index=True)
    contract_no = fields.Char(index=True)
    signing_place = fields.Char(index=True)
    contract_type_legacy_id = fields.Char(index=True)
    contract_type = fields.Char(index=True)
    completion_date = fields.Datetime(index=True)
    expected_sign_date = fields.Datetime(index=True)
    total_amount = fields.Float()
    currency_legacy_id = fields.Char(index=True)
    currency_name = fields.Char(index=True)
    prepayment_amount = fields.Float()
    install_debug_payment = fields.Float()
    warranty_deposit = fields.Float()
    payment_terms = fields.Text()
    partner_legacy_id = fields.Char(index=True)
    partner_name = fields.Char(index=True)
    contact_name = fields.Char(index=True)
    contact_phone = fields.Char(index=True)
    bank_name = fields.Char(index=True)
    bank_account = fields.Char(index=True)
    sign_status = fields.Char(index=True)
    purchase_engineer = fields.Char(index=True)
    special_condition = fields.Text()
    attachment_ref = fields.Char()
    person_legacy_id = fields.Char(index=True)
    creator_legacy_user_id = fields.Char(index=True)
    creator_name = fields.Char(index=True)
    created_time = fields.Datetime(index=True)
    modifier_legacy_user_id = fields.Char(index=True)
    modifier_name = fields.Char(index=True)
    modified_time = fields.Datetime(index=True)
    is_supplement_contract = fields.Char(index=True)
    related_contract_legacy_id = fields.Char(index=True)
    related_contract_no = fields.Char(index=True)
    contract_attribute = fields.Char(index=True)
    credit_code = fields.Char(index=True)
    tax_rate = fields.Float()
    note = fields.Text()
    source_table = fields.Char(default="T_CGHT_INFO", required=True, index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_purchase_contract_unique", "unique(legacy_record_id)", "Legacy purchase contract id must be unique."),
    ]
