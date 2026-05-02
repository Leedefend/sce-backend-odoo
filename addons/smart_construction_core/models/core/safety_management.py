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
    approval_deadline = fields.Date(string="审批时限", index=True)
    copied_user_ids = fields.Many2many(
        "res.users",
        "sc_safety_plan_copied_user_rel",
        "plan_id",
        "user_id",
        string="抄送人",
    )
    attachment_ids = fields.Many2many("ir.attachment", "sc_safety_plan_attachment_rel", "plan_id", "attachment_id", string="方案附件")
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
    approval_deadline = fields.Date(string="确认时限", index=True)
    owner_id = fields.Many2one("res.users", string="交底人", default=lambda self: self.env.user, index=True)
    copied_user_ids = fields.Many2many(
        "res.users",
        "sc_safety_disclosure_copied_user_rel",
        "disclosure_id",
        "user_id",
        string="抄送人",
    )
    participant_note = fields.Text(string="交底对象")
    content = fields.Text(string="交底内容")
    attachment_ids = fields.Many2many("ir.attachment", "sc_safety_disclosure_attachment_rel", "disclosure_id", "attachment_id", string="交底附件")
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
    library_level = fields.Selection([("group", "集团"), ("company", "公司"), ("project", "项目")], string="风险库层级", default="company", index=True)
    version_no = fields.Char(string="版本号")
    active = fields.Boolean(default=True)
    item_ids = fields.One2many("sc.risk.item", "library_id", string="风险项")


class ScRiskItem(models.Model):
    _name = "sc.risk.item"
    _description = "风险项"
    _order = "library_id, risk_level, id"

    library_id = fields.Many2one("sc.risk.library", string="风险库", required=True, ondelete="cascade", index=True)
    name = fields.Char(string="风险名称", required=True)
    category = fields.Char(string="风险分类", index=True)
    subcategory = fields.Char(string="风险子类", index=True)
    risk_level = fields.Selection([("low", "低"), ("medium", "中"), ("high", "高"), ("critical", "重大")], string="风险等级", default="medium", index=True)
    control_measure = fields.Text(string="管控措施")
    group_attention = fields.Boolean(string="集团重点关注")
    qualification_required = fields.Char(string="所需资质")
    bottom_line = fields.Boolean(string="底线风险")


class ScHazardSource(models.Model):
    _name = "sc.hazard.source"
    _description = "危险源"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "valid_to desc, id desc"

    name = fields.Char(string="危险源名称", required=True, tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    risk_item_id = fields.Many2one("sc.risk.item", string="风险项", index=True)
    location = fields.Char(string="位置", index=True)
    coordinate = fields.Char(string="坐标")
    valid_from = fields.Date(string="有效期开始")
    valid_to = fields.Date(string="有效期结束", index=True)
    owner_id = fields.Many2one("res.users", string="责任人", default=lambda self: self.env.user, index=True)
    reporter_id = fields.Many2one("res.users", string="上报人", default=lambda self: self.env.user, index=True)
    control_status = fields.Selection([("uncontrolled", "未管控"), ("controlled", "已管控"), ("expired", "已过期")], string="管控状态", default="uncontrolled", index=True)
    attachment_ids = fields.Many2many("ir.attachment", "sc_hazard_source_attachment_rel", "hazard_id", "attachment_id", string="现场附件")
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
    source_channel = fields.Selection([("pc", "PC"), ("app", "APP"), ("import", "导入"), ("system", "系统")], string="来源端", default="pc", index=True)
    issue_category = fields.Selection(
        [("check", "安全检查"), ("patrol", "安全巡检"), ("disclosure", "交底问题"), ("photo", "随手拍"), ("emergency", "应急管理")],
        string="问题来源场景",
        default="check",
        index=True,
    )
    location = fields.Char(string="问题位置", index=True)
    coordinate = fields.Char(string="坐标")
    issue_level = fields.Selection([("normal", "一般"), ("important", "重要"), ("critical", "重大")], string="问题等级", default="normal", index=True)
    responsible_party_id = fields.Many2one("res.partner", string="责任单位", index=True)
    owner_id = fields.Many2one("res.users", string="责任人", default=lambda self: self.env.user, index=True)
    rechecker_id = fields.Many2one("res.users", string="复验人", index=True)
    cc_user_ids = fields.Many2many("res.users", "sc_safety_issue_cc_user_rel", "issue_id", "user_id", string="抄送人")
    rectification_deadline = fields.Date(string="整改期限", index=True)
    reminder_before_days = fields.Integer(string="提前提醒天数")
    overdue_notice_sent = fields.Boolean(string="逾期提醒已发送")
    closed_date = fields.Date(string="闭环日期", index=True)
    overdue_days = fields.Integer(string="逾期天数", compute="_compute_overdue_days", store=True)
    is_overdue = fields.Boolean(string="是否逾期", compute="_compute_overdue_days", store=True, index=True)
    description = fields.Text(string="问题描述")
    voice_text = fields.Text(string="语音转文字")
    attachment_ids = fields.Many2many("ir.attachment", "sc_safety_issue_attachment_rel", "issue_id", "attachment_id", string="问题附件")
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

    @api.depends("state", "rectification_deadline", "closed_date")
    def _compute_overdue_days(self):
        today = fields.Date.context_today(self)
        for issue in self:
            end_date = issue.closed_date or today
            if issue.rectification_deadline and issue.state != "cancel" and end_date > issue.rectification_deadline:
                issue.overdue_days = (end_date - issue.rectification_deadline).days
                issue.is_overdue = issue.state != "closed" or bool(issue.closed_date and issue.closed_date > issue.rectification_deadline)
            else:
                issue.overdue_days = 0
                issue.is_overdue = False

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
        self.write({"state": "closed", "closed_date": fields.Date.context_today(self)})
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
    source_channel = fields.Selection([("pc", "PC"), ("app", "APP"), ("import", "导入")], string="来源端", default="pc", index=True)
    handler_id = fields.Many2one("res.users", string="整改人", default=lambda self: self.env.user, index=True)
    result = fields.Text(string="整改结果", required=True)
    attachment_ids = fields.Many2many("ir.attachment", "sc_safety_rectification_attachment_rel", "rectification_id", "attachment_id", string="整改附件")
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
    source_channel = fields.Selection([("pc", "PC"), ("app", "APP"), ("import", "导入")], string="来源端", default="pc", index=True)
    recheck_user_id = fields.Many2one("res.users", string="复验人", default=lambda self: self.env.user, index=True)
    result = fields.Selection([("passed", "通过"), ("failed", "不通过")], string="复验结果", required=True, index=True)
    comment = fields.Text(string="复验意见")
    attachment_ids = fields.Many2many("ir.attachment", "sc_safety_recheck_attachment_rel", "recheck_id", "attachment_id", string="复验附件")
    photo_batch_ids = fields.One2many("sc.site.photo.batch", "safety_recheck_id", string="照片批次")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.result == "passed":
                record.issue_id.write({"state": "closed", "closed_date": fields.Date.context_today(record)})
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
    patrol_type = fields.Selection([("routine", "常规巡检"), ("third_party", "第三方评估"), ("special", "专项巡检")], string="巡检类型", default="routine", index=True)
    check_standard_id = fields.Many2one("sc.check.standard", string="检查模板", index=True)
    owner_id = fields.Many2one("res.users", string="巡检人", default=lambda self: self.env.user, index=True)
    member_ids = fields.Many2many("res.users", "sc_safety_patrol_member_rel", "task_id", "user_id", string="巡检成员")
    planned_scope = fields.Char(string="巡检范围")
    score = fields.Float(string="得分")
    pass_rate = fields.Float(string="合格率(%)")
    state = fields.Selection([("draft", "草稿"), ("planned", "已计划"), ("done", "已完成"), ("cancel", "已取消")], string="状态", default="draft", index=True)
    note = fields.Text(string="说明")
