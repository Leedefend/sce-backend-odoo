# -*- coding: utf-8 -*-
"""Backfill receipt invoice line source document numbers from parent requests.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/ops/receipt_invoice_source_document_backfill.py
"""

import json
import sys
import traceback


SOURCE_DOCUMENT_EXPR = "NULLIF(substring(request.note FROM 'document_no=([^\\n;]+)'), '')"


def _scalar(sql, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def main():
    before_missing = int(
        _scalar("SELECT COUNT(*) FROM sc_receipt_invoice_line WHERE COALESCE(source_document_no, '') = ''") or 0
    )
    candidates = int(
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
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_receipt_invoice_line AS line
           SET source_document_no = %s,
               write_uid = 1,
               write_date = NOW()
          FROM payment_request AS request
         WHERE request.id = line.request_id
           AND COALESCE(line.source_document_no, '') = ''
           AND %s IS NOT NULL
        """
        % (SOURCE_DOCUMENT_EXPR, SOURCE_DOCUMENT_EXPR)
    )
    updated = env.cr.rowcount  # noqa: F821
    env.cr.commit()  # noqa: F821

    after_missing = int(
        _scalar("SELECT COUNT(*) FROM sc_receipt_invoice_line WHERE COALESCE(source_document_no, '') = ''") or 0
    )
    result = {
        "operation": "receipt_invoice_source_document_backfill",
        "status": "PASS",
        "before_missing_source_document_no": before_missing,
        "candidate_rows": candidates,
        "updated_rows": updated,
        "after_missing_source_document_no": after_missing,
    }
    print("RECEIPT_INVOICE_SOURCE_DOCUMENT_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


try:
    sys.exit(main())
except Exception as err:
    result = {
        "operation": "receipt_invoice_source_document_backfill",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("RECEIPT_INVOICE_SOURCE_DOCUMENT_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
