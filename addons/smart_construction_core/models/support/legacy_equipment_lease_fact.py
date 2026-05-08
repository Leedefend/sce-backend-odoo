# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyEquipmentLeaseFact(models.Model):
    _name = "sc.legacy.equipment.lease.fact"
    _description = "历史设备/租赁事实"
    _order = "document_date desc, source_table, legacy_record_id"

    legacy_record_id = fields.Char(string="记录编号", required=True, index=True)
    legacy_parent_id = fields.Char(string="父单编号", index=True)
    legacy_pid = fields.Char(string="附件编号", index=True)
    source_table = fields.Char(string="来源表", required=True, index=True)
    source_dataset = fields.Char(string="数据来源", index=True)
    fact_type = fields.Selection(
        [
            ("lease_contract", "租赁合同"),
            ("lease_contract_line", "租赁合同明细"),
            ("equipment_transfer", "设备/租赁转入"),
            ("equipment_shift", "机械台班"),
            ("lease_summary", "租赁汇总"),
            ("lease_settlement", "租赁结算"),
            ("lease_request", "租赁申请"),
            ("lease_partner", "租赁单位"),
        ],
        string="事实类型",
        required=True,
        index=True,
    )
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
    project_name = fields.Char(string="项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目锚点", index=True, ondelete="set null")
    company_id = fields.Many2one("res.company", string="公司", related="project_id.company_id", store=True, readonly=True, index=True)
    partner_legacy_id = fields.Char(string="租赁/使用单位原编号", index=True)
    partner_name = fields.Char(string="租赁/使用单位", index=True)
    contract_legacy_id = fields.Char(string="合同原编号", index=True)
    contract_no = fields.Char(string="合同编号", index=True)
    equipment_legacy_id = fields.Char(string="设备原编号", index=True)
    equipment_name = fields.Char(string="设备/租赁内容", index=True)
    equipment_spec = fields.Char(string="规格型号", index=True)
    equipment_uom = fields.Char(string="单位", index=True)
    work_part = fields.Char(string="施工部位", index=True)
    department_name = fields.Char(string="部门", index=True)

    document_date = fields.Datetime(string="单据日期", index=True)
    start_date = fields.Datetime(string="开始日期", index=True)
    end_date = fields.Datetime(string="结束日期", index=True)
    created_time = fields.Datetime(string="创建时间", index=True)
    creator_name = fields.Char(string="创建人", index=True)
    creator_legacy_user_id = fields.Char(string="创建人原编号", index=True)

    qty = fields.Float(string="数量")
    unit_price = fields.Float(string="单价")
    amount_total = fields.Float(string="金额")
    amount_no_tax = fields.Float(string="不含税金额")
    tax_amount = fields.Float(string="税额")
    tax_rate = fields.Float(string="税率")
    amount_payable = fields.Float(string="应付金额")
    amount_deduction = fields.Float(string="扣款金额")

    bank_name = fields.Char(string="开户行")
    bank_account = fields.Char(string="银行账号")
    attachment_ref = fields.Char(string="附件")
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_equipment_lease_unique",
            "unique(source_table, legacy_record_id)",
            "同一历史设备/租赁事实只能导入一次。",
        ),
    ]
