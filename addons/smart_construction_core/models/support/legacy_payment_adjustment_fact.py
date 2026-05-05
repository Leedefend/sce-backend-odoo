# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyPaymentAdjustmentFact(models.Model):
    _name = "sc.legacy.payment.adjustment.fact"
    _description = "历史付款退款/调整事实"
    _order = "document_date desc, id desc"

    legacy_source_model = fields.Char(string="历史来源模型", required=True, index=True)
    legacy_source_table = fields.Char(string="历史来源表", required=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", required=True, index=True)
    legacy_pid = fields.Char(string="历史PID", index=True)
    document_no = fields.Char(string="来源单号", index=True)
    document_date = fields.Date(string="单据日期", index=True)
    legacy_document_state = fields.Char(string="历史状态", index=True)
    adjustment_classification = fields.Selection(
        [
            ("refund_or_return", "退款/退回"),
            ("account_or_internal_adjustment", "调户/内部调整"),
            ("negative_without_text_semantics", "负数未明语义"),
        ],
        string="调整分类",
        required=True,
        index=True,
    )
    source_amount = fields.Monetary(string="历史金额", currency_field="currency_id")
    absolute_amount = fields.Monetary(string="绝对金额", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, ondelete="cascade")
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="project_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    operation_strategy = fields.Selection(
        related="project_id.operation_strategy",
        string="经营方式",
        store=True,
        readonly=True,
        index=True,
    )
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True, ondelete="set null")
    legacy_project_id = fields.Char(string="旧项目ID", index=True)
    legacy_project_name = fields.Char(string="旧项目名称")
    legacy_partner_id = fields.Char(string="旧往来单位ID", index=True)
    legacy_partner_name = fields.Char(string="旧往来单位名称")
    source_note = fields.Text(string="来源备注")
    note = fields.Text(string="承接说明")
    import_batch = fields.Char(string="导入批次", required=True, index=True)
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_payment_adjustment_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "同一历史付款退款/调整事实只能导入一次。",
        ),
        ("source_amount_non_positive", "CHECK(source_amount <= 0)", "历史付款退款/调整金额必须为非正数。"),
        ("absolute_amount_nonnegative", "CHECK(absolute_amount >= 0)", "绝对金额必须为非负数。"),
    ]
