# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ScEquipmentPlan(models.Model):
    _name = "sc.equipment.plan"
    _description = "设备计划"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "plan_date desc, id desc"

    name = fields.Char(string="计划单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    plan_date = fields.Date(string="计划日期", required=True, default=fields.Date.context_today, index=True)
    start_date = fields.Date(string="计划开始日期", index=True)
    end_date = fields.Date(string="计划结束日期", index=True)
    usage_location = fields.Char(string="计划使用地点", index=True)
    owner_id = fields.Many2one("res.users", string="负责人", default=lambda self: self.env.user, index=True)
    supplier_id = fields.Many2one("res.partner", string="建议供应单位", index=True)
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("approved", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.equipment.plan.line", "plan_id", string="计划明细")
    note = fields.Text(string="计划说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_equipment_plan_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用设备计划已迁移为专业设备计划。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.equipment.plan") or _("设备计划")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if record.state != "draft":
                raise UserError(_("只有草稿状态的设备计划可以提交。"))
            if not record.line_ids:
                raise ValidationError(_("提交设备计划前必须维护计划明细。"))
            record.line_ids._check_values()
        self.write({"state": "submitted"})
        return True

    def action_approve(self):
        for record in self:
            if record.state != "submitted":
                raise UserError(_("只有已提交状态的设备计划可以确认。"))
            record.line_ids._check_values()
        self.write({"state": "approved"})
        return True

    def action_cancel(self):
        for record in self:
            if record.state not in ("draft", "submitted"):
                raise UserError(_("只有草稿或已提交状态的设备计划可以取消。"))
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        for record in self:
            if record.state != "cancel":
                raise UserError(_("只有已取消状态的设备计划可以重置为草稿。"))
        self.write({"state": "draft"})
        return True

    @api.constrains("start_date", "end_date")
    def _check_date_order(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("计划开始日期不能晚于计划结束日期。"))


class ScEquipmentPlanLine(models.Model):
    _name = "sc.equipment.plan.line"
    _description = "设备计划明细"
    _order = "plan_id, sequence, id"

    plan_id = fields.Many2one("sc.equipment.plan", string="计划单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="plan_id.project_id", store=True, index=True)
    equipment_name = fields.Char(string="设备名称", required=True)
    equipment_code = fields.Char(string="设备编号")
    planned_qty = fields.Float(string="计划台数", required=True, default=1)
    planned_hours = fields.Float(string="计划台时")
    usage_location = fields.Char(string="使用地点")
    operator_requirement = fields.Char(string="操作要求")
    note = fields.Char(string="备注")

    @api.constrains("planned_qty", "planned_hours")
    def _check_values(self):
        for record in self:
            if record.planned_qty <= 0:
                raise ValidationError(_("计划台数必须大于0。"))
            if record.planned_hours < 0:
                raise ValidationError(_("计划台时不能为负数。"))


class ScEquipmentRequest(models.Model):
    _name = "sc.equipment.request"
    _description = "设备申请"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, id desc"

    name = fields.Char(string="申请单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    plan_id = fields.Many2one("sc.equipment.plan", string="来源设备计划", index=True)
    request_date = fields.Date(string="申请日期", required=True, default=fields.Date.context_today, index=True)
    required_date = fields.Date(string="需用日期", index=True)
    usage_location = fields.Char(string="使用地点", index=True)
    requester_id = fields.Many2one("res.users", string="申请人", default=lambda self: self.env.user, index=True)
    supplier_id = fields.Many2one("res.partner", string="建议供应单位", index=True)
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    quantity_total = fields.Float(
        string="总数量",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    amount_total = fields.Monetary(
        string="总金额",
        currency_field="currency_id",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    invoice_amount = fields.Monetary(
        string="已开票金额",
        currency_field="currency_id",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    paid_amount = fields.Monetary(
        string="已付款金额",
        currency_field="currency_id",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    unpaid_amount = fields.Monetary(
        string="未付款金额",
        currency_field="currency_id",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    uninvoiced_amount = fields.Monetary(
        string="未开票金额",
        currency_field="currency_id",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    tax_rate_text = fields.Char(
        string="税率",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    vat_type_text = fields.Char(
        string="增值税类型",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("approved", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.equipment.request.line", "request_id", string="申请明细")
    note = fields.Text(string="申请说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_equipment_request_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用设备申请已迁移为专业设备申请。"),
    ]

    @api.depends("line_ids.requested_qty")
    def _compute_request_boundary_fields(self):
        for record in self:
            record.quantity_total = sum(record.line_ids.mapped("requested_qty"))
            record.amount_total = 0.0
            record.invoice_amount = 0.0
            record.paid_amount = 0.0
            record.unpaid_amount = 0.0
            record.uninvoiced_amount = 0.0
            record.tax_rate_text = False
            record.vat_type_text = False

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.equipment.request") or _("设备申请")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if record.state != "draft":
                raise UserError(_("只有草稿状态的设备申请可以提交。"))
            if not record.line_ids:
                raise ValidationError(_("提交设备申请前必须维护申请明细。"))
            record.line_ids._check_values()
            record._check_business_anchor()
        self.write({"state": "submitted"})
        return True

    def action_approve(self):
        for record in self:
            if record.state != "submitted":
                raise UserError(_("只有已提交状态的设备申请可以确认。"))
            record.line_ids._check_values()
            record._check_business_anchor()
        self.write({"state": "approved"})
        return True

    def action_cancel(self):
        for record in self:
            if record.state not in ("draft", "submitted"):
                raise UserError(_("只有草稿或已提交状态的设备申请可以取消。"))
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        for record in self:
            if record.state != "cancel":
                raise UserError(_("只有已取消状态的设备申请可以重置为草稿。"))
        self.write({"state": "draft"})
        return True

    def _check_business_anchor(self):
        for record in self:
            if not record.plan_id:
                continue
            if record.plan_id.project_id != record.project_id:
                raise UserError(_("设备申请的项目必须与来源设备计划一致。"))
            if record.plan_id.state != "approved":
                raise UserError(_("设备申请只能引用已确认的设备计划。"))
            if record.supplier_id and record.plan_id.supplier_id and record.supplier_id != record.plan_id.supplier_id:
                raise UserError(_("设备申请的供应单位必须与来源设备计划一致。"))


class ScEquipmentRequestLine(models.Model):
    _name = "sc.equipment.request.line"
    _description = "设备申请明细"
    _order = "request_id, sequence, id"

    request_id = fields.Many2one("sc.equipment.request", string="申请单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="request_id.project_id", store=True, index=True)
    equipment_name = fields.Char(string="设备名称", required=True)
    equipment_code = fields.Char(string="设备编号")
    requested_qty = fields.Float(string="申请台数", required=True, default=1)
    planned_hours = fields.Float(string="预计台时")
    usage_location = fields.Char(string="使用地点")
    operator_requirement = fields.Char(string="操作要求")
    note = fields.Char(string="备注")

    @api.constrains("requested_qty", "planned_hours")
    def _check_values(self):
        for record in self:
            if record.requested_qty <= 0:
                raise ValidationError(_("申请台数必须大于0。"))
            if record.planned_hours < 0:
                raise ValidationError(_("预计台时不能为负数。"))


class ScEquipmentUsage(models.Model):
    _name = "sc.equipment.usage"
    _description = "设备使用登记"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "usage_date desc, id desc"

    name = fields.Char(string="登记单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    request_id = fields.Many2one("sc.equipment.request", string="来源设备申请", index=True)
    usage_date = fields.Date(string="使用日期", required=True, default=fields.Date.context_today, index=True, tracking=True)
    equipment_name = fields.Char(string="设备名称", required=True, index=True, tracking=True)
    equipment_code = fields.Char(string="设备编号", index=True)
    usage_location = fields.Char(string="使用地点", required=True, index=True)
    operator_name = fields.Char(string="操作人员", required=True, index=True)
    usage_qty = fields.Float(string="使用台数", required=True, default=1)
    usage_hours = fields.Float(string="使用台时", required=True)
    supplier_id = fields.Many2one("res.partner", string="供应单位", index=True)
    recorder_id = fields.Many2one("res.users", string="记录人", default=lambda self: self.env.user, index=True)
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("confirmed", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_equipment_usage_attachment_rel",
        "usage_id",
        "attachment_id",
        string="附件",
    )
    note = fields.Text(string="使用说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_equipment_usage_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用设备使用登记已迁移为专业设备使用登记。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.equipment.usage") or _("设备使用登记")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if record.state != "draft":
                raise UserError(_("只有草稿状态的设备使用登记可以提交。"))
            record._check_business_anchor()
        self._check_values()
        self.write({"state": "submitted"})
        return True

    def action_confirm(self):
        for record in self:
            if record.state != "submitted":
                raise UserError(_("只有已提交状态的设备使用登记可以确认。"))
            record._check_business_anchor()
        self._check_values()
        self.write({"state": "confirmed"})
        return True

    def action_cancel(self):
        for record in self:
            if record.state not in ("draft", "submitted"):
                raise UserError(_("只有草稿或已提交状态的设备使用登记可以取消。"))
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        for record in self:
            if record.state != "cancel":
                raise UserError(_("只有已取消状态的设备使用登记可以重置为草稿。"))
        self.write({"state": "draft"})
        return True

    def _check_business_anchor(self):
        for record in self:
            if not record.request_id:
                continue
            if record.request_id.project_id != record.project_id:
                raise UserError(_("设备使用登记的项目必须与来源设备申请一致。"))
            if record.request_id.state != "approved":
                raise UserError(_("设备使用登记只能引用已确认的设备申请。"))
            if record.supplier_id and record.request_id.supplier_id and record.supplier_id != record.request_id.supplier_id:
                raise UserError(_("设备使用登记的供应单位必须与来源设备申请一致。"))

    @api.constrains("usage_qty", "usage_hours")
    def _check_values(self):
        for record in self:
            if record.usage_qty <= 0:
                raise ValidationError(_("使用台数必须大于0。"))
            if record.usage_hours <= 0:
                raise ValidationError(_("使用台时必须大于0。"))


class ScEquipmentSettlement(models.Model):
    _name = "sc.equipment.settlement"
    _description = "设备结算"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "settlement_date desc, id desc"

    name = fields.Char(string="结算单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    supplier_id = fields.Many2one("res.partner", string="供应单位", required=True, index=True, tracking=True)
    settlement_date = fields.Date(string="结算日期", required=True, default=fields.Date.context_today, index=True)
    owner_id = fields.Many2one("res.users", string="经办人", default=lambda self: self.env.user, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    amount_untaxed = fields.Monetary(string="未税金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id", compute="_compute_amounts", store=True)
    amount_total = fields.Monetary(string="结算金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    settlement_content = fields.Char(
        string="结算内容",
        compute="_compute_settlement_content",
        store=True,
        readonly=True,
    )
    payment_paid_amount = fields.Monetary(
        string="已付款金额",
        currency_field="currency_id",
        compute="_compute_payment_boundary_amounts",
        store=True,
        readonly=True,
    )
    payment_unpaid_amount = fields.Monetary(
        string="未付款金额",
        currency_field="currency_id",
        compute="_compute_payment_boundary_amounts",
        store=True,
        readonly=True,
    )
    payment_requested_amount = fields.Monetary(
        string="已申请金额",
        currency_field="currency_id",
        compute="_compute_payment_boundary_amounts",
        store=True,
        readonly=True,
    )
    payment_unrequested_amount = fields.Monetary(
        string="未申请金额",
        currency_field="currency_id",
        compute="_compute_payment_boundary_amounts",
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("confirmed", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.equipment.settlement.line", "settlement_id", string="结算明细")
    note = fields.Text(string="结算说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_equipment_settlement_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用设备结算已迁移为专业设备结算。"),
    ]

    @api.depends("line_ids.amount_untaxed", "line_ids.tax_amount", "line_ids.amount_total")
    def _compute_amounts(self):
        for record in self:
            record.amount_untaxed = sum(record.line_ids.mapped("amount_untaxed"))
            record.tax_amount = sum(record.line_ids.mapped("tax_amount"))
            record.amount_total = sum(record.line_ids.mapped("amount_total"))

    @api.depends("line_ids.equipment_name", "note")
    def _compute_settlement_content(self):
        for record in self:
            names = [name for name in record.line_ids.mapped("equipment_name") if name]
            record.settlement_content = "、".join(names[:3]) or record.note or False

    @api.depends("amount_total")
    def _compute_payment_boundary_amounts(self):
        for record in self:
            amount = record.amount_total or 0.0
            record.payment_paid_amount = 0.0
            record.payment_unpaid_amount = amount
            record.payment_requested_amount = 0.0
            record.payment_unrequested_amount = amount

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.equipment.settlement") or _("设备结算")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if record.state != "draft":
                raise UserError(_("只有草稿状态的设备结算可以提交。"))
            if not record.line_ids:
                raise ValidationError(_("提交设备结算前必须维护结算明细。"))
            record.line_ids._check_values()
            record._check_business_anchor()
        self.write({"state": "submitted"})
        return True

    def action_confirm(self):
        for record in self:
            if record.state != "submitted":
                raise UserError(_("只有已提交状态的设备结算可以确认。"))
            record.line_ids._check_values()
            record._check_business_anchor()
        self.write({"state": "confirmed"})
        return True

    def action_cancel(self):
        for record in self:
            if record.state not in ("draft", "submitted"):
                raise UserError(_("只有草稿或已提交状态的设备结算可以取消。"))
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        for record in self:
            if record.state != "cancel":
                raise UserError(_("只有已取消状态的设备结算可以重置为草稿。"))
        self.write({"state": "draft"})
        return True

    def _check_business_anchor(self):
        for record in self:
            for line in record.line_ids.filtered("usage_id"):
                if line.usage_id.project_id != record.project_id:
                    raise UserError(_("设备结算明细引用的使用登记必须属于同一项目。"))
                if line.usage_id.state != "confirmed":
                    raise UserError(_("设备结算只能引用已确认的设备使用登记。"))
                if line.usage_id.supplier_id and line.usage_id.supplier_id != record.supplier_id:
                    raise UserError(_("设备结算明细引用的使用登记供应单位必须与结算单一致。"))


class ScEquipmentSettlementLine(models.Model):
    _name = "sc.equipment.settlement.line"
    _description = "设备结算明细"
    _order = "settlement_id, sequence, id"

    settlement_id = fields.Many2one("sc.equipment.settlement", string="结算单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="settlement_id.project_id", store=True, index=True)
    usage_id = fields.Many2one("sc.equipment.usage", string="使用登记", index=True)
    equipment_name = fields.Char(string="设备名称", required=True)
    equipment_code = fields.Char(string="设备编号")
    qty = fields.Float(string="结算台时", required=True, default=1)
    unit_name = fields.Char(string="单位", default="台时")
    currency_id = fields.Many2one("res.currency", string="币种", related="settlement_id.currency_id", store=True)
    unit_price = fields.Monetary(string="结算单价", currency_field="currency_id", required=True)
    tax_rate = fields.Float(string="税率%")
    amount_untaxed = fields.Monetary(string="未税金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id", compute="_compute_amounts", store=True)
    amount_total = fields.Monetary(string="含税金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    note = fields.Char(string="备注")

    @api.depends("qty", "unit_price", "tax_rate")
    def _compute_amounts(self):
        for record in self:
            amount_untaxed = record.qty * record.unit_price
            tax_amount = amount_untaxed * record.tax_rate / 100
            record.amount_untaxed = amount_untaxed
            record.tax_amount = tax_amount
            record.amount_total = amount_untaxed + tax_amount

    @api.constrains("qty", "unit_price", "tax_rate")
    def _check_values(self):
        for record in self:
            if record.qty <= 0:
                raise ValidationError(_("结算台时必须大于0。"))
            if record.unit_price < 0:
                raise ValidationError(_("结算单价不能为负数。"))
            if record.tax_rate < 0:
                raise ValidationError(_("税率不能为负数。"))


class ScEquipmentPrice(models.Model):
    _name = "sc.equipment.price"
    _description = "设备价格库"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "effective_date desc, id desc"

    name = fields.Char(string="价格编号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="适用项目", index=True, tracking=True)
    supplier_id = fields.Many2one("res.partner", string="供应单位", index=True)
    equipment_name = fields.Char(string="设备名称", required=True, index=True, tracking=True)
    equipment_code = fields.Char(string="设备编号", index=True)
    unit_name = fields.Char(string="计价单位", required=True, default="台时")
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    unit_price = fields.Monetary(string="单价", currency_field="currency_id", required=True, tracking=True)
    tax_rate = fields.Float(string="税率%")
    effective_date = fields.Date(string="生效日期", required=True, default=fields.Date.context_today, index=True)
    expire_date = fields.Date(string="失效日期", index=True)
    state = fields.Selection(
        [("draft", "草稿"), ("active", "生效"), ("inactive", "停用")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    note = fields.Text(string="价格说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_equipment_price_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用设备价格已迁移为专业设备价格。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.equipment.price") or _("设备价格")
        return super().create(vals_list)

    def action_activate(self):
        for record in self:
            if record.state != "draft":
                raise UserError(_("只有草稿状态的设备价格可以生效。"))
        self._check_values()
        self.write({"state": "active"})
        return True

    def action_deactivate(self):
        for record in self:
            if record.state != "active":
                raise UserError(_("只有生效状态的设备价格可以停用。"))
        self.write({"state": "inactive"})
        return True

    def action_reset_draft(self):
        for record in self:
            if record.state != "inactive":
                raise UserError(_("只有停用状态的设备价格可以重置为草稿。"))
        self.write({"state": "draft"})
        return True

    @api.constrains("unit_price", "tax_rate", "effective_date", "expire_date")
    def _check_values(self):
        for record in self:
            if record.unit_price < 0:
                raise ValidationError(_("设备单价不能为负数。"))
            if record.tax_rate < 0:
                raise ValidationError(_("税率不能为负数。"))
            if record.effective_date and record.expire_date and record.effective_date > record.expire_date:
                raise ValidationError(_("生效日期不能晚于失效日期。"))
