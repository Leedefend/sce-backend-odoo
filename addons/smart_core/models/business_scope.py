# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ScBusinessScopeMixin(models.AbstractModel):
    _name = "sc.business.scope.mixin"
    _description = "Smart Core Platform Business Scope Mixin"

    PLATFORM_BUSINESS_SCOPE_FIELDS = (
        "business_scope_key",
        "business_direction",
        "carrier_type",
        "carrier_model",
        "carrier_res_id",
    )
    SOURCE_KIND = "platform_business_scope_metadata"
    SOURCE_AUTHORITIES = ("company", "business", "carrier")
    NO_BUSINESS_FACT_AUTHORITY = True

    business_scope_key = fields.Char(
        string="业务范围键",
        index=True,
        help="Optional platform scope metadata. It does not replace the industry carrier.",
    )
    business_direction = fields.Selection(
        [
            ("income", "收入"),
            ("expense", "支出"),
            ("bilateral_mixed", "双向/混合"),
            ("governance", "治理"),
            ("neutral", "中性"),
        ],
        string="业务方向",
        index=True,
        help="Optional cross-industry business direction metadata.",
    )
    carrier_type = fields.Char(
        string="载体类型",
        index=True,
        help="Optional future carrier discriminator such as project, case, order, or contract.",
    )
    carrier_model = fields.Char(
        string="载体模型",
        index=True,
        help="Optional technical model name of the carrier when known.",
    )
    carrier_res_id = fields.Integer(
        string="载体记录ID",
        index=True,
        help="Optional technical record id of the carrier when known.",
    )

    @api.model
    def source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "metadata_only": True,
            "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": self._name,
            "scope_fields": list(self.PLATFORM_BUSINESS_SCOPE_FIELDS),
        }

    def platform_business_scope_values(self):
        self.ensure_one()
        return {field: self[field] for field in self.PLATFORM_BUSINESS_SCOPE_FIELDS}
