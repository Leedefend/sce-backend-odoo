# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class ScLegacyMaterialCategory(models.Model):
    _name = "sc.legacy.material.category"
    _description = "物料分类"
    _order = "legacy_category_id"

    legacy_category_id = fields.Char(string="分类编号", required=True, index=True)
    legacy_guid = fields.Char(string="分类标识", index=True)
    code = fields.Char(string="编码", index=True)
    name = fields.Char(string="名称", required=True, index=True)
    parent_legacy_category_id = fields.Char(string="上级分类编号", index=True)
    parent_id = fields.Many2one("sc.legacy.material.category", string="上级分类", index=True, ondelete="set null")
    legacy_project_id = fields.Char(string="项目原编号", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    depth = fields.Char(string="层级", index=True)
    uom_text = fields.Char(string="单位")
    source_table = fields.Char(string="来源表", default="C_Base_CBFL", required=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        ("legacy_category_id_unique", "unique(legacy_category_id)", "Legacy material category id must be unique."),
    ]


class ScLegacyMaterialDetail(models.Model):
    _name = "sc.legacy.material.detail"
    _description = "物料档案"
    _order = "legacy_material_id"

    legacy_material_id = fields.Char(string="物料编号", required=True, index=True)
    code = fields.Char(string="编码", index=True)
    name = fields.Char(string="名称", required=True, index=True)
    category_legacy_id = fields.Char(string="分类原编号", index=True)
    category_id = fields.Many2one("sc.legacy.material.category", string="分类", index=True, ondelete="set null")
    parent_legacy_material_id = fields.Char(string="上级物料编号", index=True)
    uom_text = fields.Char(string="单位", index=True)
    aux_uom_text = fields.Char(string="辅助单位")
    planned_price = fields.Float(string="计划价")
    internal_price = fields.Float(string="内部价")
    legacy_project_id = fields.Char(string="项目原编号", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    depth = fields.Char(string="层级", index=True)
    spec_model = fields.Char(string="规格型号", index=True)
    pinyin = fields.Char(string="拼音")
    short_pinyin = fields.Char(string="拼音简码")
    import_time = fields.Datetime(string="导入时间")
    remark = fields.Text(string="备注")
    source_table = fields.Char(string="来源表", default="T_Base_MaterialDetail", required=True)
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
    promotion_state = fields.Selection(
        [("archived", "档案"), ("promoted", "已生成产品")],
        string="提升状态",
        default="archived",
        index=True,
        readonly=True,
    )
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        ("legacy_material_id_unique", "unique(legacy_material_id)", "Legacy material id must be unique."),
    ]

    def action_promote_to_product(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_material_manager"):
            raise UserError(_("只有物资经理可以将历史物料提升为产品。"))
        unit_uom = self.env.ref("uom.product_uom_unit", raise_if_not_found=False)
        ProductTemplate = self.env["product.template"].sudo()
        for record in self:
            if record.promoted_product_tmpl_id:
                continue
            template = False
            if record.code:
                template = ProductTemplate.search([("default_code", "=", record.code)], limit=1)
            if not template:
                template = ProductTemplate.create(
                    {
                        "name": record.name,
                        "default_code": record.code or record.legacy_material_id,
                        "list_price": record.planned_price or 0.0,
                        "standard_price": record.internal_price or 0.0,
                        "type": "consu",
                        "uom_id": unit_uom.id if unit_uom else False,
                        "uom_po_id": unit_uom.id if unit_uom else False,
                        "legacy_material_detail_id": record.id,
                        "legacy_material_id": record.legacy_material_id,
                    }
                )
            else:
                template.write(
                    {
                        "legacy_material_detail_id": record.id,
                        "legacy_material_id": record.legacy_material_id,
                    }
                )
            record.sudo().write(
                {
                    "promoted_product_tmpl_id": template.id,
                    "promoted_product_id": template.product_variant_id.id,
                    "promotion_state": "promoted",
                }
            )
        action = self.env.ref("product.product_template_action", raise_if_not_found=False)
        if action and len(self) == 1 and self.promoted_product_tmpl_id:
            result = action.sudo().read()[0]
            result.update({"res_id": self.promoted_product_tmpl_id.id, "views": [(False, "form")]})
            return result
        return True
