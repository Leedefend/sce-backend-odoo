# -*- coding: utf-8 -*-
"""Audit receipt invoice line source document number coverage.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/verify/receipt_invoice_source_document_audit.py
"""

import json
import sys
import traceback


SOURCE_DOCUMENT_EXPR = "NULLIF(substring(request.note FROM 'document_no=([^\\n;]+)'), '')"


def _scalar(sql, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def _fetchall(sql, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


def main():
    failures = []
    total = int(_scalar("SELECT COUNT(*) FROM sc_receipt_invoice_line") or 0)
    missing = int(_scalar("SELECT COUNT(*) FROM sc_receipt_invoice_line WHERE COALESCE(source_document_no, '') = ''") or 0)
    parent_document_available = int(
        _scalar(
            """
            SELECT COUNT(*)
              FROM sc_receipt_invoice_line AS line
              JOIN payment_request AS request ON request.id = line.request_id
             WHERE %s IS NOT NULL
            """
            % SOURCE_DOCUMENT_EXPR
        )
        or 0
    )
    missing_with_parent_document = int(
        _scalar(
            """
            SELECT COUNT(*)
              FROM sc_receipt_invoice_line AS line
              JOIN payment_request AS request ON request.id = line.request_id
             WHERE COALESCE(line.source_document_no, '') = ''
               AND %s IS NOT NULL
            """
            % SOURCE_DOCUMENT_EXPR
        )
        or 0
    )
    mismatched_parent_document = int(
        _scalar(
            """
            SELECT COUNT(*)
              FROM sc_receipt_invoice_line AS line
              JOIN payment_request AS request ON request.id = line.request_id
             WHERE %s IS NOT NULL
               AND COALESCE(line.source_document_no, '') <> %s
            """
            % (SOURCE_DOCUMENT_EXPR, SOURCE_DOCUMENT_EXPR)
        )
        or 0
    )
    if missing_with_parent_document or mismatched_parent_document:
        failures.append(
            {
                "check": "source_document_no_matches_parent_request_document_no",
                "missing_with_parent_document": missing_with_parent_document,
                "mismatched_parent_document": mismatched_parent_document,
                "sample": _fetchall(
                    """
                    SELECT line.id, line.request_id, line.source_document_no,
                           %s AS parent_source_document_no,
                           line.invoice_document_no, line.legacy_invoice_line_id
                      FROM sc_receipt_invoice_line AS line
                      JOIN payment_request AS request ON request.id = line.request_id
                     WHERE %s IS NOT NULL
                       AND COALESCE(line.source_document_no, '') <> %s
                     ORDER BY line.id
                     LIMIT 20
                    """
                    % (SOURCE_DOCUMENT_EXPR, SOURCE_DOCUMENT_EXPR, SOURCE_DOCUMENT_EXPR)
                ),
            }
        )

    result = {
        "audit": "receipt_invoice_source_document_audit",
        "status": "PASS" if not failures else "FAIL",
        "total": total,
        "missing_source_document_no": missing,
        "parent_document_available": parent_document_available,
        "missing_with_parent_document": missing_with_parent_document,
        "mismatched_parent_document": mismatched_parent_document,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("RECEIPT_INVOICE_SOURCE_DOCUMENT_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    result = {
        "audit": "receipt_invoice_source_document_audit",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("RECEIPT_INVOICE_SOURCE_DOCUMENT_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
