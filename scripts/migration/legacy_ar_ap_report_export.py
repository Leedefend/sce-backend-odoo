#!/usr/bin/env python3
"""Export old UP_USP_SELECT_YSYFHZB_XM_ZJ project summary rows from MSSQL."""

from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = Path(
    os.getenv("LEGACY_AR_AP_REPORT_CSV", str(REPO_ROOT / "artifacts/migration/legacy_ar_ap_report_v1.csv"))
)
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
MSSQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
MSSQL_PASSWORD = os.getenv("LEGACY_MSSQL_PASSWORD", "LegacyRestore!2026")
MSSQL_DB = os.getenv("LEGACY_MSSQL_DB", "LegacyDb")

FIELDS = [
    "legacy_project_name",
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
    "tax_burden_rate",
    "actual_available_balance",
    "self_funding_income_amount",
    "self_funding_refund_amount",
    "self_funding_unreturned_amount",
    "output_surcharge_amount",
    "input_surcharge_amount",
    "deduction_surcharge_amount",
]


def run_sql(sql: str) -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        MSSQL_CONTAINER,
        SQLCMD,
        "-S",
        "localhost",
        "-U",
        "sa",
        "-P",
        MSSQL_PASSWORD,
        "-C",
        "-d",
        MSSQL_DB,
        "-s",
        "|",
        "-h",
        "-1",
    ]
    completed = subprocess.run(cmd, input=sql, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError({"sqlcmd_failed": completed.returncode, "stderr": completed.stderr[-2000:]})
    return completed.stdout


def proc_definition() -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        MSSQL_CONTAINER,
        SQLCMD,
        "-S",
        "localhost",
        "-U",
        "sa",
        "-P",
        MSSQL_PASSWORD,
        "-C",
        "-d",
        MSSQL_DB,
        "-Q",
        "SET NOCOUNT ON; SELECT OBJECT_DEFINITION(OBJECT_ID('dbo.UP_USP_SELECT_YSYFHZB_XM_ZJ'));",
        "-y",
        "0",
        "-Y",
        "0",
        "-w",
        "65535",
    ]
    completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError({"sqlcmd_failed": completed.returncode, "stderr": completed.stderr[-2000:]})
    lines = []
    in_proc = False
    for line in completed.stdout.splitlines():
        stripped = line.rstrip()
        if "CREATE PROC" in stripped:
            in_proc = True
        if not in_proc:
            continue
        if stripped.startswith("(") and "rows affected" in stripped:
            break
        lines.append(stripped)
    return "\n".join(lines)


def export_sql() -> str:
    proc = proc_definition()
    export_proc = "dbo.__codex_export_ysyfhzb_xm_zj"
    proc = proc.replace("CREATE PROC UP_USP_SELECT_YSYFHZB_XM_ZJ", f"CREATE PROC {export_proc}", 1)
    proc = proc.replace("CREATE PROC dbo.UP_USP_SELECT_YSYFHZB_XM_ZJ", f"CREATE PROC {export_proc}", 1)
    proc = proc.replace(
        "AND XMID IN (select XMID from T_ProjectContract_Out where f_HTDLRQ>=@KSRQ AND f_HTDLRQ<=@JZRQ)",
        "AND XMID COLLATE Chinese_PRC_CI_AS IN (select XMID COLLATE Chinese_PRC_CI_AS from T_ProjectContract_Out where f_HTDLRQ>=@KSRQ AND f_HTDLRQ<=@JZRQ)",
    )
    return (
        f"IF OBJECT_ID('{export_proc}', 'P') IS NOT NULL DROP PROC {export_proc};\n"
        "GO\n"
        + proc
        + f"\nGO\nEXEC {export_proc} @XMMC='', @KSRQ='2000-01-01', @JZRQ='2026-05-27';\n"
        + f"GO\nDROP PROC {export_proc};\n"
    )


def parse_rows(output: str) -> list[list[str]]:
    rows = []
    for line in output.splitlines():
        if not line.strip() or line.startswith("(") or line.startswith("Warning:"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != len(FIELDS):
            raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "line": line[:500]})
        rows.append(parts)
    return rows


def main() -> None:
    rows = parse_rows(run_sql(export_sql()))
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(FIELDS)
        writer.writerows(rows)
    print({"path": str(OUTPUT_CSV), "rows": len(rows)})


if __name__ == "__main__":
    main()
