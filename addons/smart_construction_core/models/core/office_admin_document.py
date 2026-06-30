# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ScOfficeAdminDocument(models.Model):
    _name = "sc.office.admin.document"
    _description = "人事行政审批单"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin", "sc.delete.guard.mixin"]
    _order = "business_date desc, id desc"

    def _selection_fact_type(self):
        return [
            ("leave_request", "请假/休假审批"),
            ("seal_use", "印章使用审批"),
        ]

    leave_type = fields.Selection(
        [
            ("annual", "年假"),
            ("personal", "事假"),
            ("sick", "病假"),
            ("marriage", "婚假"),
            ("maternity", "产假/陪产假"),
            ("bereavement", "丧假"),
            ("compensatory", "调休"),
            ("other", "其他"),
        ],
        string="请假类型",
        tracking=True,
    )
    start_datetime = fields.Datetime(string="开始时间", tracking=True)
    end_datetime = fields.Datetime(string="结束时间", tracking=True)
    duration_days = fields.Float(string="天数")
    seal_type = fields.Selection(
        [
            ("company", "公章"),
            ("contract", "合同章"),
            ("finance", "财务章"),
            ("legal_person", "法人章"),
            ("project", "项目章"),
            ("other", "其他"),
        ],
        string="印章类型",
        tracking=True,
    )
    use_purpose = fields.Char(string="使用事项", tracking=True)
    use_date = fields.Date(string="使用日期", tracking=True)
    return_date = fields.Date(string="归还日期")
    legacy_document_no = fields.Char(string="历史单号", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_source_id = fields.Char(string="历史来源ID", index=True, readonly=True)
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_office_admin_document_attachment_rel",
        "document_id",
        "attachment_id",
        string="附件",
    )
    office_admin_status_display = fields.Char(string="单据状态", compute="_compute_office_admin_formal_visible_fields", store=True, readonly=True)
    office_admin_document_no = fields.Char(string="单据编号", compute="_compute_office_admin_formal_visible_fields", store=True, readonly=True)
    office_admin_project_name = fields.Char(string="项目名称", compute="_compute_office_admin_formal_visible_fields", store=True, readonly=True)
    office_admin_applicant_name = fields.Char(string="申请人姓名", compute="_compute_office_admin_formal_visible_fields", store=True, readonly=True)
    office_admin_department_name = fields.Char(string="所在部门", compute="_compute_office_admin_formal_visible_fields", store=True, readonly=True)
    office_admin_leave_time = fields.Char(string="请假时间", compute="_compute_office_admin_formal_visible_fields", store=True, readonly=True)
    office_admin_cancel_time = fields.Char(string="销假时间", compute="_compute_office_admin_formal_visible_fields", store=True, readonly=True)
    office_admin_leave_duration = fields.Char(string="请假时长", compute="_compute_office_admin_formal_visible_fields", store=True, readonly=True)
    office_admin_leave_days = fields.Char(string="请假天数", compute="_compute_office_admin_formal_visible_fields", store=True, readonly=True)
    office_admin_note_display = fields.Char(string="备注", compute="_compute_office_admin_formal_visible_fields", store=True, readonly=True)
    office_admin_source_created_by = fields.Char(string="录入人", compute="_compute_office_admin_formal_visible_fields", store=True, readonly=True)
    office_admin_source_created_at = fields.Char(string="录入时间", compute="_compute_office_admin_formal_visible_fields", store=True, readonly=True)

    _sql_constraints = [
        (
            "office_admin_legacy_source_unique",
            "unique(legacy_source_table, legacy_source_id)",
            "同一历史人事行政审批单只能投影一次。",
        ),
    ]

    def _business_specific_fields(self):
        return [
            "leave_type",
            "start_datetime",
            "end_datetime",
            "duration_days",
            "seal_type",
            "use_purpose",
            "use_date",
            "return_date",
            "legacy_document_no",
            "legacy_document_state",
            "legacy_source_table",
            "legacy_source_id",
        ]

    @staticmethod
    def _office_admin_state_label(value):
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
    def _office_admin_visible_field(suffix):
        return "legacy_%s_%s" % ("visible", suffix)

    def _office_admin_visible_value(self, suffix):
        self.ensure_one()
        field_name = self._office_admin_visible_field(suffix)
        return self[field_name] if field_name in self._fields else False

    @staticmethod
    def _office_admin_datetime_text(value):
        return fields.Datetime.to_string(value) if value else ""

    @api.depends(
        "legacy_document_state",
        "state",
        "legacy_document_no",
        "document_no",
        "name",
        "project_id",
        "requester_id",
        "department_id",
        "start_datetime",
        "end_datetime",
        "duration_days",
        "description",
        "result_note",
        "source_created_by",
        "source_created_at",
        "create_uid",
        "create_date",
    )
    def _compute_office_admin_formal_visible_fields(self):
        for record in self:
            status_value = record.legacy_document_state or record.state
            duration_text = "" if record.duration_days in (False, None) else str(record.duration_days)
            record.office_admin_status_display = record._office_admin_state_label(status_value)
            record.office_admin_document_no = record.legacy_document_no or record.document_no or record.name or ""
            record.office_admin_project_name = (
                record._office_admin_visible_value("project_name") or record.project_id.display_name or ""
            )
            record.office_admin_applicant_name = (
                record._office_admin_visible_value("applicant") or record.requester_id.name or ""
            )
            record.office_admin_department_name = (
                record._office_admin_visible_value("department") or record.department_id.display_name or ""
            )
            record.office_admin_leave_time = (
                record._office_admin_visible_value("leave_time") or record._office_admin_datetime_text(record.start_datetime)
            )
            record.office_admin_cancel_time = (
                record._office_admin_visible_value("cancel_time") or record._office_admin_datetime_text(record.end_datetime)
            )
            record.office_admin_leave_duration = record._office_admin_visible_value("leave_duration") or duration_text
            record.office_admin_leave_days = record._office_admin_visible_value("leave_days") or duration_text
            record.office_admin_note_display = (
                record._office_admin_visible_value("note") or record.result_note or record.description or ""
            )
            record.office_admin_source_created_by = (
                record._office_admin_visible_value("creator_name")
                or record.source_created_by
                or record.create_uid.name
                or ""
            )
            source_created_at = (
                record._office_admin_visible_value("created_time")
                or record.source_created_at
                or record.create_date
            )
            record.office_admin_source_created_at = (
                fields.Datetime.to_string(source_created_at) if source_created_at else ""
            )

    def _check_submit_requirements(self):
        super()._check_submit_requirements()
        for record in self:
            if record.fact_type == "leave_request":
                record._require_fields(["requester_id", "department_id", "leave_type", "start_datetime", "end_datetime"])
                if record.start_datetime and record.end_datetime and record.start_datetime > record.end_datetime:
                    raise ValidationError(_("请假开始时间不能晚于结束时间。"))
            elif record.fact_type == "seal_use":
                record._require_fields(["requester_id", "department_id", "seal_type", "use_purpose", "use_date"])

    def unlink(self):
        locked = self.filtered(lambda rec: rec.state not in ("draft", "cancel"))
        if locked:
            raise UserError("仅草稿或已取消的人事行政审批单允许删除。")
        self._sc_raise_delete_blockers(action_label="删除人事行政审批单")
        return super().unlink()
