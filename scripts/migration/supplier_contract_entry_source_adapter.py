#!/usr/bin/env python3
"""Extract supplier-contract entry user/time evidence from legacy MSSQL.

Input is the supplier contract gap CSV exported by business_fact_backfill_audit.py.
Output is consumed by supplier_contract_entry_source_backfill_write.py.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(os.getenv("ROOT_DIR", Path.cwd()))
INPUT_CSV = Path(
    os.getenv(
        "SUPPLIER_CONTRACT_ENTRY_REQUIRED_CSV",
        str(ROOT / "artifacts/business-fact-audit/sc_demo_after_scbs_source_creator_supplement/contract_supplier_entry_source_missing_rows_v1.csv"),
    )
)
ARTIFACT_ROOT = Path(
    os.getenv(
        "MIGRATION_ARTIFACT_ROOT",
        str(ROOT / "artifacts/migration/supplier_contract_entry_source_v1"),
    )
)
OUTPUT_CSV = ARTIFACT_ROOT / "supplier_contract_entry_source_from_legacy_mssql_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "supplier_contract_entry_source_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
CHUNK_SIZE = int(os.getenv("SUPPLIER_CONTRACT_ENTRY_CHUNK_SIZE", "500"))


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def clean_sql(field: str) -> str:
    return (
        "REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), "
        + field
        + "), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"
    )


def sql_literal(value: str) -> str:
    return "'" + clean(value).replace("'", "''") + "'"


def docker_container_state(container: str) -> str:
    completed = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Status}}", container],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "missing"
    return clean(completed.stdout) or "unknown"


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fail_summary(reason: str, detail: object | None = None) -> None:
    summary = {
        "status": "BLOCKED",
        "mode": "supplier_contract_entry_source_adapter",
        "reason": reason,
        "detail": detail or {},
        "input_csv": str(INPUT_CSV),
        "output_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, summary)
    raise RuntimeError(summary)


def read_required(path: Path) -> set[str]:
    required: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            legacy_contract_id = clean(row.get("legacy_contract_id"))
            if legacy_contract_id:
                required.add(legacy_contract_id)
    return required


def chunks(values: list[str], size: int):
    for index in range(0, len(values), size):
        yield values[index : index + size]


def sqlcmd(sql: str) -> list[str]:
    return [
        "docker",
        "exec",
        SQL_CONTAINER,
        SQLCMD,
        "-S",
        "localhost",
        "-U",
        "sa",
        "-P",
        SQL_PASSWORD,
        "-C",
        "-d",
        SQL_DATABASE,
        "-W",
        "-s",
        "\t",
        "-h",
        "-1",
        "-Q",
        sql,
    ]


def query_chunk(record_ids: list[str]) -> list[dict[str, str]]:
    values_sql = ", ".join(f"({sql_literal(item)})" for item in record_ids)
    sql = f"""
SET NOCOUNT ON;
WITH required(legacy_contract_id) AS (
  SELECT * FROM (VALUES {values_sql}) v(legacy_contract_id)
)
SELECT
  {clean_sql('src.Id')} AS legacy_contract_id,
  {clean_sql('src.LRRID')} AS entry_legacy_user_id,
  {clean_sql('src.f_LRR')} AS entry_user_text,
  COALESCE(CONVERT(varchar(23), src.f_LRRQ, 121), '') AS entry_time
FROM required r
JOIN dbo.T_GYSHT_INFO src ON src.Id = r.legacy_contract_id
WHERE NULLIF(LTRIM(RTRIM(COALESCE(CONVERT(varchar(max), src.f_LRR), ''))), '') IS NOT NULL
   OR src.f_LRRQ IS NOT NULL
ORDER BY src.Id;
"""
    completed = subprocess.run(sqlcmd(sql), text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            {
                "sqlcmd_failed": completed.returncode,
                "stdout": completed.stdout[-2000:],
                "stderr": completed.stderr[-2000:],
            }
        )
    rows: list[dict[str, str]] = []
    fields = ["legacy_contract_id", "entry_legacy_user_id", "entry_user_text", "entry_time"]
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("("):
            continue
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) != len(fields):
            raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(fields), "line": line[:500]})
        rows.append(dict(zip(fields, parts)))
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["legacy_contract_id", "entry_legacy_user_id", "entry_user_text", "entry_time"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


state = docker_container_state(SQL_CONTAINER)
if state != "running":
    fail_summary("legacy_mssql_container_not_running", {"container": SQL_CONTAINER, "state": state})

required = read_required(INPUT_CSV)
result_rows: list[dict[str, str]] = []
try:
    for part in chunks(sorted(required), CHUNK_SIZE):
        result_rows.extend(query_chunk(part))
except Exception as exc:
    fail_summary("legacy_mssql_query_failed", {"error": str(exc)})

write_csv(OUTPUT_CSV, result_rows)
summary = {
    "status": "PASS",
    "mode": "supplier_contract_entry_source_adapter",
    "input_csv": str(INPUT_CSV),
    "output_csv": str(OUTPUT_CSV),
    "required_count": len(required),
    "output_rows": len(result_rows),
    "missing_rows": len(required) - len({row["legacy_contract_id"] for row in result_rows}),
}
write_json(OUTPUT_JSON, summary)
print("SUPPLIER_CONTRACT_ENTRY_SOURCE=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
