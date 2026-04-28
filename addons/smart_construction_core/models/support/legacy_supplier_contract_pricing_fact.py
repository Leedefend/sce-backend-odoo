# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacySupplierContractPricingFact(models.Model):
    _name = "sc.legacy.supplier.contract.pricing.fact"
    _description = "历史供应商合同计价方式事实"
    _order = "project_name, partner_name, legacy_contract_id"

    legacy_contract_id = fields.Char(string="历史合同ID", required=True, index=True)
    document_state = fields.Char(string="历史状态", index=True)
    deleted_flag = fields.Char(string="删除标记", index=True)
    project_legacy_id = fields.Char(string="历史项目ID", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    partner_legacy_id = fields.Char(string="历史供应商ID", index=True)
    partner_name = fields.Char(string="供应商", index=True)
    partner_id = fields.Many2one("res.partner", string="供应商记录", index=True, ondelete="set null")
    pricing_method_legacy_id = fields.Char(string="历史计价方式ID", index=True)
    pricing_method_text = fields.Char(string="计价方式", index=True)
    amount_total = fields.Float(string="合同金额")
    import_batch = fields.Char(string="导入批次", default="legacy_supplier_contract_pricing_v1", required=True, index=True)
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_supplier_contract_pricing_unique",
            "unique(legacy_contract_id)",
            "Legacy supplier contract pricing must be unique.",
        ),
    ]
