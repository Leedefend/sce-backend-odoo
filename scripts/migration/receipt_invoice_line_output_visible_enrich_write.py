from __future__ import annotations

import json
import os
from pathlib import Path


def artifact_root() -> Path:
    root = Path(os.environ.get("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
        return root
    except OSError:
        fallback = Path("/tmp/sce_migration_artifacts")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def scalar(query: str, params: tuple = ()) -> int:
    env.cr.execute(query, params)  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return int(row[0] or 0)


def coverage() -> dict[str, int]:
    return {
        "total": scalar("SELECT COUNT(*) FROM sc_receipt_invoice_line WHERE active"),
        "invoice_date_present": scalar(
            "SELECT COUNT(*) FROM sc_receipt_invoice_line WHERE active AND invoice_date IS NOT NULL"
        ),
        "invoice_document_no_present": scalar(
            "SELECT COUNT(*) FROM sc_receipt_invoice_line WHERE active AND NULLIF(invoice_document_no, '') IS NOT NULL"
        ),
        "invoice_issue_company_present": scalar(
            "SELECT COUNT(*) FROM sc_receipt_invoice_line WHERE active AND NULLIF(invoice_issue_company, '') IS NOT NULL"
        ),
        "surcharge_amount_positive": scalar(
            "SELECT COUNT(*) FROM sc_receipt_invoice_line WHERE active AND COALESCE(surcharge_amount, 0) > 0"
        ),
    }


before = coverage()
company_name = env.company.name or ""  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH enriched AS (
      SELECT
        ril.id,
        COALESCE(ril.invoice_date, surcharge.invoice_date, registration.invoice_date) AS invoice_date,
        COALESCE(NULLIF(ril.invoice_document_no, ''), NULLIF(surcharge.document_no, ''), NULLIF(registration.document_no, '')) AS invoice_document_no,
        COALESCE(NULLIF(ril.invoice_document_state, ''), NULLIF(surcharge.document_state, ''), NULLIF(registration.legacy_document_state, '')) AS invoice_document_state,
        COALESCE(
          NULLIF(ril.invoice_issue_company, ''),
          NULLIF(registration.invoice_issue_company, ''),
          NULLIF(project_issue_company.invoice_issue_company, ''),
          NULLIF(%s, '')
        ) AS invoice_issue_company,
        CASE
          WHEN COALESCE(ril.surcharge_amount, 0) = 0 THEN COALESCE(surcharge.surcharge_amount, 0)
          ELSE ril.surcharge_amount
        END AS surcharge_amount
      FROM sc_receipt_invoice_line ril
      LEFT JOIN LATERAL (
        SELECT
          MIN(s.invoice_date) AS invoice_date,
          MIN(NULLIF(s.document_no, '')) AS document_no,
          MIN(NULLIF(s.document_state, '')) AS document_state,
          COALESCE(SUM(s.surcharge_amount), 0) AS surcharge_amount
        FROM sc_legacy_invoice_surcharge_fact s
        WHERE s.active
          AND s.direction = 'output'
          AND NULLIF(s.invoice_no, '') = NULLIF(ril.invoice_no, '')
          AND (s.project_id = ril.project_id OR s.project_id IS NULL OR ril.project_id IS NULL)
      ) surcharge ON TRUE
      LEFT JOIN LATERAL (
        SELECT
          ir.invoice_date,
          ir.document_no,
          ir.legacy_document_state,
          ir.invoice_issue_company
        FROM sc_invoice_registration ir
        WHERE ir.active
          AND ir.direction = 'output'
          AND NULLIF(ir.invoice_no, '') = NULLIF(ril.invoice_no, '')
          AND (ir.project_id = ril.project_id OR ir.project_id IS NULL OR ril.project_id IS NULL)
        ORDER BY
          CASE WHEN ir.project_id = ril.project_id THEN 0 ELSE 1 END,
          ir.invoice_date DESC NULLS LAST,
          ir.id DESC
        LIMIT 1
      ) registration ON TRUE
      LEFT JOIN LATERAL (
        SELECT ranked.invoice_issue_company
        FROM (
          SELECT NULLIF(peer.invoice_issue_company, '') AS invoice_issue_company, COUNT(*) AS fact_count
          FROM sc_receipt_invoice_line peer
          WHERE peer.active
            AND peer.project_id = ril.project_id
            AND NULLIF(peer.invoice_issue_company, '') IS NOT NULL
          GROUP BY NULLIF(peer.invoice_issue_company, '')
        ) ranked
        ORDER BY ranked.fact_count DESC, ranked.invoice_issue_company
        LIMIT 1
      ) project_issue_company ON TRUE
      WHERE ril.active
    )
    UPDATE sc_receipt_invoice_line AS target
       SET invoice_date = enriched.invoice_date,
           invoice_document_no = enriched.invoice_document_no,
           invoice_document_state = enriched.invoice_document_state,
           invoice_issue_company = enriched.invoice_issue_company,
           surcharge_amount = enriched.surcharge_amount
      FROM enriched
     WHERE target.id = enriched.id
       AND (
         target.invoice_date IS DISTINCT FROM enriched.invoice_date
         OR COALESCE(target.invoice_document_no, '') IS DISTINCT FROM COALESCE(enriched.invoice_document_no, '')
         OR COALESCE(target.invoice_document_state, '') IS DISTINCT FROM COALESCE(enriched.invoice_document_state, '')
         OR COALESCE(target.invoice_issue_company, '') IS DISTINCT FROM COALESCE(enriched.invoice_issue_company, '')
         OR COALESCE(target.surcharge_amount, 0) IS DISTINCT FROM COALESCE(enriched.surcharge_amount, 0)
       )
    """,
    (company_name,),
)
updated_rows = env.cr.rowcount  # noqa: F821
after = coverage()

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "receipt_invoice_line_output_visible_enrich_write",
    "database": env.cr.dbname,  # noqa: F821
    "updated_rows": updated_rows,
    "before": before,
    "after": after,
    "source_facts": {
        "receipt_invoice_line": "sc.receipt.invoice.line",
        "output_surcharge_fact": "sc.legacy.invoice.surcharge.fact(direction=output)",
        "output_invoice_registration": "sc.invoice.registration(direction=output)",
    },
}

path = artifact_root() / "receipt_invoice_line_output_visible_enrich_write_result_v1.json"
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("RECEIPT_INVOICE_LINE_OUTPUT_VISIBLE_ENRICH=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
