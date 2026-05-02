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
