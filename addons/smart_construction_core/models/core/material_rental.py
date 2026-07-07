# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


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
        for record in self:
            if record.state != "draft":
                raise UserError(_("只有草稿租赁计划可以提交。"))
            record._check_business_anchor()
            record.write({"state": "submitted"})
        return True

    def action_approve(self):
        for record in self:
            if record.state != "submitted":
                raise UserError(_("只有已提交租赁计划可以确认。"))
            record._check_business_anchor()
            record.write({"state": "approved"})
        return True

    def action_cancel(self):
        for record in self:
            if record.state not in ("draft", "submitted"):
                raise UserError(_("只有草稿或已提交租赁计划可以取消。"))
            record.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        for record in self:
            if record.state != "cancel":
                raise UserError(_("只有已取消租赁计划可以重置为草稿。"))
            record.write({"state": "draft"})
        return True

    def _check_business_anchor(self):
        for record in self:
            if not record.line_ids:
                raise UserError(_("租赁计划必须填写计划明细。"))
            if record.contract_id:
                if record.contract_id.project_id != record.project_id:
                    raise UserError(_("租赁计划关联合同必须属于当前项目。"))
                if record.contract_id.partner_id and record.supplier_id and record.contract_id.partner_id != record.supplier_id:
                    raise UserError(_("租赁计划建议供应商必须与合同相对方一致。"))
            for line in record.line_ids:
                if line.planned_qty <= 0:
                    raise UserError(_("计划租赁数量必须大于 0。"))
                if line.planned_days <= 0:
                    raise UserError(_("计划租赁天数必须大于 0。"))
                if line.daily_price < 0:
                    raise UserError(_("计划日租单价不能为负数。"))


class ScMaterialRentalPlanLine(models.Model):
    _name = "sc.material.rental.plan.line"
    _description = "周转材料租赁计划明细"
    _order = "plan_id, sequence, id"

    plan_id = fields.Many2one("sc.material.rental.plan", string="租赁计划", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="plan_id.project_id", store=True, index=True)
    material_catalog_id = fields.Many2one("sc.material.catalog", string="材料档案", index=True)
    product_id = fields.Many2one("product.product", string="材料", index=True)
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._apply_material_catalog_defaults(vals)
        return super().create(vals_list)

    @api.model
    def _apply_material_catalog_defaults(self, vals):
        catalog = self.env["sc.material.catalog"].browse(vals.get("material_catalog_id")) if vals.get("material_catalog_id") else False
        if not catalog:
            return vals
        vals.setdefault("material_name", catalog.display_name)
        vals.setdefault("material_spec", catalog.spec_model or False)
        vals.setdefault("unit_name", catalog.uom_text or False)
        return vals

    @api.onchange("material_catalog_id")
    def _onchange_material_catalog_id(self):
        for line in self:
            catalog = line.material_catalog_id
            if not catalog:
                continue
            line.material_name = catalog.display_name
            line.material_spec = catalog.spec_model or line.material_spec
            line.unit_name = catalog.uom_text or line.unit_name

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            if line.product_id and not line.material_catalog_id:
                line.material_name = line.product_id.display_name
                line.material_spec = line.product_id.default_code or line.material_spec
                line.unit_name = line.product_id.uom_id.name or line.unit_name


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
    account_holder = fields.Char(string="开户人姓名", related="supplier_id.sc_account_name", store=True, readonly=True)
    bank_name = fields.Char(string="开户行", related="supplier_id.sc_bank_name", store=True, readonly=True, index=True)
    bank_account = fields.Char(string="银行账号", related="supplier_id.sc_bank_account", store=True, readonly=True, index=True)
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
        for record in self:
            if record.state != "draft":
                raise UserError(_("只有草稿租赁单可以启用。"))
            record._check_business_anchor()
            record.write({"state": "active"})
        return True

    def action_return(self):
        for record in self:
            if record.state != "active":
                raise UserError(_("只有租赁中的租赁单可以退还。"))
            record._check_business_anchor()
            record.write({"state": "returned"})
        return True

    def action_settle(self):
        for record in self:
            if record.state != "returned":
                raise UserError(_("只有已退还的租赁单可以结算。"))
            record._check_business_anchor()
            record.write({"state": "settled"})
        return True

    def action_cancel(self):
        for record in self:
            if record.state not in ("draft", "active"):
                raise UserError(_("只有草稿或租赁中的租赁单可以取消。"))
            record.write({"state": "cancel"})
        return True

    def _check_business_anchor(self):
        for record in self:
            if not record.line_ids:
                raise UserError(_("租赁单必须填写租赁明细。"))
            if record.plan_id:
                if record.plan_id.project_id != record.project_id:
                    raise UserError(_("租赁单来源计划必须属于当前项目。"))
                if record.plan_id.state != "approved":
                    raise UserError(_("租赁单来源计划必须已确认。"))
            if record.contract_id:
                if record.contract_id.project_id != record.project_id:
                    raise UserError(_("租赁合同必须属于当前项目。"))
                if record.contract_id.partner_id and record.contract_id.partner_id != record.supplier_id:
                    raise UserError(_("租赁单供应商必须与租赁合同相对方一致。"))
            for line in record.line_ids:
                if line.qty <= 0:
                    raise UserError(_("租赁数量必须大于 0。"))
                if line.rental_days <= 0:
                    raise UserError(_("租赁天数必须大于 0。"))
                if line.daily_price < 0:
                    raise UserError(_("日租单价不能为负数。"))


class ScMaterialRentalOrderLine(models.Model):
    _name = "sc.material.rental.order.line"
    _description = "周转材料租赁明细"
    _order = "order_id, sequence, id"

    order_id = fields.Many2one("sc.material.rental.order", string="租赁单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    material_catalog_id = fields.Many2one("sc.material.catalog", string="材料档案", index=True)
    product_id = fields.Many2one("product.product", string="材料", index=True)
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._apply_material_catalog_defaults(vals)
        return super().create(vals_list)

    @api.model
    def _apply_material_catalog_defaults(self, vals):
        catalog = self.env["sc.material.catalog"].browse(vals.get("material_catalog_id")) if vals.get("material_catalog_id") else False
        if not catalog:
            return vals
        vals.setdefault("material_name", catalog.display_name)
        vals.setdefault("material_spec", catalog.spec_model or False)
        vals.setdefault("unit_name", catalog.uom_text or False)
        return vals

    @api.onchange("material_catalog_id")
    def _onchange_material_catalog_id(self):
        for line in self:
            catalog = line.material_catalog_id
            if not catalog:
                continue
            line.material_name = catalog.display_name
            line.material_spec = catalog.spec_model or line.material_spec
            line.unit_name = catalog.uom_text or line.unit_name

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            if line.product_id and not line.material_catalog_id:
                line.material_name = line.product_id.display_name
                line.material_spec = line.product_id.default_code or line.material_spec
                line.unit_name = line.product_id.uom_id.name or line.unit_name


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
        for record in self:
            if record.state != "draft":
                raise UserError(_("只有草稿租赁结算可以提交。"))
            record._check_business_anchor()
            record.write({"state": "submitted"})
        return True

    def action_confirm(self):
        for record in self:
            if record.state != "submitted":
                raise UserError(_("只有已提交租赁结算可以确认。"))
            record._check_business_anchor()
            record.write({"state": "confirmed"})
        return True

    def action_paid(self):
        for record in self:
            if record.state != "confirmed":
                raise UserError(_("只有已确认租赁结算可以支付。"))
            record._check_business_anchor()
            record.write({"state": "paid"})
        return True

    def action_cancel(self):
        for record in self:
            if record.state not in ("draft", "submitted", "confirmed"):
                raise UserError(_("只有未支付租赁结算可以取消。"))
            record.write({"state": "cancel"})
        return True

    def _check_business_anchor(self):
        for record in self:
            if not record.line_ids:
                raise UserError(_("租赁结算必须填写结算明细。"))
            if record.rental_order_id:
                if record.rental_order_id.project_id != record.project_id:
                    raise UserError(_("租赁结算来源租赁单必须属于当前项目。"))
                if record.rental_order_id.state not in ("returned", "settled"):
                    raise UserError(_("租赁结算来源租赁单必须已退还或已结算。"))
                if record.rental_order_id.supplier_id != record.supplier_id:
                    raise UserError(_("租赁结算供应商必须与来源租赁单一致。"))
            if record.contract_id:
                if record.contract_id.project_id != record.project_id:
                    raise UserError(_("租赁结算合同必须属于当前项目。"))
                if record.contract_id.partner_id and record.contract_id.partner_id != record.supplier_id:
                    raise UserError(_("租赁结算供应商必须与合同相对方一致。"))
            if record.payment_request_id:
                if record.payment_request_id.project_id != record.project_id:
                    raise UserError(_("租赁结算支付申请必须属于当前项目。"))
                if record.payment_request_id.partner_id and record.payment_request_id.partner_id != record.supplier_id:
                    raise UserError(_("租赁结算供应商必须与支付申请收款方一致。"))
            for line in record.line_ids:
                if line.qty <= 0:
                    raise UserError(_("租赁结算数量必须大于 0。"))
                if line.rental_days <= 0:
                    raise UserError(_("租赁结算天数必须大于 0。"))
                if line.daily_price < 0 or line.damage_amount < 0:
                    raise UserError(_("租赁结算金额不能为负数。"))


class ScMaterialRentalSettlementLine(models.Model):
    _name = "sc.material.rental.settlement.line"
    _description = "周转材料租赁结算明细"
    _order = "settlement_id, sequence, id"

    settlement_id = fields.Many2one("sc.material.rental.settlement", string="租赁结算", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    material_catalog_id = fields.Many2one("sc.material.catalog", string="材料档案", index=True)
    product_id = fields.Many2one("product.product", string="材料", index=True)
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._apply_material_catalog_defaults(vals)
        return super().create(vals_list)

    @api.model
    def _apply_material_catalog_defaults(self, vals):
        catalog = self.env["sc.material.catalog"].browse(vals.get("material_catalog_id")) if vals.get("material_catalog_id") else False
        if not catalog:
            return vals
        vals.setdefault("material_name", catalog.display_name)
        vals.setdefault("material_spec", catalog.spec_model or False)
        vals.setdefault("unit_name", catalog.uom_text or False)
        return vals

    @api.onchange("material_catalog_id")
    def _onchange_material_catalog_id(self):
        for line in self:
            catalog = line.material_catalog_id
            if not catalog:
                continue
            line.material_name = catalog.display_name
            line.material_spec = catalog.spec_model or line.material_spec
            line.unit_name = catalog.uom_text or line.unit_name

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            if line.product_id and not line.material_catalog_id:
                line.material_name = line.product_id.display_name
                line.material_spec = line.product_id.default_code or line.material_spec
                line.unit_name = line.product_id.uom_id.name or line.unit_name
