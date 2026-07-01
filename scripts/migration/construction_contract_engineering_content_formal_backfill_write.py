#!/usr/bin/env python3
"""Backfill formal contract engineering content from historical visible content."""

from __future__ import annotations

import json
import os
from pathlib import Path


def _artifact_path() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or "/tmp")
    root.mkdir(parents=True, exist_ok=True)
    return root / "construction_contract_engineering_content_formal_backfill_result.json"


def _column_exists(table: str, column: str) -> bool:
    env.cr.execute(  # noqa: F821
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = %s
           AND column_name = %s
         LIMIT 1
        """,
        (table, column),
    )
    return bool(env.cr.fetchone())  # noqa: F821


TABLE = "construction_contract"
required_columns = {"engineering_content", "legacy_visible_engineering_content"}
missing = sorted(column for column in required_columns if not _column_exists(TABLE, column))
if missing:
    result = {
        "mode": "construction_contract_engineering_content_formal_backfill",
        "status": "skipped",
        "missing_columns": missing,
    }
else:
    env.cr.execute(  # noqa: F821
        """
        UPDATE construction_contract
           SET engineering_content = legacy_visible_engineering_content
         WHERE COALESCE(engineering_content, '') = ''
           AND COALESCE(legacy_visible_engineering_content, '') <> ''
        """
    )
    updated = env.cr.rowcount  # noqa: F821
    env.cr.commit()  # noqa: F821
    result = {
        "mode": "construction_contract_engineering_content_formal_backfill",
        "status": "ok",
        "updated": updated,
    }

output = _artifact_path()
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
