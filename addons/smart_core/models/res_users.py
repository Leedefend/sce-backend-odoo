# -*- coding: utf-8 -*-
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"
    SOURCE_KIND = "odoo_auth_session_extension"
    SOURCE_AUTHORITIES = ("res.users",)
    NO_BUSINESS_FACT_AUTHORITY = True

    token_version = fields.Integer(default=0)

    def source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": self._name,
        }
