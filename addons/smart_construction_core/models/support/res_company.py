# -*- coding: utf-8 -*-
from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def _sc_ensure_cny_currency(self):
        """Keep the product RMB-only for business users on install and upgrade."""
        currency = self.env.ref("base.CNY", raise_if_not_found=False)
        if not currency:
            return False
        currency.sudo().active = True
        self.sudo().search([]).write({"currency_id": currency.id})
        return True
