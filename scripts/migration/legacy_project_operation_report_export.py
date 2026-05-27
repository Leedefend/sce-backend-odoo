#!/usr/bin/env python3
"""Export old SELECT_XMJYTJB project operation report rows from MSSQL."""

from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = Path(
    os.getenv(
        "LEGACY_PROJECT_OPERATION_REPORT_CSV",
        str(REPO_ROOT / "artifacts/migration/legacy_project_operation_report_v1.csv"),
    )
)
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
MSSQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
MSSQL_PASSWORD = os.getenv("LEGACY_MSSQL_PASSWORD", "LegacyRestore!2026")
MSSQL_DB = os.getenv("LEGACY_MSSQL_DB", "LegacyDb")

FIELDS = [
    "legacy_project_id",
    "legacy_pid",
    "legacy_project_name",
    "current_receipt_amount",
    "current_deduction_registered_amount",
    "current_subcontract_amount",
    "personal_income_tax_amount",
    "enterprise_income_tax_amount",
    "interest_amount",
    "management_fee_refundable_amount",
    "management_fee_nonrefundable_amount",
    "other_amount",
    "vat_nonrefundable_amount",
    "vat_three_percent_amount",
    "construction_stamp_tax_amount",
    "prepaid_vat_amount",
    "purchase_sale_stamp_tax_amount",
    "risk_reserve_amount",
    "surcharge_nonrefundable_amount",
    "surcharge_amount",
    "vat_amount",
    "output_tax_amount",
    "input_tax_amount",
    "actual_deduction_vat_amount",
    "deduction_rate",
    "deductible_surcharge_amount",
    "actual_deduction_surcharge_amount",
    "net_income_amount",
    "operation_income_amount",
]


def run_sql() -> str:
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
        "EXEC dbo.SELECT_XMJYTJB @XMID='fb0c4133-f011-44a4-a285-59cfd30aec27'",
        "-s",
        "|",
        "-h",
        "-1",
    ]
    completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError({"sqlcmd_failed": completed.returncode, "stderr": completed.stderr[-2000:]})
    return completed.stdout


def parse_rows(output: str) -> list[list[str]]:
    rows = []
    for line in output.splitlines():
        if not line.strip() or line.startswith("("):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != len(FIELDS):
            raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "line": line[:500]})
        rows.append(parts)
    return rows


def main() -> None:
    rows = parse_rows(run_sql())
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(FIELDS)
        writer.writerows(rows)
    print({"path": str(OUTPUT_CSV), "rows": len(rows)})


if __name__ == "__main__":
    main()
