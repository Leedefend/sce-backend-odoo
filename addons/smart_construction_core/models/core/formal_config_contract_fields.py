# -*- coding: utf-8 -*-
"""Formal fields used by released business configuration contracts.

These fields are product-facing projections.  They intentionally compute
from stable model fields instead of p1/legacy visible aliases so released
configuration data can stop depending on migration-era field names.
"""

from odoo import api, fields, models


def _display_value(record, source_name):
    if source_name not in record._fields:
        return ""
    value = record[source_name]
    field = record._fields[source_name]
    if field.type == "boolean":
        return "是" if value else "否"
    if value in (False, None, "") and field.type not in ("integer", "float", "monetary") :
        return ""
    if field.type == "selection":
        selection = field.selection(record) if callable(field.selection) else field.selection
        return dict(selection or []).get(value, value or "")
    if field.type in ("many2one",):
        return value.display_name if value else ""
    if field.type in ("many2many", "one2many") :
        if not value:
            return ""
        if "attachment" in source_name:
            return "附件(%s)" % len(value)
        return ", ".join(value.mapped("display_name")[:5])
    if field.type == "datetime":
        return fields.Datetime.to_string(value) if value else ""
    if field.type == "date":
        return fields.Date.to_string(value) if value else ""
    return str(value) if value not in (False, None) else ""


def _compute_formal_config_contract_fields(records, mapping):
    for record in records:
        for target, sources in mapping.items():
            text = ""
            for source_name in sources:
                text = _display_value(record, source_name)
                if text != "":
                    break
            record[target] = text


_PAYMENTREQUEST_FORMAL_CONFIG_FIELDS = {
    'payment_request_payment_account_no_display': ('付款账号', ('payment_account_no_display',)),
    'payment_request_bank_name_display': ('开户行', ('payee_bank_name_display',)),
    'payment_request_cost_type_display': ('成本分类名称', ('cost_type_display',)),
    'payment_request_account_holder_display': ('户名', ('payee_account_name_display',)),
    'payment_request_has_related_document_display': ('是否关联单据', ('related_document_text',)),
    'payment_request_account_no_display': ('账号', ('payee_account_no_display',)),
    'payment_request_attachment_text_display': ('附件', ('attachment_ids',)),
}

class PaymentRequestFormalConfigContractFields(models.Model):
    _inherit = 'payment.request'

    for _field_name, (_field_label, _field_sources) in _PAYMENTREQUEST_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _PAYMENTREQUEST_FORMAL_CONFIG_FIELDS.items()},
        )

_CONSTRUCTIONDIARY_FORMAL_CONFIG_FIELDS = {
    'diary_morning_weather_display': ('上午气候', ('weather',)),
    'diary_afternoon_weather_display': ('下午气候', ('weather',)),
    'diary_daily_construction_content_display': ('当日施工内容', ('description',)),
    'diary_operator_manager_display': ('操作负责人', ('handler_name',)),
    'diary_construction_worker_display': ('施工员', ('handler_name',)),
    'diary_temperature_display': ('温度', ('weather',)),
}

class ConstructionDiaryFormalConfigContractFields(models.Model):
    _inherit = 'sc.construction.diary'

    for _field_name, (_field_label, _field_sources) in _CONSTRUCTIONDIARY_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _CONSTRUCTIONDIARY_FORMAL_CONFIG_FIELDS.items()},
        )

_EQUIPMENTREQUEST_FORMAL_CONFIG_FIELDS = {
    'equipment_request_document_no_display': ('单据编号', ('name',)),
    'equipment_request_contract_title_display': ('合同标题', ('name',)),
    'equipment_request_contract_no_display': ('合同编号', ('name',)),
    'equipment_request_source_created_by_display': ('录入人', ('source_created_by',)),
    'equipment_request_rental_content_display': ('租赁内容', ('note',)),
}

class EquipmentRequestFormalConfigContractFields(models.Model):
    _inherit = 'sc.equipment.request'

    for _field_name, (_field_label, _field_sources) in _EQUIPMENTREQUEST_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _EQUIPMENTREQUEST_FORMAL_CONFIG_FIELDS.items()},
        )

_EQUIPMENTSETTLEMENT_FORMAL_CONFIG_FIELDS = {
    'equipment_settlement_payment_status_display': ('付款状态', ('state',)),
    'equipment_settlement_document_status_display': ('单据状态', ('state',)),
    'equipment_settlement_source_created_by_display': ('录入人', ('source_created_by',)),
    'equipment_settlement_payment_request_status_display': ('支付申请状态', ('state',)),
}

class EquipmentSettlementFormalConfigContractFields(models.Model):
    _inherit = 'sc.equipment.settlement'

    for _field_name, (_field_label, _field_sources) in _EQUIPMENTSETTLEMENT_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _EQUIPMENTSETTLEMENT_FORMAL_CONFIG_FIELDS.items()},
        )

_EQUIPMENTUSAGE_FORMAL_CONFIG_FIELDS = {
    'equipment_usage_note_display': ('备注', ('note',)),
    'equipment_usage_former_name_list_display': ('曾用名单', ('note',)),
    'equipment_usage_attachment_text_display': ('附件', ('attachment_ids',)),
}

class EquipmentUsageFormalConfigContractFields(models.Model):
    _inherit = 'sc.equipment.usage'

    for _field_name, (_field_label, _field_sources) in _EQUIPMENTUSAGE_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _EQUIPMENTUSAGE_FORMAL_CONFIG_FIELDS.items()},
        )

_FINANCINGLOAN_FORMAL_CONFIG_FIELDS = {
    'financing_loan_borrow_rate_display': ('借款利率', ('rate_label',)),
    'financing_loan_interest_amount_display': ('利息', ('rate_label',)),
    'financing_loan_note_display': ('备注', ('note',)),
    'financing_loan_actual_annual_rate_display': ('实际年利率', ('rate_label',)),
    'financing_loan_loan_interest_display': ('贷款利息', ('rate_label',)),
    'financing_loan_repayment_time_display': ('还款时间', ('due_date',)),
    'financing_loan_attachment_text_display': ('附件', ('attachment_ids',)),
}

class FinancingLoanFormalConfigContractFields(models.Model):
    _inherit = 'sc.financing.loan'

    for _field_name, (_field_label, _field_sources) in _FINANCINGLOAN_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _FINANCINGLOAN_FORMAL_CONFIG_FIELDS.items()},
        )

_FUNDACCOUNT_FORMAL_CONFIG_FIELDS = {
    'fund_account_opening_balance_display': ('初期余额', ('opening_balance',)),
    'fund_account_document_no_display': ('单据编号', ('name',)),
    'fund_account_bank_account_display': ('开户账号', ('account_no',)),
    'fund_account_source_origin_display': ('录入来源', ('source_origin',)),
    'fund_account_is_transition_account_display': ('是否过渡账户', ('fixed_account',)),
    'fund_account_is_default_account_display': ('是否默认账号', ('is_default',)),
    'fund_account_account_name_display': ('账号名称', ('name',)),
    'fund_account_account_type_display': ('账号类型', ('account_type',)),
    'fund_account_account_status_display': ('账户状态', ('state',)),
    'fund_account_project_name_display': ('项目名称', ('project_id',)),
}

class FundAccountFormalConfigContractFields(models.Model):
    _inherit = 'sc.fund.account'

    for _field_name, (_field_label, _field_sources) in _FUNDACCOUNT_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _FUNDACCOUNT_FORMAL_CONFIG_FIELDS.items()},
        )

class FundOperationFormalConfigContractFields(models.Model):
    _inherit = 'sc.fund.account.operation'

    fund_operation_attachment_text_display = fields.Char(
        string='附件',
        compute="_compute_formal_config_contract_fields",
        readonly=True,
    )

    def _fund_operation_attachment_ref_value(self):
        return ""

    @api.depends("attachment_ids")
    def _compute_formal_config_contract_fields(self):
        for record in self:
            if record.attachment_ids:
                record.fund_operation_attachment_text_display = "附件(%s)" % len(record.attachment_ids)
                continue
            legacy_attachment = (record._fund_operation_attachment_ref_value() or "").strip()
            record.fund_operation_attachment_text_display = legacy_attachment

_INVOICEREGISTRATION_FORMAL_CONFIG_FIELDS = {
    'invoice_registration_document_no_display': ('单据编号', ('document_no',)),
    'invoice_registration_contract_no_display': ('合同编号', ('contract_id',)),
    'invoice_registration_tax_included_amount_display': ('含税金额', ('amount_total',)),
    'invoice_registration_invoice_status_display': ('开票状态', ('invoice_state',)),
    'invoice_registration_source_created_by_display': ('录入人', ('creator_name',)),
    'invoice_registration_push_result_display': ('推送结果', ('push_result',)),
    'invoice_registration_applicant_display': ('申请人', ('applicant_name',)),
    'invoice_registration_application_date_display': ('申请日期', ('application_date',)),
    'invoice_registration_accumulated_invoice_amount_display': ('累计开票金额', ('amount_total',)),
    'invoice_registration_surcharge_amount_display': ('附加税', ('surcharge_amount',)),
}

class InvoiceRegistrationFormalConfigContractFields(models.Model):
    _inherit = 'sc.invoice.registration'

    for _field_name, (_field_label, _field_sources) in _INVOICEREGISTRATION_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _INVOICEREGISTRATION_FORMAL_CONFIG_FIELDS.items()},
        )

_LABORREQUEST_FORMAL_CONFIG_FIELDS = {
    'labor_request_document_no_display': ('单据编号', ('name',)),
    'labor_request_contract_no_display': ('合同编号', ('name',)),
    'labor_request_source_created_by_display': ('录入人', ('source_created_by',)),
    'labor_request_push_project_name_display': ('推送项目名称', ('project_id',)),
    'labor_request_title_display': ('标题', ('name',)),
    'labor_request_project_name_display': ('项目名称', ('project_id',)),
}

class LaborRequestFormalConfigContractFields(models.Model):
    _inherit = 'sc.labor.request'

    for _field_name, (_field_label, _field_sources) in _LABORREQUEST_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _LABORREQUEST_FORMAL_CONFIG_FIELDS.items()},
        )

_LABORSETTLEMENT_FORMAL_CONFIG_FIELDS = {
    'labor_settlement_payment_status_display': ('付款状态', ('state',)),
    'labor_settlement_document_no_display': ('单据编号', ('name',)),
    'labor_settlement_contract_no_display': ('合同编号', ('name',)),
    'labor_settlement_source_created_by_display': ('录入人', ('source_created_by',)),
    'labor_settlement_payment_request_status_display': ('支付申请状态', ('state',)),
    'labor_settlement_title_display': ('标题', ('name',)),
}

class LaborSettlementFormalConfigContractFields(models.Model):
    _inherit = 'sc.labor.settlement'

    for _field_name, (_field_label, _field_sources) in _LABORSETTLEMENT_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _LABORSETTLEMENT_FORMAL_CONFIG_FIELDS.items()},
        )

_FUNDDAILYSNAPSHOT_FORMAL_CONFIG_FIELDS = {
    'fund_daily_snapshot_account_counterparty_display': ('账户往来', ('document_scope',)),
}

class FundDailySnapshotFormalConfigContractFields(models.Model):
    _inherit = 'sc.legacy.fund.daily.snapshot.fact'

    for _field_name, (_field_label, _field_sources) in _FUNDDAILYSNAPSHOT_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _FUNDDAILYSNAPSHOT_FORMAL_CONFIG_FIELDS.items()},
        )

_MATERIALINBOUND_FORMAL_CONFIG_FIELDS = {
    'material_inbound_document_status_display': ('单据状态', ('state',)),
    'material_inbound_attachment_text_display': ('附件', ('attachment_ids',)),
}

class MaterialInboundFormalConfigContractFields(models.Model):
    _inherit = 'sc.material.inbound'

    for _field_name, (_field_label, _field_sources) in _MATERIALINBOUND_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _MATERIALINBOUND_FORMAL_CONFIG_FIELDS.items()},
        )

_MATERIALPURCHASE_FORMAL_CONFIG_FIELDS = {
    'material_purchase_contract_no_display': ('合同编号', ('name',)),
    'material_purchase_source_created_by_display': ('录入人', ('source_created_by',)),
    'material_purchase_title_display': ('标题', ('name',)),
    'material_purchase_purchasing_unit_display': ('购货单位', ('project_id',)),
    'material_purchase_attachment_text_display': ('附件', ('attachment_ids',)),
    'material_purchase_project_name_display': ('项目名称', ('project_id',)),
}

class MaterialPurchaseFormalConfigContractFields(models.Model):
    _inherit = 'sc.material.purchase.request'

    for _field_name, (_field_label, _field_sources) in _MATERIALPURCHASE_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _MATERIALPURCHASE_FORMAL_CONFIG_FIELDS.items()},
        )

_RENTALORDER_FORMAL_CONFIG_FIELDS = {
    'rental_order_document_date_display': ('单据日期', ('rental_date',)),
    'rental_order_document_amount_display': ('单据金额', ('amount_total',)),
    'rental_order_contract_no_display': ('合同编号', ('contract_id',)),
    'rental_order_total_amount_display': ('总金额', ('amount_total',)),
    'rental_order_material_name_display': ('材料名称', ('rental_material_name',)),
    'rental_order_rental_content_display': ('租赁内容', ('note',)),
    'rental_order_rental_deposit_display': ('租赁押金', ('rental_deposit_amount_text',)),
    'rental_order_specification_display': ('规格型号', ('rental_material_spec',)),
}

class RentalOrderFormalConfigContractFields(models.Model):
    _inherit = 'sc.material.rental.order'

    for _field_name, (_field_label, _field_sources) in _RENTALORDER_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _RENTALORDER_FORMAL_CONFIG_FIELDS.items()},
        )

_RENTALSETTLEMENT_FORMAL_CONFIG_FIELDS = {
    'rental_settlement_source_created_by_display': ('录入人', ('source_created_by',)),
}

class RentalSettlementFormalConfigContractFields(models.Model):
    _inherit = 'sc.material.rental.settlement'

    for _field_name, (_field_label, _field_sources) in _RENTALSETTLEMENT_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _RENTALSETTLEMENT_FORMAL_CONFIG_FIELDS.items()},
        )

_MATERIALSETTLEMENT_FORMAL_CONFIG_FIELDS = {
    'material_settlement_payment_status_display': ('付款状态', ('state',)),
    'material_settlement_document_status_display': ('单据状态', ('state',)),
    'material_settlement_document_no_display': ('单据编号', ('name',)),
    'material_settlement_source_created_by_display': ('录入人', ('source_created_by',)),
    'material_settlement_payment_request_status_display': ('支付申请状态', ('state',)),
    'material_settlement_unpaid_amount_display': ('未付款金额', ('payment_remaining_amount',)),
    'material_settlement_unrequested_amount_display': ('未申请金额', ('payment_remaining_amount',)),
    'material_settlement_title_display': ('标题', ('name',)),
    'material_settlement_attachment_text_display': ('附件', ('attachment_ids',)),
}

class MaterialSettlementFormalConfigContractFields(models.Model):
    _inherit = 'sc.material.settlement'

    for _field_name, (_field_label, _field_sources) in _MATERIALSETTLEMENT_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _MATERIALSETTLEMENT_FORMAL_CONFIG_FIELDS.items()},
        )

_PAYMENTEXECUTION_FORMAL_CONFIG_FIELDS = {
    'payment_execution_payment_account_name_display': ('付款账户名称', ('partner_payment_account_name_display',)),
    'payment_execution_payment_amount_display': ('付款金额', ('paid_amount',)),
    'payment_execution_supplier_name_display': ('供应商名称', ('partner_payment_payee_unit',)),
    'payment_execution_document_status_display': ('单据状态', ('partner_payment_status_display',)),
    'payment_execution_document_no_display': ('单据编号', ('partner_payment_document_no',)),
    'payment_execution_bank_name_display': ('开户行', ('receipt_bank_name',)),
    'payment_execution_source_created_by_display': ('录入人', ('partner_payment_source_created_by',)),
    'payment_execution_payment_request_no_display': ('支付申请单号', ('payment_request_id',)),
    'payment_execution_account_display': ('账户', ('receipt_account_no',)),
    'payment_execution_attachment_text_display': ('附件', ('partner_payment_attachment_text',)),
}

class PaymentExecutionFormalConfigContractFields(models.Model):
    _inherit = 'sc.payment.execution'

    for _field_name, (_field_label, _field_sources) in _PAYMENTEXECUTION_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _PAYMENTEXECUTION_FORMAL_CONFIG_FIELDS.items()},
        )

_RECEIPTINCOME_FORMAL_CONFIG_FIELDS = {
    'receipt_income_document_status_display': ('单据状态', ('legacy_document_state_label',)),
    'receipt_income_document_no_display': ('单据编号', ('document_no',)),
    'receipt_income_contract_amount_display': ('合同金额', ('amount',)),
    'receipt_income_partner_name_display': ('往来单位', ('legacy_partner_name',)),
    'receipt_income_contractor_company_display': ('承包单位', ('legacy_company_name',)),
    'receipt_income_construction_management_contract_display': ('施工管理合同', ('legacy_contract_no',)),
    'receipt_income_business_time_display': ('时间', ('date_receipt',)),
    'receipt_income_current_allocated_amount_display': ('本期拨付金额合计', ('amount',)),
    'receipt_income_current_receipt_amount_display': ('本期收款', ('amount',)),
    'receipt_income_project_name_display': ('项目名称', ('legacy_project_name',)),
}

class ReceiptIncomeFormalConfigContractFields(models.Model):
    _inherit = 'sc.receipt.income'

    receipt_income_attachment_text_display = fields.Char(
        string='附件',
        compute="_compute_formal_config_contract_fields",
        readonly=True,
    )

    for _field_name, (_field_label, _field_sources) in _RECEIPTINCOME_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    def _receipt_income_attachment_ref_value(self):
        return ""

    @api.depends("attachment_ids")
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _RECEIPTINCOME_FORMAL_CONFIG_FIELDS.items()},
        )
        for record in self:
            if record.attachment_ids:
                record.receipt_income_attachment_text_display = "附件(%s)" % len(record.attachment_ids)
                continue
            legacy_attachment = (record._receipt_income_attachment_ref_value() or "").strip()
            record.receipt_income_attachment_text_display = legacy_attachment

_SUBCONTRACTREGISTER_FORMAL_CONFIG_FIELDS = {
    'subcontract_register_subcontract_content_display': ('分包内容', ('subcontract_scope',)),
    'subcontract_register_document_no_display': ('单据编号', ('name',)),
    'subcontract_register_contract_no_display': ('合同编号', ('contract_id',)),
    'subcontract_register_title_display': ('标题', ('name',)),
    'subcontract_register_amount_display': ('金额', ('amount_total',)),
}

class SubcontractRegisterFormalConfigContractFields(models.Model):
    _inherit = 'sc.subcontract.register'

    for _field_name, (_field_label, _field_sources) in _SUBCONTRACTREGISTER_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _SUBCONTRACTREGISTER_FORMAL_CONFIG_FIELDS.items()},
        )

_SUBCONTRACTREQUEST_FORMAL_CONFIG_FIELDS = {
    'subcontract_request_subcontract_content_display': ('分包内容', ('subcontract_scope',)),
    'subcontract_request_subcontractor_display': ('分包商', ('suggested_subcontractor_id',)),
    'subcontract_request_subcontract_type_display': ('分包类型', ('subcontract_type_text',)),
    'subcontract_request_source_created_by_display': ('录入人', ('source_created_by',)),
    'subcontract_request_source_created_at_display': ('录入时间', ('source_created_at',)),
    'subcontract_request_title_display': ('标题', ('name',)),
}

class SubcontractRequestFormalConfigContractFields(models.Model):
    _inherit = 'sc.subcontract.request'

    for _field_name, (_field_label, _field_sources) in _SUBCONTRACTREQUEST_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _SUBCONTRACTREQUEST_FORMAL_CONFIG_FIELDS.items()},
        )

_SUBCONTRACTSETTLEMENT_FORMAL_CONFIG_FIELDS = {
    'subcontract_settlement_payment_status_display': ('付款状态', ('state',)),
    'subcontract_settlement_document_no_display': ('单据编号', ('name',)),
    'subcontract_settlement_contract_no_display': ('合同编号', ('contract_id',)),
    'subcontract_settlement_source_created_by_display': ('录入人', ('source_created_by',)),
    'subcontract_settlement_payment_request_status_display': ('支付申请状态', ('state',)),
    'subcontract_settlement_title_display': ('标题', ('name',)),
    'subcontract_settlement_settlement_end_date_display': ('终止结算日期', ('settlement_date',)),
    'subcontract_settlement_settlement_start_date_display': ('起始结算日期', ('settlement_date',)),
}

class SubcontractSettlementFormalConfigContractFields(models.Model):
    _inherit = 'sc.subcontract.settlement'

    for _field_name, (_field_label, _field_sources) in _SUBCONTRACTSETTLEMENT_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _SUBCONTRACTSETTLEMENT_FORMAL_CONFIG_FIELDS.items()},
        )

_TAXDEDUCTION_FORMAL_CONFIG_FIELDS = {
    'tax_deduction_is_transfer_out_display': ('是否转出', ('is_transfer_out',)),
}

class TaxDeductionFormalConfigContractFields(models.Model):
    _inherit = 'sc.tax.deduction.registration'

    for _field_name, (_field_label, _field_sources) in _TAXDEDUCTION_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _TAXDEDUCTION_FORMAL_CONFIG_FIELDS.items()},
        )

_TENDERBID_FORMAL_CONFIG_FIELDS = {
    'tender_bid_attachment_text_display': ('附件', ('biz_attachment_ids',)),
}

class TenderBidFormalConfigContractFields(models.Model):
    _inherit = 'tender.bid'

    for _field_name, (_field_label, _field_sources) in _TENDERBID_FORMAL_CONFIG_FIELDS.items():
        locals()[_field_name] = fields.Char(
            string=_field_label,
            compute="_compute_formal_config_contract_fields",
            readonly=True,
        )

    @api.depends()
    def _compute_formal_config_contract_fields(self):
        _compute_formal_config_contract_fields(
            self,
            {field_name: sources for field_name, (_label, sources) in _TENDERBID_FORMAL_CONFIG_FIELDS.items()},
        )
