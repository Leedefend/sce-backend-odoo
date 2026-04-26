# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyDeductionAdjustmentLine(models.Model):
    _name = "sc.legacy.deduction.adjustment.line"
    _description = "Legacy Deduction Settlement Adjustment Line Fact"
    _order = "document_date desc, legacy_line_id"

    legacy_line_id = fields.Char(required=True, index=True)
    legacy_header_id = fields.Char(index=True)
    legacy_pid = fields.Char(index=True)
    legacy_header_pid = fields.Char(index=True)
    project_legacy_id = fields.Char(index=True)
    project_name = fields.Char(index=True)
    project_id = fields.Many2one("project.project", index=True, ondelete="set null")
    document_no = fields.Char(index=True)
    document_date = fields.Datetime(index=True)
    document_state = fields.Char(index=True)
    title = fields.Char(index=True)
    fund_plan_legacy_id = fields.Char(index=True)
    fund_plan_name = fields.Char(index=True)
    fund_plan_no = fields.Char(index=True)
    fund_confirmation_legacy_id = fields.Char(index=True)
    deduction_account = fields.Char(index=True)
    deduction_account_legacy_id = fields.Char(index=True)
    adjustment_item_legacy_id = fields.Char(index=True)
    adjustment_item_name = fields.Char(index=True)
    accumulated_planned_amount = fields.Float()
    accumulated_actual_amount = fields.Float()
    current_planned_amount = fields.Float()
    current_actual_amount = fields.Float()
    returned_flag = fields.Char(index=True)
    registrant_name = fields.Char(index=True)
    creator_legacy_user_id = fields.Char(index=True)
    creator_name = fields.Char(index=True)
    created_time = fields.Datetime(index=True)
    modifier_legacy_user_id = fields.Char(index=True)
    modifier_name = fields.Char(index=True)
    modified_time = fields.Datetime(index=True)
    attachment_ref = fields.Char()
    note = fields.Text()
    source_table = fields.Char(default="T_KK_SJDJB_CB", required=True, index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_deduction_line_unique", "unique(legacy_line_id)", "Legacy deduction adjustment line id must be unique."),
    ]
