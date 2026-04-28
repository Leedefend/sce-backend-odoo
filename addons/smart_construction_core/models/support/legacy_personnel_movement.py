# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyPersonnelMovement(models.Model):
    _name = "sc.legacy.personnel.movement"
    _description = "Legacy Personnel Movement Fact"
    _order = "entry_date desc, legacy_movement_id"

    legacy_movement_id = fields.Char(required=True, index=True)
    legacy_pid = fields.Char(index=True)
    document_no = fields.Char(index=True)
    person_legacy_id = fields.Char(index=True)
    person_name = fields.Char(index=True)
    movement_type = fields.Char(index=True)
    movement_code = fields.Char(index=True)
    department_legacy_id = fields.Char(index=True)
    department_name = fields.Char(index=True)
    position_legacy_id = fields.Char(index=True)
    entry_date = fields.Datetime(index=True)
    leave_date = fields.Datetime(index=True)
    leave_reason = fields.Char(index=True)
    salary_month = fields.Char(index=True)
    notify_user_legacy_ids = fields.Char(index=True)
    notify_user_names = fields.Char()
    creator_legacy_user_id = fields.Char(index=True)
    creator_user_id = fields.Many2one("res.users", index=True, ondelete="set null")
    creator_name = fields.Char(index=True)
    created_time = fields.Datetime(index=True)
    attachment_ref = fields.Char()
    attachment_name = fields.Char()
    attachment_path = fields.Char()
    note = fields.Text()
    source_table = fields.Char(default="PM_RYYDGL", required=True, index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_personnel_movement_unique", "unique(legacy_movement_id)", "Legacy personnel movement id must be unique."),
    ]
