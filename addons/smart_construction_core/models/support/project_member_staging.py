# -*- coding: utf-8 -*-
from odoo import fields, models


class ScProjectMemberStaging(models.Model):
    _name = "sc.project.member.staging"
    _description = "Project Member Neutral Staging"
    _order = "id desc"

    legacy_member_id = fields.Char(required=True, index=True)
    legacy_project_id = fields.Char(index=True)
    legacy_user_ref = fields.Char(index=True)
    project_id = fields.Many2one("project.project", required=True, index=True, ondelete="cascade")
    user_id = fields.Many2one("res.users", required=True, index=True, ondelete="cascade")
    legacy_role_text = fields.Char()
    role_fact_status = fields.Selection(
        [("missing", "Missing"), ("resolved", "Resolved")],
        default="missing",
        required=True,
        index=True,
    )
    import_batch = fields.Char(required=True, index=True)
    evidence = fields.Char()
    notes = fields.Text()
    active = fields.Boolean(default=True, index=True)
