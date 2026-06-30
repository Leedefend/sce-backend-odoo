# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
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
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_document_admin_document_attachment_rel",
        "document_id",
        "attachment_id",
        string="附件",
    )
    document_admin_status_display = fields.Char(string="单据状态", compute="_compute_document_admin_formal_visible_fields", store=True, readonly=True)
    document_admin_project_name = fields.Char(string="项目名称", compute="_compute_document_admin_formal_visible_fields", store=True, readonly=True)
    document_admin_type_display = fields.Char(string="资料类型", compute="_compute_document_admin_formal_visible_fields", store=True, readonly=True)
    document_admin_description_display = fields.Char(string="资料说明", compute="_compute_document_admin_formal_visible_fields", store=True, readonly=True)
    document_admin_note_display = fields.Char(string="备注", compute="_compute_document_admin_formal_visible_fields", store=True, readonly=True)
    document_admin_source_created_by = fields.Char(string="录入人", compute="_compute_document_admin_formal_visible_fields", store=True, readonly=True)
    document_admin_source_created_at = fields.Char(string="录入时间", compute="_compute_document_admin_formal_visible_fields", store=True, readonly=True)

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

    @staticmethod
    def _document_admin_state_label(value):
        return {
            "-1": "已作废",
            "0": "未审核",
            "1": "审批中",
            "2": "审核通过",
            "draft": "草稿",
            "in_progress": "办理中",
            "done": "已完成",
            "cancel": "已取消",
        }.get(str(value or ""), str(value or ""))

    @staticmethod
    def _document_admin_visible_field(suffix):
        return "legacy_%s_%s" % ("visible", suffix)

    def _document_admin_visible_value(self, suffix):
        self.ensure_one()
        field_name = self._document_admin_visible_field(suffix)
        return self[field_name] if field_name in self._fields else False

    @api.depends(
        "legacy_document_state",
        "state",
        "project_id",
        "fact_type",
        "description",
        "result_note",
        "document_title",
        "certificate_name",
        "source_created_by",
        "source_created_at",
        "create_uid",
        "create_date",
    )
    def _compute_document_admin_formal_visible_fields(self):
        fact_type_labels = dict(self._selection_fact_type())
        for record in self:
            status_value = record.legacy_document_state or record.state
            record.document_admin_status_display = record._document_admin_state_label(status_value)
            record.document_admin_project_name = (
                record._document_admin_visible_value("project_name") or record.project_id.display_name or ""
            )
            record.document_admin_type_display = (
                record._document_admin_visible_value("document_type") or fact_type_labels.get(record.fact_type, "") or ""
            )
            record.document_admin_description_display = (
                record._document_admin_visible_value("description")
                or record.description
                or record.document_title
                or record.certificate_name
                or ""
            )
            record.document_admin_note_display = (
                record._document_admin_visible_value("note") or record.result_note or ""
            )
            record.document_admin_source_created_by = (
                record._document_admin_visible_value("creator_name")
                or record.source_created_by
                or record.create_uid.name
                or ""
            )
            source_created_at = (
                record._document_admin_visible_value("created_time")
                or record.source_created_at
                or record.create_date
            )
            record.document_admin_source_created_at = (
                fields.Datetime.to_string(source_created_at) if source_created_at else ""
            )

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
