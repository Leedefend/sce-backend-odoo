#!/usr/bin/env python3
"""Probe same-table legacy record key collisions across restored legacy databases."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration/business_fact_upgrade"))
SOURCE_SPEC = os.getenv(
    "LEGACY_BUSINESS_FACT_SOURCES",
    "main:legacy-mssql-restore:LegacyDb,scbs:legacy-mssql-scbs:LegacyScbs20260417",
)
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD") or os.getenv("LEGACY_MSSQL_PASSWORD") or "LegacyRestore!2026"
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
OUTPUT_JSON = ARTIFACT_ROOT / "legacy_multi_db_replay_key_collision_probe_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "legacy_multi_db_replay_key_collision_probe_v1.md"

BUSINESS_CLASSES = {
    "candidate_effective_business_fact",
    "candidate_secondary_business_fact",
    "candidate_needs_manual_screen",
}
ID_CANDIDATES = ("Id", "ID", "id", "Guid", "GUID", "Pid", "PID")
MAX_TABLES = int(os.getenv("LEGACY_KEY_COLLISION_MAX_TABLES", "25"))
SAMPLE_IDS = int(os.getenv("LEGACY_KEY_COLLISION_SAMPLE_IDS", "300"))


def parse_sources(raw: str) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for item in raw.split(","):
        parts = [part.strip() for part in item.split(":")]
        if len(parts) != 3 or not all(parts):
            raise RuntimeError({"invalid_legacy_business_fact_source": item, "expected": "label:container:database"})
        label, container, database = parts
        sources.append({"label": label, "container": container, "database": database})
    if len(sources) < 2:
        raise RuntimeError({"at_least_two_sources_required": raw})
    return sources


def source_root(label: str) -> Path:
    return ARTIFACT_ROOT if label == "main" else ARTIFACT_ROOT / label


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def sql_identifier(name: str) -> str:
    return "[" + name.replace("]", "]]") + "]"


def run_sql(source: dict[str, str], sql: str) -> str:
    command = [
        "docker",
        "exec",
        "-i",
        source["container"],
        "bash",
        "-lc",
        f"{SQLCMD} -S localhost -U sa -P {shell_quote(SQL_PASSWORD)} -C -d {shell_quote(source['database'])} -W -s '|' -h -1",
    ]
    completed = subprocess.run(command, input=sql, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            {
                "sqlcmd_failed": completed.returncode,
                "source": source,
                "stdout": completed.stdout[-2000:],
                "stderr": completed.stderr[-2000:],
            }
        )
    return completed.stdout


def load_candidate_tables(label: str) -> dict[str, int]:
    path = source_root(label) / "legacy_db_full_business_fact_loss_scan_v1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    tables: dict[str, int] = {}
    for row in payload.get("tables") or []:
        row_count = int(row.get("row_count") or 0)
        if row.get("classification") in BUSINESS_CLASSES and row_count > 0:
            tables[str(row["table"])] = row_count
    return tables


def id_columns(source: dict[str, str], table: str) -> list[str]:
    sql = f"""
SET NOCOUNT ON;
SELECT c.name
FROM sys.columns c
JOIN sys.tables t ON t.object_id = c.object_id
JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE s.name = 'dbo' AND t.name = N'{table.replace("'", "''")}'
ORDER BY c.column_id;
"""
    columns = [line.strip() for line in run_sql(source, sql).splitlines() if line.strip()]
    preferred = [column for column in ID_CANDIDATES if column in columns]
    if preferred:
        return preferred
    return [column for column in columns if column.lower().endswith("id")][:3]


def load_ids(source: dict[str, str], table: str, column: str) -> set[str]:
    sql = f"""
SET NOCOUNT ON;
SELECT TOP ({SAMPLE_IDS}) key_value
FROM (
  SELECT DISTINCT CONVERT(varchar(200), {sql_identifier(column)}) AS key_value
  FROM dbo.{sql_identifier(table)}
  WHERE {sql_identifier(column)} IS NOT NULL
    AND NULLIF(LTRIM(RTRIM(CONVERT(varchar(200), {sql_identifier(column)}))), '') IS NOT NULL
) sample
ORDER BY key_value;
"""
    return {line.strip() for line in run_sql(source, sql).splitlines() if line.strip()}


def main() -> int:
    sources = parse_sources(SOURCE_SPEC)
    left, right = sources[0], sources[1]
    left_tables = load_candidate_tables(left["label"])
    right_tables = load_candidate_tables(right["label"])
    common_tables_all = sorted(set(left_tables) & set(right_tables))
    common_tables = sorted(
        common_tables_all,
        key=lambda table: (-min(left_tables[table], right_tables[table]), table),
    )[:MAX_TABLES]

    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for table in common_tables:
        left_columns = id_columns(left, table)
        right_columns = id_columns(right, table)
        common_columns = [column for column in left_columns if column in set(right_columns)]
        if not common_columns:
            skipped.append({"table": table, "reason": "no_common_id_column", "left": left_columns, "right": right_columns})
            continue
        column = common_columns[0]
        left_ids = load_ids(left, table, column)
        right_ids = load_ids(right, table, column)
        collisions = sorted(left_ids & right_ids)
        rows.append(
            {
                "table": table,
                "id_column": column,
                "left_rows": left_tables.get(table),
                "right_rows": right_tables.get(table),
                "left_sample_ids": len(left_ids),
                "right_sample_ids": len(right_ids),
                "collision_sample_count": len(collisions),
                "collision_examples": collisions[:20],
            }
        )

    collision_tables = [row for row in rows if row["collision_sample_count"]]
    payload = {
        "status": "PASS",
        "mode": "legacy_multi_db_replay_key_collision_probe",
        "artifact_root": str(ARTIFACT_ROOT),
        "source_spec": SOURCE_SPEC,
        "sources": sources,
        "common_candidate_tables": len(common_tables_all),
        "checked_table_limit": MAX_TABLES,
        "checked_tables": len(rows),
        "skipped_tables": skipped,
        "collision_tables": collision_tables,
        "summary": {
            "collision_table_count": len(collision_tables),
            "collision_key_sample_count": sum(int(row["collision_sample_count"]) for row in collision_tables),
            "requires_source_database_in_replay_key": bool(collision_tables),
            "sample_ids_per_table": SAMPLE_IDS,
        },
        "decision": "source_database_dimension_required" if collision_tables else "source_table_record_key_currently_sufficient",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = f"""# Legacy Multi DB Replay Key Collision Probe v1

Status: {payload["status"]}

Decision: `{payload["decision"]}`

## Summary

```json
{json.dumps(payload["summary"], ensure_ascii=False, indent=2)}
```

## Collision Tables

```json
{json.dumps(collision_tables[:80], ensure_ascii=False, indent=2)}
```

## Skipped

```json
{json.dumps(skipped[:80], ensure_ascii=False, indent=2)}
```
"""
    OUTPUT_REPORT.write_text(report, encoding="utf-8")
    print(
        "LEGACY_MULTI_DB_REPLAY_KEY_COLLISION_PROBE="
        + json.dumps(
            {
                "status": payload["status"],
                "common_candidate_tables": payload["common_candidate_tables"],
                "checked_tables": payload["checked_tables"],
                "collision_table_count": payload["summary"]["collision_table_count"],
                "collision_key_sample_count": payload["summary"]["collision_key_sample_count"],
                "decision": payload["decision"],
                "artifact_root": str(ARTIFACT_ROOT),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
