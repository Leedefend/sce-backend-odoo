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
        MoveLine = self.env["account.move.line"].sudo()
        for company in self.sudo().search([]):
            if company.currency_id == currency:
                continue
            if MoveLine.search_count([("company_id", "=", company.id)], limit=1):
                _logger.info(
                    "Skip CNY currency bootstrap for company %s because journal items already exist.",
                    company.display_name,
                )
                continue
            company.currency_id = currency
        return True
