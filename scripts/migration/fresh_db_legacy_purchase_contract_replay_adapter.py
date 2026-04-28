#!/usr/bin/env python3
"""Build replay payload for legacy purchase/general contract residual facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_purchase_contract_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_purchase_contract_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_record_id", "legacy_pid", "source_dataset", "document_no",
    "document_state", "submitted_time", "applicant_name",
    "applicant_department_legacy_id", "applicant_department",
    "project_legacy_id", "project_name", "contract_name", "contract_no",
    "signing_place", "contract_type_legacy_id", "contract_type",
    "completion_date", "expected_sign_date", "total_amount",
    "currency_legacy_id", "currency_name", "prepayment_amount",
    "install_debug_payment", "warranty_deposit", "payment_terms",
    "partner_legacy_id", "partner_name", "contact_name", "contact_phone",
    "bank_name", "bank_account", "sign_status", "purchase_engineer",
    "special_condition", "attachment_ref", "person_legacy_id",
    "creator_legacy_user_id", "creator_name", "created_time",
    "modifier_legacy_user_id", "modifier_name", "modified_time",
    "is_supplement_contract", "related_contract_legacy_id",
    "related_contract_no", "contract_attribute", "credit_code", "tax_rate",
    "note", "active",
]


def clean_sql(field: str) -> str:
    return f"REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), {field}), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"


def sqlcmd(sql: str) -> list[str]:
    return [
        "docker", "exec", SQL_CONTAINER, SQLCMD, "-S", "localhost", "-U", "sa",
        "-P", SQL_PASSWORD, "-C", "-d", SQL_DATABASE, "-W", "-s", "\t", "-h", "-1", "-Q", sql,
    ]


def run_sql(sql: str) -> str:
    return subprocess.check_output(sqlcmd(sql), text=True)


def payload_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("pid")} AS legacy_pid,
  {clean_sql("SJBMC")} AS source_dataset,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("DJZT")} AS document_state,
  COALESCE(CONVERT(varchar(23), TJSJ, 121), '') AS submitted_time,
  {clean_sql("SQR")} AS applicant_name,
  {clean_sql("SQRBMID")} AS applicant_department_legacy_id,
  {clean_sql("SQRBM")} AS applicant_department,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("XMMC")} AS project_name,
  {clean_sql("HTMC")} AS contract_name,
  {clean_sql("HTBH")} AS contract_no,
  {clean_sql("HTQDDD")} AS signing_place,
  {clean_sql("HTLXID")} AS contract_type_legacy_id,
  {clean_sql("HTLX")} AS contract_type,
  COALESCE(CONVERT(varchar(23), WGRQ, 121), '') AS completion_date,
  COALESCE(CONVERT(varchar(23), HTYJQDRQ, 121), '') AS expected_sign_date,
  {clean_sql("ZJE")} AS total_amount,
  {clean_sql("HBID")} AS currency_legacy_id,
  {clean_sql("HB")} AS currency_name,
  {clean_sql("YFK")} AS prepayment_amount,
  {clean_sql("AZTSK")} AS install_debug_payment,
  {clean_sql("ZBJ")} AS warranty_deposit,
  {clean_sql("FKFSSM")} AS payment_terms,
  {clean_sql("DWID")} AS partner_legacy_id,
  {clean_sql("DWMC")} AS partner_name,
  {clean_sql("LXR")} AS contact_name,
  {clean_sql("LXDH")} AS contact_phone,
  {clean_sql("KHH")} AS bank_name,
  {clean_sql("YHZH")} AS bank_account,
  {clean_sql("QYZT")} AS sign_status,
  {clean_sql("CGGCS")} AS purchase_engineer,
  {clean_sql("TSQK")} AS special_condition,
  {clean_sql("FJ")} AS attachment_ref,
  {clean_sql("PersonId")} AS person_legacy_id,
  {clean_sql("LRRID")} AS creator_legacy_user_id,
  {clean_sql("LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), LRSJ, 121), '') AS created_time,
  {clean_sql("XGRID")} AS modifier_legacy_user_id,
  {clean_sql("XGR")} AS modifier_name,
  COALESCE(CONVERT(varchar(23), XGSJ, 121), '') AS modified_time,
  {clean_sql("SFBCHT")} AS is_supplement_contract,
  {clean_sql("GLYHTID")} AS related_contract_legacy_id,
  {clean_sql("GLYHTBH")} AS related_contract_no,
  {clean_sql("HTSX")} AS contract_attribute,
  {clean_sql("XYDM")} AS credit_code,
  {clean_sql("D_BYK_SLV")} AS tax_rate,
  {clean_sql("BZ")} AS note,
  CASE WHEN ISNULL(DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.T_CGHT_INFO
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
ORDER BY TJSJ, Id;
"""


def write_csv_payload() -> int:
    count = 0
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with subprocess.Popen(sqlcmd(payload_sql()), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
        if proc.stdout is None:
            raise RuntimeError("sqlcmd stdout unavailable")
        with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(FIELDS)
            for line in proc.stdout:
                stripped = line.strip()
                if not stripped or stripped.startswith("(") and stripped.endswith("rows affected)"):
                    continue
                parts = line.rstrip("\r\n").split("\t")
                if len(parts) != len(FIELDS):
                    raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(FIELDS), "line": line[:500]})
                writer.writerow(parts)
                count += 1
        return_code = proc.wait()
    if return_code != 0:
        raise RuntimeError({"sqlcmd_failed": return_code})
    return count


def scalar(sql: str) -> str:
    raw = run_sql(sql)
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and not (stripped.startswith("(") and stripped.endswith("rows affected)")):
            return stripped
    return "0"


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    rows = write_csv_payload()
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_purchase_contract_replay_adapter",
        "total_rows": rows,
        "active_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.T_CGHT_INFO WHERE ISNULL(DEL,0)=0;")),
        "project_count": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(DISTINCT XMID) FROM dbo.T_CGHT_INFO;")),
        "partner_text_count": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(DISTINCT DWMC) FROM dbo.T_CGHT_INFO WHERE NULLIF(LTRIM(RTRIM(DWMC)), '') IS NOT NULL;")),
        "amount_sum": scalar("SET NOCOUNT ON; SELECT COALESCE(SUM(ZJE),0) FROM dbo.T_CGHT_INFO;"),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_purchase_contract_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_PURCHASE_CONTRACT_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
