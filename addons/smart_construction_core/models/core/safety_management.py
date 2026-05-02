# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ScSafetyPlan(models.Model):
    _name = "sc.safety.plan"
    _description = "安全施工方案"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "plan_date desc, id desc"

    name = fields.Char(string="方案名称", required=True, tracking=True)
    plan_type = fields.Selection(
        [("general", "分部分项"), ("civilized", "安全文明"), ("dangerous", "危大工程"), ("environment", "环保"), ("epidemic", "防疫")],
        string="方案类型",
        required=True,
        default="general",
        index=True,
    )
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    owner_id = fields.Many2one("res.users", string="负责人", default=lambda self: self.env.user, index=True)
    plan_date = fields.Date(string="编制日期", default=fields.Date.context_today, index=True)
    state = fields.Selection([("draft", "草稿"), ("submitted", "已提交"), ("approved", "已审批"), ("cancel", "已取消")], default="draft", string="状态", index=True, tracking=True)
    description = fields.Text(string="方案说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    def action_submit(self):
        self.write({"state": "submitted"})
        return True

    def action_approve(self):
        self.write({"state": "approved"})
        return True


class ScSafetyDisclosure(models.Model):
    _name = "sc.safety.disclosure"
    _description = "安全交底"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "disclosure_date desc, id desc"

    name = fields.Char(string="交底主题", required=True, tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    safety_plan_id = fields.Many2one("sc.safety.plan", string="关联方案", index=True)
    disclosure_date = fields.Date(string="交底日期", default=fields.Date.context_today, index=True)
    owner_id = fields.Many2one("res.users", string="交底人", default=lambda self: self.env.user, index=True)
    participant_note = fields.Text(string="交底对象")
    content = fields.Text(string="交底内容")
    state = fields.Selection([("draft", "草稿"), ("submitted", "已提交"), ("approved", "已确认"), ("cancel", "已取消")], default="draft", string="状态", index=True)
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)


class ScRiskLibrary(models.Model):
    _name = "sc.risk.library"
    _description = "风险库"
    _order = "name"

    name = fields.Char(string="风险库名称", required=True)
    company_id = fields.Many2one("res.company", string="公司", default=lambda self: self.env.company, index=True)
    active = fields.Boolean(default=True)
    item_ids = fields.One2many("sc.risk.item", "library_id", string="风险项")


class ScRiskItem(models.Model):
    _name = "sc.risk.item"
    _description = "风险项"
    _order = "library_id, risk_level, id"

    library_id = fields.Many2one("sc.risk.library", string="风险库", required=True, ondelete="cascade", index=True)
    name = fields.Char(string="风险名称", required=True)
    category = fields.Char(string="风险分类", index=True)
    risk_level = fields.Selection([("low", "低"), ("medium", "中"), ("high", "高"), ("critical", "重大")], string="风险等级", default="medium", index=True)
    control_measure = fields.Text(string="管控措施")
    group_attention = fields.Boolean(string="集团重点关注")


class ScHazardSource(models.Model):
    _name = "sc.hazard.source"
    _description = "危险源"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "valid_to desc, id desc"

    name = fields.Char(string="危险源名称", required=True, tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    risk_item_id = fields.Many2one("sc.risk.item", string="风险项", index=True)
    location = fields.Char(string="位置", index=True)
    valid_from = fields.Date(string="有效期开始")
    valid_to = fields.Date(string="有效期结束", index=True)
    owner_id = fields.Many2one("res.users", string="责任人", default=lambda self: self.env.user, index=True)
    state = fields.Selection([("draft", "草稿"), ("reported", "已上报"), ("controlled", "已管控"), ("closed", "已关闭")], default="draft", string="状态", index=True)
    description = fields.Text(string="说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)


class ScSafetyIssue(models.Model):
    _name = "sc.safety.issue"
    _description = "安全问题"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "issue_date desc, id desc"

    name = fields.Char(string="问题标题", required=True, tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    hazard_source_id = fields.Many2one("sc.hazard.source", string="关联危险源", index=True)
    issue_date = fields.Date(string="发现日期", default=fields.Date.context_today, index=True)
    location = fields.Char(string="问题位置", index=True)
    issue_level = fields.Selection([("normal", "一般"), ("important", "重要"), ("critical", "重大")], string="问题等级", default="normal", index=True)
    responsible_party_id = fields.Many2one("res.partner", string="责任单位", index=True)
    owner_id = fields.Many2one("res.users", string="责任人", default=lambda self: self.env.user, index=True)
    rectification_deadline = fields.Date(string="整改期限", index=True)
    description = fields.Text(string="问题描述")
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("rectifying", "整改中"), ("rechecking", "待复验"), ("closed", "已闭环"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    rectification_ids = fields.One2many("sc.safety.rectification", "issue_id", string="整改记录")
    recheck_ids = fields.One2many("sc.safety.recheck", "issue_id", string="复验记录")
    photo_batch_ids = fields.One2many("sc.site.photo.batch", "safety_issue_id", string="照片批次")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    def action_submit(self):
        self.write({"state": "submitted"})
        return True

    def action_start_rectification(self):
        self.write({"state": "rectifying"})
        return True

    def action_request_recheck(self):
        self.write({"state": "rechecking"})
        return True

    def action_close(self):
        self.write({"state": "closed"})
        return True


class ScSafetyRectification(models.Model):
    _name = "sc.safety.rectification"
    _description = "安全整改"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "rectification_date desc, id desc"

    issue_id = fields.Many2one("sc.safety.issue", string="安全问题", required=True, ondelete="cascade", index=True)
    name = fields.Char(string="整改标题", related="issue_id.name", store=True)
    project_id = fields.Many2one("project.project", string="项目", related="issue_id.project_id", store=True, index=True)
    issue_level = fields.Selection(related="issue_id.issue_level", string="问题等级", store=True, index=True)
    issue_state = fields.Selection(related="issue_id.state", string="问题状态", store=True, index=True)
    responsible_party_id = fields.Many2one("res.partner", string="责任单位", related="issue_id.responsible_party_id", store=True, index=True)
    rectification_deadline = fields.Date(string="整改期限", related="issue_id.rectification_deadline", store=True, index=True)
    rectification_date = fields.Date(string="整改日期", default=fields.Date.context_today, index=True)
    handler_id = fields.Many2one("res.users", string="整改人", default=lambda self: self.env.user, index=True)
    result = fields.Text(string="整改结果", required=True)
    photo_batch_ids = fields.One2many("sc.site.photo.batch", "safety_rectification_id", string="照片批次")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.mapped("issue_id").filtered(lambda issue: issue.state in ("draft", "submitted")).write({"state": "rectifying"})
        return records


class ScSafetyRecheck(models.Model):
    _name = "sc.safety.recheck"
    _description = "安全复验"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "recheck_date desc, id desc"

    issue_id = fields.Many2one("sc.safety.issue", string="安全问题", required=True, ondelete="cascade", index=True)
    name = fields.Char(string="复验标题", related="issue_id.name", store=True)
    project_id = fields.Many2one("project.project", string="项目", related="issue_id.project_id", store=True, index=True)
    issue_level = fields.Selection(related="issue_id.issue_level", string="问题等级", store=True, index=True)
    issue_state = fields.Selection(related="issue_id.state", string="问题状态", store=True, index=True)
    responsible_party_id = fields.Many2one("res.partner", string="责任单位", related="issue_id.responsible_party_id", store=True, index=True)
    recheck_date = fields.Date(string="复验日期", default=fields.Date.context_today, index=True)
    recheck_user_id = fields.Many2one("res.users", string="复验人", default=lambda self: self.env.user, index=True)
    result = fields.Selection([("passed", "通过"), ("failed", "不通过")], string="复验结果", required=True, index=True)
    comment = fields.Text(string="复验意见")
    photo_batch_ids = fields.One2many("sc.site.photo.batch", "safety_recheck_id", string="照片批次")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.result == "passed":
                record.issue_id.write({"state": "closed"})
            elif record.result == "failed":
                record.issue_id.write({"state": "rectifying"})
        return records


class ScSafetyPatrolTask(models.Model):
    _name = "sc.safety.patrol.task"
    _description = "安全巡检任务"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "planned_date desc, id desc"

    name = fields.Char(string="巡检任务", required=True, tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    planned_date = fields.Date(string="计划巡检日期", index=True)
    owner_id = fields.Many2one("res.users", string="巡检人", default=lambda self: self.env.user, index=True)
    state = fields.Selection([("draft", "草稿"), ("planned", "已计划"), ("done", "已完成"), ("cancel", "已取消")], string="状态", default="draft", index=True)
    note = fields.Text(string="说明")
