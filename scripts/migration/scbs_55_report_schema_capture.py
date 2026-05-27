#!/usr/bin/env python3
"""Capture old SCBS LowCode/Report schema from the restored MSSQL database.

This script is read-only. It is intended to run on the server host where the
`legacy-mssql-restore` container is available. It extracts report SQL,
parameters, and user-visible columns for the low-code report entries in the
55-entry user-visible surface.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


OUTPUT_JSON_NAME = "scbs_55_report_schema_capture_result_v1.json"
OUTPUT_REPORT_NAME = "scbs_55_report_schema_capture_report_v1.md"

REPORT_CONFIGS = [
    ("46", "库存统计表（新）", "b6977b9743334b6cb8f35dc5768e1a5e"),
    ("47", "账户收支统计表", "868e20eb104b4847854d458a0232268e"),
    ("48", "成本统计表（综合）", "ad8b30d6c2f145598232d835c631540f"),
    ("49", "投标保证金报表", "2205259cb52c43b79cfe997ee1f4b643"),
    ("50", "发票成本进度报表", "0b44ca60c88a4845b8f489b346896853"),
    ("51", "发票分析报表", "0c3c8434fff54c9e80fb3e483c318150"),
    ("52", "项目经营统计表", "c901291a239649bf8e93e91255fc86b4"),
    ("53", "应收应付报表", "87f061c0258145239daa5bb639a4cfb3"),
]


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration/scbs_55_report_schema_20260527"))
    candidates.append(Path.cwd() / "artifacts/migration/scbs_55_report_schema_20260527")
    candidates.append(Path("/tmp/scbs_55_report_schema"))
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path("/tmp/scbs_55_report_schema")


def sqlcmd() -> list[str]:
    return [
        "docker",
        "exec",
        "-i",
        os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore"),
        os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd"),
        "-S",
        os.getenv("LEGACY_MSSQL_SERVER", "localhost"),
        "-U",
        os.getenv("LEGACY_MSSQL_USER", "sa"),
        "-P",
        os.getenv("LEGACY_MSSQL_PASSWORD", "LegacyRestore!2026"),
        "-C",
        "-d",
        os.getenv("LEGACY_MSSQL_DB", "LegacyDb"),
        "-y",
        "0",
        "-Y",
        "0",
        "-w",
        "65535",
    ]


def run_sql(sql: str) -> str:
    cmd = sqlcmd() + ["-Q", sql]
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    text = result.stdout.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end < start:
        raise RuntimeError(f"sqlcmd did not return JSON: {text[:1000]}")
    return "".join(text[start : end + 1].splitlines())


def parse_json(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return None


def visible_columns(nodes: Any) -> list[str]:
    result: list[str] = []

    def walk(items: Any) -> None:
        if not isinstance(items, list):
            return
        for item in items:
            if not isinstance(item, dict):
                continue
            info = item.get("Info") if isinstance(item.get("Info"), dict) else item
            if info and not info.get("IsHide"):
                name = str(info.get("Name") or "").strip()
                field = str(info.get("Field") or "").strip()
                if name or field:
                    result.append(f"{name or field}({field})" if field else name)
            walk(item.get("ChildConfig"))

    walk(nodes)
    return result


def parameter_names(nodes: Any) -> list[str]:
    if not isinstance(nodes, list):
        return []
    names = []
    for item in nodes:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("param") or "").strip()
        param = str(item.get("param") or "").strip()
        if name and param and name != param:
            names.append(f"{name}({param})")
        elif param or name:
            names.append(param or name)
    return names


def source_tables(sql: str) -> list[str]:
    names = []
    for match in re.finditer(r"\b(?:FROM|JOIN)\s+([A-Za-z0-9_\.\[\]]+)", sql or "", re.IGNORECASE):
        table = match.group(1).strip("[]")
        if table.upper() not in {"SELECT", "WITH"} and table not in names:
            names.append(table)
    return names


def normalize(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_config = {row["config_id"]: row for row in raw_rows}
    entries = []
    for seq, name, config_id in REPORT_CONFIGS:
        row = by_config.get(config_id)
        if not row:
            entries.append({"seq": seq, "name": name, "config_id": config_id, "status": "MISSING"})
            continue
        table_columns = parse_json(row.get("table_columns"))
        sql_columns = parse_json(row.get("sql_columns"))
        parameter_data = parse_json(row.get("parameter_data"))
        search_config = parse_json(row.get("search_config"))
        sql_sentence = row.get("sql_sentence") or ""
        entries.append(
            {
                "seq": seq,
                "name": name,
                "config_id": config_id,
                "status": "PASS" if sql_sentence or row.get("procedure_name") else "REVIEW",
                "config_name": row.get("config_name") or "",
                "function_name": row.get("function_name") or "",
                "config_type": row.get("config_type") or "",
                "report_data_source": row.get("report_data_source") or "",
        "procedure_name": row.get("procedure_name") or "",
                "sql_id": row.get("sql_id") or "",
                "sql_title": row.get("sql_title") or "",
                "sql_sentence": sql_sentence,
                "source_tables": source_tables(sql_sentence),
                "parameter_data": parameter_data or [],
                "parameter_names": parameter_names(parameter_data),
                "search_config": search_config or [],
                "sql_columns": sql_columns or [],
                "table_columns": table_columns or [],
                "visible_columns": visible_columns(table_columns),
            }
        )
    return entries


def markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBS 55 Report Schema Capture v1",
        "",
        f"Status: {payload['status']}",
        f"Entry Count: {payload['entry_count']}",
        "",
        "| seq | report | config | data source | params | visible columns | source tables | status |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["entries"]:
        params = ", ".join(row.get("parameter_names") or [])
        columns = ", ".join((row.get("visible_columns") or [])[:20])
        tables = ", ".join(row.get("source_tables") or [])
        lines.append(
            "| {seq} | {name} | `{config_id}` | {report_data_source} | {params} | {columns} | {tables} | {status} |".format(
                seq=row.get("seq", ""),
                name=row.get("name", ""),
                config_id=row.get("config_id", ""),
                report_data_source=row.get("report_data_source", ""),
                params=params,
                columns=columns.replace("|", "/"),
                tables=tables.replace("|", "/"),
                status=row.get("status", ""),
            )
        )
    lines.extend(["", "## Detail", "", "```json", json.dumps(payload["entries"], ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


ids = ",".join("('%s')" % config_id for _, _, config_id in REPORT_CONFIGS)
sql = f"""
SET NOCOUNT ON;
DECLARE @ids TABLE (id varchar(64));
INSERT INTO @ids(id) VALUES {ids};
SELECT
    f.ID AS config_id,
    f.CONFIGNAME AS config_name,
    f.CONFIGTYPE AS config_type,
    JSON_VALUE(CAST(f.DETAIL_CONFIG AS nvarchar(max)), '$.Info.FunctionName') AS function_name,
    JSON_VALUE(CAST(f.DETAIL_CONFIG AS nvarchar(max)), '$.Info.ReportDataSorce') AS report_data_source,
    JSON_VALUE(CAST(f.DETAIL_CONFIG AS nvarchar(max)), '$.SQLConfig.Procedure') AS procedure_name,
    JSON_VALUE(CAST(f.DETAIL_CONFIG AS nvarchar(max)), '$.SQLConfig.SQLID') AS sql_id,
    s.BT AS sql_title,
    COALESCE(NULLIF(JSON_VALUE(CAST(f.DETAIL_CONFIG AS nvarchar(max)), '$.SQLConfig.SQLSentence'), ''), CAST(s.SQL AS nvarchar(max))) AS sql_sentence,
    JSON_QUERY(CAST(f.DETAIL_CONFIG AS nvarchar(max)), '$.SQLConfig.ColumnConfig') AS sql_columns,
    JSON_QUERY(CAST(f.DETAIL_CONFIG AS nvarchar(max)), '$.SQLConfig.ParameterData') AS parameter_data,
    JSON_QUERY(CAST(f.DETAIL_CONFIG AS nvarchar(max)), '$.TableConfig.ColumnConfig') AS table_columns,
    JSON_QUERY(CAST(f.DETAIL_CONFIG AS nvarchar(max)), '$.Search.WhereComInfo') AS search_config
FROM BASE_LOWCODE_FORM_CONFIG f
JOIN @ids i ON i.id = f.ID
LEFT JOIN BASE_LOWCODE_CUSTOM_SQL s
  ON s.ID = JSON_VALUE(CAST(f.DETAIL_CONFIG AS nvarchar(max)), '$.SQLConfig.SQLID')
FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

artifact_dir = artifact_root()
raw_rows = json.loads(run_sql(sql))
entries = normalize(raw_rows)
payload = {
    "status": "PASS" if all(row["status"] == "PASS" for row in entries) else "REVIEW",
    "mode": "scbs_55_report_schema_capture",
    "entry_count": len(entries),
    "entries": entries,
    "db_writes": 0,
}
(artifact_dir / OUTPUT_JSON_NAME).write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
(artifact_dir / OUTPUT_REPORT_NAME).write_text(markdown(payload), encoding="utf-8")
print("SCBS_55_REPORT_SCHEMA_CAPTURE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(2)
