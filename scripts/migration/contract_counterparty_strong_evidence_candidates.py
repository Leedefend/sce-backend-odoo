#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from pathlib import Path


OUTPUT_CSV = Path("artifacts/migration/contract_counterparty_strong_evidence_candidates_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/contract_counterparty_strong_evidence_summary_v1.json")

SQLCMD = [
    "docker",
    "exec",
    "legacy-sqlserver",
    "/opt/mssql-tools18/bin/sqlcmd",
    "-S",
    "localhost",
    "-U",
    "sa",
    "-P",
    "ChangeThis_Strong_Password_123!",
    "-C",
    "-d",
    "LegacyDb",
    "-s",
    "\t",
    "-W",
    "-h",
    "-1",
]

FIELDS = [
    "legacy_contract_id",
    "legacy_document_no",
    "legacy_contract_no",
    "legacy_project_id",
    "contract_title",
    "fbf_text",
    "cbf_text",
    "legacy_contract_deleted_flag",
    "repayment_partner_id",
    "repayment_partner_name",
    "repayment_rows",
    "company_name",
    "company_credit_code",
    "company_tax_no",
    "company_deleted_flag",
    "evidence_type",
    "evidence_strength",
    "manual_confirm_required",
    "confirmed_partner_action",
    "review_note",
]

SQL = r"""
SET NOCOUNT ON;
WITH single_counterparty AS (
    SELECT
        CONVERT(nvarchar(100), SGHTID) AS SGHTID,
        MIN(CONVERT(nvarchar(100), WLDWID)) AS WLDWID,
        MIN(CONVERT(nvarchar(500), WLDWMC)) AS WLDWMC,
        COUNT(*) AS repayment_rows
    FROM dbo.C_JFHKLR
    WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), SGHTID))), '') IS NOT NULL
      AND NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), WLDWID))), '') IS NOT NULL
    GROUP BY CONVERT(nvarchar(100), SGHTID)
    HAVING COUNT(DISTINCT CONVERT(nvarchar(100), WLDWID)) = 1
)
SELECT
    CONVERT(nvarchar(100), p.Id) AS legacy_contract_id,
    CONVERT(nvarchar(200), ISNULL(p.DJBH, '')) AS legacy_document_no,
    CONVERT(nvarchar(200), ISNULL(p.HTBH, '')) AS legacy_contract_no,
    CONVERT(nvarchar(100), ISNULL(p.XMID, '')) AS legacy_project_id,
    CONVERT(nvarchar(500), ISNULL(p.HTBT, '')) AS contract_title,
    CONVERT(nvarchar(500), ISNULL(p.FBF, '')) AS fbf_text,
    CONVERT(nvarchar(500), ISNULL(p.CBF, '')) AS cbf_text,
    CONVERT(nvarchar(20), ISNULL(p.DEL, '')) AS legacy_contract_deleted_flag,
    s.WLDWID AS repayment_partner_id,
    CONVERT(nvarchar(500), ISNULL(s.WLDWMC, '')) AS repayment_partner_name,
    CONVERT(nvarchar(20), s.repayment_rows) AS repayment_rows,
    CONVERT(nvarchar(500), ISNULL(c.DWMC, '')) AS company_name,
    CONVERT(nvarchar(100), ISNULL(c.TYSHXYDM, '')) AS company_credit_code,
    CONVERT(nvarchar(100), ISNULL(c.SH, '')) AS company_tax_no,
    CONVERT(nvarchar(20), ISNULL(c.DEL, '')) AS company_deleted_flag,
    N'repayment_single_counterparty' AS evidence_type,
    N'strong' AS evidence_strength,
    N'yes' AS manual_confirm_required,
    N'' AS confirmed_partner_action,
    N'' AS review_note
FROM single_counterparty s
JOIN dbo.T_ProjectContract_Out p
  ON CONVERT(nvarchar(100), p.Id) = s.SGHTID
JOIN dbo.T_Base_CooperatCompany c
  ON CONVERT(nvarchar(100), c.Id) = s.WLDWID
ORDER BY p.Id;
"""


def clean_cell(value: str) -> str:
    return value.strip()


def main() -> int:
    proc = subprocess.run(
        [*SQLCMD, "-Q", SQL],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    rows = []
    for line in proc.stdout.splitlines():
        line = line.rstrip("\r\n")
        if not line or line.startswith("("):
            continue
        parts = [clean_cell(part) for part in line.split("\t")]
        if len(parts) != len(FIELDS):
            raise ValueError(f"Unexpected column count {len(parts)} for line: {line[:240]}")
        rows.append(dict(zip(FIELDS, parts)))

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    company_deleted = Counter(row["company_deleted_flag"] for row in rows)
    contract_deleted = Counter(row["legacy_contract_deleted_flag"] for row in rows)
    result = {
        "status": "PASS",
        "mode": "legacy_db_readonly_strong_evidence_candidate_generation",
        "candidate_rows": len(rows),
        "company_deleted_flag_counts": dict(sorted(company_deleted.items())),
        "contract_deleted_flag_counts": dict(sorted(contract_deleted.items())),
        "output_csv": str(OUTPUT_CSV),
        "decision": "NO-GO for partner or contract import; strong-evidence confirmation table prepared",
        "next_step": "manual review the strong-evidence candidates before any partner materialization",
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("CONTRACT_COUNTERPARTY_STRONG_EVIDENCE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
