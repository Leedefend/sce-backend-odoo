# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScLegacyScbsMaterialMap(models.Model):
    _name = "sc.legacy.scbs.material.map"
    _description = "SCBS旧库材料映射"
    _order = "mapping_state, review_priority, amount_total desc, material_name"
    _rec_name = "display_name"

    display_name = fields.Char(string="显示名称", compute="_compute_display_name", store=True)
    source_table = fields.Char(string="来源表", default="T_RK_RKDCB", required=True, index=True)
    source_domain = fields.Char(string="来源域", default="SCBS", required=True, index=True)
    material_key = fields.Char(string="材料组键", required=True, index=True)
    legacy_material_id = fields.Char(string="SCBS材料ID", index=True)
    material_name = fields.Char(string="材料名称", index=True)
    spec_model = fields.Char(string="规格型号", index=True)
    uom_text = fields.Char(string="单位", index=True)
    company_id = fields.Many2one(
        "res.company",
        string="隔离公司",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        ondelete="restrict",
    )
    material_catalog_id = fields.Many2one(
        "sc.material.catalog",
        string="目标材料档案",
        index=True,
        ondelete="set null",
    )
    mapping_state = fields.Selection(
        [
            ("candidate", "候选"),
            ("confirmed", "已确认"),
            ("create_required", "需新建材料档案"),
            ("conflict", "冲突"),
            ("ignored", "忽略"),
        ],
        string="映射状态",
        default="candidate",
        required=True,
        index=True,
    )
    suggested_action = fields.Selection(
        [
            ("manual_material_identity_required", "人工确认材料身份"),
            ("confirm_exact_text_catalog_or_create_new", "确认精确文本候选或新建"),
            ("review_name_spec_catalog_or_create_new", "复核名称规格候选或新建"),
            ("create_or_map_material_catalog", "新建或映射材料档案"),
        ],
        string="建议动作",
        default="create_or_map_material_catalog",
        required=True,
        index=True,
    )
    coverage_state = fields.Selection(
        [
            ("catalog_ready_by_legacy_id", "旧ID已命中"),
            ("catalog_candidate_exact_text", "精确文本候选"),
            ("catalog_candidate_name_spec", "名称规格候选"),
            ("catalog_missing", "材料档案缺失"),
            ("missing_legacy_material_id", "缺少SCBS材料ID"),
        ],
        string="覆盖状态",
        default="catalog_missing",
        required=True,
        index=True,
    )
    review_priority = fields.Integer(string="复核优先级", default=99, index=True)
    exact_text_catalog_id = fields.Many2one(
        "sc.material.catalog",
        string="精确文本候选档案",
        index=True,
        ondelete="set null",
    )
    exact_text_match_count = fields.Integer(string="精确文本候选数")
    name_spec_catalog_id = fields.Many2one(
        "sc.material.catalog",
        string="名称规格候选档案",
        index=True,
        ondelete="set null",
    )
    name_spec_match_count = fields.Integer(string="名称规格候选数")
    line_rows = fields.Integer(string="明细行数", index=True)
    header_rows = fields.Integer(string="入库单数", index=True)
    qty_total = fields.Float(string="数量信号")
    amount_total = fields.Float(string="金额信号", index=True)
    reviewer_id = fields.Many2one("res.users", string="确认人", readonly=True, ondelete="set null")
    reviewed_at = fields.Datetime(string="确认时间", readonly=True)
    evidence = fields.Text(string="证据")
    note = fields.Text(string="备注")
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "scbs_material_key_uniq",
            "unique(source_table, material_key)",
            "同一来源表的SCBS材料组键只能出现一次。",
        ),
    ]

    @api.depends("material_name", "spec_model", "uom_text", "legacy_material_id")
    def _compute_display_name(self):
        for rec in self:
            parts = [value for value in [rec.material_name, rec.spec_model, rec.uom_text] if value]
            name = " / ".join(parts) if parts else _("未命名材料")
            if rec.legacy_material_id:
                name = "%s [%s]" % (name, rec.legacy_material_id)
            rec.display_name = name

    @api.constrains("material_catalog_id")
    def _check_material_catalog_company(self):
        for rec in self:
            catalog_company = rec.material_catalog_id.project_id.company_id
            if catalog_company and catalog_company != rec.company_id:
                raise ValidationError(_("目标材料档案所属项目公司必须与映射隔离公司一致。"))

    def action_confirm(self):
        for rec in self:
            if not rec.material_catalog_id:
                raise ValidationError(_("确认材料映射前必须选择目标材料档案。"))
            rec.write(
                {
                    "mapping_state": "confirmed",
                    "reviewer_id": self.env.user.id,
                    "reviewed_at": fields.Datetime.now(),
                }
            )

    def action_mark_create_required(self):
        self.write({"mapping_state": "create_required"})

    def action_mark_conflict(self):
        self.write({"mapping_state": "conflict"})

    def action_ignore(self):
        self.write({"mapping_state": "ignored"})
