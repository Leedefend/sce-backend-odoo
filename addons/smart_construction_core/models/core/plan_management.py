# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScPlan(models.Model):
    _name = "sc.plan"
    _description = "计划"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "planned_start desc, id desc"

    name = fields.Char(string="计划名称", required=True, tracking=True)
    plan_type = fields.Selection(
        [
            ("key_node", "关键节点计划"),
            ("master", "项目主项计划"),
            ("special", "项目专项计划"),
            ("company_special", "公司专项计划"),
            ("organization", "组织计划"),
        ],
        string="计划类型",
        required=True,
        default="master",
        index=True,
        tracking=True,
    )
    project_id = fields.Many2one("project.project", string="项目", index=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    owner_id = fields.Many2one("res.users", string="责任人", default=lambda self: self.env.user, index=True)
    department_id = fields.Many2one("hr.department", string="责任部门", index=True)
    planned_start = fields.Date(string="计划开始", index=True)
    planned_finish = fields.Date(string="计划完成", index=True)
    actual_start = fields.Date(string="实际开始", index=True)
    actual_finish = fields.Date(string="实际完成", index=True)
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("in_progress", "执行中"),
            ("done", "已完成"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        required=True,
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.plan.line", "plan_id", string="计划节点")
    version_ids = fields.One2many("sc.plan.version", "plan_id", string="计划版本")
    report_ids = fields.One2many("sc.plan.report", "plan_id", string="汇报")
    progress_rate = fields.Float(string="完成率(%)", compute="_compute_progress_rate", store=True)
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)
    note = fields.Text(string="说明")

    @api.depends("line_ids.progress_rate")
    def _compute_progress_rate(self):
        for plan in self:
            lines = plan.line_ids
            plan.progress_rate = sum(lines.mapped("progress_rate")) / len(lines) if lines else 0.0

    @api.constrains("planned_start", "planned_finish", "actual_start", "actual_finish")
    def _check_date_order(self):
        for rec in self:
            if rec.planned_start and rec.planned_finish and rec.planned_start > rec.planned_finish:
                raise ValidationError(_("计划开始不能晚于计划完成。"))
            if rec.actual_start and rec.actual_finish and rec.actual_start > rec.actual_finish:
                raise ValidationError(_("实际开始不能晚于实际完成。"))

    def action_confirm(self):
        self.write({"state": "confirmed"})
        return True

    def action_start(self):
        self.write({"state": "in_progress", "actual_start": fields.Date.context_today(self)})
        return True

    def action_done(self):
        self.write({"state": "done", "actual_finish": fields.Date.context_today(self)})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True


class ScPlanLine(models.Model):
    _name = "sc.plan.line"
    _description = "计划节点"
    _parent_name = "parent_id"
    _parent_store = True
    _order = "plan_id, sequence, id"

    plan_id = fields.Many2one("sc.plan", string="计划", required=True, ondelete="cascade", index=True)
    parent_id = fields.Many2one("sc.plan.line", string="上级节点", index=True, ondelete="cascade")
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many("sc.plan.line", "parent_id", string="子节点")
    sequence = fields.Integer(default=10)
    name = fields.Char(string="节点名称", required=True)
    owner_id = fields.Many2one("res.users", string="责任人", index=True)
    planned_start = fields.Date(string="计划开始", index=True)
    planned_finish = fields.Date(string="计划完成", index=True)
    actual_start = fields.Date(string="实际开始", index=True)
    actual_finish = fields.Date(string="实际完成", index=True)
    completion_standard = fields.Text(string="完成标准")
    progress_rate = fields.Float(string="完成率(%)")
    state = fields.Selection(
        [("draft", "未开始"), ("in_progress", "执行中"), ("done", "已完成"), ("blocked", "受阻"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
    )
    predecessor_ids = fields.Many2many(
        "sc.plan.line",
        "sc_plan_line_predecessor_rel",
        "line_id",
        "predecessor_id",
        string="前置节点",
    )
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    @api.constrains("progress_rate")
    def _check_progress_rate(self):
        for rec in self:
            if rec.progress_rate < 0 or rec.progress_rate > 100:
                raise ValidationError(_("完成率必须在 0 到 100 之间。"))


class ScPlanVersion(models.Model):
    _name = "sc.plan.version"
    _description = "计划版本"
    _order = "plan_id, version_no desc, id desc"

    plan_id = fields.Many2one("sc.plan", string="计划", required=True, ondelete="cascade", index=True)
    version_no = fields.Char(string="版本号", required=True)
    version_date = fields.Date(string="版本日期", default=fields.Date.context_today, index=True)
    change_reason = fields.Text(string="修订原因")
    snapshot_note = fields.Text(string="版本说明")
    state = fields.Selection([("draft", "草稿"), ("approved", "已确认")], string="状态", default="draft", index=True)
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("uniq_plan_version_no", "unique(plan_id, version_no)", "同一计划下版本号不能重复。"),
    ]


class ScPlanReport(models.Model):
    _name = "sc.plan.report"
    _description = "计划汇报"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "report_date desc, id desc"

    name = fields.Char(string="汇报标题", required=True, default="计划汇报")
    plan_id = fields.Many2one("sc.plan", string="计划", required=True, ondelete="cascade", index=True)
    line_id = fields.Many2one("sc.plan.line", string="计划节点", index=True)
    reporter_id = fields.Many2one("res.users", string="汇报人", default=lambda self: self.env.user, index=True)
    report_date = fields.Date(string="汇报日期", default=fields.Date.context_today, index=True)
    progress_rate = fields.Float(string="汇报完成率(%)")
    summary = fields.Text(string="完成情况")
    risk_note = fields.Text(string="风险说明")
    state = fields.Selection([("draft", "草稿"), ("submitted", "已提交"), ("accepted", "已确认")], default="draft", string="状态", index=True)
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    @api.constrains("progress_rate")
    def _check_progress_rate(self):
        for rec in self:
            if rec.progress_rate < 0 or rec.progress_rate > 100:
                raise ValidationError(_("汇报完成率必须在 0 到 100 之间。"))


class ScPlanWarningLog(models.Model):
    _name = "sc.plan.warning.log"
    _description = "计划预警日志"
    _order = "warning_date desc, id desc"

    plan_id = fields.Many2one("sc.plan", string="计划", required=True, ondelete="cascade", index=True)
    line_id = fields.Many2one("sc.plan.line", string="计划节点", index=True)
    warning_type = fields.Selection(
        [("due_soon", "即将逾期"), ("overdue", "已逾期"), ("risk", "风险预警")],
        string="预警类型",
        required=True,
        index=True,
    )
    warning_date = fields.Date(string="预警日期", default=fields.Date.context_today, index=True)
    owner_id = fields.Many2one("res.users", string="责任人", index=True)
    message = fields.Text(string="预警内容")
    state = fields.Selection([("open", "未处理"), ("closed", "已关闭")], string="状态", default="open", index=True)
