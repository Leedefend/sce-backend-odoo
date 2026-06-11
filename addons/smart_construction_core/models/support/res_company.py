# -*- coding: utf-8 -*-
import logging

from odoo import api, models


_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def _sc_ensure_cny_currency(self):
        """Keep the product RMB-only for business users on install and upgrade."""
        currency = self.env.ref("base.CNY", raise_if_not_found=False)
        if not currency:
            return False
        currency.sudo().active = True
        for company in self.sudo().search([]):
            if company.currency_id == currency:
                continue
            _logger.info("Set company %s currency to CNY.", company.display_name)
            company.currency_id = currency
        return True
