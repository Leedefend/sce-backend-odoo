# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyMaterialStockFact(models.Model):
    _name = "sc.legacy.material.stock.fact"
    _description = "历史物资库存事实"
    _order = "document_date desc, source_table, legacy_record_id"

    legacy_record_id = fields.Char(string="记录编号", required=True, index=True)
    legacy_parent_id = fields.Char(string="父单编号", index=True)
    legacy_pid = fields.Char(string="附件编号", index=True)
    source_table = fields.Char(string="来源表", required=True, index=True)
    source_dataset = fields.Char(string="数据来源", index=True)
    fact_type = fields.Selection(
        [
            ("stock_in", "入库单"),
            ("stock_in_line", "入库明细"),
            ("stock_out", "出库单"),
            ("stock_out_line", "出库明细"),
            ("material_budget_item", "材料预算/清单"),
            ("material_cost_relation", "材料成本关系"),
            ("material_lease_contract", "物资租赁合同"),
            ("material_lease_settlement", "物资租赁结算"),
            ("scbs_stock_in", "SCBS材料入库"),
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
    partner_legacy_id = fields.Char(string="往来单位原编号", index=True)
    partner_name = fields.Char(string="往来单位", index=True)
    contract_legacy_id = fields.Char(string="合同原编号", index=True)
    contract_no = fields.Char(string="合同编号", index=True)
    material_legacy_id = fields.Char(string="材料原编号", index=True)
    material_code = fields.Char(string="材料编码", index=True)
    material_name = fields.Char(string="材料名称", index=True)
    material_spec = fields.Char(string="规格型号", index=True)
    material_uom = fields.Char(string="单位", index=True)
    work_part = fields.Char(string="施工部位", index=True)
    department_name = fields.Char(string="部门/仓库", index=True)

    document_date = fields.Datetime(string="单据日期", index=True)
    created_time = fields.Datetime(string="创建时间", index=True)
    creator_name = fields.Char(string="创建人", index=True)
    creator_legacy_user_id = fields.Char(string="创建人原编号", index=True)

    qty = fields.Float(string="数量")
    unit_price = fields.Float(string="单价")
    amount_total = fields.Float(string="含税金额/金额")
    amount_no_tax = fields.Float(string="不含税金额")
    tax_amount = fields.Float(string="税额")
    tax_rate = fields.Float(string="税率")

    attachment_ref = fields.Char(string="附件")
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_material_stock_unique",
            "unique(source_table, legacy_record_id)",
            "同一历史物资库存事实只能导入一次。",
        ),
    ]
