# -*- coding: utf-8 -*-

from odoo import _, fields, models
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
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_office_admin_document_attachment_rel",
        "document_id",
        "attachment_id",
        string="附件",
    )

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
