# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScMaterialAcceptance(models.Model):
    _name = "sc.material.acceptance"
    _description = "材料进场验收"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "acceptance_date desc, id desc"

    name = fields.Char(string="验收单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    acceptance_date = fields.Date(string="验收日期", default=fields.Date.context_today, index=True, tracking=True)
    supplier_id = fields.Many2one("res.partner", string="供应商", index=True)
    purchase_order_id = fields.Many2one("purchase.order", string="采购订单", index=True)
    warehouse_id = fields.Many2one("stock.warehouse", string="仓库", index=True)
    dest_location_id = fields.Many2one("stock.location", string="入库库位", index=True)
    inspector_id = fields.Many2one("res.users", string="验收人", default=lambda self: self.env.user, index=True)
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submitted", "已提交"),
            ("accepted", "验收通过"),
            ("rejected", "验收不通过"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.material.acceptance.line", "acceptance_id", string="验收明细")
    attachment_ids = fields.Many2many("ir.attachment", string="验收附件")
    note = fields.Text(string="验收说明")
    rejection_reason = fields.Text(string="不通过原因")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        (
            "legacy_material_acceptance_unique",
            "unique(legacy_fact_model, legacy_fact_id)",
            "来源通用材料记录已迁移为材料验收单。",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.material.acceptance") or _("材料进场验收")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if not record.line_ids:
                raise ValidationError(_("提交前必须维护验收明细。"))
        self.write({"state": "submitted"})
        return True

    def action_accept(self):
        for record in self:
            record.line_ids._check_quantities()
        self.write({"state": "accepted", "rejection_reason": False})
        return True

    def action_reject(self):
        for record in self:
            if not record.rejection_reason:
                raise ValidationError(_("验收不通过前必须填写不通过原因。"))
        self.write({"state": "rejected"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True


class ScMaterialAcceptanceLine(models.Model):
    _name = "sc.material.acceptance.line"
    _description = "材料进场验收明细"
    _order = "acceptance_id, sequence, id"

    acceptance_id = fields.Many2one("sc.material.acceptance", string="验收单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="acceptance_id.project_id", store=True, index=True)
    product_id = fields.Many2one("product.product", string="材料", required=True, index=True)
    material_catalog_id = fields.Many2one("sc.material.catalog", string="材料档案", index=True)
    material_spec = fields.Char(string="规格型号")
    product_uom_id = fields.Many2one("uom.uom", string="单位")
    planned_qty = fields.Float(string="计划数量")
    received_qty = fields.Float(string="到场数量", required=True)
    accepted_qty = fields.Float(string="合格数量")
    rejected_qty = fields.Float(string="不合格数量")
    result = fields.Selection([("accepted", "合格"), ("partial", "部分合格"), ("rejected", "不合格")], string="验收结果", default="accepted", index=True)
    issue_note = fields.Text(string="问题说明")

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for record in self:
            if record.product_id:
                record.product_uom_id = record.product_id.uom_id
                if not record.material_spec:
                    record.material_spec = record.product_id.default_code or ""

    @api.constrains("received_qty", "accepted_qty", "rejected_qty")
    def _check_quantities(self):
        for record in self:
            if record.received_qty < 0 or record.accepted_qty < 0 or record.rejected_qty < 0:
                raise ValidationError(_("材料验收数量不能为负数。"))
            if record.accepted_qty + record.rejected_qty > record.received_qty:
                raise ValidationError(_("合格数量与不合格数量之和不能大于到场数量。"))
