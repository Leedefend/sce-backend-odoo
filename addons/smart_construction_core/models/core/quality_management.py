# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


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
    default_rechecker_id = fields.Many2one("res.users", string="默认复验人", index=True)
    cc_user_ids = fields.Many2many(
        "res.users",
        "sc_check_standard_cc_user_rel",
        "standard_id",
        "user_id",
        string="默认抄送人",
    )
    import_source = fields.Selection(
        [("manual", "手工维护"), ("excel", "Excel导入"), ("standard_library", "标准库引入"), ("inherit", "逐级继承")],
        string="标准来源",
        default="manual",
        index=True,
    )
    effective_from = fields.Date(string="生效日期", index=True)
    effective_to = fields.Date(string="失效日期", index=True)
    applies_building_room = fields.Boolean(string="适用楼栋房间", default=True)
    applies_road_coordinate = fields.Boolean(string="适用道路坐标")
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
    control_type = fields.Selection([("main", "主控项"), ("general", "一般项"), ("score", "评分项")], string="控制类型", default="general", index=True)
    default_pass = fields.Boolean(string="默认合格")
    measurement_method = fields.Char(string="工程量/实测计算方式")
    acceptance_flow = fields.Selection(
        [("self", "自检"), ("supervisor", "监理验收"), ("owner", "甲方抽验"), ("multi", "多级验收")],
        string="验收流程",
        default="self",
        index=True,
    )
    score_weight = fields.Float(string="评分权重")


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
    source_channel = fields.Selection([("pc", "PC"), ("app", "APP"), ("import", "导入"), ("system", "系统")], string="来源端", default="pc", index=True)
    issue_category = fields.Selection(
        [("quality", "质量检查"), ("process", "工序验收"), ("material", "材料验收"), ("patrol", "巡检评估"), ("photo", "随手拍")],
        string="问题来源场景",
        default="quality",
        index=True,
    )
    location = fields.Char(string="问题部位", index=True)
    building = fields.Char(string="楼栋/道路")
    room = fields.Char(string="房间/坐标描述")
    coordinate = fields.Char(string="坐标")
    issue_level = fields.Selection([("normal", "一般"), ("important", "重要"), ("critical", "重大")], string="问题等级", default="normal", index=True)
    responsible_party_id = fields.Many2one("res.partner", string="责任单位", index=True)
    owner_id = fields.Many2one("res.users", string="责任人", default=lambda self: self.env.user, index=True)
    rechecker_id = fields.Many2one("res.users", string="复验人", index=True)
    cc_user_ids = fields.Many2many(
        "res.users",
        "sc_quality_issue_cc_user_rel",
        "issue_id",
        "user_id",
        string="抄送人",
    )
    rectification_deadline = fields.Date(string="整改期限", index=True)
    reminder_before_days = fields.Integer(string="提前提醒天数")
    overdue_notice_sent = fields.Boolean(string="逾期提醒已发送")
    closed_date = fields.Date(string="闭环日期", index=True)
    overdue_days = fields.Integer(string="逾期天数", compute="_compute_overdue_days", store=True)
    is_overdue = fields.Boolean(string="是否逾期", compute="_compute_overdue_days", store=True, index=True)
    description = fields.Text(string="问题描述")
    voice_text = fields.Text(string="语音转文字")
    attachment_ids = fields.Many2many("ir.attachment", "sc_quality_issue_attachment_rel", "issue_id", "attachment_id", string="问题附件")
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
        for issue in self:
            if issue.state != "draft":
                raise UserError(_("只有草稿状态的质量问题可以提交。"))
            issue._check_business_anchor()
        snapshots = {issue.id: issue._snapshot_audit_payload() for issue in self}
        self.write({"state": "submitted"})
        for issue in self:
            issue._audit_transition("quality_issue_submitted", snapshots[issue.id], issue._snapshot_audit_payload(), "action_submit")
        return True

    def action_start_rectification(self):
        for issue in self:
            if issue.state != "submitted":
                raise UserError(_("只有已提交状态的质量问题可以开始整改。"))
        snapshots = {issue.id: issue._snapshot_audit_payload() for issue in self}
        self.write({"state": "rectifying"})
        for issue in self:
            issue._audit_transition("quality_rectification_started", snapshots[issue.id], issue._snapshot_audit_payload(), "action_start_rectification")
        return True

    def action_request_recheck(self):
        for issue in self:
            if issue.state != "rectifying":
                raise UserError(_("只有整改中的质量问题可以申请复验。"))
            if not issue.rectification_ids:
                raise UserError(_("申请复验前必须登记整改记录。"))
        snapshots = {issue.id: issue._snapshot_audit_payload() for issue in self}
        self.write({"state": "rechecking"})
        for issue in self:
            issue._audit_transition("quality_recheck_requested", snapshots[issue.id], issue._snapshot_audit_payload(), "action_request_recheck")
        return True

    def action_close(self):
        for issue in self:
            if issue.state != "rechecking":
                raise UserError(_("只有待复验状态的质量问题可以闭环。"))
            if not issue.recheck_ids.filtered(lambda recheck: recheck.result == "passed"):
                raise UserError(_("质量问题闭环前必须有通过的复验记录。"))
        snapshots = {issue.id: issue._snapshot_audit_payload() for issue in self}
        self.write({"state": "closed", "closed_date": fields.Date.context_today(self)})
        for issue in self:
            issue._audit_transition("quality_issue_closed", snapshots[issue.id], issue._snapshot_audit_payload(), "action_close")
        return True

    def action_cancel(self):
        for issue in self:
            if issue.state not in ("draft", "submitted", "rectifying", "rechecking"):
                raise UserError(_("只有未闭环的质量问题可以取消。"))
        snapshots = {issue.id: issue._snapshot_audit_payload() for issue in self}
        self.write({"state": "cancel"})
        for issue in self:
            issue._audit_transition("quality_issue_cancelled", snapshots[issue.id], issue._snapshot_audit_payload(), "action_cancel")
        return True

    def _check_business_anchor(self):
        for issue in self:
            if not issue.location and not issue.description:
                raise UserError(_("质量问题提交前必须维护问题部位或问题描述。"))

    def _snapshot_audit_payload(self):
        self.ensure_one()
        return {
            "state": self.state,
            "project_id": self.project_id.id,
            "name": self.name,
            "issue_level": self.issue_level,
            "location": self.location,
            "rectification_count": len(self.rectification_ids),
            "recheck_count": len(self.recheck_ids),
            "closed_date": fields.Date.to_string(self.closed_date) if self.closed_date else False,
        }

    def _audit_transition(self, event_code, before, after, action_name):
        self.ensure_one()
        return self.env["sc.audit.log"].write_event(
            event_code=event_code,
            model=self._name,
            res_id=self.id,
            action=action_name,
            before=before,
            after=after,
            project_id=self.project_id,
            company_id=self.project_id.company_id,
        )


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
    source_channel = fields.Selection([("pc", "PC"), ("app", "APP"), ("import", "导入")], string="来源端", default="pc", index=True)
    handler_id = fields.Many2one("res.users", string="整改人", default=lambda self: self.env.user, index=True)
    result = fields.Text(string="整改结果", required=True)
    attachment_ids = fields.Many2many("ir.attachment", "sc_quality_rectification_attachment_rel", "rectification_id", "attachment_id", string="整改附件")
    photo_batch_ids = fields.One2many("sc.site.photo.batch", "quality_rectification_id", string="照片批次")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        invalid_issues = records.mapped("issue_id").filtered(lambda issue: issue.state not in ("submitted", "rectifying"))
        if invalid_issues:
            raise UserError(_("只有已提交或整改中的质量问题可以登记整改。"))
        submitted_issues = records.mapped("issue_id").filtered(lambda issue: issue.state == "submitted")
        snapshots = {issue.id: issue._snapshot_audit_payload() for issue in submitted_issues}
        submitted_issues.write({"state": "rectifying"})
        for issue in submitted_issues:
            issue._audit_transition(
                "quality_rectification_started",
                snapshots[issue.id],
                issue._snapshot_audit_payload(),
                "quality_rectification_create",
            )
        for record in records:
            issue = record.issue_id
            self.env["sc.audit.log"].write_event(
                event_code="quality_rectification_registered",
                model=record._name,
                res_id=record.id,
                action="create",
                after={"issue_id": issue.id, "issue_state": issue.state, "project_id": issue.project_id.id},
                project_id=issue.project_id,
                company_id=issue.project_id.company_id,
            )
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
    source_channel = fields.Selection([("pc", "PC"), ("app", "APP"), ("import", "导入")], string="来源端", default="pc", index=True)
    recheck_user_id = fields.Many2one("res.users", string="复验人", default=lambda self: self.env.user, index=True)
    result = fields.Selection([("passed", "通过"), ("failed", "不通过")], string="复验结果", required=True, index=True)
    comment = fields.Text(string="复验意见")
    attachment_ids = fields.Many2many("ir.attachment", "sc_quality_recheck_attachment_rel", "recheck_id", "attachment_id", string="复验附件")
    photo_batch_ids = fields.One2many("sc.site.photo.batch", "quality_recheck_id", string="照片批次")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.issue_id.state != "rechecking":
                raise UserError(_("只有待复验的质量问题可以登记复验。"))
            before = record.issue_id._snapshot_audit_payload()
            if record.result == "passed":
                record.issue_id.write({"state": "closed", "closed_date": fields.Date.context_today(record)})
                event_code = "quality_issue_closed"
            elif record.result == "failed":
                record.issue_id.write({"state": "rectifying"})
                event_code = "quality_recheck_failed"
            else:
                event_code = "quality_recheck_registered"
            after = record.issue_id._snapshot_audit_payload()
            self.env["sc.audit.log"].write_event(
                event_code="quality_recheck_registered",
                model=record._name,
                res_id=record.id,
                action="create",
                after={"issue_id": record.issue_id.id, "result": record.result, "issue_state": record.issue_id.state},
                project_id=record.issue_id.project_id,
                company_id=record.issue_id.project_id.company_id,
            )
            record.issue_id._audit_transition(event_code, before, after, "quality_recheck_create")
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
    source_channel = fields.Selection([("pc", "PC"), ("app", "APP"), ("import", "导入")], string="来源端", default="app", index=True)
    album_category = fields.Selection(
        [("quick_photo", "随手拍"), ("meeting_review", "会议回顾"), ("inspection", "检查留痕"), ("rectification", "整改留痕"), ("recheck", "复验留痕")],
        string="相册分类",
        default="inspection",
        index=True,
    )
    attachment_ids = fields.Many2many("ir.attachment", string="照片附件")
    note = fields.Text(string="说明")

    def unlink(self):
        if self.mapped("quality_issue_id").filtered(lambda issue: issue.state == "closed"):
            raise ValidationError(_("已闭环质量问题的照片批次不允许删除。"))
        if self.mapped("safety_issue_id").filtered(lambda issue: issue.state == "closed"):
            raise ValidationError(_("已闭环安全问题的照片批次不允许删除。"))
        return super().unlink()
