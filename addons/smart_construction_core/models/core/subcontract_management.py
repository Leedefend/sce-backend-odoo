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
