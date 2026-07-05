# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models


class ProjectProjectUserHistoryFields(models.Model):
    _inherit = "project.project"

    legacy_attachment_ref = fields.Char(string="历史附件引用")


class OfficeAdminDocumentUserHistoryFields(models.Model):
    _inherit = "sc.office.admin.document"

    legacy_visible_project_name = fields.Char(string="历史可见项目名称", readonly=True)
    legacy_visible_applicant = fields.Char(string="历史可见申请人", readonly=True)
    legacy_visible_department = fields.Char(string="历史可见部门", readonly=True)
    legacy_visible_leave_days = fields.Char(string="历史可见请假天数", readonly=True)
    legacy_visible_leave_type = fields.Char(string="历史可见请假类型", readonly=True)
    legacy_visible_leave_time = fields.Char(string="历史可见请假时间", readonly=True)
    legacy_visible_cancel_time = fields.Char(string="历史可见销假时间", readonly=True)
    legacy_visible_note = fields.Text(string="历史可见备注", readonly=True)
    legacy_visible_leave_duration = fields.Char(string="历史可见请假时长", readonly=True)
    legacy_visible_creator_name = fields.Char(string="历史可见录入人", readonly=True)
    legacy_visible_created_time = fields.Datetime(string="历史可见录入时间", readonly=True)
    legacy_visible_seal_use_time = fields.Date(string="历史可见用印时间", readonly=True)
    legacy_visible_department_manager_sign = fields.Char(string="历史可见部门负责人签字", readonly=True)
    legacy_visible_seal_type = fields.Char(string="历史可见用印种类", readonly=True)
    legacy_visible_seal_text = fields.Char(string="历史可见用印文本名称及文号", readonly=True)
    legacy_visible_handler_sign = fields.Char(string="历史可见经办人签字", readonly=True)
    legacy_visible_leader_sign = fields.Char(string="历史可见领导签字", readonly=True)
    legacy_visible_copy_count = fields.Char(string="历史可见份数", readonly=True)
    legacy_visible_return_time = fields.Date(string="历史可见归还时间", readonly=True)
    legacy_visible_contract_amount = fields.Char(string="历史可见合同金额", readonly=True)
    legacy_visible_contract_no = fields.Char(string="历史可见合同编号", readonly=True)
    legacy_visible_company = fields.Char(string="历史可见所属公司", readonly=True)
    legacy_visible_seal_company = fields.Char(string="历史可见使用印章公司", readonly=True)
    legacy_visible_take_out = fields.Char(string="历史可见是否外带", readonly=True)
    legacy_visible_attachment = fields.Char(string="历史可见附件", readonly=True)

    def _office_admin_visible_value(self, suffix):
        self.ensure_one()
        field_name = "legacy_visible_%s" % suffix
        return self[field_name] if field_name in self._fields else False


class DocumentAdminDocumentUserHistoryFields(models.Model):
    _inherit = "sc.document.admin.document"

    legacy_visible_project_name = fields.Char(string="历史可见项目名称", readonly=True)
    legacy_visible_document_type = fields.Char(string="历史可见资料类型", readonly=True)
    legacy_visible_description = fields.Text(string="历史可见资料说明", readonly=True)
    legacy_visible_creator_name = fields.Char(string="历史可见录入人", readonly=True)
    legacy_visible_note = fields.Text(string="历史可见备注", readonly=True)
    legacy_visible_created_time = fields.Datetime(string="历史可见录入时间", readonly=True)
    legacy_visible_application_date = fields.Date(string="历史可见申请日期", readonly=True)
    legacy_visible_department = fields.Char(string="历史可见借阅部门或项目部名称", readonly=True)
    legacy_visible_borrower = fields.Char(string="历史可见借阅人", readonly=True)
    legacy_visible_contact = fields.Char(string="历史可见联系方式", readonly=True)
    legacy_visible_borrow_form = fields.Char(string="历史可见借阅形式", readonly=True)
    legacy_visible_borrow_date = fields.Date(string="历史可见借阅日期", readonly=True)
    legacy_visible_responsible_person = fields.Char(string="历史可见负责人", readonly=True)
    legacy_visible_return_request_date = fields.Date(string="历史可见归还申请日期", readonly=True)
    legacy_visible_return_apply_time = fields.Datetime(string="历史可见申请归还时间", readonly=True)
    legacy_visible_returned = fields.Char(string="历史可见是否归还", readonly=True)
    legacy_visible_return_confirm_time = fields.Datetime(string="历史可见确认归还时间", readonly=True)
    legacy_visible_return_date = fields.Date(string="历史可见归还日期", readonly=True)
    legacy_visible_modifier = fields.Char(string="历史可见修改人", readonly=True)
    legacy_visible_modified_date = fields.Datetime(string="历史可见修改日期", readonly=True)
    legacy_visible_modify_note = fields.Text(string="历史可见修改备注", readonly=True)
    legacy_visible_reviewer = fields.Char(string="历史可见审定人", readonly=True)
    legacy_visible_review_time = fields.Datetime(string="历史可见审定时间", readonly=True)
    legacy_visible_review_opinion = fields.Text(string="历史可见审定意见", readonly=True)

    def _document_admin_visible_value(self, suffix):
        self.ensure_one()
        field_name = "legacy_visible_%s" % suffix
        return self[field_name] if field_name in self._fields else False


class TaxDeductionRegistrationUserHistoryFields(models.Model):
    _inherit = "sc.tax.deduction.registration"

    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True, readonly=True)
    legacy_visible_project_name = fields.Char(string="历史可见项目名称", readonly=True, index=True)

    def _history_surface_allowed_write_fields(self):
        return super()._history_surface_allowed_write_fields() | {"creator_legacy_user_id"}


class SettlementOrderUserHistoryFields(models.Model):
    _inherit = "sc.settlement.order"

    legacy_visible_attachment = fields.Char(string="历史可见附件", readonly=True)
    legacy_attachment_ref = fields.Char(string="历史附件引用", readonly=True)

    def _settlement_attachment_ref_value(self):
        self.ensure_one()
        return self.legacy_attachment_ref or ""

    def _backfill_history_surface_fields(self):
        super()._backfill_history_surface_fields()
        old_column = "legacy_visible_attachment"
        self.env.cr.execute(
            """
            SELECT 1
              FROM information_schema.columns
             WHERE table_name = 'sc_settlement_order'
               AND column_name = %s
             LIMIT 1
            """,
            [old_column],
        )
        if not self.env.cr.fetchone():
            return
        self.env.cr.execute(
            f"""
            UPDATE sc_settlement_order
               SET legacy_attachment_ref = {old_column}
             WHERE COALESCE(legacy_attachment_ref, '') = ''
               AND COALESCE({old_column}, '') <> ''
            """
        )


class InvoiceRegistrationUserHistoryFields(models.Model):
    _inherit = "sc.invoice.registration"

    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True, readonly=True)
    legacy_attachment_ref = fields.Char(string="历史附件引用", readonly=True)
    legacy_visible_project_name = fields.Char(string="历史可见项目名称", readonly=True, index=True)
    legacy_visible_data_type = fields.Char(string="历史可见数据类型", readonly=True, index=True)
    legacy_visible_contract_no = fields.Char(string="历史可见合同编号", readonly=True)
    legacy_visible_application_date = fields.Datetime(string="历史可见申请日期", readonly=True)
    legacy_visible_invoice_state = fields.Char(string="历史可见开票状态", readonly=True)
    legacy_visible_partner_name = fields.Char(string="历史可见受票方名称", readonly=True)
    legacy_visible_cumulative_invoice_amount = fields.Char(string="历史可见累计开票金额", readonly=True)
    legacy_visible_invoice_count = fields.Char(string="历史可见开票张数", readonly=True)
    legacy_visible_current_invoice_amount = fields.Char(string="历史可见本次开票金额", readonly=True)
    legacy_visible_note = fields.Text(string="历史可见备注", readonly=True)
    legacy_visible_kingdee_no = fields.Char(string="历史可见金蝶单据编号", readonly=True)
    legacy_visible_surcharge_amount = fields.Char(string="历史可见附加税", readonly=True)
    legacy_visible_tax_rate = fields.Char(string="历史可见税率", readonly=True)
    legacy_visible_related_receipt_amount = fields.Char(string="历史可见关联回款金额", readonly=True)
    legacy_visible_invoice_no = fields.Char(string="历史可见发票号", readonly=True)
    legacy_visible_invoice_type = fields.Char(string="历史可见发票种类", readonly=True)
    legacy_visible_invoice_issue_company = fields.Char(string="历史可见开票单位", readonly=True)

    def _history_surface_allowed_write_fields(self):
        return super()._history_surface_allowed_write_fields() | {"creator_legacy_user_id", "legacy_attachment_ref"}

    def _invoice_attachment_ref_value(self):
        self.ensure_one()
        return self.legacy_attachment_ref or ""


class HrPayrollDocumentUserHistoryFields(models.Model):
    _inherit = "sc.hr.payroll.document"

    legacy_visible_creator_name = fields.Char(string="历史录入人", readonly=True)
    legacy_visible_created_time = fields.Datetime(string="历史录入时间", readonly=True)
    legacy_visible_people_count = fields.Char(string="历史人数", readonly=True)
    legacy_visible_type = fields.Char(string="历史类型", readonly=True)
    legacy_visible_note = fields.Text(string="历史备注", readonly=True)
    legacy_visible_certificate_fee = fields.Char(string="历史证书费用", readonly=True)
    legacy_visible_item_type = fields.Char(string="历史事项类型", readonly=True)

    def init(self):
        super().init()
        legacy_columns_by_key = {
            "creator_name": "legacy_visible_creator_name",
            "created_time": "legacy_visible_created_time",
            "people_count": "legacy_visible_people_count",
            "type": "legacy_visible_type",
            "note": "legacy_visible_note",
            "certificate_fee": "legacy_visible_certificate_fee",
        }
        self.env.cr.execute(
            """
            SELECT array_agg(attname)
              FROM pg_attribute
             WHERE attrelid = 'sc_hr_payroll_document'::regclass
               AND attname = ANY(%s)
               AND NOT attisdropped
            """,
            [list(legacy_columns_by_key.values())],
        )
        legacy_columns = set(self.env.cr.fetchone()[0] or [])
        required_columns = set(legacy_columns_by_key.values())
        if not required_columns.issubset(legacy_columns):
            return
        creator_name_col = legacy_columns_by_key["creator_name"]
        created_time_col = legacy_columns_by_key["created_time"]
        people_count_col = legacy_columns_by_key["people_count"]
        type_col = legacy_columns_by_key["type"]
        note_col = legacy_columns_by_key["note"]
        certificate_fee_col = legacy_columns_by_key["certificate_fee"]
        self.env.cr.execute(
            f"""
            UPDATE sc_hr_payroll_document
               SET employee_type = COALESCE(NULLIF(employee_type, ''), NULLIF({type_col}, ''), NULLIF(item_type, '')),
                   people_count = COALESCE(
                       people_count,
                       CASE
                           WHEN COALESCE({people_count_col}, '') ~ '^[0-9]+$'
                           THEN {people_count_col}::integer
                           ELSE NULL
                       END
                   ),
                   certificate_fee = COALESCE(
                       certificate_fee,
                       CASE
                           WHEN regexp_replace(COALESCE({certificate_fee_col}, ''), '[^0-9\\.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                           THEN regexp_replace({certificate_fee_col}, '[^0-9\\.-]', '', 'g')::numeric
                           ELSE NULL
                       END
                   ),
                   result_note = COALESCE(NULLIF(result_note, ''), NULLIF({note_col}, '')),
                   source_created_by = COALESCE(NULLIF(source_created_by, ''), NULLIF({creator_name_col}, '')),
                   source_created_at = COALESCE(source_created_at, {created_time_col})
             WHERE legacy_source_table IS NOT NULL
            """
        )


class ConstructionDiaryUserHistoryFields(models.Model):
    _inherit = "sc.construction.diary"

    legacy_attachment_ref = fields.Char(string="历史附件引用", readonly=True)
    legacy_line_attachment_ref = fields.Char(string="历史明细附件引用", readonly=True)
    legacy_attachment_name = fields.Char(string="历史附件名", readonly=True)
    legacy_attachment_path = fields.Char(string="历史附件路径", readonly=True)


class GeneralContractUserHistoryFields(models.Model):
    _inherit = "sc.general.contract"

    legacy_attachment_ref = fields.Char(string="历史附件引用", readonly=True)


class FundAccountOperationUserHistoryFields(models.Model):
    _inherit = "sc.fund.account.operation"

    creator_legacy_user_id = fields.Char(string="历史录入人ID", readonly=True, index=True)
    legacy_visible_document_no = fields.Char(string="历史可见单据编号", readonly=True)
    legacy_visible_project_name = fields.Char(string="历史可见项目名称", readonly=True)
    legacy_visible_account_name = fields.Char(string="历史可见账户号码", readonly=True)
    legacy_visible_counterparty_account_name = fields.Char(string="历史可见收款账户", readonly=True)
    legacy_visible_transfer_type = fields.Char(string="历史可见转账类别", readonly=True)
    legacy_visible_reason = fields.Char(string="历史可见事由", readonly=True)
    legacy_visible_note = fields.Text(string="历史可见备注", readonly=True)
    legacy_visible_attachment = fields.Char(string="历史可见附件", readonly=True)
    legacy_attachment_ref = fields.Char(string="历史附件引用", readonly=True)

    def _fund_operation_visible_value(self, suffix):
        self.ensure_one()
        field_name = "legacy_visible_%s" % suffix
        return self[field_name] if field_name in self._fields else ""

    def _fund_operation_attachment_ref_value(self):
        self.ensure_one()
        return self.legacy_attachment_ref or ""


class ExpenseClaimUserHistoryFields(models.Model):
    _inherit = "sc.expense.claim"

    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True, readonly=True)
    legacy_visible_document_state = fields.Char(string="历史可见单据状态", readonly=True)
    legacy_visible_document_no = fields.Char(string="历史可见单据编号", readonly=True)
    legacy_visible_attachment = fields.Char(string="历史可见附件", readonly=True)
    legacy_visible_amount = fields.Char(string="历史可见金额", readonly=True)
    legacy_visible_title = fields.Char(string="历史可见标题", readonly=True)
    legacy_visible_adjustment_item = fields.Char(string="历史可见上缴内容", readonly=True)
    legacy_visible_returned_flag = fields.Char(string="历史可见是否退回", readonly=True)
    legacy_visible_borrower = fields.Char(string="历史可见借款人", readonly=True)
    legacy_visible_loan_amount = fields.Char(string="历史可见借款金额", readonly=True)
    legacy_visible_repayment_amount = fields.Char(string="历史可见还款金额", readonly=True)
    legacy_visible_loan_rate = fields.Char(string="历史可见借款利率", readonly=True)
    legacy_visible_interest = fields.Char(string="历史可见利息", readonly=True)
    legacy_visible_repayment_time = fields.Datetime(string="历史可见还款时间", readonly=True)
    legacy_visible_date = fields.Datetime(string="历史可见日期", readonly=True)
    legacy_visible_push_result = fields.Char(string="历史可见推送结果", readonly=True)
    legacy_visible_payment_time = fields.Char(string="历史可见付款时间", readonly=True)
    legacy_visible_expense_type = fields.Char(string="历史可见成本类别", readonly=True)
    legacy_visible_note = fields.Text(string="历史可见备注", readonly=True)
    legacy_visible_project_name = fields.Char(string="历史可见项目名称", readonly=True)
    legacy_visible_department = fields.Char(string="历史可见部门", readonly=True)
    legacy_visible_summary = fields.Text(string="历史可见事项说明/用途", readonly=True)

    def init(self):
        super().init()
        legacy_department_col = "legacy_visible_department"
        legacy_document_state_col = "legacy_visible_document_state"
        self.env.cr.execute(
            """
            SELECT attname
              FROM pg_attribute
             WHERE attrelid = 'sc_expense_claim'::regclass
               AND NOT attisdropped
               AND attname = ANY(%s)
            """,
            [[legacy_department_col, legacy_document_state_col]],
        )
        legacy_columns = {row[0] for row in self.env.cr.fetchall()}
        department_expr = (
            f"COALESCE(NULLIF(department_name, ''), NULLIF({legacy_department_col}, ''))"
            if legacy_department_col in legacy_columns
            else "department_name"
        )
        state_expr = (
            f"COALESCE(NULLIF(payment_state, ''), NULLIF(legacy_document_state, ''), NULLIF({legacy_document_state_col}, ''), state)"
            if legacy_document_state_col in legacy_columns
            else "COALESCE(NULLIF(payment_state, ''), NULLIF(legacy_document_state, ''), state)"
        )
        self.env.cr.execute(
            f"""
            UPDATE sc_expense_claim
               SET department_name = {department_expr},
                   payment_state = {state_expr}
             WHERE source_origin = 'legacy'
            """
        )

    def _history_surface_allowed_write_fields(self):
        return super()._history_surface_allowed_write_fields() | {"creator_legacy_user_id"}


class FinancingLoanUserHistoryFields(models.Model):
    _inherit = "sc.financing.loan"

    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True, readonly=True)
    legacy_counterparty_id = fields.Char(string="历史往来方ID", index=True, readonly=True)
    legacy_amount_field = fields.Char(string="历史金额字段", index=True, readonly=True)
    legacy_attachment_ref = fields.Char(string="历史附件引用", index=True, readonly=True)
    legacy_visible_project_name = fields.Char(string="历史可见项目名称", readonly=True)
    legacy_visible_actual_loan_amount = fields.Char(string="历史可见实际借款金额", readonly=True)
    legacy_visible_receipt_account = fields.Char(string="历史可见收款账户", readonly=True)
    legacy_visible_company_name = fields.Char(string="历史可见公司名称", readonly=True)
    legacy_visible_payer_unit = fields.Char(string="历史可见付款单位", readonly=True)
    legacy_visible_receiver_unit = fields.Char(string="历史可见收款单位", readonly=True)
    legacy_visible_counterparty_name = fields.Char(string="历史可见往来单位名称", readonly=True)
    legacy_visible_counterparty_account = fields.Char(string="历史可见往来单位账户", readonly=True)
    legacy_visible_loan_account = fields.Char(string="历史可见借款账号/贷款账户", readonly=True)
    legacy_visible_request_department = fields.Char(string="历史可见申请部门", readonly=True)
    legacy_visible_request_time = fields.Datetime(string="历史可见申请时间", readonly=True)
    legacy_visible_applicant = fields.Char(string="历史可见申请人", readonly=True)
    legacy_visible_budget_included = fields.Char(string="历史可见是否预算内", readonly=True)
    legacy_visible_fund_usage_plan = fields.Text(string="历史可见主要资金使用安排", readonly=True)
    legacy_visible_payee = fields.Char(string="历史可见收款人", readonly=True)
    legacy_visible_bank_name = fields.Char(string="历史可见开户银行", readonly=True)
    legacy_visible_note = fields.Text(string="历史可见备注", readonly=True)
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

    @api.depends(
        "partner_id",
        "partner_id.display_name",
        "legacy_counterparty_name",
        "legacy_visible_counterparty_name",
        "legacy_visible_payer_unit",
        "legacy_visible_receiver_unit",
        "legacy_visible_company_name",
        "legacy_visible_receipt_account",
        "legacy_visible_counterparty_account",
        "legacy_visible_loan_account",
        "legacy_visible_loan_bank",
        "legacy_visible_repayment_account",
    )
    def _compute_formal_partner_account_fields(self):
        return super()._compute_formal_partner_account_fields()

    def _financing_loan_visible_value(self, suffix):
        self.ensure_one()
        field_name = "legacy_visible_%s" % suffix
        return self[field_name] if field_name in self._fields else False

    def _history_surface_allowed_write_fields(self):
        return super()._history_surface_allowed_write_fields() | {"creator_legacy_user_id"}


class ReceiptIncomeUserHistoryFields(models.Model):
    _inherit = "sc.receipt.income"

    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True, readonly=True)
    legacy_attachment_ref = fields.Char(string="历史附件引用", readonly=True)
    legacy_residual_reason = fields.Char(string="残余原因", index=True, readonly=True)

    def _history_surface_allowed_write_fields(self):
        return super()._history_surface_allowed_write_fields() | {"creator_legacy_user_id", "legacy_attachment_ref"}

    def _receipt_income_attachment_ref_value(self):
        self.ensure_one()
        return self.legacy_attachment_ref or ""


class PaymentExecutionUserHistoryFields(models.Model):
    _inherit = "sc.payment.execution"

    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True, readonly=True)
    legacy_attachment_ref = fields.Char(string="历史附件引用", readonly=True)
    legacy_residual_reason = fields.Char(string="残余原因", index=True, readonly=True)

    def _history_surface_allowed_write_fields(self):
        return super()._history_surface_allowed_write_fields() | {"creator_legacy_user_id", "legacy_attachment_ref"}


class MaterialInboundUserVisibleFields(models.Model):
    _inherit = "sc.material.inbound"

    @api.model
    def _user_visible_parse_legacy_amount(self, value):
        text = str(value or "").replace(",", "").replace("￥", "").replace("¥", "").strip()
        if not text:
            return False
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        if not match:
            return False
        try:
            return float(match.group(0))
        except ValueError:
            return False

    @api.model
    def _user_visible_parse_legacy_datetime(self, value):
        text = str(value or "").strip()
        if not text:
            return False
        return fields.Datetime.to_datetime(text)

    @staticmethod
    def _user_visible_business_creator(value):
        text = str(value or "").strip()
        if not text:
            return False
        if text.lower() in {"admin", "administrator", "system", "odoobot"} or text in {"系统", "系统导入"}:
            return "历史数据导入"
        return text

    @api.depends("amount_total", "legacy_visible_10")
    def _compute_tax_included_amount(self):
        for record in self:
            legacy_value = record._user_visible_parse_legacy_amount(getattr(record, "legacy_visible_10", False))
            record.tax_included_amount = legacy_value if legacy_value is not False else record.amount_total

    @api.depends("amount_total", "legacy_fact_type", "legacy_visible_09", "legacy_visible_13", "legacy_visible_14", "legacy_visible_16")
    def _compute_inbound_boundary_fields(self):
        for record in self:
            amount = record.amount_total or 0.0
            if record.legacy_fact_type == "direct_acceptance:入库":
                record.tax_rate_text = record.legacy_visible_09 or False
                record.payment_paid_amount = record._user_visible_parse_legacy_amount(record.legacy_visible_13) or 0.0
                record.payment_unpaid_amount = record._user_visible_parse_legacy_amount(record.legacy_visible_14) or 0.0
                record.settlement_settled_amount = record._user_visible_parse_legacy_amount(record.legacy_visible_16) or 0.0
                continue
            record.tax_rate_text = False
            record.payment_paid_amount = 0.0
            record.payment_unpaid_amount = amount
            record.settlement_settled_amount = 0.0

    @api.depends(
        "legacy_fact_type",
        "legacy_visible_01",
        "legacy_visible_12",
        "legacy_visible_15",
        "legacy_visible_17",
        "legacy_visible_20",
        "legacy_visible_21",
        "legacy_visible_22",
        "project_id",
        "create_uid",
        "create_date",
        "state",
    )
    def _compute_inbound_formal_visible_fields(self):
        state_labels = dict(self._fields["state"].selection)
        for record in self:
            if record.legacy_fact_type == "direct_acceptance:入库":
                record.document_status = record.legacy_visible_01 or False
                record.project_name_display = record.legacy_visible_17 or (record.project_id.display_name if record.project_id else False)
                record.payment_status_text = record.legacy_visible_12 or False
                record.settlement_status_text = record.legacy_visible_15 or False
                record.source_created_by = record._user_visible_business_creator(record.legacy_visible_20)
                record.source_created_at = record._user_visible_parse_legacy_datetime(record.legacy_visible_21)
                record.buyer_name = record.legacy_visible_22 or False
                continue
            record.document_status = state_labels.get(record.state) or False
            record.project_name_display = record.project_id.display_name if record.project_id else False
            record.payment_status_text = False
            record.settlement_status_text = False
            record.source_created_by = record._user_visible_business_creator(record.create_uid.name if record.create_uid else False)
            record.source_created_at = record.create_date or False
            record.buyer_name = False

    @api.depends(
        "line_ids.product_id",
        "line_ids.material_catalog_id",
        "line_ids.material_spec",
        "line_ids.product_uom_id",
        "line_ids.qty",
        "line_ids.unit_price",
        "line_ids.note",
        "legacy_fact_type",
        "legacy_visible_05",
        "legacy_visible_06",
        "legacy_visible_07",
        "legacy_visible_08",
        "legacy_visible_11",
        "legacy_visible_18",
    )
    def _compute_inbound_line_summaries(self):
        for record in self:
            if record.legacy_fact_type == "direct_acceptance:入库":
                record.material_name_summary = record.legacy_visible_05 or False
                record.material_spec_summary = record.legacy_visible_06 or False
                record.material_uom_summary = record._summarize_inbound_line_text(
                    record.line_ids.mapped("product_uom_id.name")
                )
                record.quantity_summary = record.legacy_visible_07 or False
                record.total_qty = record._user_visible_parse_legacy_amount(record.legacy_visible_11) or 0.0
                record.unit_price_summary = record.legacy_visible_08 or False
                record.line_note_summary = record.legacy_visible_18 or False
                continue
            record.material_name_summary = record._summarize_inbound_line_text(
                line.material_catalog_id.display_name or line.product_id.display_name
                for line in record.line_ids
            )
            record.material_spec_summary = record._summarize_inbound_line_text(
                record.line_ids.mapped("material_spec")
            )
            record.material_uom_summary = record._summarize_inbound_line_text(
                record.line_ids.mapped("product_uom_id.name")
            )
            record.quantity_summary = record._summarize_inbound_line_text(
                record._format_summary_number(line.qty) for line in record.line_ids
            )
            record.total_qty = sum(record.line_ids.mapped("qty"))
            record.unit_price_summary = record._summarize_inbound_line_text(
                record._format_summary_number(line.unit_price) for line in record.line_ids
            )
            record.line_note_summary = record._summarize_inbound_line_text(record.line_ids.mapped("note"))

    def init(self):
        super().init()
        self.env.cr.execute(
            """
            UPDATE sc_material_inbound inbound
               SET document_status = NULLIF(legacy_visible_01, ''),
                   project_name_display = COALESCE(NULLIF(legacy_visible_17, ''), project.name->>'zh_CN', project.name->>'en_US'),
                   tax_rate_text = NULLIF(legacy_visible_09, ''),
                   tax_included_amount = CASE
                       WHEN regexp_replace(COALESCE(legacy_visible_10, ''), '[^0-9.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace(legacy_visible_10, '[^0-9.-]', '', 'g')::numeric
                       ELSE tax_included_amount
                   END,
                   payment_status_text = NULLIF(legacy_visible_12, ''),
                   payment_paid_amount = CASE
                       WHEN regexp_replace(COALESCE(legacy_visible_13, ''), '[^0-9.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace(legacy_visible_13, '[^0-9.-]', '', 'g')::numeric
                       ELSE payment_paid_amount
                   END,
                   payment_unpaid_amount = CASE
                       WHEN regexp_replace(COALESCE(legacy_visible_14, ''), '[^0-9.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace(legacy_visible_14, '[^0-9.-]', '', 'g')::numeric
                       ELSE payment_unpaid_amount
                   END,
                   settlement_status_text = NULLIF(legacy_visible_15, ''),
                   settlement_settled_amount = CASE
                       WHEN regexp_replace(COALESCE(legacy_visible_16, ''), '[^0-9.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace(legacy_visible_16, '[^0-9.-]', '', 'g')::numeric
                       ELSE settlement_settled_amount
                   END,
                   source_created_by = CASE
                       WHEN LOWER(NULLIF(BTRIM(legacy_visible_20), '')) IN ('admin', 'administrator', 'system', 'odoobot')
                         OR NULLIF(BTRIM(legacy_visible_20), '') IN ('系统', '系统导入')
                       THEN '历史数据导入'
                       ELSE NULLIF(BTRIM(legacy_visible_20), '')
                   END,
                   source_created_at = CASE
                       WHEN COALESCE(legacy_visible_21, '') ~ '^\\d{4}-\\d{2}-\\d{2}'
                       THEN legacy_visible_21::timestamp
                       ELSE NULL
                   END,
                   buyer_name = NULLIF(legacy_visible_22, ''),
                   material_name_summary = NULLIF(legacy_visible_05, ''),
                   material_spec_summary = NULLIF(legacy_visible_06, ''),
                   quantity_summary = NULLIF(legacy_visible_07, ''),
                   total_qty = CASE
                       WHEN regexp_replace(COALESCE(legacy_visible_11, ''), '[^0-9.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace(legacy_visible_11, '[^0-9.-]', '', 'g')::numeric
                       ELSE total_qty
                   END,
                   unit_price_summary = NULLIF(legacy_visible_08, ''),
                   line_note_summary = NULLIF(legacy_visible_18, '')
              FROM project_project project
             WHERE inbound.project_id = project.id
               AND inbound.legacy_fact_type = 'direct_acceptance:入库'
            """
        )
        self.env.cr.execute(
            """
            UPDATE sc_equipment_usage
               SET source_created_by = '历史数据导入'
             WHERE LOWER(BTRIM(source_created_by)) IN ('admin', 'administrator', 'system', 'odoobot')
                OR BTRIM(source_created_by) IN ('系统', '系统导入')
            """
        )
        self.env.cr.execute(
            """
            UPDATE sc_material_inbound
               SET source_created_by = '历史数据导入'
             WHERE LOWER(BTRIM(source_created_by)) IN ('admin', 'administrator', 'system', 'odoobot')
                OR BTRIM(source_created_by) IN ('系统', '系统导入')
            """
        )
        self.env.cr.execute(
            """
            UPDATE sc_invoice_registration
               SET source_created_by = COALESCE(NULLIF(BTRIM(creator_name), ''), '历史数据导入'),
                   source_created_at = COALESCE(created_time, create_date)
             WHERE (source_created_by IS NULL OR BTRIM(source_created_by) = '')
                OR source_created_at IS NULL
            """
        )


INVOICE_DOCUMENT_STATE_LABELS = {
    "-1": "已作废",
    "0": "未审核",
    "1": "审核中",
    "2": "审核通过",
}


class InvoiceRegistrationUserVisibleFields(models.Model):
    _inherit = "sc.invoice.registration"

    @staticmethod
    def _invoice_user_visible_business_creator(value):
        text = str(value or "").strip()
        if not text:
            return ""
        if text.lower() in {"admin", "administrator", "system", "odoobot"} or text in {"系统", "系统导入"}:
            return "历史数据导入"
        return text

    @api.depends(
        "legacy_document_state",
        "state",
        "legacy_visible_01",
        "legacy_visible_03",
        "legacy_visible_04",
        "legacy_visible_05",
        "legacy_visible_06",
        "legacy_visible_07",
        "legacy_visible_12",
        "legacy_visible_15",
        "legacy_visible_16",
        "legacy_visible_17",
        "legacy_visible_project_name",
        "project_id",
        "recipient_unit_name",
        "legacy_partner_name",
        "partner_id",
        "invoice_issue_company",
        "legacy_visible_invoice_issue_company",
        "actual_invoice_issue_company",
        "invoice_count",
        "note",
        "legacy_visible_note",
        "legacy_attachment_ref",
        "attachment_ids",
        "creator_name",
        "created_time",
        "business_category_id",
    )
    def _compute_formal_list_visible_fields(self):
        state_labels = dict(self._fields["state"].selection)
        for record in self:
            is_output_registration = record.business_category_id.code == "invoice.output.registration"
            visible_project_index = "legacy_visible_05" if is_output_registration else "legacy_visible_03"
            visible_recipient_index = "legacy_visible_06" if is_output_registration else "legacy_visible_05"
            visible_issue_company_index = "legacy_visible_04" if is_output_registration else "legacy_visible_06"
            visible_attachment_index = "legacy_visible_16" if is_output_registration else "legacy_visible_17"
            visible_creator_index = "legacy_visible_17" if is_output_registration else "legacy_visible_16"

            legacy_state = record.legacy_visible_01 or record.legacy_document_state
            record.document_status_display = (
                INVOICE_DOCUMENT_STATE_LABELS.get(str(legacy_state), legacy_state)
                or state_labels.get(record.state)
                or ""
            )
            record.project_name_display = (
                getattr(record, visible_project_index)
                or record.legacy_visible_project_name
                or record.project_id.display_name
                or ""
            )
            record.recipient_unit_display = (
                getattr(record, visible_recipient_index)
                or record.recipient_unit_name
                or record.legacy_partner_name
                or record.partner_id.display_name
                or ""
            )
            record.invoice_issue_company_display = (
                getattr(record, visible_issue_company_index)
                or record.invoice_issue_company
                or record.legacy_visible_invoice_issue_company
                or ""
            )
            record.actual_invoice_issue_company_display = (
                record.legacy_visible_07
                or record.actual_invoice_issue_company
                or record.invoice_issue_company
                or record.legacy_visible_invoice_issue_company
                or ""
            )
            record.invoice_quantity_display = record.legacy_visible_12 or (
                str(record.invoice_count) if record.invoice_count else ""
            )
            record.note_display = record.legacy_visible_15 or record.legacy_visible_note or record.note or ""
            record.invoice_attachment_text = (
                getattr(record, visible_attachment_index)
                or record._invoice_attachment_ref_label()
                or ("附件(%s)" % len(record.attachment_ids) if record.attachment_ids else "")
            )
            creator = record._invoice_user_visible_business_creator(
                getattr(record, visible_creator_index) or record.creator_name or ""
            )
            if not creator and (record.source_origin == "legacy" or record.legacy_source_model or record.legacy_source_table):
                creator = "历史数据导入"
            record.source_created_by = creator
            record.source_created_at = record.created_time or False

    def init(self):
        super().init()
        self.env.cr.execute(
            """
            UPDATE sc_invoice_registration
               SET application_date = COALESCE(application_date, legacy_visible_application_date::date, document_date),
                   invoice_state = COALESCE(NULLIF(invoice_state, ''), NULLIF(legacy_visible_invoice_state, ''), NULLIF(legacy_document_state, ''), state),
                   recipient_unit_name = COALESCE(NULLIF(recipient_unit_name, ''), NULLIF(legacy_visible_partner_name, ''), NULLIF(legacy_partner_name, '')),
                   caliber = COALESCE(NULLIF(caliber, ''), NULLIF(legacy_visible_data_type, ''), source_kind),
                   actual_invoice_issue_company = COALESCE(
                       NULLIF(actual_invoice_issue_company, ''),
                       NULLIF(legacy_visible_invoice_issue_company, ''),
                       NULLIF(invoice_issue_company, '')
                   ),
                   actual_invoice_amount = COALESCE(
                       actual_invoice_amount,
                       CASE
                           WHEN regexp_replace(COALESCE(legacy_visible_current_invoice_amount, ''), '[^0-9\\.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                           THEN regexp_replace(legacy_visible_current_invoice_amount, '[^0-9\\.-]', '', 'g')::numeric
                           ELSE NULL
                       END,
                       amount_total
                   ),
                   invoice_count = COALESCE(
                       NULLIF(invoice_count, 0),
                       CASE
                           WHEN regexp_replace(COALESCE(legacy_visible_invoice_count, ''), '[^0-9-]', '', 'g') ~ '^-?[0-9]+$'
                           THEN regexp_replace(legacy_visible_invoice_count, '[^0-9-]', '', 'g')::integer
                           ELSE NULL
                       END,
                       0
                   ),
                   invoice_issue_company = COALESCE(NULLIF(invoice_issue_company, ''), NULLIF(legacy_visible_invoice_issue_company, '')),
                   invoice_no = COALESCE(NULLIF(invoice_no, ''), NULLIF(legacy_visible_invoice_no, '')),
                   invoice_type = COALESCE(NULLIF(invoice_type, ''), NULLIF(legacy_visible_invoice_type, '')),
                   tax_rate = COALESCE(NULLIF(tax_rate, ''), NULLIF(legacy_visible_tax_rate, '')),
                   surcharge_amount = COALESCE(
                       surcharge_amount,
                       CASE
                           WHEN regexp_replace(COALESCE(legacy_visible_surcharge_amount, ''), '[^0-9\\.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                           THEN regexp_replace(legacy_visible_surcharge_amount, '[^0-9\\.-]', '', 'g')::numeric
                           ELSE NULL
                       END
                   ),
                   related_receipt_amount = COALESCE(
                       related_receipt_amount,
                       CASE
                           WHEN regexp_replace(COALESCE(legacy_visible_related_receipt_amount, ''), '[^0-9\\.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                           THEN regexp_replace(legacy_visible_related_receipt_amount, '[^0-9\\.-]', '', 'g')::numeric
                           ELSE NULL
                       END
                   ),
                   kingdee_document_no = COALESCE(NULLIF(kingdee_document_no, ''), NULLIF(legacy_visible_kingdee_no, '')),
                   note = COALESCE(NULLIF(note, ''), NULLIF(legacy_visible_note, '')),
                   business_category_id = COALESCE(
                       business_category_id,
                       CASE
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
                   )
             WHERE legacy_source_model IS NOT NULL OR legacy_source_table IS NOT NULL
            """
        )


PAYMENT_REQUEST_DOCUMENT_STATE_LABELS = {
    "-1": "已作废",
    "0": "未审核",
    "1": "审批中",
    "2": "审核通过",
}

PAYMENT_APPLY_ACCEPTANCE_VISIBLE_INDEXES = {
    "单据状态": 1,
    "单据编号": 2,
    "申请日期": 3,
    "项目名称": 4,
    "收款单位": 5,
    "实际收款单位": 6,
    "付款单位": 7,
    "申请付款金额": 8,
    "实际付款金额": 9,
    "类型（成本）": 11,
    "备注": 12,
    "是否关联单据": 13,
    "付款账号": 14,
    "金额大写": 15,
    "户名": 16,
    "开户行": 17,
    "账号": 18,
    "录入人": 20,
    "录入时间": 21,
}


class PaymentRequestUserVisibleFields(models.Model):
    _inherit = "payment.request"

    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True, readonly=True)

    legacy_visible_document_no = fields.Char(
        string="历史可见单据编号",
        readonly=True,
        index=True,
    )
    legacy_visible_project_name = fields.Char(
        string="历史可见项目名称",
        readonly=True,
        index=True,
    )
    legacy_visible_request_date = fields.Char(
        string="历史可见申请日期",
        readonly=True,
    )
    legacy_visible_payee_unit = fields.Char(
        string="历史可见收款单位",
        readonly=True,
        index=True,
    )
    legacy_visible_actual_payee_unit = fields.Char(
        string="历史可见实际收款单位",
        readonly=True,
        index=True,
    )
    legacy_visible_payer_unit = fields.Char(
        string="历史可见付款单位",
        readonly=True,
        index=True,
    )
    legacy_visible_request_amount = fields.Char(
        string="历史申请付款金额",
        readonly=True,
    )
    legacy_visible_cost_category_name = fields.Char(
        string="历史成本分类名称",
        readonly=True,
        index=True,
    )
    legacy_visible_cost_type = fields.Char(
        string="历史类型（成本）",
        readonly=True,
        index=True,
    )
    legacy_visible_remark = fields.Text(
        string="历史备注",
        readonly=True,
    )
    legacy_visible_amount_uppercase = fields.Char(
        string="历史金额大写",
        readonly=True,
    )
    legacy_visible_actual_paid_amount = fields.Char(
        string="历史实际付款金额",
        readonly=True,
    )
    legacy_visible_available_balance = fields.Char(
        string="历史可用余额",
        readonly=True,
    )
    legacy_visible_writer = fields.Char(
        string="历史填写人",
        readonly=True,
        index=True,
    )
    legacy_visible_attachment = fields.Char(
        string="历史可见附件",
        readonly=True,
    )

    _rec_names_search = [
        "name",
        "legacy_visible_document_no",
        "project_id.name",
        "legacy_visible_project_name",
        "partner_id.name",
        "actual_payee_unit",
        "payer_unit",
        "payment_account_name",
        "legacy_visible_payee_unit",
        "legacy_visible_actual_payee_unit",
        "legacy_visible_payer_unit",
        "contract_id.subject",
        "contract_id.legacy_contract_no",
        "contract_id.legacy_document_no",
    ]

    @api.depends(
        "name",
        "type",
        "amount",
        "currency_id.symbol",
        "project_id.display_name",
        "legacy_visible_project_name",
        "partner_id.display_name",
        "actual_payee_unit",
        "payer_unit",
        "legacy_visible_payee_unit",
        "legacy_visible_actual_payee_unit",
        "legacy_visible_payer_unit",
        "legacy_visible_document_no",
        "legacy_visible_request_amount",
    )
    def _compute_display_name(self):
        for record in self:
            flow = "收款申请" if record.type == "receive" else "付款申请"
            project_name = (
                record.project_id.display_name
                or record.legacy_visible_project_name
                or ""
            ).strip()
            partner_name = (
                record.actual_payee_unit
                or record.payer_unit
                or record.partner_id.display_name
                or record.legacy_visible_actual_payee_unit
                or record.legacy_visible_payee_unit
                or record.legacy_visible_payer_unit
                or ""
            ).strip()
            amount_text = record._display_amount_label()
            document_no = (
                record.name
                or record.legacy_visible_document_no
                or ""
            ).strip()
            parts = [part for part in (flow, project_name, partner_name, amount_text, document_no) if part]
            record.display_name = " / ".join(parts) or flow

    def _display_amount_label(self):
        self.ensure_one()
        if self.amount:
            symbol = (self.currency_id.symbol or "").strip()
            return "%s%s" % (symbol, "{:,.2f}".format(self.amount))
        return (self.legacy_visible_request_amount or "").strip()

    @api.depends("outflow_line_ids.source_line_type", "legacy_visible_cost_category_name")
    def _compute_reconciliation_summary(self):
        for record in self:
            line_types = [
                line_type
                for line_type in record.outflow_line_ids.mapped("source_line_type")
                if line_type
            ]
            unique_types = sorted(set(line_types))
            record.cost_category_name = " / ".join(unique_types[:5]) or record.legacy_visible_cost_category_name

    @api.depends(
        "legacy_document_state",
        "state",
        "legacy_visible_project_name",
        "project_id",
        "legacy_visible_payee_unit",
        "partner_id",
        "actual_payee_unit",
        "legacy_visible_actual_payee_unit",
        "payer_unit",
        "legacy_visible_payer_unit",
        "legacy_visible_request_amount",
        "amount",
        "legacy_visible_actual_paid_amount",
        "legacy_visible_cost_type",
        "legacy_visible_cost_category_name",
        "cost_category_name",
        "legacy_visible_remark",
        "note",
        "settlement_id",
        "line_settlement_summary",
        "legacy_relation_summary",
        "material_settlement_id",
        "contract_id",
        "payment_account_no",
        "legacy_payment_account_no",
        "partner_bank_account",
        "accepted_amount_uppercase",
        "legacy_visible_amount_uppercase",
        "amount_uppercase",
        "payment_account_name",
        "legacy_payee_account_name",
        "partner_account_name",
        "payment_bank_name",
        "legacy_payee_bank_name",
        "partner_bank_name",
        "legacy_payee_account_no",
        "legacy_visible_writer",
        "creator_name",
        "created_time",
        "legacy_source_table",
        "legacy_visible_document_no",
        "name",
    )
    def _compute_payment_apply_formal_visible_fields(self):
        state_labels = dict(self._fields["state"].selection)
        for record in self:
            accepted_visible = record._payment_apply_acceptance_visible_payload()
            state_text = accepted_visible.get("单据状态")
            if not state_text and record.legacy_document_state:
                state_text = PAYMENT_REQUEST_DOCUMENT_STATE_LABELS.get(record.legacy_document_state, record.legacy_document_state)
            request_amount = record._parse_legacy_amount(
                accepted_visible.get("申请付款金额") if "申请付款金额" in accepted_visible else record.legacy_visible_request_amount
            )
            actual_paid = record._parse_legacy_amount(
                accepted_visible.get("实际付款金额") if "实际付款金额" in accepted_visible else record.legacy_visible_actual_paid_amount
            )
            has_related = any(
                (
                    record.settlement_id,
                    record.line_settlement_summary,
                    record.legacy_relation_summary,
                    record.material_settlement_id,
                    record.contract_id,
                )
            )
            record.document_status_display = state_text or state_labels.get(record.state) or ""
            record.project_name_display = accepted_visible.get("项目名称", record.legacy_visible_project_name or record.project_id.display_name or "")
            record.payee_unit_display = accepted_visible.get("收款单位", record.legacy_visible_payee_unit or record.partner_id.display_name or "")
            record.actual_payee_unit_display = accepted_visible.get(
                "实际收款单位",
                record.actual_payee_unit
                or record.legacy_visible_actual_payee_unit
                or record.legacy_visible_payee_unit
                or record.partner_id.display_name
                or "",
            )
            record.payer_unit_display = accepted_visible.get(
                "付款单位",
                record.payer_unit or record.legacy_visible_payer_unit or record.legacy_payment_account_name or "",
            )
            record.request_amount_display = request_amount if request_amount is not None else (record.amount or 0.0)
            record.actual_paid_amount_display = (
                actual_paid if actual_paid is not None else (record.paid_amount_total if not accepted_visible else 0.0)
            )
            record.cost_type_display = accepted_visible.get(
                "类型（成本）",
                record.legacy_visible_cost_type or record.legacy_visible_cost_category_name or record.cost_category_name or "",
            )
            record.note_display = accepted_visible.get("备注", record.legacy_visible_remark or record.note or "")
            record.related_document_text = accepted_visible.get("是否关联单据", "是" if has_related else "否")
            record.payment_account_no_display = accepted_visible.get(
                "付款账号",
                record.payment_account_no or record.legacy_payment_account_no or record.partner_bank_account or "",
            )
            record.amount_uppercase_display = accepted_visible.get(
                "金额大写",
                record.accepted_amount_uppercase or record.legacy_visible_amount_uppercase or record.amount_uppercase or "",
            )
            record.payee_account_name_display = accepted_visible.get(
                "户名",
                record.payment_account_name or record.legacy_payee_account_name or record.partner_account_name or "",
            )
            record.payee_bank_name_display = accepted_visible.get(
                "开户行",
                record.payment_bank_name or record.legacy_payee_bank_name or record.partner_bank_name or "",
            )
            record.payee_account_no_display = accepted_visible.get(
                "账号",
                record.payment_account_no or record.legacy_payee_account_no or record.partner_bank_account or "",
            )
            record.source_created_by = accepted_visible.get("录入人", record.legacy_visible_writer or record.creator_name or "")
            record.source_created_at = record.created_time or False

    def _payment_apply_acceptance_visible_payload(self):
        self.ensure_one()
        if self.legacy_source_table != "SCBSLY_DIRECT_PAYMENT_APPLY_ACCEPTED":
            return {}
        document_no = self.legacy_visible_document_no or self.name
        if not document_no or "sc.legacy.direct.acceptance.fact" not in self.env:
            return {}
        fact = self.env["sc.legacy.direct.acceptance.fact"].sudo().search(
            [
                ("active", "=", True),
                ("source_system", "=", "online_old_scbsly"),
                ("acceptance_label", "=", "支付申请"),
                "|",
                ("document_no", "=", document_no),
                ("legacy_record_id", "=", document_no),
            ],
            order="id desc",
            limit=1,
        )
        if not fact:
            return {}
        return {
            label: self._strip_legacy_file_suffix(getattr(fact, "legacy_visible_%02d" % index, ""))
            for label, index in PAYMENT_APPLY_ACCEPTANCE_VISIBLE_INDEXES.items()
        }

    def _prepare_execution_vals(self):
        vals = super()._prepare_execution_vals()
        vals["default_note"] = self.note or self.legacy_visible_remark
        return vals
