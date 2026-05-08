# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyBusinessFactResidual(models.Model):
    _name = "sc.legacy.business.fact.residual"
    _description = "历史业务事实原貌承接"
    _order = "source_label, family, source_table, legacy_record_id"

    source_label = fields.Char(string="来源标签", required=True, index=True)
    source_container = fields.Char(string="来源容器", index=True)
    source_database = fields.Char(string="来源库", required=True, index=True)
    source_table = fields.Char(string="来源表", required=True, index=True)
    source_dataset = fields.Char(string="来源数据集", index=True)
    legacy_record_id = fields.Char(string="记录编号", required=True, index=True)
    legacy_parent_id = fields.Char(string="父单编号", index=True)
    legacy_pid = fields.Char(string="附件编号", index=True)

    family = fields.Char(string="业务族群", index=True)
    classification = fields.Char(string="扫描分类", index=True)
    business_signal_score = fields.Integer(string="业务信号分")
    document_no = fields.Char(string="单号", index=True)
    document_date = fields.Datetime(string="单据日期", index=True)
    project_legacy_id = fields.Char(string="项目原编号", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    partner_legacy_id = fields.Char(string="往来单位原编号", index=True)
    partner_name = fields.Char(string="往来单位", index=True)
    amount_total = fields.Float(string="金额")

    raw_payload = fields.Text(string="原始字段 JSON")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_business_fact_residual_unique",
            "unique(source_database, source_table, legacy_record_id)",
            "同一来源库、来源表、记录编号的历史业务事实只能承接一次。",
        ),
    ]
