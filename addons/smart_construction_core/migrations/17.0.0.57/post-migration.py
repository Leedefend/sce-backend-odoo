# -*- coding: utf-8 -*-


def migrate(cr, version):
    cr.execute(
        """
        UPDATE sc_payment_execution AS e
           SET payment_request_partner_id = r.partner_id,
               actual_payee_partner_id = e.partner_id
          FROM payment_request AS r
         WHERE r.id = e.payment_request_id
           AND (
                e.payment_request_partner_id IS DISTINCT FROM r.partner_id
                OR e.actual_payee_partner_id IS DISTINCT FROM e.partner_id
           )
        """
    )
    cr.execute(
        """
        UPDATE sc_payment_execution
           SET actual_payee_partner_id = partner_id
         WHERE payment_request_id IS NULL
           AND actual_payee_partner_id IS DISTINCT FROM partner_id
        """
    )
    cr.execute(
        """
        UPDATE sc_payment_execution
           SET payment_request_partner_relation = CASE
                WHEN payment_request_id IS NULL THEN 'no_request'
                WHEN payment_request_partner_id IS NULL THEN 'missing_request_partner'
                WHEN actual_payee_partner_id IS NULL THEN 'missing_actual_payee'
                WHEN payment_request_partner_id = actual_payee_partner_id THEN 'same_partner'
                ELSE 'actual_payee_differs'
           END
         WHERE payment_request_partner_relation IS DISTINCT FROM CASE
                WHEN payment_request_id IS NULL THEN 'no_request'
                WHEN payment_request_partner_id IS NULL THEN 'missing_request_partner'
                WHEN actual_payee_partner_id IS NULL THEN 'missing_actual_payee'
                WHEN payment_request_partner_id = actual_payee_partner_id THEN 'same_partner'
                ELSE 'actual_payee_differs'
           END
        """
    )
