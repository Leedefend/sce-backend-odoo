"""Project legacy tax deduction facts into the user-facing tax deduction entry."""

from __future__ import annotations

import json
import os
from pathlib import Path

from odoo import fields


def artifact_root() -> Path:
    root = os.environ.get("MIGRATION_ARTIFACT_ROOT") or os.environ.get("HISTORY_CONTINUITY_ARTIFACT_ROOT")
    if root:
        return Path(root)
    candidates = [
        Path("/mnt/artifacts/migration"),
        Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"),  # noqa: F821
    ]
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


output_json = artifact_root() / "fresh_db_tax_deduction_registration_projection_write_result_v1.json"
output_json.parent.mkdir(parents=True, exist_ok=True)

Target = env["sc.tax.deduction.registration"].sudo()  # noqa: F821
Legacy = env["sc.legacy.tax.deduction.fact"].sudo()  # noqa: F821


def target_state(document_state):
    state = str(document_state or "").strip()
    if state in {"-1", "cancel", "cancelled", "作废", "已作废"}:
        return "cancel"
    if state in {"0", "draft", "未审核"}:
        return "draft"
    if state in {"1", "审核中", "已确认"}:
        return "confirmed"
    return "legacy_confirmed"


source_domain = [("active", "=", True), ("project_id", "!=", False)]
candidate_count = Legacy.search_count(source_domain)
before = Target.search_count([])

created = 0
updated = 0
skipped_missing_project = 0

for line in Legacy.search(source_domain, order="document_date desc, id desc"):
    if not line.project_id:
        skipped_missing_project += 1
        continue
    document_date = line.document_date or line.invoice_date or fields.Date.context_today(Target)
    values = {
        "source_origin": "legacy",
        "state": target_state(line.document_state),
        "document_no": line.document_no,
        "document_date": document_date,
        "deduction_confirm_date": line.deduction_confirm_date or document_date,
        "project_id": line.project_id.id,
        "partner_id": line.partner_id.id if line.partner_id else False,
        "partner_name": line.partner_name,
        "invoice_no": line.invoice_no,
        "invoice_code": line.invoice_code,
        "invoice_date": line.invoice_date or None,
        "invoice_amount_untaxed": line.invoice_amount_untaxed or 0.0,
        "invoice_tax_amount": line.invoice_tax_amount or 0.0,
        "invoice_amount_total": line.invoice_amount_total or 0.0,
        "deduction_amount": line.deduction_amount or 0.0,
        "deduction_tax_amount": line.deduction_tax_amount or 0.0,
        "deduction_surcharge_amount": line.deduction_surcharge_amount or 0.0,
        "is_transfer_out": bool(line.is_transfer_out),
        "legacy_source_model": "sc.legacy.tax.deduction.fact",
        "legacy_source_table": line.source_table,
        "legacy_record_id": line.legacy_line_id,
        "legacy_document_state": line.document_state or "历史已确认",
        "creator_legacy_user_id": line.creator_legacy_user_id,
        "creator_name": line.creator_name,
        "created_time": line.created_time or None,
        "note": line.note or None,
    }
    existing = Target.search(
        [
            ("legacy_source_model", "=", values["legacy_source_model"]),
            ("legacy_record_id", "=", values["legacy_record_id"]),
        ],
        limit=1,
    )
    if existing:
        env.cr.execute(  # noqa: F821
            """
            UPDATE sc_tax_deduction_registration
               SET state = %s,
                   document_no = %s,
                   document_date = %s,
                   deduction_confirm_date = %s,
                   project_id = %s,
                   partner_id = %s,
                   partner_name = %s,
                   invoice_no = %s,
                   invoice_code = %s,
                   invoice_date = %s,
                   invoice_amount_untaxed = %s,
                   invoice_tax_amount = %s,
                   invoice_amount_total = %s,
                   deduction_amount = %s,
                   deduction_tax_amount = %s,
                   deduction_surcharge_amount = %s,
                   is_transfer_out = %s,
                   legacy_source_table = %s,
                   legacy_document_state = %s,
                   creator_legacy_user_id = %s,
                   creator_name = %s,
                   created_time = %s,
                   note = %s,
                   active = TRUE,
                   write_date = NOW()
             WHERE id = %s
            """,
            [
                values["state"],
                values["document_no"],
                values["document_date"],
                values["deduction_confirm_date"],
                values["project_id"],
                values["partner_id"] or None,
                values["partner_name"],
                values["invoice_no"],
                values["invoice_code"],
                values["invoice_date"],
                values["invoice_amount_untaxed"],
                values["invoice_tax_amount"],
                values["invoice_amount_total"],
                values["deduction_amount"],
                values["deduction_tax_amount"],
                values["deduction_surcharge_amount"],
                values["is_transfer_out"],
                values["legacy_source_table"],
                values["legacy_document_state"],
                values["creator_legacy_user_id"],
                values["creator_name"],
                values["created_time"],
                values["note"],
                existing.id,
            ],
        )
        updated += 1
        continue
    values["name"] = line.document_no or f"DKDJ-{document_date.strftime('%Y%m%d')}-{created + 1:05d}"
    Target.create(values)
    created += 1

env.cr.commit()  # noqa: F821

after = Target.search_count([])
visible = Target.search_count([("active", "=", True)])
expected_visible = candidate_count - skipped_missing_project
result = {
    "mode": "fresh_db_tax_deduction_registration_projection_write",
    "source_domain": source_domain,
    "candidate_count": candidate_count,
    "before": before,
    "created": created,
    "updated": updated,
    "skipped_missing_project": skipped_missing_project,
    "expected_visible_rows": expected_visible,
    "after": after,
    "visible_rows": visible,
    "status": "PASS" if visible >= expected_visible and after >= expected_visible else "REVIEW",
}

output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
