#!/usr/bin/env python3
"""Precheck legacy global AR/AP procedure before reconciliation."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_JSON = ARTIFACT_DIR / "legacy_ar_ap_company_proc_precheck_v1.json"
OUTPUT_MD = REPO_ROOT / "docs/migration_alignment/legacy_ar_ap_company_proc_precheck_batch_ak_v1.md"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
PROC_NAME = "UP_USP_SELECT_YSYFHZB_XM_ZJ"


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


def run_sql(sql: str, timeout: int = 60) -> dict[str, object]:
    proc = subprocess.run(
        sqlcmd(sql),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    lines = [
        line.rstrip("\r\n")
        for line in proc.stdout.splitlines()
        if line.strip() and not (line.strip().startswith("(") and line.strip().endswith("rows affected)"))
    ]
    return {
        "return_code": proc.returncode,
        "line_count": len(lines),
        "lines": lines,
        "sample": lines[:30],
    }


def split_rows(result: dict[str, object], columns: list[str]) -> list[dict[str, str]]:
    rows = []
    for line in result.get("lines", []):
        parts = str(line).split("\t")
        if len(parts) != len(columns):
            continue
        rows.append({column: parts[index] for index, column in enumerate(columns)})
    return rows


def has_sql_error(result: dict[str, object]) -> bool:
    markers = ("Msg ", "Cannot ", "Error ", "Timeout ")
    return any(str(line).startswith(markers) for line in result.get("lines", []))


def parameter_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  p.name,
  TYPE_NAME(p.user_type_id) AS type_name,
  CONVERT(varchar(20), p.max_length) AS max_length,
  CONVERT(varchar(20), p.precision) AS precision_value,
  CONVERT(varchar(20), p.scale) AS scale_value,
  CONVERT(varchar(20), p.has_default_value) AS has_default_value,
  CONVERT(varchar(20), p.is_output) AS is_output
FROM sys.parameters p
WHERE p.object_id = OBJECT_ID(N'dbo.{PROC_NAME}')
ORDER BY p.parameter_id;
"""


def result_set_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  CONVERT(varchar(20), column_ordinal) AS column_ordinal,
  COALESCE(name, '') AS name,
  COALESCE(system_type_name, '') AS system_type_name,
  CONVERT(varchar(20), is_nullable) AS is_nullable,
  COALESCE(error_message, '') AS error_message
FROM sys.dm_exec_describe_first_result_set_for_object(OBJECT_ID(N'dbo.{PROC_NAME}'), NULL)
ORDER BY column_ordinal;
"""


def definition_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT OBJECT_DEFINITION(OBJECT_ID(N'dbo.{PROC_NAME}')) AS definition_text;
"""


def execution_sql(params: list[dict[str, str]]) -> str:
    assignments = []
    for item in params:
        name = item["name"]
        type_name = item["type_name"].lower()
        if "date" in type_name or "time" in type_name:
            value = "NULL"
        elif type_name in {"int", "bigint", "smallint", "tinyint", "decimal", "numeric", "float", "real", "money"}:
            value = "NULL"
        else:
            value = "N''"
        assignments.append(f"{name} = {value}")
    return "SET NOCOUNT ON;\nEXEC dbo.{proc} {args};".format(proc=PROC_NAME, args=", ".join(assignments))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, payload: dict[str, object]) -> None:
    params = payload["parameters"]
    result_columns = payload["result_columns"]
    exec_attempt = payload["execution_attempt"]
    lines = [
        "# 应收应付报表旧过程预检 Batch-AK",
        "",
        "## 批次定位",
        "",
        "- Layer Target：Migration Evidence / Legacy Procedure Precheck",
        "- Module：`scripts/migration`, `docs/migration_alignment`",
        f"- 旧过程：`{PROC_NAME}`",
        "- 目标：进入新旧对账前，确认旧过程参数、结果集元数据和直接执行限制。",
        "",
        "## 参数",
        "",
        "| 参数 | 类型 | 长度 | 默认值 | 输出参数 |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for item in params:
        lines.append(
            "| {name} | {type_name} | {max_length} | {has_default_value} | {is_output} |".format(**item)
        )
    lines.extend(
        [
            "",
            "## 结果集元数据",
            "",
            "| 序号 | 字段 | 类型 | 可空 | 错误 |",
            "| ---: | --- | --- | --- | --- |",
        ]
    )
    for item in result_columns:
        lines.append(
            "| {column_ordinal} | {name} | {system_type_name} | {is_nullable} | {error_message} |".format(**item)
        )
    lines.extend(
        [
            "",
            "## 空参数执行尝试",
            "",
            f"- return_code：`{exec_attempt['return_code']}`",
            f"- line_count：`{exec_attempt['line_count']}`",
            "",
            "样本输出：",
            "",
            "```text",
        ]
    )
    lines.extend(str(line) for line in exec_attempt.get("sample", []))
    lines.extend(
        [
            "```",
            "",
            "## 判断",
            "",
            payload["decision_note"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parameter_result = run_sql(parameter_sql())
    result_set_result = run_sql(result_set_sql())
    definition_result = run_sql(definition_sql())
    params = split_rows(
        parameter_result,
        ["name", "type_name", "max_length", "precision_value", "scale_value", "has_default_value", "is_output"],
    )
    result_columns = split_rows(
        result_set_result,
        ["column_ordinal", "name", "system_type_name", "is_nullable", "error_message"],
    )
    exec_attempt = run_sql(execution_sql(params), timeout=90) if params else {"return_code": 1, "line_count": 0, "sample": []}
    execution_ok = exec_attempt["return_code"] == 0 and not has_sql_error(exec_attempt)
    decision = "legacy_proc_direct_execution_ready" if execution_ok else "legacy_proc_direct_execution_blocked"
    decision_note = (
        "旧过程可以在恢复容器中直接执行，可进入样本条件对账。"
        if execution_ok
        else "旧过程空参数直接执行失败；对账前需要根据参数语义构造真实条件，或处理过程内部依赖限制。"
    )
    payload = {
        "mode": "legacy_ar_ap_company_proc_precheck",
        "procedure": PROC_NAME,
        "parameters": params,
        "parameter_query": {key: value for key, value in parameter_result.items() if key != "lines"},
        "result_columns": result_columns,
        "result_set_query": {key: value for key, value in result_set_result.items() if key != "lines"},
        "definition_sample": definition_result.get("sample", []),
        "execution_attempt": exec_attempt,
        "decision": decision,
        "decision_note": decision_note,
    }
    write_json(OUTPUT_JSON, payload)
    write_md(OUTPUT_MD, payload)
    print("LEGACY_AR_AP_COMPANY_PROC_PRECHECK=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
