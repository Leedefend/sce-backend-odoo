# -*- coding: utf-8 -*-


def migrate(cr, version):
    cr.execute(
        """
        UPDATE tender_guarantee
           SET state = 'confirmed',
               write_date = NOW()
         WHERE state IS NULL
        """
    )
