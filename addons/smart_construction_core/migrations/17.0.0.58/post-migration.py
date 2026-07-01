# -*- coding: utf-8 -*-


def migrate(cr, version):
    # Payment requests are the user-confirmed formal carrier for payment basis.
    # Payment executions consume those confirmed anchors; this does not infer
    # from raw legacy text or rewrite source facts.
    cr.execute(
        """
        WITH unique_confirmed_request AS (
            SELECT
                e.id AS execution_id,
                MIN(r2.id) AS request_id,
                COUNT(*) AS candidate_count
              FROM sc_payment_execution AS e
              JOIN payment_request AS current_request ON current_request.id = e.payment_request_id
              JOIN payment_request AS r2
                ON r2.type = 'pay'
               AND r2.project_id = e.project_id
               AND r2.partner_id = e.partner_id
               AND r2.amount = e.paid_amount
               AND r2.date_request = e.date_payment
             WHERE e.payment_request_id IS NOT NULL
               AND e.project_id IS NOT NULL
               AND current_request.project_id IS NOT NULL
               AND e.project_id <> current_request.project_id
             GROUP BY e.id
            HAVING COUNT(*) = 1
        )
        UPDATE sc_payment_execution AS e
           SET payment_request_id = unique_confirmed_request.request_id
          FROM unique_confirmed_request
         WHERE e.id = unique_confirmed_request.execution_id
        """
    )
    cr.execute(
        """
        UPDATE sc_payment_execution AS e
           SET contract_id = r.contract_id
          FROM payment_request AS r
          JOIN construction_contract AS c ON c.id = r.contract_id
         WHERE r.id = e.payment_request_id
           AND e.contract_id IS NULL
           AND r.contract_id IS NOT NULL
           AND e.project_id IS NOT NULL
           AND r.project_id IS NOT NULL
           AND e.project_id = r.project_id
           AND c.project_id = e.project_id
        """
    )
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
