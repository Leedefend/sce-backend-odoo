# -*- coding: utf-8 -*-
from odoo import api, fields, models


DOCUMENT_STATE_LABELS = {
    "0": "草稿",
    "1": "审批中",
    "2": "审核通过",
    "3": "否决",
    "draft": "草稿",
    "submit": "审批中",
    "approved": "审核通过",
    "done": "审核通过",
    "cancel": "否决",
}


def _text(value):
    return str(value or "").strip()


def _amount_text(value, blank_zero=True):
    if value is False or value is None:
        return ""
    amount = float(value)
    if blank_zero and amount == 0.0:
        return ""
    return str(amount)


def _attachment_label(record, attachment_ref):
    ref = _text(attachment_ref)
    if not ref:
        return ""
    if "sc.legacy.file.index" not in record.env:
        return "附件(1)"
    count = record.env["sc.legacy.file.index"].sudo().search_count([
        ("active", "=", True),
        ("bill_id", "=", ref),
    ])
    return "附件(%s)" % (count or 1)


def _accepted_fact_visible(record, acceptance_label, document_no, visible_index):
    doc = _text(document_no)
    if not doc or "sc.legacy.direct.acceptance.fact" not in record.env:
        return ""
    fact = record.env["sc.legacy.direct.acceptance.fact"].sudo().search(
        [
            ("active", "=", True),
            ("source_system", "=", "online_old_scbsly"),
            ("acceptance_label", "=", acceptance_label),
            ("document_no", "=", doc),
        ],
        order="id desc",
        limit=1,
    )
    if not fact:
        return ""
    return _text(getattr(fact, f"legacy_visible_{visible_index:02d}", ""))


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
    accepted_visible_01 = fields.Char(string="单据状态", compute="_compute_accepted_visible_fields")
    accepted_visible_06 = fields.Char(string="初始金额", compute="_compute_accepted_visible_fields")
    accepted_visible_09 = fields.Char(string="附件", compute="_compute_accepted_visible_fields")

    _sql_constraints = [
        ("legacy_fuel_card_fact_unique", "unique(legacy_source_model, legacy_record_id)", "同一历史油卡登记只能导入一次。"),
    ]

    @api.depends("document_state", "initial_amount", "attachment_ref")
    def _compute_accepted_visible_fields(self):
        for record in self:
            state = _text(record.document_state)
            record.accepted_visible_01 = DOCUMENT_STATE_LABELS.get(state, state)
            record.accepted_visible_06 = _amount_text(record.initial_amount)
            record.accepted_visible_09 = _attachment_label(record, record.attachment_ref)


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
    accepted_visible_01 = fields.Char(string="单据状态", compute="_compute_accepted_visible_fields")
    accepted_visible_06 = fields.Char(string="充值总额", compute="_compute_accepted_visible_fields")
    accepted_visible_07 = fields.Char(string="充值日期", compute="_compute_accepted_visible_fields")
    accepted_visible_10 = fields.Char(string="附件", compute="_compute_accepted_visible_fields")

    _sql_constraints = [
        (
            "legacy_fuel_card_recharge_fact_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "同一历史油卡充值登记只能导入一次。",
        ),
    ]

    @api.depends("document_state", "recharge_amount", "document_date", "attachment_ref")
    def _compute_accepted_visible_fields(self):
        for record in self:
            state = _text(record.document_state)
            record.accepted_visible_01 = DOCUMENT_STATE_LABELS.get(state, state)
            record.accepted_visible_06 = _amount_text(record.recharge_amount, blank_zero=False)
            record.accepted_visible_07 = _accepted_fact_visible(record, "充值登记", record.document_no, 7) or (
                fields.Datetime.to_string(record.document_date) if record.document_date else ""
            )
            record.accepted_visible_10 = _attachment_label(record, record.attachment_ref)


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
    accepted_visible_01 = fields.Char(string="单据状态", compute="_compute_accepted_visible_fields")
    accepted_visible_05 = fields.Char(string="加油金额", compute="_compute_accepted_visible_fields")
    accepted_visible_06 = fields.Char(string="累计加油金额", compute="_compute_accepted_visible_fields")
    accepted_visible_07 = fields.Char(string="油卡剩余金额", compute="_compute_accepted_visible_fields")
    accepted_visible_09 = fields.Char(string="累计充值金额", compute="_compute_accepted_visible_fields")
    accepted_visible_11 = fields.Char(string="附件", compute="_compute_accepted_visible_fields")

    _sql_constraints = [
        ("legacy_fuel_card_refuel_fact_unique", "unique(legacy_source_model, legacy_record_id)", "同一历史加油登记只能导入一次。"),
    ]

    @api.depends(
        "document_state",
        "document_no",
        "fuel_amount",
        "total_fuel_amount",
        "balance_amount",
        "total_recharge_amount",
        "attachment_ref",
    )
    def _compute_accepted_visible_fields(self):
        for record in self:
            state = _text(record.document_state)
            record.accepted_visible_01 = DOCUMENT_STATE_LABELS.get(state, state)
            record.accepted_visible_05 = _amount_text(record.fuel_amount)
            record.accepted_visible_06 = _amount_text(record.total_fuel_amount)
            record.accepted_visible_07 = _amount_text(record.balance_amount)
            record.accepted_visible_09 = _amount_text(record.total_recharge_amount)
            record.accepted_visible_11 = _accepted_fact_visible(record, "加油登记", record.document_no, 11) or _attachment_label(
                record, record.attachment_ref
            )
