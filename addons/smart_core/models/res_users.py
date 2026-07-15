# -*- coding: utf-8 -*-
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"
    SOURCE_KIND = "odoo_auth_session_extension"
    SOURCE_AUTHORITIES = ("res.users",)
    NO_BUSINESS_FACT_AUTHORITY = True

    token_version = fields.Integer(default=0)

    def write(self, vals):
        if self.env.context.get("sc_skip_token_epoch_bump"):
            return super().write(vals)

        security_fields = {"active", "company_id", "company_ids", "groups_id", "login", "password"}
        must_invalidate = bool(security_fields.intersection(vals)) and "token_version" not in vals
        result = super().write(vals)
        if must_invalidate:
            for user in self.exists():
                user.with_context(sc_skip_token_epoch_bump=True).write(
                    {"token_version": int(user.token_version or 0) + 1}
                )
        return result

    def source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": self._name,
        }
