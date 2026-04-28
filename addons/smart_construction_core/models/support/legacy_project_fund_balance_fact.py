# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyProjectFundBalanceFact(models.Model):
    _name = "sc.legacy.project.fund.balance.fact"
    _description = "历史项目资金余额事实"
    _order = "project_name, legacy_project_id"

    legacy_project_id = fields.Char(string="历史项目ID", required=True, index=True)
    project_name = fields.Char(string="项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    project_self_funding_amount = fields.Float(string="项目自筹资金")
    actual_receipt_amount = fields.Float(string="累计实际收款")
    receipt_amount = fields.Float(string="累计收款")
    payment_amount = fields.Float(string="累计付款")
    external_fund_amount = fields.Float(string="外来资金")
    in_transit_amount = fields.Float(string="在途资金")
    actual_available_balance = fields.Float(string="实际可用余额")
    book_balance = fields.Float(string="账面余额")
    import_batch = fields.Char(string="导入批次", default="legacy_project_fund_balance_v1", required=True, index=True)
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_project_fund_balance_unique",
            "unique(legacy_project_id)",
            "Legacy project fund balance must be unique.",
        ),
    ]
