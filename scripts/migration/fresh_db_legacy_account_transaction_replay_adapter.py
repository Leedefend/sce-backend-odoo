#!/usr/bin/env python3
"""Build replay payloads for legacy account transaction lines."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
PAYLOAD_CSV = ARTIFACT_DIR / "fresh_db_legacy_account_transaction_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_account_transaction_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "source_key",
    "source_table",
    "legacy_record_id",
    "document_no",
    "transaction_date",
    "document_state",
    "deleted_flag",
    "project_legacy_id",
    "project_name",
    "account_legacy_id",
    "account_name",
    "counterparty_account_legacy_id",
    "counterparty_account_name",
    "direction",
    "metric_bucket",
    "amount",
    "category",
    "source_summary",
    "note",
    "active",
]


def clean_sql(field: str) -> str:
    return f"REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), {field}), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"


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


def write_sql_csv(path: Path, fields: list[str], sql: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with subprocess.Popen(sqlcmd(sql), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
        if proc.stdout is None:
            raise RuntimeError("sqlcmd stdout unavailable")
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(fields)
            for line in proc.stdout:
                stripped = line.strip()
                if not stripped or stripped.startswith("(") and stripped.endswith("rows affected)"):
                    continue
                parts = line.rstrip("\r\n").split("\t")
                if len(parts) != len(fields):
                    raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(fields), "line": line[:500]})
                writer.writerow(parts)
                count += 1
        return_code = proc.wait()
    if return_code != 0:
        raise RuntimeError({"sqlcmd_failed": return_code, "path": str(path)})
    return count


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    sql = f"""
SET NOCOUNT ON;
WITH base AS (
  SELECT *
  FROM dbo.C_FKGL_ZHJZJWL
  WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
    AND ISNULL(DEL, 0) = 0
    AND ISNULL(DJZT, '0') = '2'
    AND ISNULL(JE, 0) <> 0
)
SELECT
  {clean_sql("Id + ':expense'")} AS source_key,
  'C_FKGL_ZHJZJWL' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), FSSJ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(ZCXMID, ''), XMID)")} AS project_legacy_id,
  {clean_sql("COALESCE(NULLIF(ZCXMMC, ''), XMMC)")} AS project_name,
  {clean_sql("ZCZH_Id")} AS account_legacy_id,
  {clean_sql("ZCZH")} AS account_name,
  {clean_sql("SKZH_Id")} AS counterparty_account_legacy_id,
  {clean_sql("SKZH")} AS counterparty_account_name,
  'expense' AS direction,
  'account_transfer' AS metric_bucket,
  {clean_sql("JE")} AS amount,
  {clean_sql("f_LB")} AS category,
  {clean_sql("SY")} AS source_summary,
  {clean_sql("BZ")} AS note,
  '1' AS active
FROM base
WHERE NULLIF(LTRIM(RTRIM(ZCZH_Id)), '') IS NOT NULL
UNION ALL
SELECT
  {clean_sql("Id + ':income'")} AS source_key,
  'C_FKGL_ZHJZJWL' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), FSSJ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(SKXMID, ''), XMID)")} AS project_legacy_id,
  {clean_sql("COALESCE(NULLIF(SKXMMC, ''), XMMC)")} AS project_name,
  {clean_sql("SKZH_Id")} AS account_legacy_id,
  {clean_sql("SKZH")} AS account_name,
  {clean_sql("ZCZH_Id")} AS counterparty_account_legacy_id,
  {clean_sql("ZCZH")} AS counterparty_account_name,
  'income' AS direction,
  'account_transfer' AS metric_bucket,
  {clean_sql("JE")} AS amount,
  {clean_sql("f_LB")} AS category,
  {clean_sql("SY")} AS source_summary,
  {clean_sql("BZ")} AS note,
  '1' AS active
FROM base
WHERE NULLIF(LTRIM(RTRIM(SKZH_Id)), '') IS NOT NULL
UNION ALL
SELECT
  {clean_sql("Id + ':company_income'")} AS source_key,
  'C_CWSFK_GSCWSR' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), SKSJ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("XMMC")} AS project_name,
  {clean_sql("SKZHID")} AS account_legacy_id,
  {clean_sql("SKZH")} AS account_name,
  {clean_sql("FKDWID")} AS counterparty_account_legacy_id,
  {clean_sql("FKDW")} AS counterparty_account_name,
  'income' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("JZJE")} AS amount,
  {clean_sql("SKLB")} AS category,
  {clean_sql("BT")} AS source_summary,
  {clean_sql("BZ")} AS note,
  '1' AS active
FROM dbo.C_CWSFK_GSCWSR
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(SKZHID)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(JZJE, 0) <> 0
UNION ALL
SELECT
  {clean_sql("Id + ':company_expense'")} AS source_key,
  'C_CWSFK_GSCWZC' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), FKSJ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("XMMC")} AS project_name,
  {clean_sql("FKZHID")} AS account_legacy_id,
  {clean_sql("FKZHMC")} AS account_name,
  {clean_sql("SKDWID")} AS counterparty_account_legacy_id,
  {clean_sql("SKDWMC")} AS counterparty_account_name,
  'expense' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("FKJE")} AS amount,
  {clean_sql("CBLBMC")} AS category,
  {clean_sql("BT")} AS source_summary,
  {clean_sql("BZ")} AS note,
  '1' AS active
FROM dbo.C_CWSFK_GSCWZC
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(FKZHID)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(FKJE, 0) <> 0
UNION ALL
SELECT
  {clean_sql("Id + ':receipt_income'")} AS source_key,
  'C_JFHKLR' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), f_RQ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(XMID, ''), NULLIF(LYXMID, ''), NULLIF(TSXMID, ''))")} AS project_legacy_id,
  {clean_sql("COALESCE(NULLIF(XMMC, ''), NULLIF(LYXM, ''), NULLIF(TSXMMC, ''))")} AS project_name,
  {clean_sql("SKZHID")} AS account_legacy_id,
  {clean_sql("SKZH")} AS account_name,
  {clean_sql("WLDWID")} AS counterparty_account_legacy_id,
  {clean_sql("WLDWMC")} AS counterparty_account_name,
  'income' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("f_JE")} AS amount,
  {clean_sql("f_SRLBName")} AS category,
  {clean_sql("BT")} AS source_summary,
  {clean_sql("f_BZ")} AS note,
  '1' AS active
FROM dbo.C_JFHKLR
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(SKZHID)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(f_JE, 0) <> 0
UNION ALL
SELECT
  {clean_sql("Id + ':receipt_refund'")} AS source_key,
  'C_JFHKLR_TH' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), THSJ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("XMMC")} AS project_name,
  {clean_sql("THZHID")} AS account_legacy_id,
  {clean_sql("THZH")} AS account_name,
  {clean_sql("WLDWID")} AS counterparty_account_legacy_id,
  {clean_sql("WLDW")} AS counterparty_account_name,
  'expense' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("THJE")} AS amount,
  {clean_sql("ZJLB")} AS category,
  {clean_sql("THBZ")} AS source_summary,
  {clean_sql("BZ")} AS note,
  '1' AS active
FROM dbo.C_JFHKLR_TH
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(THZHID)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(THJE, 0) <> 0
UNION ALL
SELECT
  {clean_sql("cb.Id + ':self_funding_refund'")} AS source_key,
  'C_JFHKLR_TH_ZCDF_CB' AS source_table,
  {clean_sql("cb.Id")} AS legacy_record_id,
  {clean_sql("zb.DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), COALESCE(cb.THSJ, cb.JNSJ, zb.DJRQ), 23)")} AS transaction_date,
  {clean_sql("zb.DJZT")} AS document_state,
  {clean_sql("zb.DEL")} AS deleted_flag,
  {clean_sql("zb.XMID")} AS project_legacy_id,
  {clean_sql("zb.XMMC")} AS project_name,
  {clean_sql("cb.THZHID")} AS account_legacy_id,
  {clean_sql("cb.THZH")} AS account_name,
  {clean_sql("cb.JNDWID")} AS counterparty_account_legacy_id,
  {clean_sql("cb.JNDW")} AS counterparty_account_name,
  'expense' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("cb.BCTK")} AS amount,
  {clean_sql("cb.ZJLB")} AS category,
  {clean_sql("zb.WLDWFKDW")} AS source_summary,
  {clean_sql("cb.BZ")} AS note,
  '1' AS active
FROM dbo.C_JFHKLR_TH_ZCDF zb
JOIN dbo.C_JFHKLR_TH_ZCDF_CB cb ON zb.Id = cb.ZBID
WHERE NULLIF(LTRIM(RTRIM(cb.Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(cb.THZHID)), '') IS NOT NULL
  AND ISNULL(zb.DEL, 0) = 0
  AND ISNULL(zb.DJZT, '0') = '2'
  AND ISNULL(cb.BCTK, 0) <> 0
UNION ALL
SELECT
  {clean_sql("Id + ':supplier_payment'")} AS source_key,
  'T_FK_Supplier' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), f_FKRQ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(f_XMID, ''), NULLIF(f_LYXMID, ''), NULLIF(TSXMID, ''))")} AS project_legacy_id,
  {clean_sql("COALESCE(NULLIF(XMMC, ''), NULLIF(f_LYXM, ''), NULLIF(TSXMMC, ''))")} AS project_name,
  {clean_sql("FKZHID")} AS account_legacy_id,
  {clean_sql("COALESCE(NULLIF(FKZHMC, ''), '') + CASE WHEN NULLIF(FKZH, '') IS NOT NULL THEN '/' + FKZH ELSE '' END")} AS account_name,
  {clean_sql("f_SupplierID")} AS counterparty_account_legacy_id,
  {clean_sql("f_SupplierName")} AS counterparty_account_name,
  'expense' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("f_FKJE")} AS amount,
  {clean_sql("COALESCE(NULLIF(f_LB, ''), NULLIF(f_FKLX, ''))")} AS category,
  {clean_sql("f_YT")} AS source_summary,
  {clean_sql("COALESCE(NULLIF(BZ, ''), NULLIF(f_BZ, ''), NULLIF(Remark, ''))")} AS note,
  '1' AS active
FROM dbo.T_FK_Supplier
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(FKZHID)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(SFZFTK, '') <> '是'
  AND ISNULL(f_FKJE, 0) <> 0
UNION ALL
SELECT
  {clean_sql("Id + ':supplier_payment_refund'")} AS source_key,
  'T_FK_Supplier' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), f_FKRQ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(f_XMID, ''), NULLIF(f_LYXMID, ''), NULLIF(TSXMID, ''))")} AS project_legacy_id,
  {clean_sql("COALESCE(NULLIF(XMMC, ''), NULLIF(f_LYXM, ''), NULLIF(TSXMMC, ''))")} AS project_name,
  {clean_sql("FKZHID")} AS account_legacy_id,
  {clean_sql("COALESCE(NULLIF(FKZHMC, ''), '') + CASE WHEN NULLIF(FKZH, '') IS NOT NULL THEN '/' + FKZH ELSE '' END")} AS account_name,
  {clean_sql("f_SupplierID")} AS counterparty_account_legacy_id,
  {clean_sql("f_SupplierName")} AS counterparty_account_name,
  'income' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("f_FKJE")} AS amount,
  {clean_sql("COALESCE(NULLIF(f_LB, ''), NULLIF(f_FKLX, ''))")} AS category,
  {clean_sql("f_YT")} AS source_summary,
  {clean_sql("COALESCE(NULLIF(BZ, ''), NULLIF(f_BZ, ''), NULLIF(Remark, ''))")} AS note,
  '1' AS active
FROM dbo.T_FK_Supplier
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(FKZHID)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(SFZFTK, '') = '是'
  AND ISNULL(f_FKJE, 0) <> 0
UNION ALL
SELECT
  {clean_sql("Id + ':employee_loan_repayment'")} AS source_key,
  'BGGL_JHK_HKDJ' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), HKRQ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("XMMC")} AS project_name,
  {clean_sql("HKZHID")} AS account_legacy_id,
  {clean_sql("HKZH")} AS account_name,
  {clean_sql("COALESCE(NULLIF(WLDWID, ''), NULLIF(PersonId, ''))")} AS counterparty_account_legacy_id,
  {clean_sql("COALESCE(NULLIF(WLDWMC, ''), NULLIF(HKR, ''), NULLIF(SQR, ''))")} AS counterparty_account_name,
  'income' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("HKJE")} AS amount,
  '借款还款' AS category,
  {clean_sql("ZYZJSYAP")} AS source_summary,
  {clean_sql("FJ")} AS note,
  '1' AS active
FROM dbo.BGGL_JHK_HKDJ
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(HKZHID)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(HKJE, 0) <> 0
UNION ALL
SELECT
  {clean_sql("Id + ':employee_loan_request'")} AS source_key,
  'BGGL_JHK_JKSQ' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), SQSJ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("XMMC")} AS project_name,
  {clean_sql("ZKZHID")} AS account_legacy_id,
  {clean_sql("ZKZH")} AS account_name,
  {clean_sql("COALESCE(NULLIF(WLDWID, ''), NULLIF(SKR, ''), NULLIF(SQRID, ''))")} AS counterparty_account_legacy_id,
  {clean_sql("COALESCE(NULLIF(WLDWMC, ''), NULLIF(SKR, ''), NULLIF(SQR, ''))")} AS counterparty_account_name,
  'expense' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("JKJE")} AS amount,
  {clean_sql("COALESCE(NULLIF(FKFSMC, ''), NULLIF(FX, ''), NULLIF(SX, ''))")} AS category,
  {clean_sql("ZYZJSYAP")} AS source_summary,
  {clean_sql("COALESCE(NULLIF(BZ, ''), NULLIF(BZ1, ''))")} AS note,
  '1' AS active
FROM dbo.BGGL_JHK_JKSQ
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(ZKZHID)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(JKJE, 0) <> 0
UNION ALL
SELECT
  {clean_sql("Id + ':risk_loan_repayment'")} AS source_key,
  'ZJGL_ZCDFSZ_FXJK_HK' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), HKSJ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("XMMC")} AS project_name,
  {clean_sql("COALESCE(NULLIF(WSSKZHID, ''), NULLIF(ZCZHID, ''))")} AS account_legacy_id,
  {clean_sql("COALESCE(NULLIF(WSSKZH, ''), NULLIF(ZCZH, ''))")} AS account_name,
  {clean_sql("JKR")} AS counterparty_account_legacy_id,
  {clean_sql("COALESCE(NULLIF(SKKHH, ''), NULLIF(SKDW, ''), NULLIF(FKDW, ''))")} AS counterparty_account_name,
  'income' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("HKJE")} AS amount,
  {clean_sql("JKLX")} AS category,
  {clean_sql("YT")} AS source_summary,
  {clean_sql("BZ")} AS note,
  '1' AS active
FROM dbo.ZJGL_ZCDFSZ_FXJK_HK
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(COALESCE(NULLIF(WSSKZHID, ''), NULLIF(ZCZHID, '')))), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(HKJE, 0) <> 0
UNION ALL
SELECT
  {clean_sql("Id + ':risk_loan_request'")} AS source_key,
  'ZJGL_ZCDFSZ_FXJK_JK' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), TXRQ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("XMMC")} AS project_name,
  {clean_sql("COALESCE(NULLIF(WSZCZHID, ''), NULLIF(SKZHID, ''))")} AS account_legacy_id,
  {clean_sql("COALESCE(NULLIF(WSZCZH, ''), NULLIF(SKZH, ''))")} AS account_name,
  {clean_sql("COALESCE(NULLIF(TXRID, ''), NULLIF(JKR, ''))")} AS counterparty_account_legacy_id,
  {clean_sql("COALESCE(NULLIF(SKDW, ''), NULLIF(JKR, ''), NULLIF(TXR, ''))")} AS counterparty_account_name,
  'expense' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("JKJE")} AS amount,
  {clean_sql("JKLX")} AS category,
  {clean_sql("YT")} AS source_summary,
  {clean_sql("BZ")} AS note,
  '1' AS active
FROM dbo.ZJGL_ZCDFSZ_FXJK_JK
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(COALESCE(NULLIF(WSZCZHID, ''), NULLIF(SKZHID, '')))), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(JKJE, 0) <> 0
UNION ALL
SELECT
  {clean_sql("Id + ':paid_guarantee_deposit'")} AS source_key,
  'ZJGL_BZJGL_Pay_FBZJ' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), TXRQ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(XMID, ''), NULLIF(TBXMID, ''))")} AS project_legacy_id,
  {clean_sql("COALESCE(NULLIF(XMMC, ''), NULLIF(TBXMMC, ''))")} AS project_name,
  {clean_sql("ZFZHID")} AS account_legacy_id,
  {clean_sql("COALESCE(NULLIF(ZFZH, ''), '') + CASE WHEN NULLIF(COALESCE(ZFZHao, ZFZH), '') IS NOT NULL THEN '/' + COALESCE(NULLIF(ZFZHao, ''), ZFZH) ELSE '' END")} AS account_name,
  {clean_sql("SKDWID")} AS counterparty_account_legacy_id,
  {clean_sql("SKDW")} AS counterparty_account_name,
  'expense' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("BZJJE")} AS amount,
  {clean_sql("BZJLX")} AS category,
  {clean_sql("D_QKXYJD_THBZ")} AS source_summary,
  {clean_sql("BZ")} AS note,
  '1' AS active
FROM dbo.ZJGL_BZJGL_Pay_FBZJ
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(ZFZHID)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(BZJJE, 0) <> 0
UNION ALL
SELECT
  {clean_sql("Id + ':paid_guarantee_deposit_refund'")} AS source_key,
  'ZJGL_BZJGL_Pay_FBZJTH' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), THRQ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(XMID, ''), NULLIF(TBXMID, ''))")} AS project_legacy_id,
  {clean_sql("COALESCE(NULLIF(XMMC, ''), NULLIF(TBXMMC, ''))")} AS project_name,
  {clean_sql("THZHID")} AS account_legacy_id,
  {clean_sql("COALESCE(NULLIF(THZH, ''), '') + CASE WHEN NULLIF(COALESCE(ZHHM, Y_ZFZHao, Y_ZFZH, THZH), '') IS NOT NULL THEN '/' + COALESCE(NULLIF(ZHHM, ''), NULLIF(Y_ZFZHao, ''), NULLIF(Y_ZFZH, ''), THZH) ELSE '' END")} AS account_name,
  {clean_sql("Y_SKDWID")} AS counterparty_account_legacy_id,
  {clean_sql("Y_SKDW")} AS counterparty_account_name,
  'income' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("THJE")} AS amount,
  {clean_sql("Y_BZJLX")} AS category,
  {clean_sql("SM")} AS source_summary,
  {clean_sql("Y_BZ")} AS note,
  '1' AS active
FROM dbo.ZJGL_BZJGL_Pay_FBZJTH
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(THZHID)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(THJE, 0) <> 0
UNION ALL
SELECT
  {clean_sql("ID + ':received_guarantee_deposit'")} AS source_key,
  'ZJGL_BZJGL_Branch_SBZJDJ' AS source_table,
  {clean_sql("ID")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), DJRQ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(XMID, ''), NULLIF(TBXMID, ''))")} AS project_legacy_id,
  {clean_sql("COALESCE(NULLIF(XMMC, ''), NULLIF(TBXMMC, ''))")} AS project_name,
  {clean_sql("SKZHID")} AS account_legacy_id,
  {clean_sql("COALESCE(NULLIF(SKZHMC, ''), '') + CASE WHEN NULLIF(SKZH, '') IS NOT NULL THEN '/' + SKZH ELSE '' END")} AS account_name,
  {clean_sql("DWID")} AS counterparty_account_legacy_id,
  {clean_sql("DW")} AS counterparty_account_name,
  'income' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("JE")} AS amount,
  {clean_sql("BZJLX")} AS category,
  {clean_sql("BT")} AS source_summary,
  {clean_sql("BZ")} AS note,
  '1' AS active
FROM dbo.ZJGL_BZJGL_Branch_SBZJDJ
WHERE NULLIF(LTRIM(RTRIM(ID)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(SKZHID)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(JE, 0) <> 0
UNION ALL
SELECT
  {clean_sql("Id + ':received_guarantee_deposit_refund'")} AS source_key,
  'ZJGL_BZJGL_Branch_SBZJTH' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), DJRQ, 23)")} AS transaction_date,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(XMID, ''), NULLIF(TBXMID, ''))")} AS project_legacy_id,
  {clean_sql("COALESCE(NULLIF(XMMC, ''), NULLIF(TBXMMC, ''))")} AS project_name,
  {clean_sql("THZHID")} AS account_legacy_id,
  {clean_sql("COALESCE(NULLIF(SKZH, ''), '') + CASE WHEN NULLIF(THKHHZH, '') IS NOT NULL THEN '/' + THKHHZH ELSE '' END")} AS account_name,
  {clean_sql("SKDWID")} AS counterparty_account_legacy_id,
  {clean_sql("SKDW")} AS counterparty_account_name,
  'expense' AS direction,
  'cumulative' AS metric_bucket,
  {clean_sql("THJE")} AS amount,
  {clean_sql("LX")} AS category,
  {clean_sql("BT")} AS source_summary,
  {clean_sql("BZ")} AS note,
  '1' AS active
FROM dbo.ZJGL_BZJGL_Branch_SBZJTH
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(THZHID)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(DJZT, '0') = '2'
  AND ISNULL(THJE, 0) <> 0
ORDER BY transaction_date, legacy_record_id, direction;
"""
    rows = write_sql_csv(PAYLOAD_CSV, FIELDS, sql)
    payload = {
        "mode": "fresh_db_legacy_account_transaction_replay_adapter",
        "source_table": "C_FKGL_ZHJZJWL,C_CWSFK_GSCWSR,C_CWSFK_GSCWZC,C_JFHKLR,C_JFHKLR_TH,C_JFHKLR_TH_ZCDF_CB,T_FK_Supplier,BGGL_JHK_HKDJ,BGGL_JHK_JKSQ,ZJGL_ZCDFSZ_FXJK_HK,ZJGL_ZCDFSZ_FXJK_JK,ZJGL_BZJGL_Pay_FBZJ,ZJGL_BZJGL_Pay_FBZJTH,ZJGL_BZJGL_Branch_SBZJDJ,ZJGL_BZJGL_Branch_SBZJTH",
        "rows": rows,
        "csv": str(PAYLOAD_CSV),
        "decision": "legacy_account_transaction_payload_ready" if rows else "STOP_REVIEW_REQUIRED",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_ACCOUNT_TRANSACTION_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
