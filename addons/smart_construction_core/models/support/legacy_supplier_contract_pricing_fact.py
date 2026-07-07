# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ScLegacySupplierContractPricingFact(models.Model):
    _name = "sc.legacy.supplier.contract.pricing.fact"
    _description = "历史供应商合同计价方式事实"
    _order = "project_name, partner_name, legacy_contract_id"

    legacy_source_table = fields.Char(string="来源表", default="T_GYSHT_INFO", required=True, index=True)
    legacy_contract_id = fields.Char(string="历史合同ID", required=True, index=True)
    document_state = fields.Char(string="历史状态", index=True)
    document_state_label = fields.Char(string="单据状态", compute="_compute_document_state_label")
    deleted_flag = fields.Char(string="删除标记", index=True)
    contract_no = fields.Char(string="合同编号", index=True)
    document_no = fields.Char(string="自编合同号", index=True)
    project_legacy_id = fields.Char(string="历史项目ID", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    partner_legacy_id = fields.Char(string="历史供应商ID", index=True)
    partner_name = fields.Char(string="供应商", index=True)
    partner_id = fields.Many2one("res.partner", string="供应商记录", index=True, ondelete="set null")
    settlement_amount = fields.Float(string="结算金额")
    original_contract_holder = fields.Char(string="合同原件")
    pricing_method_legacy_id = fields.Char(string="历史计价方式ID", index=True)
    pricing_method_text = fields.Char(string="计价方式", index=True)
    contract_type_text = fields.Char(string="合同类型", index=True)
    title = fields.Char(string="标题")
    amount_total = fields.Float(string="总金额")
    paid_amount = fields.Float(string="已付款金额")
    unpaid_amount = fields.Float(string="未付款金额")
    attachment_text = fields.Char(string="附件")
    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True)
    creator_name = fields.Char(string="录入人", index=True)
    created_time = fields.Datetime(string="历史录入时间", index=True)
    sign_date = fields.Date(string="签约日期", index=True)
    import_batch = fields.Char(string="导入批次", default="legacy_supplier_contract_pricing_v1", required=True, index=True)
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_supplier_contract_pricing_unique",
            "unique(legacy_contract_id)",
            "历史供应商合同计价记录必须唯一。",
        ),
    ]

    @api.depends("document_state", "deleted_flag")
    def _compute_document_state_label(self):
        state_labels = {
            "0": "未审核",
            "1": "审核中",
            "2": "已审核",
            "-1": "已驳回",
        }
        for record in self:
            if record.deleted_flag and record.deleted_flag not in ("0", "false", "False"):
                record.document_state_label = "已删除"
            else:
                record.document_state_label = state_labels.get(record.document_state or "", record.document_state or "")
