# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyWorkflowDetailFact(models.Model):
    _name = "sc.legacy.workflow.detail.fact"
    _description = "历史流程扩展事实"
    _order = "event_time desc, source_table, legacy_record_id"

    source_table = fields.Char(required=True, index=True)
    legacy_record_id = fields.Char(required=True, index=True)
    legacy_parent_id = fields.Char(index=True)
    legacy_pid = fields.Char(index=True)
    fact_type = fields.Char(index=True)
    source_dataset = fields.Char(index=True)
    document_no = fields.Char(index=True)
    document_title = fields.Char(index=True)
    business_table = fields.Char(index=True)
    business_id = fields.Char(index=True)
    project_legacy_id = fields.Char(index=True)
    project_name = fields.Char(index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    actor_legacy_user_id = fields.Char(index=True)
    actor_name = fields.Char(index=True)
    target_legacy_user_id = fields.Char(index=True)
    target_name = fields.Char(index=True)
    event_time = fields.Datetime(index=True)
    status_code = fields.Char(index=True)
    step_legacy_id = fields.Char(index=True)
    step_name = fields.Char(index=True)
    template_legacy_id = fields.Char(index=True)
    detail_status_legacy_id = fields.Char(index=True)
    detail_step_legacy_id = fields.Char(index=True)
    message = fields.Text()
    note = fields.Text()
    attachment_ref = fields.Char()
    pc_url = fields.Char()
    mobile_url = fields.Char()
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "legacy_workflow_detail_unique",
            "unique(source_table, legacy_record_id)",
            "同一历史流程扩展事实只能导入一次。",
        ),
    ]
