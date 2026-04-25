# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyMaterialCategory(models.Model):
    _name = "sc.legacy.material.category"
    _description = "Legacy Material Category Fact"
    _order = "legacy_category_id"

    legacy_category_id = fields.Char(required=True, index=True)
    legacy_guid = fields.Char(index=True)
    code = fields.Char(index=True)
    name = fields.Char(required=True, index=True)
    parent_legacy_category_id = fields.Char(index=True)
    parent_id = fields.Many2one("sc.legacy.material.category", index=True, ondelete="set null")
    legacy_project_id = fields.Char(index=True)
    project_id = fields.Many2one("project.project", index=True, ondelete="set null")
    depth = fields.Char(index=True)
    uom_text = fields.Char()
    source_table = fields.Char(default="C_Base_CBFL", required=True)
    note = fields.Text()
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_category_id_unique", "unique(legacy_category_id)", "Legacy material category id must be unique."),
    ]


class ScLegacyMaterialDetail(models.Model):
    _name = "sc.legacy.material.detail"
    _description = "Legacy Material Detail Fact"
    _order = "legacy_material_id"

    legacy_material_id = fields.Char(required=True, index=True)
    code = fields.Char(index=True)
    name = fields.Char(required=True, index=True)
    category_legacy_id = fields.Char(index=True)
    category_id = fields.Many2one("sc.legacy.material.category", index=True, ondelete="set null")
    parent_legacy_material_id = fields.Char(index=True)
    uom_text = fields.Char(index=True)
    aux_uom_text = fields.Char()
    planned_price = fields.Float()
    internal_price = fields.Float()
    legacy_project_id = fields.Char(index=True)
    project_id = fields.Many2one("project.project", index=True, ondelete="set null")
    depth = fields.Char(index=True)
    spec_model = fields.Char(index=True)
    pinyin = fields.Char(index=True)
    short_pinyin = fields.Char(index=True)
    import_time = fields.Datetime()
    remark = fields.Text()
    source_table = fields.Char(default="T_Base_MaterialDetail", required=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_material_id_unique", "unique(legacy_material_id)", "Legacy material id must be unique."),
    ]
