#!/usr/bin/env python3
"""Export resolved partner import reviews back into the partner write contract."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_replay_manifest_v1.json").exists():
            return candidate
    return Path.cwd()


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
IMPORT_BATCH = os.getenv("PARTNER_IMPORT_REVIEW_BATCH", "partner_business_fit_v1")
OUTPUT_DIR = ARTIFACT_ROOT / "partner_business_aligned_rebuild_v1"
PROMOTION_CSV = OUTPUT_DIR / "partner_import_review_resolved_promotions_v1.csv"
IGNORED_CSV = OUTPUT_DIR / "partner_import_review_ignored_v1.csv"
RESULT_JSON = OUTPUT_DIR / "partner_import_review_resolution_export_result_v1.json"
PROMOTION_FIELDS = [
    "partner_key",
    "legacy_partner_source",
    "legacy_partner_id",
    "legacy_partner_ids",
    "name",
    "company_type",
    "customer_rank",
    "supplier_rank",
    "sc_supplier_type",
    "sc_region",
    "street",
    "sc_registered_capital",
    "sc_business_scope",
    "sc_default_tax_rate",
    "sc_default_tax_rate_text",
    "sc_account_name",
    "sc_bank_name",
    "sc_bank_account",
    "vat",
    "legacy_credit_code",
    "source_created_by",
    "source_created_at",
    "source_project_name",
    "source_document_state",
    "source_push_result",
    "source_tax_rate",
    "source_files",
    "legacy_source_evidence",
    "review_flags",
    "gate_action",
    "gate_reason",
]
IGNORED_FIELDS = [
    "import_batch",
    "legacy_partner_source",
    "legacy_partner_id",
    "partner_name",
    "review_reason",
    "gate_reason",
    "review_flags",
    "note",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def promotion_row(review) -> dict[str, object]:
    customer_rank = review.confirmed_customer_rank
    supplier_rank = review.confirmed_supplier_rank
    return {
        "partner_key": review.legacy_partner_id or "",
        "legacy_partner_source": review.legacy_partner_source or "",
        "legacy_partner_id": review.legacy_partner_id or "",
        "legacy_partner_ids": "",
        "name": review.partner_name or "",
        "company_type": review.company_type or "company",
        "customer_rank": customer_rank,
        "supplier_rank": supplier_rank,
        "sc_supplier_type": review.sc_supplier_type or "",
        "sc_region": review.sc_region or "",
        "street": review.street or "",
        "sc_registered_capital": review.sc_registered_capital or "",
        "sc_business_scope": review.sc_business_scope or "",
        "sc_default_tax_rate": review.sc_default_tax_rate or 0,
        "sc_default_tax_rate_text": review.sc_default_tax_rate_text or "",
        "sc_account_name": review.sc_account_name or "",
        "sc_bank_name": review.sc_bank_name or "",
        "sc_bank_account": review.sc_bank_account or "",
        "vat": review.vat or "",
        "legacy_credit_code": review.vat or "",
        "source_created_by": review.source_created_by or "",
        "source_created_at": review.source_created_at or "",
        "source_project_name": review.source_project_name or "",
        "source_document_state": review.source_document_state or "",
        "source_push_result": review.source_push_result or "",
        "source_tax_rate": review.sc_default_tax_rate_text or "",
        "source_files": review.source_files or "",
        "legacy_source_evidence": review.evidence or f"partner_import_review_resolved:{review.import_batch}:{review.legacy_partner_id}",
        "review_flags": "resolved_from_import_review",
        "gate_action": "write_candidate",
        "gate_reason": "",
    }


Review = env["sc.partner.import.review"].sudo()  # noqa: F821
resolved = Review.search([("import_batch", "=", IMPORT_BATCH), ("review_state", "=", "resolved")])
ignored = Review.search([("import_batch", "=", IMPORT_BATCH), ("review_state", "=", "ignored")])
promotion_rows: list[dict[str, object]] = []
invalid_rows: list[dict[str, object]] = []
for review in resolved:
    if not review.confirmed_customer_rank and not review.confirmed_supplier_rank:
        invalid_rows.append({"legacy_partner_id": review.legacy_partner_id, "error": "missing_confirmed_role"})
        continue
    promotion_rows.append(promotion_row(review))
ignored_rows = [
    {
        "import_batch": review.import_batch or "",
        "legacy_partner_source": review.legacy_partner_source or "",
        "legacy_partner_id": review.legacy_partner_id or "",
        "partner_name": review.partner_name or "",
        "review_reason": review.review_reason or "",
        "gate_reason": review.gate_reason or "",
        "review_flags": review.review_flags or "",
        "note": review.note or "",
    }
    for review in ignored
]
write_csv(PROMOTION_CSV, PROMOTION_FIELDS, promotion_rows)
write_csv(IGNORED_CSV, IGNORED_FIELDS, ignored_rows)
summary = {
    "status": "PASS" if not invalid_rows else "FAIL",
    "mode": "fresh_db_partner_import_review_resolution_export",
    "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    "database": env.cr.dbname,  # noqa: F821
    "import_batch": IMPORT_BATCH,
    "resolved_rows": len(resolved),
    "promotion_rows": len(promotion_rows),
    "ignored_rows": len(ignored_rows),
    "invalid_rows": invalid_rows[:20],
    "promotion_action_counts": dict(Counter(row["gate_action"] for row in promotion_rows)),
    "db_writes": 0,
    "promotion_csv": str(PROMOTION_CSV),
    "ignored_csv": str(IGNORED_CSV),
}
write_json(RESULT_JSON, summary)
print("PARTNER_IMPORT_REVIEW_RESOLUTION_EXPORT=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
