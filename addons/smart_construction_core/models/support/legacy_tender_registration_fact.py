# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyTenderRegistrationFact(models.Model):
    _name = "sc.legacy.tender.registration.fact"
    _description = "历史投标报名事实"
    _order = "registration_time desc, legacy_record_id"

    legacy_record_id = fields.Char(string="记录编号", required=True, index=True)
    legacy_pid = fields.Char(string="附件编号", index=True)
    source_table = fields.Char(string="来源表", default="P_ZTB_GCBMGL", required=True, index=True)
    source_dataset = fields.Char(string="数据来源", index=True)
    document_no = fields.Char(string="单号", index=True)
    document_state = fields.Char(string="单据状态", index=True)
    state = fields.Selection(
        [("legacy_confirmed", "历史已确认"), ("cancel", "历史作废")],
        string="承载状态",
        default="legacy_confirmed",
        required=True,
        index=True,
    )

    project_legacy_id = fields.Char(string="项目原编号", index=True)
    project_name = fields.Char(string="投标项目/工程名称", index=True)
    project_id = fields.Many2one("project.project", string="项目锚点", index=True, ondelete="set null")
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="project_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    owner_name = fields.Char(string="招标人/业主", index=True)
    construction_unit_name = fields.Char(string="建设单位", index=True)
    project_manager_name = fields.Char(string="项目经理", index=True)
    contact_name = fields.Char(string="联系人", index=True)

    registration_time = fields.Datetime(string="报名时间", index=True)
    bid_time = fields.Datetime(string="投标时间", index=True)
    opening_time = fields.Datetime(string="开标时间", index=True)
    guarantee_deadline = fields.Datetime(string="保证金截止时间", index=True)
    created_time = fields.Datetime(string="创建时间", index=True)
    creator_name = fields.Char(string="创建人", index=True)
    creator_legacy_user_id = fields.Char(string="创建人原编号", index=True)

    guarantee_amount = fields.Float(string="投标保证金")
    document_fee_amount = fields.Float(string="报名/标书费")
    max_price = fields.Float(string="最高限价")
    tender_status = fields.Char(string="投标状态", index=True)
    bid_participation = fields.Char(string="是否投标", index=True)
    bid_method = fields.Char(string="招标方式", index=True)
    bid_opening_place = fields.Char(string="开标地点")
    bank_name = fields.Char(string="开户行")
    bank_account = fields.Char(string="银行账号")
    attachment_ref = fields.Char(string="附件")
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_tender_registration_unique",
            "unique(source_table, legacy_record_id)",
            "同一历史投标报名事实只能导入一次。",
        ),
    ]
