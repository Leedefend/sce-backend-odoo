# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyAttendanceCheckin(models.Model):
    _name = "sc.legacy.attendance.checkin"
    _description = "Legacy Attendance Check-in Fact"
    _order = "checkin_datetime desc, legacy_checkin_id"

    legacy_checkin_id = fields.Char(required=True, index=True)
    legacy_pid = fields.Char(index=True)
    legacy_user_id = fields.Char(index=True)
    user_id = fields.Many2one("res.users", index=True, ondelete="set null")
    group_name = fields.Char(index=True)
    checkin_type = fields.Char(index=True)
    exception_type = fields.Char(index=True)
    checkin_datetime = fields.Datetime(index=True)
    checkin_date_text = fields.Char(index=True)
    checkin_time_text = fields.Char(index=True)
    department_legacy_id = fields.Char(index=True)
    department_name = fields.Char(index=True)
    project_legacy_id = fields.Char(index=True)
    project_name = fields.Char(index=True)
    project_id = fields.Many2one("project.project", index=True, ondelete="set null")
    location_title = fields.Char(index=True)
    location_detail = fields.Char()
    wifi_name = fields.Char(index=True)
    wifi_mac = fields.Char(index=True)
    latitude = fields.Char()
    longitude = fields.Char()
    media_refs = fields.Char()
    notes = fields.Text()
    created_time = fields.Datetime(index=True)
    modified_time = fields.Datetime(index=True)
    source_table = fields.Char(default="CheckInData", required=True, index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_attendance_checkin_unique", "unique(legacy_checkin_id)", "Legacy attendance check-in id must be unique."),
    ]
