# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError


class ScHrPayrollDocument(models.Model):
    _name = "sc.hr.payroll.document"
    _description = "人事薪酬办理单"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin", "sc.delete.guard.mixin"]
    _order = "period_year desc, period_month desc, business_date desc, id desc"

    def _selection_fact_type(self):
        return [
            ("social_person_registration", "社保人员登记"),
            ("social_registration", "社保登记"),
            ("salary_registration", "工资登记"),
            ("subsidy", "补助"),
            ("bonus", "奖金"),
        ]

    employee_user_id = fields.Many2one("res.users", string="人员", index=True, tracking=True)
    employee_name = fields.Char(string="人员姓名", index=True, tracking=True)
    employee_status = fields.Char(string="人员状态", index=True)
    employee_type = fields.Char(string="人员类型", index=True)
    id_number = fields.Char(string="身份证号", index=True)
    contact_phone = fields.Char(string="联系方式", index=True)
    period_year = fields.Integer(string="年度", index=True)
    period_month = fields.Integer(string="月份", index=True)
    payer_unit = fields.Char(string="缴纳单位", index=True)
    payout_unit = fields.Char(string="发放单位", index=True)
    people_count = fields.Integer(string="人数")
    social_security_base = fields.Monetary(string="社保基数", currency_field="currency_id")
    company_amount = fields.Monetary(string="公司承担", currency_field="currency_id")
    individual_amount = fields.Monetary(string="个人承担", currency_field="currency_id")
    salary_base = fields.Monetary(string="薪资基数", currency_field="currency_id")
    gross_amount = fields.Monetary(string="应发工资", currency_field="currency_id")
    deduction_amount = fields.Monetary(string="扣款合计", currency_field="currency_id")
    net_salary = fields.Monetary(string="实发工资", currency_field="currency_id")
    item_type = fields.Char(string="事项类型", tracking=True)
    amount = fields.Monetary(string="金额", currency_field="currency_id", tracking=True)
    certificate_fee = fields.Monetary(string="证书费用", currency_field="currency_id")
    occurrence_date = fields.Date(string="发生日期", index=True)
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_hr_payroll_document_attachment_rel",
        "document_id",
        "attachment_id",
        string="附件",
    )
    legacy_document_no = fields.Char(string="历史单号", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_source_id = fields.Char(string="历史来源ID", index=True, readonly=True)

    _sql_constraints = [
        (
            "hr_payroll_legacy_source_unique",
            "unique(legacy_source_table, legacy_source_id)",
            "同一历史人事薪酬单据只能投影一次。",
        ),
    ]

    def _business_specific_fields(self):
        return [
            "employee_user_id",
            "employee_name",
            "employee_status",
            "employee_type",
            "id_number",
            "contact_phone",
            "period_year",
            "period_month",
            "payer_unit",
            "payout_unit",
            "people_count",
            "social_security_base",
            "company_amount",
            "individual_amount",
            "salary_base",
            "gross_amount",
            "deduction_amount",
            "net_salary",
            "item_type",
            "amount",
            "certificate_fee",
            "occurrence_date",
            "attachment_ids",
            "legacy_document_no",
            "legacy_document_state",
            "legacy_source_table",
            "legacy_source_id",
        ]

    def _check_submit_requirements(self):
        super()._check_submit_requirements()
        for record in self:
            if record.fact_type in ("social_person_registration", "social_registration"):
                record._require_fields(["department_id", "period_year", "period_month", "payer_unit"])
                if record.fact_type == "social_person_registration":
                    if not record.employee_user_id and not record.employee_name:
                        raise ValidationError(_("请补齐人员后再办理。"))
                    record._require_fields(["id_number", "social_security_base"])
                else:
                    record._require_fields(["company_amount", "individual_amount"])
            elif record.fact_type == "salary_registration":
                if not record.employee_user_id and not record.employee_name:
                    raise ValidationError(_("请补齐人员后再办理。"))
                record._require_fields(["department_id", "period_year", "period_month", "gross_amount", "net_salary"])
            elif record.fact_type in ("subsidy", "bonus"):
                if not record.employee_user_id and not record.employee_name:
                    raise ValidationError(_("请补齐人员后再办理。"))
                record._require_fields(["department_id", "item_type", "amount", "occurrence_date"])

            if record.period_month and (record.period_month < 1 or record.period_month > 12):
                raise ValidationError(_("月份必须在 1 到 12 之间。"))

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_hr_payroll_document
               SET employee_status = COALESCE(NULLIF(employee_status, ''), NULLIF(legacy_document_state, '')),
                   employee_type = COALESCE(NULLIF(employee_type, ''), NULLIF(item_type, '')),
                   contact_phone = COALESCE(
                       NULLIF(contact_phone, ''),
                       NULLIF(substring(COALESCE(description, '') from '联系方式[：:]\\s*([^\\n\\r]+)'), '')
                   ),
                   payout_unit = COALESCE(NULLIF(payout_unit, ''), NULLIF(payer_unit, ''))
             WHERE legacy_source_table IS NOT NULL
            """
        )

    def unlink(self):
        locked = self.filtered(lambda rec: rec.state not in ("draft", "cancel"))
        if locked:
            raise UserError("仅草稿或已取消的人事薪酬办理单允许删除。")
        self._sc_raise_delete_blockers(action_label="删除人事薪酬办理单")
        return super().unlink()
