# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScMaterialRentalPlan(models.Model):
    _name = "sc.material.rental.plan"
    _description = "周转材料租赁计划"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "plan_date desc, id desc"

    name = fields.Char(string="计划单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    contract_id = fields.Many2one("construction.contract", string="关联合同", index=True)
    supplier_id = fields.Many2one("res.partner", string="建议供应商", index=True, tracking=True)
    plan_date = fields.Date(string="计划日期", required=True, default=fields.Date.context_today, index=True)
    planned_start = fields.Date(string="计划进场日期", index=True)
    planned_end = fields.Date(string="计划退场日期", index=True)
    rent_purpose = fields.Char(string="租赁用途", index=True)
    owner_id = fields.Many2one("res.users", string="负责人", default=lambda self: self.env.user, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    estimated_amount = fields.Monetary(string="预计租赁金额", currency_field="currency_id", compute="_compute_estimated_amount", store=True)
    line_ids = fields.One2many("sc.material.rental.plan.line", "plan_id", string="计划明细")
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("approved", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        required=True,
        index=True,
        tracking=True,
    )
    note = fields.Text(string="备注")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    @api.depends("line_ids.estimated_amount")
    def _compute_estimated_amount(self):
        for record in self:
            record.estimated_amount = sum(record.line_ids.mapped("estimated_amount"))

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.material.rental.plan") or _("周转材料租赁计划")
        return super().create(vals_list)

    @api.constrains("planned_start", "planned_end")
    def _check_date_order(self):
        for record in self:
            if record.planned_start and record.planned_end and record.planned_start > record.planned_end:
                raise ValidationError(_("计划进场日期不能晚于计划退场日期。"))

    def action_submit(self):
        self.write({"state": "submitted"})
        return True

    def action_approve(self):
        self.write({"state": "approved"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True


class ScMaterialRentalPlanLine(models.Model):
    _name = "sc.material.rental.plan.line"
    _description = "周转材料租赁计划明细"
    _order = "plan_id, sequence, id"

    plan_id = fields.Many2one("sc.material.rental.plan", string="租赁计划", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="plan_id.project_id", store=True, index=True)
    product_id = fields.Many2one("product.product", string="周转材料", index=True)
    material_name = fields.Char(string="材料名称", required=True)
    material_spec = fields.Char(string="规格型号")
    unit_name = fields.Char(string="单位")
    planned_qty = fields.Float(string="计划数量", default=1.0)
    planned_days = fields.Float(string="计划租赁天数", default=1.0)
    daily_price = fields.Monetary(string="日租单价", currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", string="币种", related="plan_id.currency_id", store=True)
    estimated_amount = fields.Monetary(string="预计金额", currency_field="currency_id", compute="_compute_amount", store=True)
    note = fields.Char(string="备注")

    @api.depends("planned_qty", "planned_days", "daily_price")
    def _compute_amount(self):
        for line in self:
            line.estimated_amount = (line.planned_qty or 0.0) * (line.planned_days or 0.0) * (line.daily_price or 0.0)


class ScMaterialRentalOrder(models.Model):
    _name = "sc.material.rental.order"
    _description = "周转材料租赁单"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "rental_date desc, id desc"

    name = fields.Char(string="租赁单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    plan_id = fields.Many2one("sc.material.rental.plan", string="来源租赁计划", index=True)
    contract_id = fields.Many2one("construction.contract", string="租赁合同", index=True)
    supplier_id = fields.Many2one("res.partner", string="供应商", required=True, index=True, tracking=True)
    rental_date = fields.Date(string="租赁日期", required=True, default=fields.Date.context_today, index=True)
    planned_return_date = fields.Date(string="计划退还日期", index=True)
    owner_id = fields.Many2one("res.users", string="经办人", default=lambda self: self.env.user, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    amount_total = fields.Monetary(string="租赁金额", currency_field="currency_id", compute="_compute_amount_total", store=True)
    line_ids = fields.One2many("sc.material.rental.order.line", "order_id", string="租赁明细")
    state = fields.Selection(
        [("draft", "草稿"), ("active", "租赁中"), ("returned", "已退还"), ("settled", "已结算"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        required=True,
        index=True,
        tracking=True,
    )
    note = fields.Text(string="备注")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    @api.depends("line_ids.amount_total")
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = sum(record.line_ids.mapped("amount_total"))

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.material.rental.order") or _("周转材料租赁单")
        return super().create(vals_list)

    def action_activate(self):
        self.write({"state": "active"})
        return True

    def action_return(self):
        self.write({"state": "returned"})
        return True

    def action_settle(self):
        self.write({"state": "settled"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True


class ScMaterialRentalOrderLine(models.Model):
    _name = "sc.material.rental.order.line"
    _description = "周转材料租赁明细"
    _order = "order_id, sequence, id"

    order_id = fields.Many2one("sc.material.rental.order", string="租赁单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one("product.product", string="周转材料", index=True)
    material_name = fields.Char(string="材料名称", required=True)
    material_spec = fields.Char(string="规格型号")
    unit_name = fields.Char(string="单位")
    qty = fields.Float(string="租赁数量", default=1.0)
    rental_days = fields.Float(string="租赁天数", default=1.0)
    daily_price = fields.Monetary(string="日租单价", currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", string="币种", related="order_id.currency_id", store=True)
    amount_total = fields.Monetary(string="租赁金额", currency_field="currency_id", compute="_compute_amount_total", store=True)
    returned_qty = fields.Float(string="已退还数量")
    damage_qty = fields.Float(string="损坏数量")
    note = fields.Char(string="备注")

    @api.depends("qty", "rental_days", "daily_price")
    def _compute_amount_total(self):
        for line in self:
            line.amount_total = (line.qty or 0.0) * (line.rental_days or 0.0) * (line.daily_price or 0.0)


class ScMaterialRentalSettlement(models.Model):
    _name = "sc.material.rental.settlement"
    _description = "周转材料租赁结算"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "settlement_date desc, id desc"

    name = fields.Char(string="结算单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    rental_order_id = fields.Many2one("sc.material.rental.order", string="租赁单", index=True)
    contract_id = fields.Many2one("construction.contract", string="租赁合同", index=True)
    supplier_id = fields.Many2one("res.partner", string="供应商", required=True, index=True, tracking=True)
    payment_request_id = fields.Many2one("payment.request", string="支付申请", index=True)
    settlement_date = fields.Date(string="结算日期", required=True, default=fields.Date.context_today, index=True)
    owner_id = fields.Many2one("res.users", string="经办人", default=lambda self: self.env.user, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    rent_amount = fields.Monetary(string="租金金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    damage_amount = fields.Monetary(string="赔偿金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    amount_total = fields.Monetary(string="结算金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    line_ids = fields.One2many("sc.material.rental.settlement.line", "settlement_id", string="结算明细")
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("confirmed", "已确认"), ("paid", "已支付"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        required=True,
        index=True,
        tracking=True,
    )
    note = fields.Text(string="备注")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    @api.depends("line_ids.rent_amount", "line_ids.damage_amount")
    def _compute_amounts(self):
        for record in self:
            record.rent_amount = sum(record.line_ids.mapped("rent_amount"))
            record.damage_amount = sum(record.line_ids.mapped("damage_amount"))
            record.amount_total = record.rent_amount + record.damage_amount

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.material.rental.settlement") or _("周转材料租赁结算")
        return super().create(vals_list)

    def action_submit(self):
        self.write({"state": "submitted"})
        return True

    def action_confirm(self):
        self.write({"state": "confirmed"})
        return True

    def action_paid(self):
        self.write({"state": "paid"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True


class ScMaterialRentalSettlementLine(models.Model):
    _name = "sc.material.rental.settlement.line"
    _description = "周转材料租赁结算明细"
    _order = "settlement_id, sequence, id"

    settlement_id = fields.Many2one("sc.material.rental.settlement", string="租赁结算", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one("product.product", string="周转材料", index=True)
    material_name = fields.Char(string="材料名称", required=True)
    material_spec = fields.Char(string="规格型号")
    unit_name = fields.Char(string="单位")
    qty = fields.Float(string="结算数量", default=1.0)
    rental_days = fields.Float(string="结算天数", default=1.0)
    daily_price = fields.Monetary(string="日租单价", currency_field="currency_id")
    damage_amount = fields.Monetary(string="赔偿金额", currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", string="币种", related="settlement_id.currency_id", store=True)
    rent_amount = fields.Monetary(string="租金金额", currency_field="currency_id", compute="_compute_rent_amount", store=True)
    note = fields.Char(string="备注")

    @api.depends("qty", "rental_days", "daily_price")
    def _compute_rent_amount(self):
        for line in self:
            line.rent_amount = (line.qty or 0.0) * (line.rental_days or 0.0) * (line.daily_price or 0.0)
