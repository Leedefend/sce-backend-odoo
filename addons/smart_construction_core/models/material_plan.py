# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError


class ProjectMaterialPlan(models.Model):
    _name = "project.material.plan"
    _description = "物资计划"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char("单号", default="新建", copy=False, readonly=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="project_id.company_id",
        store=True,
        readonly=True,
    )
    date_plan = fields.Date("需用日期")
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submit", "已提交"),
            ("approved", "已批准"),
            ("done", "已完成"),
            ("cancel", "已取消"),
        ],
        default="draft",
        tracking=True,
        index=True,
    )

    line_ids = fields.One2many("project.material.plan.line", "plan_id", string="计划明细")

    submitted_by = fields.Many2one("res.users", string="提交人", readonly=True, tracking=True)
    submitted_at = fields.Datetime(string="提交时间", readonly=True, tracking=True)
    approved_by = fields.Many2one("res.users", string="批准人", readonly=True, tracking=True)
    approved_at = fields.Datetime(string="批准时间", readonly=True, tracking=True)
    reject_reason = fields.Char(string="驳回原因", readonly=True, tracking=True)

    purchase_order_count = fields.Integer(compute="_compute_po_counts")
    purchase_line_count = fields.Integer(compute="_compute_po_counts")

    def _get_material_approver(self):
        self.ensure_one()
        # 物资负责人（若项目上有定义）
        if hasattr(self.project_id, "material_manager_id") and self.project_id.material_manager_id:
            return self.project_id.material_manager_id
        # 退化为项目负责人
        if getattr(self.project_id, "user_id", False):
            return self.project_id.user_id
        # 最后退化为当前用户
        return self.env.user

    def _normalize_lines_uom(self):
        """确保明细的计量单位与产品采购单位同类别，不合法时自动纠正为采购单位。"""
        for line in self.line_ids:
            if not line.product_id:
                raise UserError(_("计划行缺少物料，请补全后再提交。"))
            base_uom = line.product_id.uom_po_id or line.product_id.uom_id
            if not base_uom:
                raise UserError(_("物料 %s 缺少默认计量单位，请先完善产品信息。") % line.product_id.display_name)
            if not line.uom_id or line.uom_id.category_id != base_uom.category_id:
                line.uom_id = base_uom

    def action_submit(self):
        seq = self.env["ir.sequence"]
        for rec in self:
            if rec.state != "draft":
                continue
            if not self.env.user.has_group("smart_construction_core.group_sc_cap_material_user"):
                raise UserError(_("你没有提交物资计划的权限。"))
            if not rec.line_ids:
                raise UserError(_("请先填写物资计划明细再提交。"))
            rec._normalize_lines_uom()
            if rec.name == "新建":
                rec.name = seq.next_by_code("project.material.plan") or rec.name
            approver = rec._get_material_approver()
            rec.write(
                {
                    "state": "submit",
                    "submitted_by": self.env.user.id,
                    "submitted_at": fields.Datetime.now(),
                    "reject_reason": False,
                }
            )
            rec.message_post(body=_("物资计划已提交，等待 %s 审核。") % approver.name)
            rec.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=approver.id,
                summary=_("请审核物资计划：%s") % rec.name,
            )

    def action_approve(self):
        for rec in self:
            if rec.state != "submit":
                continue
            if not self.env.user.has_group("smart_construction_core.group_sc_cap_material_manager"):
                raise UserError(_("你没有审批物资计划的权限。"))
            rec.write(
                {
                    "state": "approved",
                    "approved_by": self.env.user.id,
                    "approved_at": fields.Datetime.now(),
                }
            )
            rec.activity_unlink(["mail.mail_activity_data_todo"])
            rec.message_post(body=_("物资计划已批准。"))

    def action_reject(self, reason=None):
        for rec in self:
            if rec.state != "submit":
                continue
            if not self.env.user.has_group("smart_construction_core.group_sc_cap_material_manager"):
                raise UserError(_("你没有驳回物资计划的权限。"))
            rec.activity_unlink(["mail.mail_activity_data_todo"])
            rec.write(
                {
                    "state": "draft",
                    "reject_reason": reason or _("未填写原因"),
                }
            )
            rec.message_post(body=_("物资计划被驳回：%s") % rec.reject_reason)

    def action_done(self):
        for rec in self:
            if rec.state != "approved":
                continue
            if not self.env.user.has_group("smart_construction_core.group_sc_cap_material_manager"):
                raise UserError(_("你没有完成物资计划的权限。"))
            rec.state = "done"

    def action_cancel(self):
        for rec in self:
            if rec.state in ("done", "cancel"):
                continue
            if not self.env.user.has_group("smart_construction_core.group_sc_cap_material_manager"):
                raise UserError(_("你没有取消物资计划的权限。"))
            rec.state = "cancel"

    def _compute_po_counts(self):
        PurchaseLine = self.env["purchase.order.line"].sudo()
        for rec in self:
            if "plan_id" in PurchaseLine._fields:
                lines = PurchaseLine.search([("plan_id", "=", rec.id)])
                rec.purchase_line_count = len(lines)
                rec.purchase_order_count = len(lines.mapped("order_id"))
            else:
                rec.purchase_line_count = 0
                rec.purchase_order_count = 0

    def action_view_purchase_orders(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("purchase.purchase_rfq")
        action["domain"] = [("plan_id", "=", self.id)] if "plan_id" in self.env["purchase.order"]._fields else [("id", "=", 0)]
        ctx = action.get("context") or {}
        if isinstance(ctx, str):
            try:
                ctx = safe_eval(ctx)
            except Exception:
                ctx = {}
        ctx.update({"default_plan_id": self.id, "search_default_plan_id": self.id})
        action["context"] = ctx
        return action

    def action_view_purchase_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("purchase.purchase_line_form_action")
        action["domain"] = [("plan_id", "=", self.id)] if "plan_id" in self.env["purchase.order.line"]._fields else [("id", "=", 0)]
        ctx = action.get("context") or {}
        if isinstance(ctx, str):
            try:
                ctx = safe_eval(ctx)
            except Exception:
                ctx = {}
        ctx.update({"default_plan_id": self.id, "search_default_plan_id": self.id})
        action["context"] = ctx
        return action


class ProjectMaterialPlanLine(models.Model):
    _name = "project.material.plan.line"
    _description = "物资计划行"
    _order = "id"

    plan_id = fields.Many2one(
        "project.material.plan",
        string="计划单",
        required=True,
        ondelete="cascade",
        index=True,
    )
    product_id = fields.Many2one("product.product", string="物料", required=True)
    spec = fields.Char("规格")
    quantity = fields.Float("数量", default=1.0)
    uom_id = fields.Many2one("uom.uom", string="单位")
    vendor_id = fields.Many2one(
        "res.partner",
        string="建议供应商",
        domain="[('supplier_rank','>',0)]",
    )
    note = fields.Char("备注")

    @api.model_create_multi
    def create(self, vals_list):
        Product = self.env["product.product"]
        for vals in vals_list:
            if not vals.get("uom_id") and vals.get("product_id"):
                product = Product.browse(vals["product_id"])
                vals["uom_id"] = (product.uom_po_id or product.uom_id).id
        return super().create(vals_list)

    @api.onchange("product_id")
    def _onchange_product_id_set_uom(self):
        for line in self:
            if line.product_id:
                line.uom_id = line.product_id.uom_po_id or line.product_id.uom_id

    @api.constrains("product_id", "uom_id")
    def _check_uom_category(self):
        for line in self:
            if line.product_id and line.uom_id:
                base_uom = line.product_id.uom_po_id or line.product_id.uom_id
                if line.uom_id.category_id != base_uom.category_id:
                    raise ValidationError(_("计划行单位必须与产品采购单位同类别"))

    # 硬约束：非草稿状态禁止修改/删除明细
    def write(self, vals):
        lock_fields = {"product_id", "spec", "quantity", "uom_id", "vendor_id", "note"}
        for line in self:
            if line.plan_id and line.plan_id.state != "draft" and lock_fields.intersection(vals):
                raise UserError(_("已确认/完成的物资计划不允许修改明细。"))
        return super().write(vals)

    def unlink(self):
        for line in self:
            if line.plan_id and line.plan_id.state != "draft":
                raise UserError(_("已确认/完成的物资计划不允许删除明细。"))
        return super().unlink()
