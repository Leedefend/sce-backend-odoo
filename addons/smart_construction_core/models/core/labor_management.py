# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScAttendanceCheckin(models.Model):
    _name = "sc.attendance.checkin"
    _description = "考勤记录"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "attendance_date desc, id desc"

    name = fields.Char(string="考勤单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    attendance_date = fields.Date(string="考勤日期", required=True, default=fields.Date.context_today, index=True, tracking=True)
    labor_team = fields.Char(string="班组", required=True, index=True)
    work_content = fields.Char(string="作业内容", required=True)
    attendance_qty = fields.Float(string="出勤人数", required=True, default=1)
    work_hours = fields.Float(string="工时")
    contractor_id = fields.Many2one("res.partner", string="劳务单位", index=True)
    recorder_id = fields.Many2one("res.users", string="记录人", default=lambda self: self.env.user, index=True)
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("confirmed", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    note = fields.Text(string="考勤说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_attendance_checkin_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用考勤记录已迁移为专业考勤记录。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.attendance.checkin") or _("考勤记录")
        return super().create(vals_list)

    def action_submit(self):
        self._check_values()
        self.write({"state": "submitted"})
        return True

    def action_confirm(self):
        self._check_values()
        self.write({"state": "confirmed"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True

    @api.constrains("attendance_qty", "work_hours")
    def _check_values(self):
        for record in self:
            if record.attendance_qty <= 0:
                raise ValidationError(_("出勤人数必须大于0。"))
            if record.work_hours < 0:
                raise ValidationError(_("工时不能为负数。"))


class ScLaborUsage(models.Model):
    _name = "sc.labor.usage"
    _description = "劳务用工"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "usage_date desc, id desc"

    name = fields.Char(string="用工单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    usage_date = fields.Date(string="用工日期", required=True, default=fields.Date.context_today, index=True, tracking=True)
    labor_team = fields.Char(string="班组", required=True, index=True)
    contractor_id = fields.Many2one("res.partner", string="劳务单位", index=True)
    work_content = fields.Char(string="作业内容", required=True)
    worker_qty = fields.Float(string="用工人数", required=True, default=1)
    work_hours = fields.Float(string="工时")
    foreman_name = fields.Char(string="带班人")
    recorder_id = fields.Many2one("res.users", string="记录人", default=lambda self: self.env.user, index=True)
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("confirmed", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    note = fields.Text(string="用工说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_labor_usage_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用劳务用工已迁移为专业劳务用工。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.labor.usage") or _("劳务用工")
        return super().create(vals_list)

    def action_submit(self):
        self._check_values()
        self.write({"state": "submitted"})
        return True

    def action_confirm(self):
        self._check_values()
        self.write({"state": "confirmed"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True

    @api.constrains("worker_qty", "work_hours")
    def _check_values(self):
        for record in self:
            if record.worker_qty <= 0:
                raise ValidationError(_("用工人数必须大于0。"))
            if record.work_hours < 0:
                raise ValidationError(_("工时不能为负数。"))
