# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScSubcontractPlan(models.Model):
    _name = "sc.subcontract.plan"
    _description = "分包计划"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "plan_date desc, id desc"

    name = fields.Char(string="计划单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    contract_id = fields.Many2one("construction.contract", string="关联合同", index=True)
    plan_date = fields.Date(string="计划日期", required=True, default=fields.Date.context_today, index=True)
    start_date = fields.Date(string="计划开始日期", index=True)
    end_date = fields.Date(string="计划结束日期", index=True)
    subcontract_scope = fields.Char(string="分包范围", required=True, index=True, tracking=True)
    subcontractor_id = fields.Many2one("res.partner", string="建议分包单位", index=True)
    owner_id = fields.Many2one("res.users", string="负责人", default=lambda self: self.env.user, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    estimated_amount = fields.Monetary(string="预计金额", currency_field="currency_id", compute="_compute_estimated_amount", store=True)
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("approved", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.subcontract.plan.line", "plan_id", string="计划明细")
    note = fields.Text(string="计划说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_subcontract_plan_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用分包计划已迁移为专业分包计划。"),
    ]

    @api.depends("line_ids.estimated_amount")
    def _compute_estimated_amount(self):
        for record in self:
            record.estimated_amount = sum(record.line_ids.mapped("estimated_amount"))

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.subcontract.plan") or _("分包计划")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if not record.line_ids:
                raise ValidationError(_("提交分包计划前必须维护计划明细。"))
            record.line_ids._check_values()
        self.write({"state": "submitted"})
        return True

    def action_approve(self):
        for record in self:
            record.line_ids._check_values()
        self.write({"state": "approved"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True

    @api.constrains("start_date", "end_date")
    def _check_date_order(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("计划开始日期不能晚于计划结束日期。"))


class ScSubcontractPlanLine(models.Model):
    _name = "sc.subcontract.plan.line"
    _description = "分包计划明细"
    _order = "plan_id, sequence, id"

    plan_id = fields.Many2one("sc.subcontract.plan", string="计划单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="plan_id.project_id", store=True, index=True)
    work_scope = fields.Char(string="分包工作范围", required=True)
    work_content = fields.Char(string="工作内容")
    planned_qty = fields.Float(string="计划数量", default=1)
    unit_name = fields.Char(string="单位")
    currency_id = fields.Many2one("res.currency", string="币种", related="plan_id.currency_id", store=True)
    estimated_amount = fields.Monetary(string="预计金额", currency_field="currency_id")
    note = fields.Char(string="备注")

    @api.constrains("planned_qty", "estimated_amount")
    def _check_values(self):
        for record in self:
            if record.planned_qty < 0:
                raise ValidationError(_("计划数量不能为负数。"))
            if record.estimated_amount < 0:
                raise ValidationError(_("预计金额不能为负数。"))


class ScSubcontractRequest(models.Model):
    _name = "sc.subcontract.request"
    _description = "分包申请"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, id desc"

    name = fields.Char(string="申请单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    plan_id = fields.Many2one("sc.subcontract.plan", string="来源分包计划", index=True)
    contract_id = fields.Many2one("construction.contract", string="关联合同", index=True)
    request_date = fields.Date(string="申请日期", required=True, default=fields.Date.context_today, index=True)
    need_start_date = fields.Date(string="需用开始日期", index=True)
    need_end_date = fields.Date(string="需用结束日期", index=True)
    subcontract_scope = fields.Char(string="申请分包范围", required=True, index=True, tracking=True)
    suggested_subcontractor_id = fields.Many2one("res.partner", string="建议分包单位", index=True)
    applicant_id = fields.Many2one("res.users", string="申请人", default=lambda self: self.env.user, index=True, tracking=True)
    department_id = fields.Many2one("hr.department", string="申请部门", index=True)
    priority = fields.Selection(
        [("normal", "普通"), ("urgent", "紧急")],
        string="需求优先级",
        default="normal",
        required=True,
        index=True,
    )
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    estimated_amount = fields.Monetary(string="申请预计金额", currency_field="currency_id", compute="_compute_estimated_amount", store=True)
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("approved", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.subcontract.request.line", "request_id", string="申请明细")
    request_reason = fields.Text(string="申请原因")
    note = fields.Text(string="备注")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_subcontract_request_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用分包申请已迁移为专业分包申请。"),
    ]

    @api.depends("line_ids.estimated_amount")
    def _compute_estimated_amount(self):
        for record in self:
            record.estimated_amount = sum(record.line_ids.mapped("estimated_amount"))

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.subcontract.request") or _("分包申请")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if not record.line_ids:
                raise ValidationError(_("提交分包申请前必须维护申请明细。"))
            record.line_ids._check_values()
        self.write({"state": "submitted"})
        return True

    def action_approve(self):
        for record in self:
            record.line_ids._check_values()
        self.write({"state": "approved"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True

    @api.constrains("need_start_date", "need_end_date")
    def _check_need_date_order(self):
        for record in self:
            if record.need_start_date and record.need_end_date and record.need_start_date > record.need_end_date:
                raise ValidationError(_("需用开始日期不能晚于需用结束日期。"))


class ScSubcontractRequestLine(models.Model):
    _name = "sc.subcontract.request.line"
    _description = "分包申请明细"
    _order = "request_id, sequence, id"

    request_id = fields.Many2one("sc.subcontract.request", string="申请单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="request_id.project_id", store=True, index=True)
    work_scope = fields.Char(string="申请分包工作范围", required=True)
    work_content = fields.Char(string="工作内容")
    required_qty = fields.Float(string="申请数量", default=1)
    unit_name = fields.Char(string="单位")
    required_date = fields.Date(string="需用日期")
    currency_id = fields.Many2one("res.currency", string="币种", related="request_id.currency_id", store=True)
    estimated_amount = fields.Monetary(string="预计金额", currency_field="currency_id")
    note = fields.Char(string="备注")

    @api.constrains("required_qty", "estimated_amount")
    def _check_values(self):
        for record in self:
            if record.required_qty < 0:
                raise ValidationError(_("申请数量不能为负数。"))
            if record.estimated_amount < 0:
                raise ValidationError(_("预计金额不能为负数。"))


class ScSubcontractRegister(models.Model):
    _name = "sc.subcontract.register"
    _description = "分包登记"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "register_date desc, id desc"

    name = fields.Char(string="登记单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    request_id = fields.Many2one("sc.subcontract.request", string="来源分包申请", index=True)
    contract_id = fields.Many2one("construction.contract", string="分包合同", index=True)
    register_date = fields.Date(string="登记日期", required=True, default=fields.Date.context_today, index=True)
    start_date = fields.Date(string="履约开始日期", index=True)
    end_date = fields.Date(string="履约结束日期", index=True)
    subcontract_scope = fields.Char(string="登记分包范围", required=True, index=True, tracking=True)
    subcontractor_id = fields.Many2one("res.partner", string="分包单位", index=True, tracking=True)
    responsible_id = fields.Many2one("res.users", string="现场负责人", default=lambda self: self.env.user, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    registered_amount = fields.Monetary(string="登记合同金额", currency_field="currency_id", compute="_compute_registered_amount", store=True)
    state = fields.Selection(
        [("draft", "草稿"), ("active", "已登记"), ("closed", "已关闭"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.subcontract.register.line", "register_id", string="登记明细")
    management_note = fields.Text(string="管理要求")
    note = fields.Text(string="备注")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_subcontract_register_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用分包登记已迁移为专业分包登记。"),
    ]

    @api.depends("line_ids.registered_amount")
    def _compute_registered_amount(self):
        for record in self:
            record.registered_amount = sum(record.line_ids.mapped("registered_amount"))

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.subcontract.register") or _("分包登记")
        return super().create(vals_list)

    def action_register(self):
        for record in self:
            if not record.subcontractor_id:
                raise ValidationError(_("确认分包登记前必须维护分包单位。"))
            if not record.line_ids:
                raise ValidationError(_("确认分包登记前必须维护登记明细。"))
            record.line_ids._check_values()
        self.write({"state": "active"})
        return True

    def action_close(self):
        for record in self:
            record.line_ids._check_values()
        self.write({"state": "closed"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True

    @api.constrains("start_date", "end_date")
    def _check_date_order(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("履约开始日期不能晚于履约结束日期。"))


class ScSubcontractRegisterLine(models.Model):
    _name = "sc.subcontract.register.line"
    _description = "分包登记明细"
    _order = "register_id, sequence, id"

    register_id = fields.Many2one("sc.subcontract.register", string="登记单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="register_id.project_id", store=True, index=True)
    work_scope = fields.Char(string="登记分包工作范围", required=True)
    work_content = fields.Char(string="工作内容")
    contract_qty = fields.Float(string="合同数量", default=1)
    unit_name = fields.Char(string="单位")
    currency_id = fields.Many2one("res.currency", string="币种", related="register_id.currency_id", store=True)
    registered_amount = fields.Monetary(string="登记金额", currency_field="currency_id")
    note = fields.Char(string="备注")

    @api.constrains("contract_qty", "registered_amount")
    def _check_values(self):
        for record in self:
            if record.contract_qty < 0:
                raise ValidationError(_("合同数量不能为负数。"))
            if record.registered_amount < 0:
                raise ValidationError(_("登记金额不能为负数。"))


class ScSubcontractSettlement(models.Model):
    _name = "sc.subcontract.settlement"
    _description = "分包结算"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "settlement_date desc, id desc"

    name = fields.Char(string="结算单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    register_id = fields.Many2one("sc.subcontract.register", string="来源分包登记", index=True)
    contract_id = fields.Many2one("construction.contract", string="分包合同", index=True)
    subcontractor_id = fields.Many2one("res.partner", string="分包单位", required=True, index=True, tracking=True)
    settlement_date = fields.Date(string="结算日期", required=True, default=fields.Date.context_today, index=True)
    owner_id = fields.Many2one("res.users", string="经办人", default=lambda self: self.env.user, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    amount_untaxed = fields.Monetary(string="未税金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id", compute="_compute_amounts", store=True)
    amount_total = fields.Monetary(string="结算金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("confirmed", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.subcontract.settlement.line", "settlement_id", string="结算明细")
    note = fields.Text(string="结算说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_subcontract_settlement_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用分包结算已迁移为专业分包结算。"),
    ]

    @api.depends("line_ids.amount_untaxed", "line_ids.tax_amount", "line_ids.amount_total")
    def _compute_amounts(self):
        for record in self:
            record.amount_untaxed = sum(record.line_ids.mapped("amount_untaxed"))
            record.tax_amount = sum(record.line_ids.mapped("tax_amount"))
            record.amount_total = sum(record.line_ids.mapped("amount_total"))

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.subcontract.settlement") or _("分包结算")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if not record.line_ids:
                raise ValidationError(_("提交分包结算前必须维护结算明细。"))
            record.line_ids._check_values()
        self.write({"state": "submitted"})
        return True

    def action_confirm(self):
        for record in self:
            record.line_ids._check_values()
        self.write({"state": "confirmed"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True


class ScSubcontractSettlementLine(models.Model):
    _name = "sc.subcontract.settlement.line"
    _description = "分包结算明细"
    _order = "settlement_id, sequence, id"

    settlement_id = fields.Many2one("sc.subcontract.settlement", string="结算单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="settlement_id.project_id", store=True, index=True)
    register_id = fields.Many2one("sc.subcontract.register", string="分包登记", related="settlement_id.register_id", store=True, index=True)
    work_scope = fields.Char(string="结算分包工作范围", required=True)
    work_content = fields.Char(string="工作内容")
    qty = fields.Float(string="结算数量", required=True, default=1)
    unit_name = fields.Char(string="单位")
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
                raise ValidationError(_("结算数量必须大于0。"))
            if record.unit_price < 0:
                raise ValidationError(_("结算单价不能为负数。"))
            if record.tax_rate < 0:
                raise ValidationError(_("税率不能为负数。"))


class ScSubcontractPrice(models.Model):
    _name = "sc.subcontract.price"
    _description = "分包价格库"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "effective_date desc, id desc"

    name = fields.Char(string="价格编号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="适用项目", index=True, tracking=True)
    subcontractor_id = fields.Many2one("res.partner", string="分包单位", index=True)
    work_scope = fields.Char(string="分包工作范围", required=True, index=True, tracking=True)
    work_content = fields.Char(string="工作内容")
    unit_name = fields.Char(string="计价单位", required=True, default="项")
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
        ("legacy_subcontract_price_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用分包价格已迁移为专业分包价格。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.subcontract.price") or _("分包价格")
        return super().create(vals_list)

    def action_activate(self):
        self._check_values()
        self.write({"state": "active"})
        return True

    def action_deactivate(self):
        self.write({"state": "inactive"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True

    @api.constrains("unit_price", "tax_rate", "effective_date", "expire_date")
    def _check_values(self):
        for record in self:
            if record.unit_price < 0:
                raise ValidationError(_("分包单价不能为负数。"))
            if record.tax_rate < 0:
                raise ValidationError(_("税率不能为负数。"))
            if record.effective_date and record.expire_date and record.effective_date > record.expire_date:
                raise ValidationError(_("生效日期不能晚于失效日期。"))
