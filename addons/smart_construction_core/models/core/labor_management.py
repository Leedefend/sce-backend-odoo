# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScAttendanceCheckin(models.Model):
    _name = "sc.attendance.checkin"
    _description = "考勤记录"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "attendance_date desc, id desc"

    name = fields.Char(string="考勤单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    attendance_date = fields.Date(string="考勤日期", required=True, default=fields.Date.context_today, index=True, tracking=True)
    labor_team = fields.Char(string="班组", required=True, index=True)
    work_content = fields.Char(string="作业内容", required=True)
    attendance_qty = fields.Float(string="出勤人数", required=True, default=1)
    work_hours = fields.Float(string="工时")
    contractor_id = fields.Many2one("res.partner", string="劳务单位", index=True)
    recorder_id = fields.Many2one("res.users", string="记录人", default=lambda self: self.env.user, index=True)
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("confirmed", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    note = fields.Text(string="考勤说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_attendance_checkin_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用考勤记录已迁移为专业考勤记录。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.attendance.checkin") or _("考勤记录")
        return super().create(vals_list)

    def action_submit(self):
        self._check_values()
        self.write({"state": "submitted"})
        return True

    def action_confirm(self):
        self._check_values()
        self.write({"state": "confirmed"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True

    @api.constrains("attendance_qty", "work_hours")
    def _check_values(self):
        for record in self:
            if record.attendance_qty <= 0:
                raise ValidationError(_("出勤人数必须大于0。"))
            if record.work_hours < 0:
                raise ValidationError(_("工时不能为负数。"))


class ScLaborUsage(models.Model):
    _name = "sc.labor.usage"
    _description = "劳务用工"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "usage_date desc, id desc"

    name = fields.Char(string="用工单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    usage_date = fields.Date(string="用工日期", required=True, default=fields.Date.context_today, index=True, tracking=True)
    labor_team = fields.Char(string="班组", required=True, index=True)
    contractor_id = fields.Many2one("res.partner", string="劳务单位", index=True)
    work_content = fields.Char(string="作业内容", required=True)
    worker_qty = fields.Float(string="用工人数", required=True, default=1)
    work_hours = fields.Float(string="工时")
    foreman_name = fields.Char(string="带班人")
    recorder_id = fields.Many2one("res.users", string="记录人", default=lambda self: self.env.user, index=True)
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("confirmed", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    note = fields.Text(string="用工说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_labor_usage_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用劳务用工已迁移为专业劳务用工。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.labor.usage") or _("劳务用工")
        return super().create(vals_list)

    def action_submit(self):
        self._check_values()
        self.write({"state": "submitted"})
        return True

    def action_confirm(self):
        self._check_values()
        self.write({"state": "confirmed"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True

    @api.constrains("worker_qty", "work_hours")
    def _check_values(self):
        for record in self:
            if record.worker_qty <= 0:
                raise ValidationError(_("用工人数必须大于0。"))
            if record.work_hours < 0:
                raise ValidationError(_("工时不能为负数。"))


class ScLaborSettlement(models.Model):
    _name = "sc.labor.settlement"
    _description = "劳务结算"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "settlement_date desc, id desc"

    name = fields.Char(string="结算单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    contractor_id = fields.Many2one("res.partner", string="劳务单位", required=True, index=True, tracking=True)
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
    line_ids = fields.One2many("sc.labor.settlement.line", "settlement_id", string="结算明细")
    note = fields.Text(string="结算说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_labor_settlement_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用劳务结算已迁移为专业劳务结算。"),
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
                vals["name"] = seq.next_by_code("sc.labor.settlement") or _("劳务结算")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if not record.line_ids:
                raise ValidationError(_("提交结算前必须维护结算明细。"))
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


class ScLaborSettlementLine(models.Model):
    _name = "sc.labor.settlement.line"
    _description = "劳务结算明细"
    _order = "settlement_id, sequence, id"

    settlement_id = fields.Many2one("sc.labor.settlement", string="结算单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="settlement_id.project_id", store=True, index=True)
    labor_team = fields.Char(string="班组")
    work_content = fields.Char(string="作业内容", required=True)
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
