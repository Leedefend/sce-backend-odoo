# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScCheckStandard(models.Model):
    _name = "sc.check.standard"
    _description = "检查标准"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "scope, name"

    name = fields.Char(string="标准名称", required=True, tracking=True)
    standard_type = fields.Selection(
        [("quality", "质量"), ("safety", "安全"), ("process", "工序"), ("material", "材料"), ("measurement", "实测实量")],
        string="标准类型",
        required=True,
        default="quality",
        index=True,
    )
    scope = fields.Selection([("group", "集团"), ("company", "公司"), ("project", "项目")], string="适用层级", default="company", index=True)
    company_id = fields.Many2one("res.company", string="公司", default=lambda self: self.env.company, index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True)
    parent_id = fields.Many2one("sc.check.standard", string="继承来源", index=True)
    active = fields.Boolean(default=True)
    item_ids = fields.One2many("sc.check.standard.item", "standard_id", string="检查项")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)


class ScCheckStandardItem(models.Model):
    _name = "sc.check.standard.item"
    _description = "检查标准项"
    _order = "standard_id, sequence, id"

    standard_id = fields.Many2one("sc.check.standard", string="检查标准", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string="检查项", required=True)
    requirement = fields.Text(string="检查要求")
    bottom_line = fields.Boolean(string="底线项", default=False)
    tag = fields.Char(string="标签")
    photo_required = fields.Boolean(string="要求拍照", default=False)


class ScQualityIssue(models.Model):
    _name = "sc.quality.issue"
    _description = "质量问题"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "issue_date desc, id desc"

    name = fields.Char(string="问题标题", required=True, tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    standard_id = fields.Many2one("sc.check.standard", string="检查标准", index=True)
    standard_item_id = fields.Many2one("sc.check.standard.item", string="检查项", index=True)
    issue_date = fields.Date(string="发现日期", default=fields.Date.context_today, index=True)
    location = fields.Char(string="问题部位", index=True)
    building = fields.Char(string="楼栋/道路")
    room = fields.Char(string="房间/坐标描述")
    issue_level = fields.Selection([("normal", "一般"), ("important", "重要"), ("critical", "重大")], string="问题等级", default="normal", index=True)
    responsible_party_id = fields.Many2one("res.partner", string="责任单位", index=True)
    owner_id = fields.Many2one("res.users", string="责任人", default=lambda self: self.env.user, index=True)
    rectification_deadline = fields.Date(string="整改期限", index=True)
    description = fields.Text(string="问题描述")
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submitted", "已提交"),
            ("rectifying", "整改中"),
            ("rechecking", "待复验"),
            ("closed", "已闭环"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    rectification_ids = fields.One2many("sc.quality.rectification", "issue_id", string="整改记录")
    recheck_ids = fields.One2many("sc.quality.recheck", "issue_id", string="复验记录")
    photo_batch_ids = fields.One2many("sc.site.photo.batch", "quality_issue_id", string="照片批次")
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

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True


class ScQualityRectification(models.Model):
    _name = "sc.quality.rectification"
    _description = "质量整改"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "rectification_date desc, id desc"

    issue_id = fields.Many2one("sc.quality.issue", string="质量问题", required=True, ondelete="cascade", index=True)
    name = fields.Char(string="整改标题", related="issue_id.name", store=True)
    project_id = fields.Many2one("project.project", string="项目", related="issue_id.project_id", store=True, index=True)
    issue_level = fields.Selection(related="issue_id.issue_level", string="问题等级", store=True, index=True)
    issue_state = fields.Selection(related="issue_id.state", string="问题状态", store=True, index=True)
    responsible_party_id = fields.Many2one("res.partner", string="责任单位", related="issue_id.responsible_party_id", store=True, index=True)
    rectification_deadline = fields.Date(string="整改期限", related="issue_id.rectification_deadline", store=True, index=True)
    rectification_date = fields.Date(string="整改日期", default=fields.Date.context_today, index=True)
    handler_id = fields.Many2one("res.users", string="整改人", default=lambda self: self.env.user, index=True)
    result = fields.Text(string="整改结果", required=True)
    photo_batch_ids = fields.One2many("sc.site.photo.batch", "quality_rectification_id", string="照片批次")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.mapped("issue_id").filtered(lambda issue: issue.state in ("draft", "submitted")).write({"state": "rectifying"})
        return records


class ScQualityRecheck(models.Model):
    _name = "sc.quality.recheck"
    _description = "质量复验"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "recheck_date desc, id desc"

    issue_id = fields.Many2one("sc.quality.issue", string="质量问题", required=True, ondelete="cascade", index=True)
    name = fields.Char(string="复验标题", related="issue_id.name", store=True)
    project_id = fields.Many2one("project.project", string="项目", related="issue_id.project_id", store=True, index=True)
    issue_level = fields.Selection(related="issue_id.issue_level", string="问题等级", store=True, index=True)
    issue_state = fields.Selection(related="issue_id.state", string="问题状态", store=True, index=True)
    responsible_party_id = fields.Many2one("res.partner", string="责任单位", related="issue_id.responsible_party_id", store=True, index=True)
    recheck_date = fields.Date(string="复验日期", default=fields.Date.context_today, index=True)
    recheck_user_id = fields.Many2one("res.users", string="复验人", default=lambda self: self.env.user, index=True)
    result = fields.Selection([("passed", "通过"), ("failed", "不通过")], string="复验结果", required=True, index=True)
    comment = fields.Text(string="复验意见")
    photo_batch_ids = fields.One2many("sc.site.photo.batch", "quality_recheck_id", string="照片批次")
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


class ScSitePhotoBatch(models.Model):
    _name = "sc.site.photo.batch"
    _description = "现场照片批次"
    _order = "batch_date desc, id desc"

    name = fields.Char(string="批次名称", required=True)
    project_id = fields.Many2one("project.project", string="项目", index=True)
    evidence_stage = fields.Selection(
        [("check", "检查"), ("rectification", "整改"), ("recheck", "复验"), ("other", "其他")],
        string="证据阶段",
        default="check",
        required=True,
        index=True,
    )
    quality_issue_id = fields.Many2one("sc.quality.issue", string="质量问题", index=True)
    quality_rectification_id = fields.Many2one("sc.quality.rectification", string="质量整改", index=True)
    quality_recheck_id = fields.Many2one("sc.quality.recheck", string="质量复验", index=True)
    safety_issue_id = fields.Many2one("sc.safety.issue", string="安全问题", index=True)
    safety_rectification_id = fields.Many2one("sc.safety.rectification", string="安全整改", index=True)
    safety_recheck_id = fields.Many2one("sc.safety.recheck", string="安全复验", index=True)
    batch_date = fields.Date(string="批次日期", default=fields.Date.context_today, index=True)
    owner_id = fields.Many2one("res.users", string="上传人", default=lambda self: self.env.user, index=True)
    location = fields.Char(string="拍摄位置")
    attachment_ids = fields.Many2many("ir.attachment", string="照片附件")
    note = fields.Text(string="说明")

    def unlink(self):
        if self.mapped("quality_issue_id").filtered(lambda issue: issue.state == "closed"):
            raise ValidationError(_("已闭环质量问题的照片批次不允许删除。"))
        if self.mapped("safety_issue_id").filtered(lambda issue: issue.state == "closed"):
            raise ValidationError(_("已闭环安全问题的照片批次不允许删除。"))
        return super().unlink()
