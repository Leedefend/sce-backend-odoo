# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Legacy identity carrier fields for idempotent migration replay.
    legacy_partner_id = fields.Char(index=True)
    legacy_partner_source = fields.Char(index=True)
    legacy_partner_name = fields.Char()
    legacy_credit_code = fields.Char()
    legacy_tax_no = fields.Char(index=True)
    legacy_deleted_flag = fields.Char()
    legacy_source_evidence = fields.Char()
