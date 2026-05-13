#!/usr/bin/env python3
"""Create minimal expense contract anchors referenced by legacy invoice lines."""

from __future__ import annotations

import json
import os
from pathlib import Path


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


Contract = env["construction.contract"].sudo().with_context(sc_test_mode=True)  # noqa: F821
artifact_root = resolve_artifact_root()
output_json = artifact_root / "fresh_db_invoice_contract_anchor_projection_write_result_v1.json"

env.cr.execute(  # noqa: F821
    """
    WITH source AS (
      SELECT
        NULLIF(l.contract_legacy_id, '') AS legacy_contract_id,
        COUNT(*) AS invoice_line_count,
        COUNT(DISTINCT l.project_id) FILTER (WHERE l.project_id IS NOT NULL) AS project_count,
        MIN(l.project_id) FILTER (WHERE l.project_id IS NOT NULL) AS project_id,
        COUNT(DISTINCT l.partner_id) FILTER (WHERE l.partner_id IS NOT NULL) AS partner_count,
        MIN(l.partner_id) FILTER (WHERE l.partner_id IS NOT NULL) AS partner_id,
        MIN(NULLIF(l.project_legacy_id, '')) AS legacy_project_id,
        MIN(NULLIF(l.project_name, '')) AS project_name,
        MIN(NULLIF(l.supplier_name, '')) AS supplier_name,
        MIN(NULLIF(l.document_no, '')) AS sample_document_no,
        MIN(NULLIF(l.invoice_no, '')) AS sample_invoice_no,
        SUM(COALESCE(l.amount_total, 0)) AS amount_total
      FROM sc_legacy_invoice_registration_line l
      LEFT JOIN construction_contract c ON c.legacy_contract_id = l.contract_legacy_id
      WHERE l.active
        AND NULLIF(l.contract_legacy_id, '') IS NOT NULL
        AND LOWER(l.contract_legacy_id) <> 'null'
        AND c.id IS NULL
      GROUP BY l.contract_legacy_id
    )
    SELECT
      legacy_contract_id,
      invoice_line_count,
      project_count,
      project_id,
      partner_count,
      partner_id,
      legacy_project_id,
      project_name,
      supplier_name,
      sample_document_no,
      sample_invoice_no,
      amount_total
    FROM source
    WHERE project_count = 1
      AND partner_count = 1
      AND project_id IS NOT NULL
      AND partner_id IS NOT NULL
    ORDER BY legacy_contract_id
    """
)
rows = env.cr.dictfetchall()  # noqa: F821

created = 0
skipped_existing = 0
blocked_missing_required = 0
for row in rows:
    legacy_contract_id = row["legacy_contract_id"]
    if Contract.search([("legacy_contract_id", "=", legacy_contract_id)], limit=1):
        skipped_existing += 1
        continue
    project_id = row["project_id"]
    partner_id = row["partner_id"]
    if not project_id or not partner_id:
        blocked_missing_required += 1
        continue
    subject = "发票关联支出合同"
    if row.get("supplier_name"):
        subject = f"发票关联支出合同-{row['supplier_name']}"
    vals = {
        "legacy_contract_id": legacy_contract_id,
        "legacy_project_id": row.get("legacy_project_id") or "",
        "legacy_counterparty_text": row.get("supplier_name") or "",
        "subject": subject[:120],
        "type": "in",
        "project_id": project_id,
        "partner_id": partner_id,
        "note": "\n".join(
            item
            for item in [
                "[migration:invoice_contract_anchor]",
                f"legacy_contract_id={legacy_contract_id}",
                f"invoice_line_count={int(row.get('invoice_line_count') or 0)}",
                f"amount_total={float(row.get('amount_total') or 0):.2f}",
                row.get("project_name") or "",
                row.get("supplier_name") or "",
                row.get("sample_document_no") or "",
                row.get("sample_invoice_no") or "",
            ]
            if item
        ),
    }
    Contract.create(vals)
    created += 1

env.cr.execute(  # noqa: F821
    """
    WITH source AS (
      SELECT
        l.contract_legacy_id,
        COUNT(*) AS rows,
        COUNT(DISTINCT l.project_id) FILTER (WHERE l.project_id IS NOT NULL) AS project_count,
        COUNT(DISTINCT l.partner_id) FILTER (WHERE l.partner_id IS NOT NULL) AS partner_count
      FROM sc_legacy_invoice_registration_line l
      LEFT JOIN construction_contract c ON c.legacy_contract_id = l.contract_legacy_id
      WHERE l.active
        AND NULLIF(l.contract_legacy_id, '') IS NOT NULL
        AND LOWER(l.contract_legacy_id) <> 'null'
        AND c.id IS NULL
      GROUP BY l.contract_legacy_id
    )
    SELECT COUNT(*), COALESCE(SUM(rows), 0)
    FROM source
    WHERE project_count <> 1 OR partner_count <> 1
    """
)
blocked_ambiguous_contracts, blocked_ambiguous_invoice_lines = env.cr.fetchone()  # noqa: F821
env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_invoice_contract_anchor_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "candidate_contracts": len(rows),
    "created_contracts": created,
    "skipped_existing": skipped_existing,
    "blocked_missing_required": blocked_missing_required,
    "blocked_ambiguous_contracts": int(blocked_ambiguous_contracts or 0),
    "blocked_ambiguous_invoice_lines": int(blocked_ambiguous_invoice_lines or 0),
}
write_json(output_json, payload)
print("FRESH_DB_INVOICE_CONTRACT_ANCHOR_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
