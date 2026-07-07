# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScMaterialCatalog(models.Model):
    _name = "sc.material.catalog"
    _description = "材料档案"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, id"

    name = fields.Char(string="材料名称", required=True, index=True, tracking=True)
    code = fields.Char(string="材料编码", index=True, tracking=True)
    category_id = fields.Many2one("product.category", string="材料分类", index=True, ondelete="set null")
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        ondelete="restrict",
    )
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
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_material_catalog_attachment_rel",
        "material_catalog_id",
        "attachment_id",
        string="附件",
    )
    promoted_product_tmpl_id = fields.Many2one(
        "product.template",
        string="历史技术产品模板",
        index=True,
        readonly=True,
        ondelete="set null",
    )
    promoted_product_id = fields.Many2one(
        "product.product",
        string="历史技术产品",
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

    @api.constrains("company_id", "project_id")
    def _check_project_company(self):
        for record in self:
            if record.project_id and record.project_id.company_id != record.company_id:
                raise ValidationError(_("材料档案所属项目必须属于同一公司。"))


class ScMaterialPrice(models.Model):
    _name = "sc.material.price"
    _description = "材料价格库"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "effective_date desc, id desc"

    name = fields.Char(string="价格名称", compute="_compute_name", store=True)
    material_catalog_id = fields.Many2one("sc.material.catalog", string="材料档案", required=True, index=True, tracking=True)
    company_id = fields.Many2one("res.company", string="公司", related="material_catalog_id.company_id", store=True, index=True)
    product_id = fields.Many2one("product.product", string="关联产品", index=True)
    supplier_id = fields.Many2one("res.partner", string="供应商", index=True, tracking=True)
    project_id = fields.Many2one("project.project", string="项目", index=True)
    price_type = fields.Selection(
        [
            ("planned", "计划价"),
            ("internal", "内部价"),
            ("quote", "报价"),
            ("contract", "合同价"),
            ("latest_purchase", "最近采购价"),
        ],
        string="价格类型",
        default="quote",
        required=True,
        index=True,
        tracking=True,
    )
    spec_model = fields.Char(string="规格型号", related="material_catalog_id.spec_model", store=True, index=True)
    uom_text = fields.Char(string="单位", related="material_catalog_id.uom_text", store=True, index=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    unit_price = fields.Monetary(string="单价", currency_field="currency_id", required=True, tracking=True)
    tax_rate = fields.Float(string="税率%")
    tax_included = fields.Boolean(string="含税", default=True)
    effective_date = fields.Date(string="生效日期", default=fields.Date.context_today, index=True)
    expiry_date = fields.Date(string="失效日期", index=True)
    source_model = fields.Char(string="来源模型", index=True)
    source_res_id = fields.Integer(string="来源记录ID", index=True)
    source_type = fields.Char(string="来源类型", index=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    @api.depends("material_catalog_id", "supplier_id", "price_type", "unit_price", "currency_id")
    def _compute_name(self):
        type_labels = dict(self._fields["price_type"].selection)
        for record in self:
            material = record.material_catalog_id.name or _("材料")
            supplier = record.supplier_id.name or _("通用")
            price_type = type_labels.get(record.price_type, record.price_type or "")
            record.name = "%s / %s / %s" % (material, supplier, price_type)

    @api.constrains("unit_price", "tax_rate", "effective_date", "expiry_date")
    def _check_price_values(self):
        for record in self:
            if record.unit_price < 0:
                raise ValidationError(_("材料价格不能为负数。"))
            if record.tax_rate < 0:
                raise ValidationError(_("税率不能为负数。"))
            if record.effective_date and record.expiry_date and record.effective_date > record.expiry_date:
                raise ValidationError(_("生效日期不能晚于失效日期。"))

    @api.constrains("material_catalog_id", "project_id")
    def _check_project_company(self):
        for record in self:
            if record.project_id and record.material_catalog_id.company_id != record.project_id.company_id:
                raise ValidationError(_("材料价格所属项目必须与材料档案属于同一公司。"))
