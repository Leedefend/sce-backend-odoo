#!/usr/bin/env python3
"""Run a read-only COLLATE-patched copy of legacy global AR/AP procedure."""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "legacy_ar_ap_company_collation_probe_rows_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "legacy_ar_ap_company_collation_probe_result_v1.json"
OUTPUT_MD = REPO_ROOT / "docs/migration_alignment/legacy_ar_ap_company_collation_probe_batch_al_v1.md"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
PROC_NAME = "UP_USP_SELECT_YSYFHZB_XM_ZJ"
PARAM_XMMC = os.getenv("LEGACY_AR_AP_XMMC", "")
PARAM_KSRQ = os.getenv("LEGACY_AR_AP_KSRQ", "2000-01-01")
PARAM_JZRQ = os.getenv("LEGACY_AR_AP_JZRQ", "")

FIELDS = [
    "project_name",
    "legacy_project_id",
    "income_contract_amount",
    "output_invoice_amount",
    "receipt_amount",
    "receivable_unpaid_amount",
    "invoiced_unreceived_amount",
    "received_uninvoiced_amount",
    "payable_contract_amount",
    "paid_amount",
    "input_invoice_amount",
    "payable_unpaid_amount",
    "paid_uninvoiced_amount",
    "output_tax_amount",
    "input_tax_amount",
    "deduction_tax_amount",
    "tax_deduction_rate",
    "actual_available_balance",
    "self_funding_income_amount",
    "self_funding_refund_amount",
    "self_funding_unreturned_amount",
    "output_surcharge_amount",
    "input_surcharge_amount",
    "deduction_surcharge_amount",
]

MONEY_FIELDS = [field for field in FIELDS if field not in {"project_name", "legacy_project_id", "tax_deduction_rate"}]


def sqlcmd_base() -> list[str]:
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
    ]


def run_sql(sql: str, wide: bool = False, timeout: int = 120) -> dict[str, object]:
    cmd = sqlcmd_base()
    if wide:
        cmd.extend(["-y", "0", "-Y", "0"])
    else:
        cmd.extend(["-W", "-s", "\t", "-h", "-1"])
    cmd.extend(["-Q", sql])
    proc = subprocess.run(
        cmd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    lines = [
        line.rstrip("\r\n")
        for line in proc.stdout.splitlines()
        if line.strip()
        and not (set(line.strip()) == {"-"})
        and line.strip() != "definition_text"
        and not (line.strip().startswith("(") and line.strip().endswith("rows affected)"))
    ]
    return {"return_code": proc.returncode, "lines": lines, "sample": lines[:10]}


def sql_literal(value: str) -> str:
    return "N'" + value.replace("'", "''") + "'"


def procedure_definition_lines() -> list[str]:
    result = run_sql(
        f"SET NOCOUNT ON; SELECT OBJECT_DEFINITION(OBJECT_ID(N'dbo.{PROC_NAME}')) AS definition_text;",
        wide=True,
    )
    if result["return_code"] != 0 or not result["lines"]:
        raise RuntimeError({"definition_failed": result})
    return [str(line) for line in result["lines"]]


def patched_sql(lines: list[str]) -> str:
    body = "\n".join(lines[5:])
    body = re.sub(
        r"(\b(?:XMMC|XMIDS|DWMC|XMID)\s+VARCHAR\(\d+\))",
        r"\1 COLLATE DATABASE_DEFAULT",
        body,
    )
    return "\n".join(
        [
            "SET NOCOUNT ON;",
            f"DECLARE @XMMC VARCHAR(5000) = {sql_literal(PARAM_XMMC)};",
            f"DECLARE @KSRQ VARCHAR(200) = {sql_literal(PARAM_KSRQ)};",
            f"DECLARE @JZRQ VARCHAR(200) = {sql_literal(PARAM_JZRQ)};",
            body,
        ]
    )


def parse_decimal(value: str) -> Decimal:
    normalized = value.strip()
    if not normalized:
        return Decimal("0")
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return Decimal("0")


def rows_from_result(result: dict[str, object]) -> list[dict[str, str]]:
    rows = []
    for line in result["lines"]:
        if str(line).startswith(("Warning:", "Msg ", "Cannot ", "Error ")):
            continue
        parts = str(line).split("\t")
        if len(parts) != len(FIELDS):
            continue
        rows.append({field: parts[index] for index, field in enumerate(FIELDS)})
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def totals(rows: list[dict[str, str]]) -> dict[str, str]:
    result = {}
    for field in MONEY_FIELDS:
        result[field] = str(sum((parse_decimal(row.get(field, "0")) for row in rows), Decimal("0")))
    return result


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, payload: dict[str, object]) -> None:
    totals_payload = payload["totals"]
    lines = [
        "# 应收应付报表旧过程 COLLATE 探针 Batch-AL",
        "",
        "## 批次定位",
        "",
        "- Layer Target：Migration Evidence / Legacy SQL Reconciliation",
        "- Module：`scripts/migration`, `docs/migration_alignment`",
        f"- 旧过程：`{PROC_NAME}`",
        "- 目标：不修改旧库对象，使用只读 ad-hoc SQL 给旧过程临时表字符字段补 `COLLATE DATABASE_DEFAULT`，验证旧库全局应收应付结果可导出。",
        "",
        "## 参数",
        "",
        f"- `@XMMC`：`{PARAM_XMMC}`",
        f"- `@KSRQ`：`{PARAM_KSRQ}`",
        f"- `@JZRQ`：`{PARAM_JZRQ}`",
        "",
        "## 结果",
        "",
        f"- 行数：`{payload['row_count']}`",
        f"- CSV：`{payload['csv']}`",
        f"- JSON：`{payload['json']}`",
        "",
        "## 汇总金额",
        "",
        "| 指标 | 金额 |",
        "| --- | ---: |",
    ]
    for field in MONEY_FIELDS:
        lines.append(f"| `{field}` | `{totals_payload[field]}` |")
    lines.extend(
        [
            "",
            "## 判断",
            "",
            "排序规则冲突来自旧过程临时表字符字段使用 tempdb 默认排序规则。给 `#TEMP_RESULT_ZJ` / `#TEMP_RESULT_ZZJG` 的项目、单位字符字段补 `COLLATE DATABASE_DEFAULT` 后，旧过程逻辑可在恢复容器中只读执行。",
            "",
            "本批只解决旧过程执行入口，不判定新旧数值一致。下一步应读取本 CSV，与 `sc.ar.ap.company.summary` 按 `legacy_project_id` 做字段级差异矩阵。",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    lines = procedure_definition_lines()
    result = run_sql(patched_sql(lines), timeout=180)
    rows = rows_from_result(result)
    write_csv(OUTPUT_CSV, rows)
    payload = {
        "mode": "legacy_ar_ap_company_collation_probe",
        "procedure": PROC_NAME,
        "parameters": {"XMMC": PARAM_XMMC, "KSRQ": PARAM_KSRQ, "JZRQ": PARAM_JZRQ},
        "row_count": len(rows),
        "raw_line_count": len(result["lines"]),
        "return_code": result["return_code"],
        "sample": rows[:5],
        "totals": totals(rows),
        "csv": str(OUTPUT_CSV),
        "json": str(OUTPUT_JSON),
        "decision": "legacy_ar_ap_company_collation_probe_ready" if rows else "STOP_REVIEW_REQUIRED",
    }
    write_json(OUTPUT_JSON, payload)
    write_md(OUTPUT_MD, payload)
    print("LEGACY_AR_AP_COMPANY_COLLATION_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
