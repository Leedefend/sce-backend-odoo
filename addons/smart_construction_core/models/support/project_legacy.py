# -*- coding: utf-8 -*-

from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    # Legacy project carriers used by migration replay scripts.
    short_name = fields.Char()
    project_environment = fields.Char()
    legacy_project_id = fields.Char(index=True)
    legacy_parent_id = fields.Char(index=True)
    legacy_company_id = fields.Char(index=True)
    legacy_company_name = fields.Char()
    legacy_specialty_type_id = fields.Char(index=True)
    specialty_type_name = fields.Char()
    legacy_price_method = fields.Char()
    business_nature = fields.Char()
    detail_address = fields.Text()
    project_profile = fields.Text()
    project_area = fields.Char()
    legacy_is_shared_base = fields.Char()
    legacy_sort = fields.Char()
    legacy_attachment_ref = fields.Char()
    project_overview = fields.Text()
    legacy_project_nature = fields.Char()
    legacy_is_material_library = fields.Char()
    other_system_id = fields.Char(index=True)
    other_system_code = fields.Char(index=True)
    legacy_stage_id = fields.Char(index=True)
    legacy_stage_name = fields.Char()
    legacy_region_id = fields.Char(index=True)
    legacy_region_name = fields.Char()
    legacy_state = fields.Char()
    legacy_project_manager_name = fields.Char()
    legacy_technical_responsibility_name = fields.Char()
