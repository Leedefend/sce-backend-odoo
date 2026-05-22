#!/usr/bin/env python3
"""Backfill legacy receipt type onto receipt income runtime records."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def resolve_repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def table_has_column(table: str, column: str) -> bool:
    env.cr.execute(  # noqa: F821
        """
        SELECT EXISTS (
          SELECT 1
          FROM information_schema.columns
          WHERE table_name = %s AND column_name = %s
        )
        """,
        (table, column),
    )
    return bool(env.cr.fetchone()[0])  # noqa: F821


def read_receipt_types(repo_root: Path) -> list[tuple[str, str, str]]:
    path = Path(os.getenv("MIGRATION_RECEIPT_RAW_CSV", str(repo_root / "tmp/raw/receipt/receipt.csv")))
    if not path.exists():
        return []
    rows: list[tuple[str, str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            legacy_id = (row.get("Id") or "").strip()
            receipt_type = (row.get("type") or "").strip()
            receipt_subtype = (row.get("BT") or "").strip()
            if legacy_id and (receipt_type or receipt_subtype):
                rows.append((legacy_id, receipt_type, receipt_subtype))
    return rows


ensure_allowed_db()
repo_root = resolve_repo_root()
artifact_root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(repo_root / "artifacts/migration")))
output_json = artifact_root / "visible_surface_receipt_income_type_normalize_write_result_v1.json"

required = [
    ("sc_receipt_income", "legacy_receipt_type"),
    ("sc_receipt_income", "legacy_receipt_subtype"),
    ("sc_legacy_receipt_income_fact", "receipt_type"),
    ("sc_legacy_receipt_income_fact", "receipt_subtype"),
    ("sc_legacy_receipt_residual_fact", "legacy_receipt_type"),
    ("sc_legacy_receipt_residual_fact", "legacy_receipt_subtype"),
]
missing = [f"{table}.{column}" for table, column in required if not table_has_column(table, column)]
if missing:
    raise RuntimeError({"missing_columns": missing, "hint": "upgrade smart_construction_core before running"})

before = {}
env.cr.execute("SELECT COUNT(*) FROM sc_receipt_income WHERE COALESCE(legacy_receipt_type, '') <> ''")  # noqa: F821
before["runtime_with_legacy_receipt_type"] = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_receipt_income WHERE COALESCE(legacy_receipt_subtype, '') <> ''")  # noqa: F821
before["runtime_with_legacy_receipt_subtype"] = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_receipt_income_fact WHERE COALESCE(receipt_type, '') <> ''")  # noqa: F821
before["legacy_fact_with_receipt_type"] = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_receipt_income_fact WHERE COALESCE(receipt_subtype, '') <> ''")  # noqa: F821
before["legacy_fact_with_receipt_subtype"] = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_receipt_residual_fact WHERE COALESCE(legacy_receipt_type, '') <> ''")  # noqa: F821
before["residual_fact_with_legacy_receipt_type"] = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_receipt_residual_fact WHERE COALESCE(legacy_receipt_subtype, '') <> ''")  # noqa: F821
before["residual_fact_with_legacy_receipt_subtype"] = env.cr.fetchone()[0]  # noqa: F821

receipt_type_rows = read_receipt_types(repo_root)
env.cr.execute("DROP TABLE IF EXISTS tmp_receipt_income_legacy_type")  # noqa: F821
env.cr.execute("CREATE TEMP TABLE tmp_receipt_income_legacy_type (legacy_record_id text PRIMARY KEY, receipt_type text, receipt_subtype text) ON COMMIT DROP")  # noqa: F821
if receipt_type_rows:
    env.cr.executemany(  # noqa: F821
        """
        INSERT INTO tmp_receipt_income_legacy_type (legacy_record_id, receipt_type, receipt_subtype)
        VALUES (%s, %s, %s)
        ON CONFLICT (legacy_record_id) DO UPDATE SET
          receipt_type = EXCLUDED.receipt_type,
          receipt_subtype = EXCLUDED.receipt_subtype
        """,
        receipt_type_rows,
    )

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_legacy_receipt_income_fact f
       SET receipt_type = NULLIF(t.receipt_type, ''),
           receipt_subtype = NULLIF(t.receipt_subtype, '')
      FROM tmp_receipt_income_legacy_type t
     WHERE f.legacy_record_id = t.legacy_record_id
       AND (
         COALESCE(f.receipt_type, '') <> COALESCE(t.receipt_type, '')
         OR COALESCE(f.receipt_subtype, '') <> COALESCE(t.receipt_subtype, '')
       )
    """
)
legacy_fact_updated = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_legacy_receipt_residual_fact
       SET legacy_receipt_type = COALESCE(NULLIF(legacy_receipt_type, ''), NULLIF(receipt_type, '')),
           legacy_receipt_subtype = COALESCE(NULLIF(legacy_receipt_subtype, ''), NULLIF(legacy_receipt_subtype, ''))
     WHERE COALESCE(legacy_receipt_type, '') = ''
       AND COALESCE(receipt_type, '') <> ''
    """
)
residual_fact_updated = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_legacy_receipt_residual_fact f
       SET legacy_receipt_type = COALESCE(NULLIF(t.receipt_type, ''), NULLIF(f.legacy_receipt_type, ''), NULLIF(f.receipt_type, '')),
           legacy_receipt_subtype = COALESCE(NULLIF(t.receipt_subtype, ''), NULLIF(f.legacy_receipt_subtype, ''))
      FROM tmp_receipt_income_legacy_type t
     WHERE f.legacy_record_id = t.legacy_record_id
       AND (
         COALESCE(f.legacy_receipt_type, '') <> COALESCE(t.receipt_type, '')
         OR COALESCE(f.legacy_receipt_subtype, '') <> COALESCE(t.receipt_subtype, '')
       )
    """
)
residual_fact_updated += env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_receipt_income r
       SET legacy_receipt_type = f.receipt_type,
           legacy_receipt_subtype = f.receipt_subtype
      FROM sc_legacy_receipt_income_fact f
     WHERE r.legacy_source_model = 'sc.legacy.receipt.income.fact'
       AND r.legacy_record_id = f.legacy_record_id
       AND (COALESCE(f.receipt_type, '') <> '' OR COALESCE(f.receipt_subtype, '') <> '')
       AND (
         COALESCE(r.legacy_receipt_type, '') <> COALESCE(f.receipt_type, '')
         OR COALESCE(r.legacy_receipt_subtype, '') <> COALESCE(f.receipt_subtype, '')
       )
    """
)
runtime_from_income_fact_updated = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_receipt_income r
       SET legacy_receipt_type = COALESCE(NULLIF(f.legacy_receipt_type, ''), NULLIF(f.receipt_type, '')),
           legacy_receipt_subtype = f.legacy_receipt_subtype
      FROM sc_legacy_receipt_residual_fact f
     WHERE r.legacy_source_model = 'sc.legacy.receipt.residual.fact'
       AND r.legacy_record_id = f.legacy_record_id
       AND (
         COALESCE(NULLIF(f.legacy_receipt_type, ''), NULLIF(f.receipt_type, '')) IS NOT NULL
         OR COALESCE(f.legacy_receipt_subtype, '') <> ''
       )
       AND (
         COALESCE(r.legacy_receipt_type, '') <> COALESCE(NULLIF(f.legacy_receipt_type, ''), NULLIF(f.receipt_type, ''), '')
         OR COALESCE(r.legacy_receipt_subtype, '') <> COALESCE(f.legacy_receipt_subtype, '')
       )
    """
)
runtime_from_residual_fact_updated = env.cr.rowcount  # noqa: F821

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_receipt_income WHERE COALESCE(legacy_receipt_type, '') <> ''")  # noqa: F821
runtime_with_type = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_receipt_income WHERE COALESCE(legacy_receipt_subtype, '') <> ''")  # noqa: F821
runtime_with_subtype = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute(  # noqa: F821
    """
    SELECT legacy_receipt_type, COUNT(*), COALESCE(SUM(amount), 0)
    FROM sc_receipt_income
    WHERE COALESCE(legacy_receipt_type, '') <> ''
    GROUP BY legacy_receipt_type
    ORDER BY COUNT(*) DESC
    """
)
runtime_type_counts = [
    {"receipt_type": row[0], "count": row[1], "amount": str(row[2])}
    for row in env.cr.fetchall()  # noqa: F821
]
env.cr.execute(  # noqa: F821
    """
    SELECT legacy_receipt_subtype, COUNT(*), COALESCE(SUM(amount), 0)
    FROM sc_receipt_income
    WHERE COALESCE(legacy_receipt_subtype, '') <> ''
    GROUP BY legacy_receipt_subtype
    ORDER BY COUNT(*) DESC
    LIMIT 40
    """
)
runtime_subtype_counts = [
    {"receipt_subtype": row[0], "count": row[1], "amount": str(row[2])}
    for row in env.cr.fetchall()  # noqa: F821
]

payload = {
    "status": "PASS",
    "mode": "visible_surface_receipt_income_type_normalize_write",
    "database": env.cr.dbname,  # noqa: F821
    "raw_receipt_type_rows": len(receipt_type_rows),
    "before": before,
    "legacy_fact_updated": legacy_fact_updated,
    "residual_fact_updated": residual_fact_updated,
    "runtime_from_income_fact_updated": runtime_from_income_fact_updated,
    "runtime_from_residual_fact_updated": runtime_from_residual_fact_updated,
    "runtime_with_legacy_receipt_type": runtime_with_type,
    "runtime_with_legacy_receipt_subtype": runtime_with_subtype,
    "runtime_type_counts": runtime_type_counts,
    "runtime_subtype_counts": runtime_subtype_counts,
    "decision": "receipt_income_legacy_receipt_type_visible",
}
write_json(output_json, payload)
print("VISIBLE_SURFACE_RECEIPT_INCOME_TYPE_NORMALIZE_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
