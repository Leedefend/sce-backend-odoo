# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScBusinessEntity(models.Model):
    _name = "sc.business.entity"
    _description = "业务核算主体"
    _order = "company_id, sequence, name"
    _rec_name = "name"

    sequence = fields.Integer(default=10, index=True)
    name = fields.Char(string="名称", required=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        string="隔离公司",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        ondelete="restrict",
    )
    partner_id = fields.Many2one("res.partner", string="关联往来单位", index=True, ondelete="set null")
    entity_type = fields.Selection(
        [
            ("internal", "内部核算"),
            ("affiliate", "挂靠/关联主体"),
            ("trade", "商贸主体"),
            ("labor", "劳务主体"),
            ("platform", "平台主体"),
            ("project_carrier", "项目经营载体"),
            ("unknown", "待确认"),
        ],
        string="主体类型",
        default="unknown",
        required=True,
        index=True,
    )
    mapping_state = fields.Selection(
        [
            ("draft", "草稿"),
            ("candidate", "候选"),
            ("confirmed", "已确认"),
            ("conflict", "冲突"),
            ("archived", "归档"),
        ],
        string="映射状态",
        default="candidate",
        required=True,
        index=True,
    )
    legacy_xmid = fields.Char(string="旧主体ID", index=True)
    legacy_xmmc = fields.Char(string="旧主体名称", index=True)
    legacy_company_id = fields.Char(string="旧公司ID", index=True)
    legacy_company_name = fields.Char(string="旧公司名称", index=True)
    legacy_visible_created_time = fields.Datetime(string="历史可见录入时间", readonly=True)
    legacy_visible_creator_name = fields.Char(string="历史可见录入人", readonly=True)
    legacy_visible_document_state = fields.Char(string="历史可见单据状态", readonly=True)
    legacy_visible_push_result = fields.Char(string="历史可见推送结果", readonly=True)
    legacy_visible_cooperation_type = fields.Char(string="历史可见合作类型", readonly=True)
    legacy_visible_bank_name = fields.Char(string="历史可见开户银行", readonly=True)
    legacy_visible_account_no = fields.Char(string="历史可见账号", readonly=True)
    legacy_visible_account_holder = fields.Char(string="历史可见开户姓名", readonly=True)
    legacy_visible_social_credit_code = fields.Char(string="历史可见统一社会信用代码", readonly=True)
    legacy_visible_main_tax_rate = fields.Char(string="历史可见主税率", readonly=True)
    legacy_visible_receipt_amount = fields.Char(string="历史可见收款金额", readonly=True)
    legacy_visible_payment_amount = fields.Char(string="历史可见付款金额", readonly=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(default=True, index=True)
    map_ids = fields.One2many("sc.legacy.business.entity.map", "business_entity_id", string="旧主体映射")
    map_count = fields.Integer(string="映射数", compute="_compute_map_count")

    @api.depends("map_ids")
    def _compute_map_count(self):
        grouped = self.env["sc.legacy.business.entity.map"].sudo().read_group(
            [("business_entity_id", "in", self.ids)],
            ["business_entity_id"],
            ["business_entity_id"],
        )
        counts = {row["business_entity_id"][0]: row["business_entity_id_count"] for row in grouped}
        for rec in self:
            rec.map_count = counts.get(rec.id, 0)

    @api.constrains("company_id", "partner_id")
    def _check_partner_company(self):
        for rec in self:
            partner_company = rec.partner_id.company_id
            if partner_company and partner_company != rec.company_id:
                raise ValidationError(_("关联往来单位必须属于同一隔离公司或为共享往来单位。"))

    @api.constrains("company_id", "legacy_xmid", "active")
    def _check_active_legacy_xmid_unique(self):
        for rec in self:
            if not rec.active or not rec.legacy_xmid:
                continue
            duplicate = self.search(
                [
                    ("id", "!=", rec.id),
                    ("active", "=", True),
                    ("company_id", "=", rec.company_id.id),
                    ("legacy_xmid", "=", rec.legacy_xmid),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(_("同一隔离公司下旧主体ID不能重复。"))


class ScLegacyBusinessEntityMap(models.Model):
    _name = "sc.legacy.business.entity.map"
    _description = "旧库业务核算主体映射"
    _order = "mapping_state, legacy_xmmc, source_table"
    _rec_name = "legacy_xmmc"

    source_table = fields.Char(string="来源表", required=True, index=True)
    source_domain = fields.Char(string="来源域", index=True)
    legacy_xmid = fields.Char(string="旧主体ID", required=True, index=True)
    legacy_xmmc = fields.Char(string="旧主体名称", index=True)
    legacy_company_id = fields.Char(string="旧公司ID", index=True)
    legacy_company_name = fields.Char(string="旧公司名称", index=True)
    company_id = fields.Many2one(
        "res.company",
        string="隔离公司",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        ondelete="restrict",
    )
    business_entity_id = fields.Many2one(
        "sc.business.entity",
        string="业务核算主体",
        index=True,
        ondelete="set null",
    )
    partner_id = fields.Many2one("res.partner", string="候选往来单位", index=True, ondelete="set null")
    mapping_state = fields.Selection(
        [
            ("candidate", "候选"),
            ("confirmed", "已确认"),
            ("conflict", "冲突"),
            ("ignored", "忽略"),
        ],
        string="映射状态",
        default="candidate",
        required=True,
        index=True,
    )
    suggested_entity_type = fields.Selection(
        [
            ("internal", "内部核算"),
            ("affiliate", "挂靠/关联主体"),
            ("trade", "商贸主体"),
            ("labor", "劳务主体"),
            ("platform", "平台主体"),
            ("project_carrier", "项目经营载体"),
            ("unknown", "待确认"),
        ],
        string="建议主体类型",
        default="unknown",
        index=True,
    )
    confidence = fields.Float(string="置信度")
    source_count = fields.Integer(string="来源数", index=True)
    rows_total = fields.Integer(string="事实行数", index=True)
    amount_total = fields.Float(string="金额/余额信号")
    evidence = fields.Text(string="证据")
    reviewer_id = fields.Many2one("res.users", string="确认人", readonly=True, ondelete="set null")
    reviewed_at = fields.Datetime(string="确认时间", readonly=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "map_source_xmid_uniq",
            "unique(source_table, legacy_xmid)",
            "同一来源表的旧主体ID只能出现一次。",
        ),
    ]

    @api.constrains("company_id", "business_entity_id", "partner_id")
    def _check_target_company(self):
        for rec in self:
            if rec.business_entity_id and rec.business_entity_id.company_id != rec.company_id:
                raise ValidationError(_("映射目标业务核算主体必须属于同一隔离公司。"))
            partner_company = rec.partner_id.company_id
            if partner_company and partner_company != rec.company_id:
                raise ValidationError(_("候选往来单位必须属于同一隔离公司或为共享往来单位。"))

    def action_confirm(self):
        for rec in self:
            if not rec.business_entity_id:
                raise ValidationError(_("确认映射前必须选择业务核算主体。"))
            rec.write(
                {
                    "mapping_state": "confirmed",
                    "reviewer_id": self.env.user.id,
                    "reviewed_at": fields.Datetime.now(),
                }
            )

    def action_mark_conflict(self):
        self.write({"mapping_state": "conflict"})

    def action_ignore(self):
        self.write({"mapping_state": "ignored"})


class ScLegacyProjectMap(models.Model):
    _name = "sc.legacy.project.map"
    _description = "旧库项目映射"
    _order = "mapping_state, legacy_gcmc"
    _rec_name = "legacy_gcmc"

    source_table = fields.Char(
        string="来源表",
        required=True,
        default="SCBS_GCMC_PROJECT_CANDIDATE",
        index=True,
    )
    source_domain = fields.Char(string="来源域", default="SCBS", index=True)
    legacy_gcmc = fields.Char(string="旧库工程名称", required=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        string="隔离公司",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        ondelete="restrict",
    )
    project_id = fields.Many2one("project.project", string="目标项目", index=True, ondelete="set null")
    mapping_state = fields.Selection(
        [
            ("candidate", "候选"),
            ("confirmed", "已确认"),
            ("conflict", "冲突"),
            ("ignored", "忽略"),
        ],
        string="映射状态",
        default="candidate",
        required=True,
        index=True,
    )
    suggested_state = fields.Selection(
        [
            ("project_candidate", "项目候选"),
            ("single_source_project_candidate", "单来源项目候选"),
            ("not_real_project_review", "非真实项目复核"),
            ("ignored_test_candidate", "测试项目忽略"),
        ],
        string="旧库建议状态",
        default="project_candidate",
        required=True,
        index=True,
    )
    match_method = fields.Selection(
        [
            ("none", "未匹配"),
            ("exact", "精确匹配"),
            ("fuzzy", "模糊建议"),
            ("manual", "人工指定"),
        ],
        string="匹配方式",
        default="none",
        required=True,
        index=True,
    )
    confidence = fields.Float(string="置信度")
    source_count = fields.Integer(string="来源数", index=True)
    rows_total = fields.Integer(string="事实行数", index=True)
    amount_total = fields.Float(string="金额信号")
    min_date = fields.Date(string="最早日期")
    max_date = fields.Date(string="最晚日期")
    payment_rows = fields.Integer(string="付款行数")
    payment_amount = fields.Float(string="付款金额")
    contract_rows = fields.Integer(string="合同行数")
    contract_amount = fields.Float(string="合同金额")
    stock_rows = fields.Integer(string="库存行数")
    stock_amount = fields.Float(string="库存金额")
    evidence = fields.Text(string="证据")
    reviewer_id = fields.Many2one("res.users", string="确认人", readonly=True, ondelete="set null")
    reviewed_at = fields.Datetime(string="确认时间", readonly=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "project_map_source_gcmc_uniq",
            "unique(source_table, legacy_gcmc)",
            "同一来源表的旧库工程名称只能出现一次。",
        ),
    ]

    @api.constrains("company_id", "project_id")
    def _check_project_company(self):
        for rec in self:
            project_company = rec.project_id.company_id
            if project_company and project_company != rec.company_id:
                raise ValidationError(_("目标项目必须属于同一隔离公司或为共享项目。"))

    def action_confirm(self):
        for rec in self:
            if not rec.project_id:
                raise ValidationError(_("确认映射前必须选择目标项目。"))
            rec.write(
                {
                    "mapping_state": "confirmed",
                    "match_method": rec.match_method if rec.match_method != "none" else "manual",
                    "reviewer_id": self.env.user.id,
                    "reviewed_at": fields.Datetime.now(),
                }
            )

    def action_mark_conflict(self):
        self.write({"mapping_state": "conflict"})

    def action_ignore(self):
        self.write({"mapping_state": "ignored"})


class ScLegacyPartnerMap(models.Model):
    _name = "sc.legacy.partner.map"
    _description = "旧库往来单位映射"
    _order = "mapping_state, legacy_partner_name"
    _rec_name = "legacy_partner_name"

    source_table = fields.Char(
        string="来源表",
        required=True,
        default="SCBS_PARTNER_DUPLICATE_CANDIDATE",
        index=True,
    )
    source_domain = fields.Char(string="来源域", default="SCBS", index=True)
    legacy_key = fields.Char(string="旧库映射键", required=True, index=True)
    legacy_partner_name = fields.Char(string="旧库往来单位", required=True, index=True)
    legacy_tax_code = fields.Char(string="旧库税号样本", index=True)
    company_id = fields.Many2one(
        "res.company",
        string="隔离公司",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        ondelete="restrict",
    )
    partner_id = fields.Many2one("res.partner", string="目标往来单位", index=True, ondelete="set null")
    mapping_state = fields.Selection(
        [
            ("candidate", "候选"),
            ("confirmed", "已确认"),
            ("conflict", "冲突"),
            ("ignored", "忽略"),
        ],
        string="映射状态",
        default="candidate",
        required=True,
        index=True,
    )
    suggested_state = fields.Selection(
        [
            ("fact_partner_candidate", "事实往来候选"),
            ("duplicate_across_carriers", "跨主体重复"),
            ("duplicate_same_carrier_or_empty_tax", "同主体/空税号重复"),
            ("tax_code_conflict", "税号冲突"),
        ],
        string="旧库建议状态",
        default="duplicate_across_carriers",
        required=True,
        index=True,
    )
    match_method = fields.Selection(
        [
            ("none", "未匹配"),
            ("tax_code", "税号匹配"),
            ("exact_name", "名称匹配"),
            ("manual", "人工指定"),
            ("multiple", "多目标候选"),
        ],
        string="匹配方式",
        default="none",
        required=True,
        index=True,
    )
    confidence = fields.Float(string="置信度")
    legacy_rows = fields.Integer(string="旧库行数", index=True)
    active_rows = fields.Integer(string="有效行数", index=True)
    tax_code_count = fields.Integer(string="税号数量", index=True)
    carrier_count = fields.Integer(string="关联主体数", index=True)
    sample_carrier = fields.Char(string="主体样本", index=True)
    max_carrier = fields.Char(string="最大主体", index=True)
    target_partner_count = fields.Integer(string="目标候选数", index=True)
    evidence = fields.Text(string="证据")
    reviewer_id = fields.Many2one("res.users", string="确认人", readonly=True, ondelete="set null")
    reviewed_at = fields.Datetime(string="确认时间", readonly=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "partner_map_source_key_uniq",
            "unique(source_table, legacy_key)",
            "同一来源表的旧库往来单位映射键只能出现一次。",
        ),
    ]

    @api.constrains("company_id", "partner_id")
    def _check_partner_company(self):
        for rec in self:
            partner_company = rec.partner_id.company_id
            if partner_company and partner_company != rec.company_id:
                raise ValidationError(_("目标往来单位必须属于同一隔离公司或为共享往来单位。"))

    def action_confirm(self):
        for rec in self:
            if not rec.partner_id:
                raise ValidationError(_("确认映射前必须选择目标往来单位。"))
            if rec.suggested_state == "tax_code_conflict" and rec.match_method != "manual":
                raise ValidationError(_("税号冲突必须人工指定后才能确认。"))
            rec.write(
                {
                    "mapping_state": "confirmed",
                    "match_method": rec.match_method if rec.match_method != "none" else "manual",
                    "reviewer_id": self.env.user.id,
                    "reviewed_at": fields.Datetime.now(),
                }
            )

    def action_mark_conflict(self):
        self.write({"mapping_state": "conflict"})

    def action_ignore(self):
        self.write({"mapping_state": "ignored"})
