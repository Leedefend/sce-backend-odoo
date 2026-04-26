# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScConstructionDiary(models.Model):
    _name = "sc.construction.diary"
    _description = "Construction Diary"
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
    document_no = fields.Char(string="来源单号", index=True)
    title = fields.Char(string="标题", index=True)
    diary_type = fields.Char(string="日志类型", index=True)
    category = fields.Char(string="分类", index=True)
    construction_unit = fields.Char(string="施工单位", index=True)
    project_manager = fields.Char(string="项目经理", index=True)
    quality_name = fields.Char(string="质量/事项", index=True)
    handler_name = fields.Char(string="经办人", index=True)
    description = fields.Text(string="日志内容")
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
    legacy_attachment_ref = fields.Char(string="历史附件引用", readonly=True)
    legacy_line_attachment_ref = fields.Char(string="历史明细附件引用", readonly=True)
    legacy_attachment_name = fields.Char(string="历史附件名", readonly=True)
    legacy_attachment_path = fields.Char(string="历史附件路径", readonly=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "Legacy construction diary source must be unique.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.construction.diary") or _("Construction Diary")
        return super().create(vals_list)

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {"note", "active", "write_uid", "write_date"}
            if set(vals) - allowed:
                raise UserError(_("历史迁移施工日志已确认，只允许补充备注。"))
        return super().write(vals)

    def action_confirm(self):
        for rec in self:
            if rec.state == "draft":
                rec.state = "confirmed"

    def action_done(self):
        for rec in self:
            if rec.state in ("draft", "confirmed"):
                rec.state = "done"

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移施工日志不能在新系统取消。"))
            if rec.state != "cancel":
                rec.state = "cancel"
