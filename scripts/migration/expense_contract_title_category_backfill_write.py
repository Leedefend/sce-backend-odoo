#!/usr/bin/env python3
"""Backfill expense contract categories from contract titles."""

from __future__ import annotations

import json
import os
from pathlib import Path


OUTPUT_JSON_NAME = "expense_contract_title_category_backfill_write_result_v1.json"
CATEGORY_ROWS = (
    ("material", "材料", 10),
    ("labor", "劳务", 20),
    ("machine", "机械", 30),
    ("rental", "租赁", 40),
    ("subcontract", "专业分包", 50),
    ("other", "其他", 60),
)


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_backfill": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/expense_contract_category/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/expense_contract_category/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scalar(sql: str, params: list | tuple | None = None) -> int:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return int(row[0] or 0) if row else 0


ensure_allowed_db()

Dictionary = env["sc.dictionary"].sudo().with_context(active_test=False)  # noqa: F821
created = 0
for code, name, sequence in CATEGORY_ROWS:
    row = Dictionary.search([("type", "=", "expense_contract_category"), ("code", "=", code)], limit=1)
    values = {
        "name": name,
        "type": "expense_contract_category",
        "code": code,
        "sequence": sequence,
        "active": True,
    }
    if row:
        row.write(values)
    else:
        Dictionary.create(values)
        created += 1

env.cr.execute(  # noqa: F821
    """
    WITH category AS (
        SELECT code, id
          FROM sc_dictionary
         WHERE type = 'expense_contract_category'
           AND active
    ), classified AS (
        SELECT c.id AS contract_id,
               CASE
                 WHEN text_blob LIKE '%%材料%%'
                   OR text_blob LIKE '%%供货%%'
                   OR text_blob LIKE '%%采购%%'
                   OR text_blob LIKE '%%供应%%'
                   OR text_blob LIKE '%%商砼%%'
                   OR text_blob LIKE '%%混凝土%%'
                   OR text_blob LIKE '%%砂石%%'
                   OR text_blob LIKE '%%钢材%%'
                   OR text_blob LIKE '%%水泥%%'
                   OR text_blob LIKE '%%砖%%'
                   OR text_blob LIKE '%%管材%%'
                   OR text_blob LIKE '%%苗木%%'
                   THEN 'material'
                 WHEN text_blob LIKE '%%劳务%%'
                   OR text_blob LIKE '%%人工%%'
                   OR text_blob LIKE '%%用工%%'
                   OR text_blob LIKE '%%清包%%'
                   OR text_blob LIKE '%%班组%%'
                   OR text_blob LIKE '%%工资%%'
                   THEN 'labor'
                 WHEN text_blob LIKE '%%机械%%'
                   OR text_blob LIKE '%%挖机%%'
                   OR text_blob LIKE '%%装载机%%'
                   OR text_blob LIKE '%%吊车%%'
                   OR text_blob LIKE '%%台班%%'
                   OR text_blob LIKE '%%设备%%'
                   OR text_blob LIKE '%%泵车%%'
                   OR text_blob LIKE '%%塔吊%%'
                   THEN 'machine'
                 WHEN text_blob LIKE '%%租赁%%'
                   OR text_blob LIKE '%%租用%%'
                   OR text_blob LIKE '%%租入%%'
                   OR text_blob LIKE '%%租金%%'
                   OR text_blob LIKE '%%钢管租赁%%'
                   OR text_blob LIKE '%%周转材料%%'
                   THEN 'rental'
                 WHEN text_blob LIKE '%%分包%%'
                   OR text_blob LIKE '%%专业分包%%'
                   OR text_blob LIKE '%%专包%%'
                   OR text_blob LIKE '%%专业承包%%'
                   THEN 'subcontract'
                 ELSE 'other'
               END AS category_code
          FROM (
              SELECT id,
                     COALESCE(subject, '') || ' ' ||
                     COALESCE(legacy_visible_title, '') || ' ' ||
                     COALESCE(legacy_visible_category, '') || ' ' ||
                     COALESCE(legacy_contract_no, '') || ' ' ||
                     COALESCE(legacy_document_no, '') || ' ' ||
                     COALESCE(legacy_external_contract_no, '') || ' ' ||
                     COALESCE(note, '') AS text_blob
                FROM construction_contract
               WHERE type = 'in'
          ) c
    )
    UPDATE construction_contract c
       SET expense_contract_category_auto_id = auto_category.id,
           expense_contract_category_id = auto_category.id,
           write_uid = 1,
           write_date = NOW()
      FROM classified
      JOIN category auto_category ON auto_category.code = classified.category_code
     WHERE c.id = classified.contract_id
    """
)
updated = env.cr.rowcount  # noqa: F821
env.cr.commit()  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    SELECT d.code, d.name, COUNT(c.id)
      FROM sc_dictionary d
      LEFT JOIN construction_contract c
        ON c.expense_contract_category_id = d.id
       AND c.type = 'in'
     WHERE d.type = 'expense_contract_category'
     GROUP BY d.code, d.name, d.sequence
     ORDER BY d.sequence
    """
)
distribution = [
    {"code": row[0], "name": row[1], "count": int(row[2] or 0)}
    for row in env.cr.fetchall()  # noqa: F821
]
missing = scalar(
    """
    SELECT COUNT(*)
      FROM construction_contract
     WHERE type = 'in'
       AND expense_contract_category_id IS NULL
    """
)
payload = {
    "status": "PASS" if missing == 0 else "FAIL",
    "mode": "expense_contract_title_category_backfill_write",
    "database": env.cr.dbname,  # noqa: F821
    "created_default_category_count": created,
    "updated_expense_contract_count": updated,
    "missing_category_count": missing,
    "distribution": distribution,
}
write_json(artifact_root() / OUTPUT_JSON_NAME, payload)
print("EXPENSE_CONTRACT_TITLE_CATEGORY_BACKFILL_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise RuntimeError(payload)
