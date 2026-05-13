# -*- coding: utf-8 -*-
"""Sync stored operation_strategy projections from project business facts.

Run with:
    odoo shell -d <db> -c <config> < scripts/migration/visible_surface_operation_strategy_sync_write.py
"""

import json
import os
import re
from pathlib import Path


SAFE_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def safe_ident(value):
    value = str(value or "")
    if not SAFE_IDENTIFIER_RE.match(value):
        raise ValueError("unsafe SQL identifier: %r" % value)
    return value


def artifact_path():
    root = Path(
        os.getenv("ARTIFACT_ROOT")
        or os.getenv("MIGRATION_ARTIFACT_ROOT")
        or "artifacts/visible_data_usability_closure"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root / "visible_surface_operation_strategy_sync_result_v1.json"


def candidate_models():
    names = []
    for model_name in sorted(env):  # noqa: F821
        model = env[model_name]  # noqa: F821
        if "project_id" not in model._fields or "operation_strategy" not in model._fields:
            continue
        field = model._fields["operation_strategy"]
        if not getattr(field, "store", False):
            continue
        names.append(model_name)
    return names


def table_has_columns(table, columns):
    env.cr.execute(  # noqa: F821
        """
        SELECT column_name
          FROM information_schema.columns
         WHERE table_schema = current_schema()
           AND table_name = %s
           AND column_name = ANY(%s)
        """,
        (table, list(columns)),
    )
    return {row[0] for row in env.cr.fetchall()}  # noqa: F821


def count_mismatch(table):
    env.cr.execute(  # noqa: F821
        """
        SELECT COUNT(*)
          FROM {table} AS t
          JOIN project_project AS p ON p.id = t.project_id
         WHERE p.operation_strategy IS NOT NULL
           AND t.operation_strategy IS DISTINCT FROM p.operation_strategy
        """.format(table=safe_ident(table))
    )
    return int(env.cr.fetchone()[0])  # noqa: F821


def sync_table(table):
    env.cr.execute(  # noqa: F821
        """
        UPDATE {table} AS t
           SET operation_strategy = p.operation_strategy
          FROM project_project AS p
         WHERE p.id = t.project_id
           AND p.operation_strategy IS NOT NULL
           AND t.operation_strategy IS DISTINCT FROM p.operation_strategy
        """.format(table=safe_ident(table))
    )
    return int(env.cr.rowcount or 0)  # noqa: F821


results = []
for model_name in candidate_models():
    model = env[model_name].sudo()  # noqa: F821
    table = safe_ident(model._table)
    if {"id", "project_id", "operation_strategy"} - table_has_columns(
        table, {"id", "project_id", "operation_strategy"}
    ):
        continue
    before = count_mismatch(table)
    updated = sync_table(table) if before else 0
    after = count_mismatch(table)
    if before or updated or after:
        results.append(
            {
                "model": model_name,
                "table": table,
                "mismatch_before": before,
                "updated": updated,
                "mismatch_after": after,
            }
        )

payload = {
    "status": "PASS" if all(row["mismatch_after"] == 0 for row in results) else "FAIL",
    "updated_total": sum(row["updated"] for row in results),
    "models": results,
}
path = artifact_path()
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
env.cr.commit()  # noqa: F821
print("VISIBLE_SURFACE_OPERATION_STRATEGY_SYNC=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
