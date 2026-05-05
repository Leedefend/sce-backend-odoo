#!/usr/bin/env python3
"""Import SCBS stock-in material mapping candidates into Odoo review model."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def artifact_root() -> Path:
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


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


def to_int(value: str | None) -> int:
    try:
        return int(float(value or 0))
    except ValueError:
        return 0


def to_float(value: str | None) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def material_key(row: dict[str, str]) -> str:
    legacy_id = row.get("legacy_material_id") or ""
    return "|".join(
        [
            legacy_id.strip(),
            (row.get("material_name") or "").strip(),
            (row.get("spec_model") or "").strip(),
            (row.get("uom_text") or "").strip(),
        ]
    )


def browse_catalog(value: str | None):
    if not value:
        return False
    try:
        catalog_id = int(float(value))
    except ValueError:
        return False
    record = env["sc.material.catalog"].sudo().browse(catalog_id)  # noqa: F821
    return record.id if record.exists() else False


ARTIFACT_ROOT = artifact_root()
WORKBOOK = Path(os.getenv("SCBS_MATERIAL_MAPPING_CSV") or (repo_root() / "artifacts/migration/scbs_stock_in_material_mapping_workbook_v1.csv"))
OUTPUT_JSON = ARTIFACT_ROOT / "scbs_stock_in_material_map_import_result_v1.json"
PREVIEW_CSV = ARTIFACT_ROOT / "scbs_stock_in_material_map_import_preview_v1.csv"

if not WORKBOOK.exists():
    raise RuntimeError({"missing_scbs_material_mapping_workbook": str(WORKBOOK)})

MaterialMap = env["sc.legacy.scbs.material.map"].sudo()  # noqa: F821
company = env.company  # noqa: F821

created = 0
updated = 0
skipped = 0
preview_rows: list[dict[str, object]] = []

with WORKBOOK.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

for row in rows:
    key = material_key(row)
    if not key.strip("|"):
        skipped += 1
        continue
    exact_catalog_id = browse_catalog(row.get("exact_text_catalog_id"))
    name_spec_catalog_id = browse_catalog(row.get("name_spec_catalog_id"))
    accepted_catalog_id = browse_catalog(row.get("accepted_material_catalog_id"))
    target_catalog_id = browse_catalog(row.get("target_material_catalog_id"))
    suggested_catalog_id = accepted_catalog_id or target_catalog_id or exact_catalog_id or name_spec_catalog_id
    vals = {
        "source_table": "T_RK_RKDCB",
        "source_domain": "SCBS",
        "material_key": key,
        "legacy_material_id": row.get("legacy_material_id") or False,
        "material_name": row.get("material_name") or False,
        "spec_model": row.get("spec_model") or False,
        "uom_text": row.get("uom_text") or False,
        "company_id": company.id,
        "material_catalog_id": suggested_catalog_id or False,
        "suggested_action": row.get("suggested_action") or "create_or_map_material_catalog",
        "coverage_state": row.get("coverage_state") or "catalog_missing",
        "review_priority": to_int(row.get("review_priority")),
        "exact_text_catalog_id": exact_catalog_id or False,
        "exact_text_match_count": to_int(row.get("exact_text_match_count")),
        "name_spec_catalog_id": name_spec_catalog_id or False,
        "name_spec_match_count": to_int(row.get("name_spec_match_count")),
        "line_rows": to_int(row.get("line_rows")),
        "header_rows": to_int(row.get("header_rows")),
        "qty_total": to_float(row.get("qty")),
        "amount_total": to_float(row.get("amount")),
        "evidence": json.dumps(
            {
                "coverage_state": row.get("coverage_state"),
                "exact_text_catalog_id": row.get("exact_text_catalog_id"),
                "exact_text_match_count": row.get("exact_text_match_count"),
                "name_spec_catalog_id": row.get("name_spec_catalog_id"),
                "name_spec_match_count": row.get("name_spec_match_count"),
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
    }
    if row.get("suggested_action") == "manual_material_identity_required":
        vals["mapping_state"] = "conflict"
    else:
        vals["mapping_state"] = "candidate"

    existing = MaterialMap.search([("source_table", "=", "T_RK_RKDCB"), ("material_key", "=", key)], limit=1)
    if existing:
        existing.write(vals)
        updated += 1
        record = existing
        action = "updated"
    else:
        record = MaterialMap.create(vals)
        created += 1
        action = "created"
    if len(preview_rows) < 50:
        preview_rows.append(
            {
                "action": action,
                "record_id": record.id,
                "mapping_state": record.mapping_state,
                "suggested_action": record.suggested_action,
                "material_name": record.material_name or "",
                "spec_model": record.spec_model or "",
                "uom_text": record.uom_text or "",
                "amount_total": record.amount_total,
                "material_catalog_id": record.material_catalog_id.id if record.material_catalog_id else "",
            }
        )

env.cr.commit()  # noqa: F821

with PREVIEW_CSV.open("w", newline="", encoding="utf-8") as f:
    fields = [
        "action",
        "record_id",
        "mapping_state",
        "suggested_action",
        "material_name",
        "spec_model",
        "uom_text",
        "amount_total",
        "material_catalog_id",
    ]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(preview_rows)

summary = {
    "status": "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "source_csv": str(WORKBOOK),
    "rows": len(rows),
    "created": created,
    "updated": updated,
    "skipped": skipped,
    "model_count": MaterialMap.search_count([("source_domain", "=", "SCBS")]),
    "confirmed_count": MaterialMap.search_count([("source_domain", "=", "SCBS"), ("mapping_state", "=", "confirmed")]),
    "candidate_count": MaterialMap.search_count([("source_domain", "=", "SCBS"), ("mapping_state", "=", "candidate")]),
    "conflict_count": MaterialMap.search_count([("source_domain", "=", "SCBS"), ("mapping_state", "=", "conflict")]),
    "preview_csv": str(PREVIEW_CSV),
    "business_policy": "material_catalog_mapping_without_product_promotion",
}
OUTPUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("SCBS_STOCK_IN_MATERIAL_MAP_IMPORT=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
