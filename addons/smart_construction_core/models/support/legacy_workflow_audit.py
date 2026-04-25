# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyWorkflowAudit(models.Model):
    _name = "sc.legacy.workflow.audit"
    _description = "Legacy Workflow Audit"
    _order = "approved_at desc, received_at desc, id desc"

    legacy_workflow_id = fields.Char(required=True, index=True)
    legacy_pid = fields.Char(index=True)
    legacy_djid = fields.Char(index=True)
    legacy_business_id = fields.Char(index=True)
    legacy_source_table = fields.Char(index=True)
    legacy_detail_status_id = fields.Char(index=True)
    legacy_detail_step_id = fields.Char(index=True)
    legacy_setup_step_id = fields.Char(index=True)
    legacy_template_id = fields.Char(index=True)
    legacy_step_name = fields.Char()
    legacy_template_name = fields.Char()
    target_model = fields.Char(index=True)
    target_external_id = fields.Char(index=True)
    target_lane = fields.Char(index=True)
    actor_legacy_user_id = fields.Char(index=True)
    actor_name = fields.Char()
    approved_at = fields.Datetime(index=True)
    received_at = fields.Datetime(index=True)
    action_classification = fields.Char(index=True)
    legacy_status = fields.Char(index=True)
    legacy_back_type = fields.Char(index=True)
    legacy_approval_type = fields.Char(index=True)
    approval_note = fields.Text()
    import_batch = fields.Char(required=True, index=True)
