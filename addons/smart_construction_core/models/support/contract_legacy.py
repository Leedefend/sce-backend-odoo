# -*- coding: utf-8 -*-
from odoo import fields, models


class ConstructionContractLegacy(models.Model):
    _inherit = "construction.contract"

    legacy_contract_id = fields.Char(index=True)
    legacy_project_id = fields.Char(index=True)
    legacy_contract_no = fields.Char(string="合同编号", index=True)
    legacy_document_no = fields.Char(string="历史单据编号", index=True)
    legacy_external_contract_no = fields.Char(string="自编合同编号", index=True)
    legacy_status = fields.Char(string="历史状态", index=True)
    legacy_deleted_flag = fields.Char(string="历史删除标识", index=True)
    legacy_counterparty_text = fields.Char(string="历史合同相对方")
