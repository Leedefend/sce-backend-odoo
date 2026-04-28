# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyConstructionDiaryLine(models.Model):
    _name = "sc.legacy.construction.diary.line"
    _description = "Legacy Construction Diary Line Fact"
    _order = "diary_date desc, legacy_line_id"

    legacy_line_id = fields.Char(required=True, index=True)
    legacy_header_id = fields.Char(index=True)
    legacy_pid = fields.Char(index=True)
    legacy_header_pid = fields.Char(index=True)
    document_no = fields.Char(index=True)
    document_state = fields.Char(index=True)
    title = fields.Char(index=True)
    diary_type = fields.Char(index=True)
    category = fields.Char(index=True)
    project_legacy_id = fields.Char(index=True)
    project_name = fields.Char(index=True)
    project_id = fields.Many2one("project.project", index=True, ondelete="set null")
    construction_unit = fields.Char(index=True)
    project_manager = fields.Char(index=True)
    diary_date = fields.Datetime(index=True)
    header_description = fields.Text()
    header_note = fields.Text()
    line_quality_legacy_id = fields.Char(index=True)
    line_quality_name = fields.Char(index=True)
    line_description = fields.Text()
    business_legacy_id = fields.Char(index=True)
    related_business_legacy_id = fields.Char(index=True)
    related_quality_type = fields.Char(index=True)
    handler_name = fields.Char(index=True)
    creator_legacy_user_id = fields.Char(index=True)
    creator_name = fields.Char(index=True)
    created_time = fields.Datetime(index=True)
    modifier_legacy_user_id = fields.Char(index=True)
    modifier_name = fields.Char(index=True)
    modified_time = fields.Datetime(index=True)
    attachment_ref = fields.Char()
    line_attachment_ref = fields.Char()
    attachment_name = fields.Char()
    attachment_path = fields.Char()
    source_table = fields.Char(default="SGZL_RZRJ_CB", required=True, index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_construction_diary_line_unique", "unique(legacy_line_id)", "Legacy construction diary line id must be unique."),
    ]
