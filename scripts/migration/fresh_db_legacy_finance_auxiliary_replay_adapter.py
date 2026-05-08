#!/usr/bin/env python3
"""Build replay payload for legacy finance auxiliary facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_finance_auxiliary_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_finance_auxiliary_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "source_table",
    "legacy_record_id",
    "legacy_parent_id",
    "legacy_pid",
    "fact_type",
    "source_dataset",
    "document_no",
    "document_date",
    "document_state",
    "project_legacy_id",
    "project_name",
    "partner_legacy_id",
    "partner_name",
    "invoice_code",
    "invoice_no",
    "invoice_type",
    "amount_total",
    "amount_no_tax",
    "tax_amount",
    "tax_rate",
    "category_code",
    "category_name",
    "handler_name",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "attachment_ref",
    "note",
    "active",
]

SOURCE_TABLES = [
    "C_API_JXFP_FPGJ",
    "C_API_JXFP_FPGJCB",
    "C_Base_SRLB",
    "C_Base_HSKMZB",
    "C_JFHKLR_TH_ZCDF",
    "C_ZJGL_GCKZF",
    "C_ZJGL_XMJS_XMJSD",
]


def text_sql(expr: str) -> str:
    return f"REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), {expr}), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"


def date_sql(expr: str) -> str:
    return f"COALESCE(CONVERT(varchar(23), {expr}, 121), '')"


def sqlcmd(sql: str) -> list[str]:
    return [
        "docker",
        "exec",
        SQL_CONTAINER,
        SQLCMD,
        "-b",
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


def run_sql(sql: str) -> str:
    return subprocess.check_output(sqlcmd(sql), text=True)


def payload_sql() -> str:
    selects = [
        f"""
SELECT
  'C_API_JXFP_FPGJ' AS source_table,
  {text_sql("h.ID")} AS legacy_record_id,
  {text_sql("h.C_API_JMZS_TASK_ID")} AS legacy_parent_id,
  {text_sql("h.PID")} AS legacy_pid,
  'input_invoice_trace' AS fact_type,
  '' AS source_dataset,
  {text_sql("h.FPHM")} AS document_no,
  {date_sql("h.KPRQ")} AS document_date,
  {text_sql("h.FPZTDM")} AS document_state,
  {text_sql("h.XMID")} AS project_legacy_id,
  {text_sql("h.XMMC")} AS project_name,
  {text_sql("h.GFSBH")} AS partner_legacy_id,
  {text_sql("COALESCE(h.GFMC, h.XFMC)")} AS partner_name,
  {text_sql("h.FPDM")} AS invoice_code,
  {text_sql("h.FPHM")} AS invoice_no,
  {text_sql("h.FPLX")} AS invoice_type,
  {text_sql("h.JSHJ")} AS amount_total,
  {text_sql("h.JE")} AS amount_no_tax,
  {text_sql("h.SE")} AS tax_amount,
  {text_sql("h.SLV")} AS tax_rate,
  {text_sql("h.JXXBZ")} AS category_code,
  {text_sql("h.KPYF")} AS category_name,
  {text_sql("h.KPR")} AS handler_name,
  {text_sql("h.LRRID")} AS creator_legacy_user_id,
  {text_sql("h.LRR")} AS creator_name,
  {date_sql("h.LRSJ")} AS created_time,
  {text_sql("COALESCE(h.FJ, h.FPFJ)")} AS attachment_ref,
  {text_sql("COALESCE(h.BZ, h.FPFJ_JSONSTR)")} AS note,
  CASE WHEN COALESCE(NULLIF(h.DEL, ''), '0') IN ('0', 'False', 'false') THEN '1' ELSE '0' END AS active
FROM dbo.C_API_JXFP_FPGJ h
WHERE NULLIF(LTRIM(RTRIM(h.ID)), '') IS NOT NULL
""",
        f"""
SELECT
  'C_API_JXFP_FPGJCB' AS source_table,
  {text_sql("h.ID")} AS legacy_record_id,
  {text_sql("h.ZBID")} AS legacy_parent_id,
  {text_sql("h.PID")} AS legacy_pid,
  'input_invoice_trace_line' AS fact_type,
  '' AS source_dataset,
  {text_sql("COALESCE(parent.FPHM, h.FPHM)")} AS document_no,
  {date_sql("parent.KPRQ")} AS document_date,
  {text_sql("parent.FPZTDM")} AS document_state,
  {text_sql("parent.XMID")} AS project_legacy_id,
  {text_sql("parent.XMMC")} AS project_name,
  {text_sql("parent.GFSBH")} AS partner_legacy_id,
  {text_sql("COALESCE(parent.GFMC, parent.XFMC)")} AS partner_name,
  {text_sql("COALESCE(parent.FPDM, h.FPDM)")} AS invoice_code,
  {text_sql("COALESCE(parent.FPHM, h.FPHM)")} AS invoice_no,
  {text_sql("parent.FPLX")} AS invoice_type,
  {text_sql("h.JE + h.SE")} AS amount_total,
  {text_sql("h.JE")} AS amount_no_tax,
  {text_sql("h.SE")} AS tax_amount,
  {text_sql("h.SLV")} AS tax_rate,
  {text_sql("h.SPBM")} AS category_code,
  {text_sql("h.MC")} AS category_name,
  {text_sql("parent.KPR")} AS handler_name,
  {text_sql("parent.LRRID")} AS creator_legacy_user_id,
  {text_sql("parent.LRR")} AS creator_name,
  {date_sql("parent.LRSJ")} AS created_time,
  {text_sql("COALESCE(parent.FJ, parent.FPFJ)")} AS attachment_ref,
  {text_sql("CONCAT('规格:', COALESCE(h.GGXH, ''), '; 单位:', COALESCE(h.JLDW, ''), '; 数量:', COALESCE(CONVERT(varchar(max), h.SL), ''), '; 单价:', COALESCE(CONVERT(varchar(max), h.DJ), ''))")} AS note,
  CASE WHEN parent.ID IS NULL OR COALESCE(NULLIF(parent.DEL, ''), '0') IN ('0', 'False', 'false') THEN '1' ELSE '0' END AS active
FROM dbo.C_API_JXFP_FPGJCB h
LEFT JOIN dbo.C_API_JXFP_FPGJ parent ON parent.ID = h.ZBID
WHERE NULLIF(LTRIM(RTRIM(h.ID)), '') IS NOT NULL
""",
        f"""
SELECT
  'C_Base_SRLB' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  {text_sql("h.f_Tree_Parentid")} AS legacy_parent_id,
  '' AS legacy_pid,
  'income_category_dictionary' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("h.f_Tree_Code")} AS document_no,
  {date_sql("h.f_Tree_importTime")} AS document_date,
  {text_sql("h.f_Tree_del")} AS document_state,
  {text_sql("h.f_Tree_XMID")} AS project_legacy_id,
  {text_sql("h.XMMC")} AS project_name,
  '' AS partner_legacy_id,
  '' AS partner_name,
  '' AS invoice_code,
  '' AS invoice_no,
  '' AS invoice_type,
  '0' AS amount_total,
  '0' AS amount_no_tax,
  '0' AS tax_amount,
  '0' AS tax_rate,
  {text_sql("h.f_Tree_Code")} AS category_code,
  {text_sql("h.f_Tree_Name")} AS category_name,
  {text_sql("h.f_Tree_importPerson")} AS handler_name,
  '' AS creator_legacy_user_id,
  {text_sql("h.f_Tree_importPerson")} AS creator_name,
  {date_sql("h.f_Tree_importTime")} AS created_time,
  '' AS attachment_ref,
  {text_sql("CONCAT('收入类别:', COALESCE(h.f_Tree_Name, ''), '; 责任人:', COALESCE(h.f_MBZRS, ''), '; 来源:', COALESCE(h.LY, ''), '; 备注:', COALESCE(h.f_Tree_remark, ''))")} AS note,
  CASE WHEN COALESCE(NULLIF(h.f_Tree_del, ''), '0') IN ('0', 'False', 'false') THEN '1' ELSE '0' END AS active
FROM dbo.C_Base_SRLB h
WHERE h.Id IS NOT NULL
""",
        f"""
SELECT
  'C_Base_HSKMZB' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  '' AS legacy_parent_id,
  {text_sql("h.PID")} AS legacy_pid,
  'accounting_subject_mapping' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("h.NKLXID")} AS document_no,
  {date_sql("h.LRSJ")} AS document_date,
  '' AS document_state,
  {text_sql("h.XMIDS")} AS project_legacy_id,
  {text_sql("h.XMMCS")} AS project_name,
  {text_sql("h.MBZRSID")} AS partner_legacy_id,
  {text_sql("h.MBZRSMC")} AS partner_name,
  '' AS invoice_code,
  '' AS invoice_no,
  '' AS invoice_type,
  '0' AS amount_total,
  '0' AS amount_no_tax,
  '0' AS tax_amount,
  '0' AS tax_rate,
  {text_sql("h.NKLXID")} AS category_code,
  {text_sql("h.NKLX")} AS category_name,
  {text_sql("h.LRR")} AS handler_name,
  '' AS creator_legacy_user_id,
  {text_sql("h.LRR")} AS creator_name,
  {date_sql("h.LRSJ")} AS created_time,
  '' AS attachment_ref,
  {text_sql("CONCAT('核算规则:', COALESCE(h.HBGZ, ''), '; 目标责任书:', COALESCE(h.MBZRSMC, ''))")} AS note,
  '1' AS active
FROM dbo.C_Base_HSKMZB h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'C_JFHKLR_TH_ZCDF' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  '' AS legacy_parent_id,
  {text_sql("h.pid")} AS legacy_pid,
  'self_funding_refund_header' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("h.DJBH")} AS document_no,
  {date_sql("h.DJRQ")} AS document_date,
  {text_sql("h.DJZT")} AS document_state,
  {text_sql("h.XMID")} AS project_legacy_id,
  {text_sql("h.XMMC")} AS project_name,
  {text_sql("h.XMJLID")} AS partner_legacy_id,
  {text_sql("COALESCE(h.XMJLMC, h.WLDWFKDW)")} AS partner_name,
  '' AS invoice_code,
  '' AS invoice_no,
  '' AS invoice_type,
  '0' AS amount_total,
  '0' AS amount_no_tax,
  '0' AS tax_amount,
  '0' AS tax_rate,
  {text_sql("h.D_SCBSJS_IsPush")} AS category_code,
  '自筹退回表头' AS category_name,
  {text_sql("h.THDJR")} AS handler_name,
  {text_sql("h.LRRID")} AS creator_legacy_user_id,
  {text_sql("h.LRR")} AS creator_name,
  {date_sql("h.LRSJ")} AS created_time,
  {text_sql("h.FJ")} AS attachment_ref,
  {text_sql("h.BZ")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_JFHKLR_TH_ZCDF h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'C_ZJGL_GCKZF' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  '' AS legacy_parent_id,
  {text_sql("h.pid")} AS legacy_pid,
  'project_payment_content' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("h.DJBH")} AS document_no,
  {date_sql("h.FKRQ")} AS document_date,
  {text_sql("h.DJZT")} AS document_state,
  {text_sql("h.XMID")} AS project_legacy_id,
  {text_sql("h.XMMC")} AS project_name,
  '' AS partner_legacy_id,
  '' AS partner_name,
  '' AS invoice_code,
  '' AS invoice_no,
  '' AS invoice_type,
  '0' AS amount_total,
  '0' AS amount_no_tax,
  '0' AS tax_amount,
  '0' AS tax_rate,
  '' AS category_code,
  {text_sql("h.FKNR")} AS category_name,
  {text_sql("h.LRR")} AS handler_name,
  {text_sql("h.LRRID")} AS creator_legacy_user_id,
  {text_sql("h.LRR")} AS creator_name,
  {date_sql("h.LRSJ")} AS created_time,
  {text_sql("h.FJ")} AS attachment_ref,
  {text_sql("h.BZ")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_ZJGL_GCKZF h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'C_ZJGL_XMJS_XMJSD' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  '' AS legacy_parent_id,
  {text_sql("h.pid")} AS legacy_pid,
  'project_settlement_tax_summary' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("h.DJBH")} AS document_no,
  {date_sql("COALESCE(h.JSRQ, h.ZBRQ)")} AS document_date,
  {text_sql("h.DJZT")} AS document_state,
  {text_sql("h.XMID")} AS project_legacy_id,
  {text_sql("h.XMMC")} AS project_name,
  '' AS partner_legacy_id,
  '' AS partner_name,
  '' AS invoice_code,
  '' AS invoice_no,
  '' AS invoice_type,
  {text_sql("h.HTZJ")} AS amount_total,
  {text_sql("h.LJJS")} AS amount_no_tax,
  {text_sql("h.YJZZS_BCJSJE + h.YJFJS_BCJSJE")} AS tax_amount,
  {text_sql("h.GLFBL")} AS tax_rate,
  {text_sql("h.DJBH")} AS category_code,
  '项目结算税费摘要' AS category_name,
  {text_sql("h.LRR")} AS handler_name,
  {text_sql("h.LRRID")} AS creator_legacy_user_id,
  {text_sql("h.LRR")} AS creator_name,
  {date_sql("h.LRSJ")} AS created_time,
  {text_sql("h.FJ")} AS attachment_ref,
  {text_sql("CONCAT('累计开票:', COALESCE(CONVERT(varchar(max), h.LJKP), ''), '; 累计回款:', COALESCE(CONVERT(varchar(max), h.LJHK), ''), '; 本次结算:', COALESCE(CONVERT(varchar(max), h.LJJS), ''), '; 销项税:', COALESCE(CONVERT(varchar(max), h.XXS_BCJSJE), ''), '; 进项税:', COALESCE(CONVERT(varchar(max), h.JXS_BCJSJE), ''), '; 管理费:', COALESCE(CONVERT(varchar(max), h.GLF_BCJSJE), ''))")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_ZJGL_XMJS_XMJSD h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
    ]
    return "\nSET NOCOUNT ON;\n" + "\nUNION ALL\n".join(selects) + "\nORDER BY source_table, legacy_record_id;\n"


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
                if not stripped or (stripped.startswith("(") and stripped.endswith("rows affected)")):
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


def scalar(sql: str) -> int:
    raw = run_sql(sql)
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and not (stripped.startswith("(") and stripped.endswith("rows affected)")):
            return int(stripped)
    return 0


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    rows = write_csv_payload()
    table_counts: dict[str, int] = {}
    active_rows = 0
    amount_total_sum = Decimal("0")
    tax_amount_sum = Decimal("0")
    with OUTPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            table = row.get("source_table") or ""
            table_counts[table] = table_counts.get(table, 0) + 1
            if row.get("active") == "1":
                active_rows += 1
            for key in ("amount_total", "tax_amount"):
                raw = (row.get(key) or "").strip()
                if not raw:
                    continue
                try:
                    amount = Decimal(raw)
                except InvalidOperation:
                    continue
                if key == "amount_total":
                    amount_total_sum += amount
                else:
                    tax_amount_sum += amount
    source_counts = {table: scalar(f"SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.{table};") for table in SOURCE_TABLES}
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_finance_auxiliary_replay_adapter",
        "total_rows": rows,
        "active_rows": active_rows,
        "source_counts": source_counts,
        "table_counts": table_counts,
        "amount_total_sum": str(amount_total_sum),
        "tax_amount_sum": str(tax_amount_sum),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_finance_auxiliary_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_FINANCE_AUXILIARY_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
