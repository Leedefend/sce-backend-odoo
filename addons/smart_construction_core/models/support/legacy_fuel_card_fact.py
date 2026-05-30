# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyFuelCardFact(models.Model):
    _name = "sc.legacy.fuel.card.fact"
    _description = "历史油卡登记"
    _order = "document_date desc, id desc"

    legacy_source_model = fields.Char(string="历史来源模型", required=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", required=True, index=True)
    legacy_parent_id = fields.Char(string="历史父记录ID", index=True)
    document_no = fields.Char(string="单据编号", index=True)
    document_date = fields.Datetime(string="单据日期", index=True)
    document_state = fields.Char(string="单据状态", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    project_legacy_id = fields.Char(string="历史项目ID", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    card_no = fields.Char(string="油卡卡号", index=True)
    initial_amount = fields.Float(string="初始金额")
    balance_amount = fields.Float(string="当前余额")
    manager_name = fields.Char(string="主要管理人", index=True)
    manager_legacy_id = fields.Char(string="主要管理人ID", index=True)
    creator_name = fields.Char(string="录入人", index=True)
    creator_legacy_user_id = fields.Char(string="录入人ID", index=True)
    created_time = fields.Datetime(string="录入时间", index=True)
    attachment_ref = fields.Char(string="附件")
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        ("legacy_fuel_card_fact_unique", "unique(legacy_source_model, legacy_record_id)", "同一历史油卡登记只能导入一次。"),
    ]


class ScLegacyFuelCardRechargeFact(models.Model):
    _name = "sc.legacy.fuel.card.recharge.fact"
    _description = "历史油卡充值登记"
    _order = "document_date desc, id desc"

    legacy_source_model = fields.Char(string="历史来源模型", required=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", required=True, index=True)
    legacy_parent_id = fields.Char(string="历史父记录ID", index=True)
    document_no = fields.Char(string="单据编号", index=True)
    document_date = fields.Datetime(string="单据日期", index=True)
    document_state = fields.Char(string="单据状态", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    project_legacy_id = fields.Char(string="历史项目ID", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    card_no = fields.Char(string="油卡卡号", index=True)
    recharge_amount = fields.Float(string="充值金额")
    used_amount = fields.Float(string="已使用金额")
    balance_amount = fields.Float(string="剩余金额")
    total_recharge_amount = fields.Float(string="累计充值金额")
    related_document_no = fields.Char(string="关联报销单", index=True)
    handler_name = fields.Char(string="充值人", index=True)
    creator_name = fields.Char(string="录入人", index=True)
    creator_legacy_user_id = fields.Char(string="录入人ID", index=True)
    created_time = fields.Datetime(string="录入时间", index=True)
    attachment_ref = fields.Char(string="附件")
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_fuel_card_recharge_fact_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "同一历史油卡充值登记只能导入一次。",
        ),
    ]


class ScLegacyFuelCardRefuelFact(models.Model):
    _name = "sc.legacy.fuel.card.refuel.fact"
    _description = "历史加油登记"
    _order = "document_date desc, id desc"

    legacy_source_model = fields.Char(string="历史来源模型", required=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", required=True, index=True)
    legacy_parent_id = fields.Char(string="历史父记录ID", index=True)
    document_no = fields.Char(string="单据编号", index=True)
    document_date = fields.Datetime(string="单据日期", index=True)
    document_state = fields.Char(string="单据状态", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    project_legacy_id = fields.Char(string="历史项目ID", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    card_no = fields.Char(string="油卡卡号", index=True)
    fuel_date = fields.Datetime(string="加油日期", index=True)
    fuel_amount = fields.Float(string="加油金额")
    initial_amount = fields.Float(string="油卡初始金额")
    total_recharge_amount = fields.Float(string="累计充值金额")
    total_fuel_amount = fields.Float(string="累计加油金额")
    balance_amount = fields.Float(string="油卡剩余金额")
    related_document_no = fields.Char(string="关联报销单", index=True)
    handler_name = fields.Char(string="登记人", index=True)
    creator_name = fields.Char(string="录入人", index=True)
    creator_legacy_user_id = fields.Char(string="录入人ID", index=True)
    created_time = fields.Datetime(string="录入时间", index=True)
    attachment_ref = fields.Char(string="附件")
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        ("legacy_fuel_card_refuel_fact_unique", "unique(legacy_source_model, legacy_record_id)", "同一历史加油登记只能导入一次。"),
    ]
