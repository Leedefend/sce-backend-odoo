# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyLaborSubcontractFact(models.Model):
    _name = "sc.legacy.labor.subcontract.fact"
    _description = "历史劳务/分包事实"
    _order = "document_date desc, source_table, legacy_record_id"

    legacy_record_id = fields.Char(string="记录编号", required=True, index=True)
    legacy_pid = fields.Char(string="附件编号", index=True)
    source_table = fields.Char(string="来源表", required=True, index=True)
    source_dataset = fields.Char(string="数据来源", index=True)
    fact_type = fields.Selection(
        [
            ("labor_contract", "劳务合同"),
            ("subcontract_contract", "分包合同"),
            ("labor_usage", "劳务用工"),
            ("labor_settlement", "劳务结算"),
            ("subcontract_settlement", "分包结算"),
            ("expense_claim", "项目费用"),
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
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="project_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    partner_legacy_id = fields.Char(string="劳务/分包单位原编号", index=True)
    partner_name = fields.Char(string="劳务/分包单位", index=True)
    contract_legacy_id = fields.Char(string="合同原编号", index=True)
    contract_no = fields.Char(string="合同编号", index=True)
    contract_name = fields.Char(string="合同名称", index=True)
    work_scope = fields.Char(string="工作范围/施工内容", index=True)
    work_part = fields.Char(string="施工部位", index=True)
    department_name = fields.Char(string="部门", index=True)

    document_date = fields.Datetime(string="单据日期", index=True)
    start_date = fields.Datetime(string="开始日期", index=True)
    end_date = fields.Datetime(string="结束日期", index=True)
    created_time = fields.Datetime(string="创建时间", index=True)
    creator_name = fields.Char(string="创建人", index=True)
    creator_legacy_user_id = fields.Char(string="创建人原编号", index=True)

    amount_total = fields.Float(string="事实金额")
    amount_contract = fields.Float(string="合同金额")
    amount_settlement = fields.Float(string="结算金额")
    amount_payable = fields.Float(string="应付金额")
    amount_deduction = fields.Float(string="扣款金额")
    tax_rate = fields.Float(string="税率")

    bank_name = fields.Char(string="开户行")
    bank_account = fields.Char(string="银行账号")
    attachment_ref = fields.Char(string="附件")
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_labor_subcontract_unique",
            "unique(source_table, legacy_record_id)",
            "同一历史劳务/分包事实只能导入一次。",
        ),
    ]
