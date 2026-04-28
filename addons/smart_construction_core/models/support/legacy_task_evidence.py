# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyTaskEvidence(models.Model):
    _name = "sc.legacy.task.evidence"
    _description = "Legacy Task Todo Evidence Fact"
    _order = "create_date desc, legacy_task_id"

    legacy_task_id = fields.Char(required=True, index=True)
    legacy_pid = fields.Char(index=True)
    project_legacy_id = fields.Char(index=True)
    project_name = fields.Char(index=True)
    project_id = fields.Many2one("project.project", index=True, ondelete="set null")
    bill_no = fields.Char(index=True)
    subject = fields.Char(required=True, index=True)
    description = fields.Text()
    start_time = fields.Datetime(index=True)
    due_time = fields.Datetime(index=True)
    finish_time = fields.Datetime(index=True)
    done_flag = fields.Char(index=True)
    read_state = fields.Char(index=True)
    read_time = fields.Datetime(index=True)
    executor_legacy_ids = fields.Char(index=True)
    primary_executor_legacy_id = fields.Char(index=True)
    primary_executor_user_id = fields.Many2one("res.users", index=True, ondelete="set null")
    participant_legacy_ids = fields.Char(index=True)
    creator_legacy_user_id = fields.Char(index=True)
    creator_user_id = fields.Many2one("res.users", index=True, ondelete="set null")
    creator_name = fields.Char(index=True)
    modifier_legacy_user_id = fields.Char(index=True)
    modifier_name = fields.Char(index=True)
    modified_time = fields.Datetime(index=True)
    finish_name = fields.Char(index=True)
    finish_remark = fields.Text()
    finish_attachment_ref = fields.Char()
    pc_url = fields.Char()
    app_url = fields.Char()
    source = fields.Char(string="Legacy Source", index=True)
    source_id = fields.Char(string="Legacy Source ID", index=True)
    source_icbd = fields.Char(string="Legacy Source ICBD", index=True)
    business_id = fields.Char(index=True)
    business_name = fields.Char(index=True)
    priority = fields.Char(index=True)
    task_type = fields.Char(index=True)
    param_text = fields.Text()
    source_table = fields.Char(default="T_BASE_TASKDONE", required=True, index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_task_id_unique", "unique(legacy_task_id)", "Legacy task id must be unique."),
    ]
