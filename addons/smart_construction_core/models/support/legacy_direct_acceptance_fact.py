# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyDirectAcceptanceFact(models.Model):
    _name = "sc.legacy.direct.acceptance.fact"
    _description = "直营旧系统验收事实"
    _order = "document_date desc, id desc"

    source_system = fields.Char(string="来源系统", required=True, index=True)
    acceptance_label = fields.Char(string="验收菜单", required=True, index=True)
    category = fields.Char(string="验收分类", index=True)
    legacy_config_id = fields.Char(string="旧系统配置ID", index=True)
    legacy_record_id = fields.Char(string="旧系统记录ID", required=True, index=True)
    legacy_parent_id = fields.Char(string="旧系统父记录ID", index=True)
    row_index = fields.Integer(string="旧系统行号", index=True)
    document_no = fields.Char(string="单据编号", index=True)
    document_title = fields.Char(string="标题/事项", index=True)
    document_date = fields.Datetime(string="单据日期", index=True)
    document_state = fields.Char(string="单据状态", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    project_legacy_id = fields.Char(string="旧系统项目ID", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    partner_name = fields.Char(string="往来单位/人员", index=True)
    amount_total = fields.Float(string="金额")
    quantity = fields.Float(string="数量")
    creator_name = fields.Char(string="录入人", index=True)
    creator_legacy_user_id = fields.Char(string="录入人ID", index=True)
    created_time = fields.Datetime(string="录入时间", index=True)
    attachment_ref = fields.Char(string="附件")
    note = fields.Text(string="备注")
    raw_payload = fields.Text(string="旧系统原始行JSON")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_direct_acceptance_fact_unique",
            "unique(source_system, acceptance_label, legacy_record_id)",
            "同一旧系统验收行只能导入一次。",
        ),
    ]
