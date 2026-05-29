# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError


class ScDocumentAdminDocument(models.Model):
    _name = "sc.document.admin.document"
    _description = "资料证照办理单"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin", "sc.delete.guard.mixin"]
    _order = "business_date desc, id desc"

    def _selection_fact_type(self):
        return [
            ("company_document_archive", "公司资料存档"),
            ("certificate_registration", "证照登记"),
            ("document_borrow", "借阅申请"),
        ]

    certificate_name = fields.Char(string="证照名称", index=True, tracking=True)
    certificate_no = fields.Char(string="证照编号", index=True, tracking=True)
    holder_name = fields.Char(string="持有人/所属单位", index=True)
    issue_authority = fields.Char(string="发证机构")
    issue_date = fields.Date(string="发证日期")
    valid_until = fields.Date(string="有效期至", index=True)
    document_title = fields.Char(string="资料名称", index=True, tracking=True)
    borrow_user_id = fields.Many2one("res.users", string="借阅人", default=lambda self: self.env.user, index=True)
    borrow_date = fields.Date(string="借阅日期", default=fields.Date.context_today, index=True)
    expected_return_date = fields.Date(string="预计归还日期", index=True)
    actual_return_date = fields.Date(string="实际归还日期", index=True)
    legacy_document_no = fields.Char(string="历史单号", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_source_id = fields.Char(string="历史来源ID", index=True, readonly=True)
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
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_document_admin_document_attachment_rel",
        "document_id",
        "attachment_id",
        string="附件",
    )

    _sql_constraints = [
        (
            "document_admin_legacy_source_unique",
            "unique(legacy_source_table, legacy_source_id)",
            "同一历史资料证照单据只能投影一次。",
        ),
    ]

    def _business_specific_fields(self):
        return [
            "document_title",
            "certificate_name",
            "certificate_no",
            "holder_name",
            "issue_authority",
            "issue_date",
            "valid_until",
            "borrow_user_id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "legacy_document_no",
            "legacy_document_state",
            "legacy_source_table",
            "legacy_source_id",
        ]

    def _check_submit_requirements(self):
        super()._check_submit_requirements()
        for record in self:
            if record.fact_type == "company_document_archive":
                record._require_fields(["document_title", "requester_id", "business_date"])
            elif record.fact_type == "certificate_registration":
                record._require_fields(["certificate_name", "certificate_no", "holder_name"])
                if record.issue_date and record.valid_until and record.issue_date > record.valid_until:
                    raise ValidationError(_("发证日期不能晚于有效期。"))
            elif record.fact_type == "document_borrow":
                record._require_fields(["document_title", "borrow_user_id", "borrow_date", "expected_return_date"])
                if record.borrow_date and record.expected_return_date and record.borrow_date > record.expected_return_date:
                    raise ValidationError(_("借阅日期不能晚于预计归还日期。"))

    def unlink(self):
        locked = self.filtered(lambda rec: rec.state not in ("draft", "cancel"))
        if locked:
            raise UserError("仅草稿或已取消的资料证照办理单允许删除。")
        self._sc_raise_delete_blockers(action_label="删除资料证照办理单")
        return super().unlink()
