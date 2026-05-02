# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
            if not record.line_ids:
                raise ValidationError(_("提交设备计划前必须维护计划明细。"))
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
