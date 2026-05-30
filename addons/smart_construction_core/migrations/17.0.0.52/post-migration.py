# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    cr.execute(
        """
        UPDATE tender_guarantee
           SET state = 'confirmed',
               write_date = NOW()
         WHERE state IS NULL
        """
    )
    env = api.Environment(cr, SUPERUSER_ID, {})
    if "sc.output.invoice.ledger" in env:
        env["sc.output.invoice.ledger"].init()
