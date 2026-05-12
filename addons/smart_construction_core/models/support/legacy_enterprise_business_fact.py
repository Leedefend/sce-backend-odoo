# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ScLegacyEnterpriseBusinessFact(models.Model):
    _name = "sc.legacy.enterprise.business.fact"
    _description = "历史企业级业务事实"
    _order = "document_date desc, fact_family, id desc"

    legacy_source_model = fields.Char(string="历史来源模型", required=True, index=True)
    legacy_source_table = fields.Char(string="历史来源表", required=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", required=True, index=True)
    legacy_pid = fields.Char(string="历史PID", index=True)
    fact_family = fields.Selection(
        [
            ("payment", "付款"),
            ("supplier_contract", "供应商合同"),
        ],
        string="事实族",
        required=True,
        index=True,
    )
    document_scope = fields.Selection(
        [
            ("enterprise_no_project", "企业级无项目事实"),
        ],
        string="单据口径",
        required=True,
        default="enterprise_no_project",
        index=True,
    )
    document_no = fields.Char(string="来源单号", index=True)
    document_date = fields.Date(string="单据日期", index=True)
    legacy_document_state = fields.Char(string="历史状态", index=True)
    company_id = fields.Many2one(
        "res.company",
        string="隔离公司",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        ondelete="restrict",
    )
    business_entity_id = fields.Many2one("sc.business.entity", string="业务核算主体", index=True, ondelete="set null")
    operation_strategy = fields.Selection(
        [
            ("direct", "公司直营"),
            ("joint", "联营项目"),
        ],
        string="经营方式",
        required=True,
        default="direct",
        index=True,
    )
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True, ondelete="set null")
    legacy_partner_id = fields.Char(string="旧往来单位ID", index=True)
    legacy_partner_name = fields.Char(string="旧往来单位名称", index=True)
    amount_total = fields.Monetary(string="历史金额", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    residual_reason = fields.Char(string="承接口径", required=True, index=True)
    legacy_business_entity_id = fields.Char(string="旧业务主体ID", index=True)
    legacy_business_entity_name = fields.Char(string="旧业务主体名称")
    legacy_project_name = fields.Char(string="旧项目/工程名称")
    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True)
    creator_name = fields.Char(string="历史录入人", index=True)
    created_time = fields.Datetime(string="历史录入时间", index=True)
    source_note = fields.Text(string="来源备注")
    note = fields.Text(string="承接说明")
    import_batch = fields.Char(string="导入批次", required=True, index=True)
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_enterprise_business_fact_unique",
            "unique(legacy_source_model, legacy_source_table, legacy_record_id)",
            "同一历史企业级业务事实只能导入一次。",
        ),
    ]

    @api.constrains("company_id", "business_entity_id", "partner_id")
    def _check_company_scope(self):
        for rec in self:
            if rec.business_entity_id and rec.business_entity_id.company_id != rec.company_id:
                raise ValidationError("业务核算主体必须属于同一隔离公司。")
            partner_company = rec.partner_id.company_id
            if partner_company and partner_company != rec.company_id:
                raise ValidationError("往来单位必须属于同一隔离公司或为共享往来单位。")
