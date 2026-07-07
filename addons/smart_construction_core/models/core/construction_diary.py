# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScConstructionDiary(models.Model):
    _name = "sc.construction.diary"
    _description = "施工日志"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_diary desc, id desc"

    name = fields.Char(string="日志编号", required=True, default="新建", copy=False)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("done", "已完成"),
            ("legacy_confirmed", "历史已确认"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        required=True,
        index=True,
    )
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    date_diary = fields.Datetime(string="日志日期", default=fields.Datetime.now, index=True)
    report_period_start = fields.Date(string="报表期间开始", index=True)
    report_period_end = fields.Date(string="报表期间结束", index=True)
    document_no = fields.Char(string="来源单号", index=True)
    title = fields.Char(string="标题", index=True)
    diary_type = fields.Selection(
        [
            ("施工日志", "施工日志"),
            ("日报表", "日报表"),
            ("周报表", "周报表"),
            ("月报表", "月报表"),
        ],
        string="日志类型",
        default="施工日志",
        index=True,
    )
    category = fields.Char(string="分类", index=True)
    construction_unit = fields.Char(string="施工单位", index=True)
    project_manager = fields.Char(string="项目经理", index=True)
    weather = fields.Char(string="天气")
    manpower_count = fields.Integer(string="现场人数")
    attendance_equipment = fields.Text(string="出勤机械")
    quality_name = fields.Char(string="质量/事项", index=True)
    handler_name = fields.Char(string="经办人", index=True)
    description = fields.Text(string="日志内容")
    material_inspection_note = fields.Text(string="材料进场/送检情况")
    design_change_note = fields.Text(string="设计变更或技术核定")
    test_block_note = fields.Text(string="试块制作")
    safety_note = fields.Text(string="安全情况")
    hidden_acceptance_note = fields.Text(string="隐蔽工程验收")
    next_plan = fields.Text(string="下步计划")
    header_description = fields.Text(string="单据说明")
    note = fields.Text(string="备注")
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_header_id = fields.Char(string="历史主表ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    legacy_quality_id = fields.Char(string="历史质量ID", index=True, readonly=True)
    legacy_business_id = fields.Char(string="历史业务ID", index=True, readonly=True)
    legacy_related_business_id = fields.Char(string="历史关联业务ID", index=True, readonly=True)
    legacy_related_quality_type = fields.Char(string="历史质量类型", index=True, readonly=True)
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_construction_diary_attachment_rel",
        "diary_id",
        "attachment_id",
        string="附件",
    )
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "历史施工日志来源记录必须唯一。",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.construction.diary") or _("Construction Diary")
            vals.setdefault("diary_type", "施工日志")
            vals.setdefault("handler_name", self.env.user.name)
            self._sync_project_defaults(vals)
            if not vals.get("title"):
                vals["title"] = self._default_diary_title(vals)
        return super().create(vals_list)

    @api.model
    def _sync_project_defaults(self, vals):
        project_id = vals.get("project_id")
        if not project_id:
            return
        project = self.env["project.project"].browse(int(project_id)).exists()
        if not project:
            return
        if not vals.get("project_manager"):
            vals["project_manager"] = (
                project.manager_id.name
                or getattr(project, "legacy_project_manager_name", False)
                or ""
            )
        if not vals.get("construction_unit"):
            vals["construction_unit"] = (
                project.company_id.name
                or getattr(project, "legacy_company_name", False)
                or ""
            )

    @api.model
    def _default_diary_title(self, vals):
        diary_type = vals.get("diary_type") or _("施工日志")
        date_value = fields.Datetime.to_datetime(vals.get("date_diary")) if vals.get("date_diary") else fields.Datetime.context_timestamp(self, fields.Datetime.now())
        date_label = fields.Date.to_string(date_value.date()) if date_value else fields.Date.context_today(self)
        project_name = ""
        if vals.get("project_id"):
            project = self.env["project.project"].browse(int(vals["project_id"])).exists()
            project_name = project.display_name if project else ""
        parts = [item for item in (project_name, date_label, diary_type) if item]
        return " - ".join(parts) or _("施工日志")

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {"note", "attendance_equipment", "active", "attachment_ids", "write_uid", "write_date"}
            if set(vals) - allowed:
                raise UserError(_("历史迁移施工日志已确认，只允许补充备注和出勤机械。"))
        return super().write(vals)

    @api.onchange("project_id")
    def _onchange_project_id(self):
        for rec in self:
            if not rec.project_id:
                continue
            if not rec.project_manager:
                rec.project_manager = (
                    rec.project_id.manager_id.name
                    or getattr(rec.project_id, "legacy_project_manager_name", False)
                    or ""
                )
            if not rec.construction_unit:
                rec.construction_unit = (
                    rec.project_id.company_id.name
                    or getattr(rec.project_id, "legacy_company_name", False)
                    or ""
                )

    @api.constrains("report_period_start", "report_period_end")
    def _check_report_period_order(self):
        for rec in self:
            if rec.report_period_start and rec.report_period_end and rec.report_period_start > rec.report_period_end:
                raise UserError(_("报表期间开始不能晚于报表期间结束。"))

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿状态的施工日志可以确认。"))
            rec._check_business_ready()
            rec.state = "confirmed"

    def action_done(self):
        for rec in self:
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认状态的施工日志可以完成。"))
            rec._check_business_ready()
            rec.state = "done"

    def _check_business_ready(self):
        self.ensure_one()
        if not self.date_diary:
            raise UserError(_("请先填写日志日期。"))
        if not (self.title or "").strip():
            raise UserError(_("请先填写施工日志标题。"))
        if not (self.diary_type or "").strip():
            raise UserError(_("请先填写日志类型。"))
        if self.manpower_count < 0:
            raise UserError(_("现场人数不能为负数。"))
        content_fields = (
            "description",
            "material_inspection_note",
            "attendance_equipment",
            "design_change_note",
            "test_block_note",
            "safety_note",
            "hidden_acceptance_note",
            "next_plan",
            "header_description",
            "note",
        )
        if not any((self[field_name] or "").strip() for field_name in content_fields):
            raise UserError(_("请至少填写一项施工日志内容。"))

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移施工日志不能在新系统取消。"))
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认状态的施工日志可以取消。"))
            rec.state = "cancel"
