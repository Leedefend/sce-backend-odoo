# -*- coding: utf-8 -*-
from odoo import fields, models


class ScMaterialCatalog(models.Model):
    _name = "sc.material.catalog"
    _description = "材料档案"
    _order = "code, id"

    name = fields.Char(string="材料名称", required=True, index=True)
    code = fields.Char(string="材料编码", index=True)
    category_id = fields.Many2one("product.category", string="材料分类", index=True, ondelete="set null")
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    spec_model = fields.Char(string="规格型号", index=True)
    uom_text = fields.Char(string="单位", index=True)
    aux_uom_text = fields.Char(string="辅助单位")
    planned_price = fields.Float(string="计划价")
    internal_price = fields.Float(string="内部价")
    depth = fields.Char(string="层级", index=True)
    pinyin = fields.Char(string="拼音")
    short_pinyin = fields.Char(string="拼音简码")
    remark = fields.Text(string="备注")
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    legacy_material_detail_id = fields.Many2one(
        "sc.legacy.material.detail",
        string="历史物料来源",
        index=True,
        readonly=True,
        ondelete="set null",
    )
    legacy_material_id = fields.Char(string="历史物料ID", index=True, readonly=True)
    legacy_category_id = fields.Char(string="历史分类ID", index=True, readonly=True)
    promoted_product_tmpl_id = fields.Many2one(
        "product.template",
        string="已提升产品模板",
        index=True,
        readonly=True,
        ondelete="set null",
    )
    promoted_product_id = fields.Many2one(
        "product.product",
        string="已提升产品",
        index=True,
        readonly=True,
        ondelete="set null",
    )
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_material_detail_unique",
            "unique(legacy_material_detail_id)",
            "Legacy material detail must be unique.",
        ),
    ]
