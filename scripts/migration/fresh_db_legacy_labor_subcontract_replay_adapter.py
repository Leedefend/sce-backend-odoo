#!/usr/bin/env python3
"""Build replay payload for legacy labor and subcontract facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_labor_subcontract_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_labor_subcontract_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_record_id",
    "legacy_pid",
    "source_table",
    "source_dataset",
    "fact_type",
    "document_no",
    "document_state",
    "project_legacy_id",
    "project_name",
    "partner_legacy_id",
    "partner_name",
    "contract_legacy_id",
    "contract_no",
    "contract_name",
    "work_scope",
    "work_part",
    "department_name",
    "document_date",
    "start_date",
    "end_date",
    "created_time",
    "creator_name",
    "creator_legacy_user_id",
    "amount_total",
    "amount_contract",
    "amount_settlement",
    "amount_payable",
    "amount_deduction",
    "tax_rate",
    "bank_name",
    "bank_account",
    "attachment_ref",
    "note",
    "active",
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


def select_clause(
    *,
    table: str,
    id_expr: str,
    pid_expr: str,
    source_dataset: str,
    fact_type: str,
    document_no: str,
    document_state: str,
    project_id: str,
    project_name: str,
    partner_id: str,
    partner_name: str,
    contract_id: str,
    contract_no: str,
    contract_name: str,
    work_scope: str,
    work_part: str,
    department: str,
    document_date: str,
    start_date: str,
    end_date: str,
    created_time: str,
    creator_name: str,
    creator_id: str,
    amount_total: str,
    amount_contract: str,
    amount_settlement: str,
    amount_payable: str,
    amount_deduction: str,
    tax_rate: str,
    bank_name: str,
    bank_account: str,
    attachment: str,
    note: str,
    active_expr: str,
    from_sql: str,
) -> str:
    return f"""
SELECT
  {text_sql(id_expr)} AS legacy_record_id,
  {text_sql(pid_expr)} AS legacy_pid,
  '{table}' AS source_table,
  {text_sql(source_dataset)} AS source_dataset,
  '{fact_type}' AS fact_type,
  {text_sql(document_no)} AS document_no,
  {text_sql(document_state)} AS document_state,
  {text_sql(project_id)} AS project_legacy_id,
  {text_sql(project_name)} AS project_name,
  {text_sql(partner_id)} AS partner_legacy_id,
  {text_sql(partner_name)} AS partner_name,
  {text_sql(contract_id)} AS contract_legacy_id,
  {text_sql(contract_no)} AS contract_no,
  {text_sql(contract_name)} AS contract_name,
  {text_sql(work_scope)} AS work_scope,
  {text_sql(work_part)} AS work_part,
  {text_sql(department)} AS department_name,
  {date_sql(document_date)} AS document_date,
  {date_sql(start_date)} AS start_date,
  {date_sql(end_date)} AS end_date,
  {date_sql(created_time)} AS created_time,
  {text_sql(creator_name)} AS creator_name,
  {text_sql(creator_id)} AS creator_legacy_user_id,
  {text_sql(amount_total)} AS amount_total,
  {text_sql(amount_contract)} AS amount_contract,
  {text_sql(amount_settlement)} AS amount_settlement,
  {text_sql(amount_payable)} AS amount_payable,
  {text_sql(amount_deduction)} AS amount_deduction,
  {text_sql(tax_rate)} AS tax_rate,
  {text_sql(bank_name)} AS bank_name,
  {text_sql(bank_account)} AS bank_account,
  {text_sql(attachment)} AS attachment_ref,
  {text_sql(note)} AS note,
  CASE WHEN {active_expr} THEN '1' ELSE '0' END AS active
{from_sql}
"""


def payload_sql() -> str:
    parts = [
        select_clause(
            table="LW_BZHTGL",
            fact_type="labor_contract",
            id_expr="Id",
            pid_expr="Pid",
            source_dataset="SJBMC",
            document_no="DJBH",
            document_state="DJZT",
            project_id="f_XMID",
            project_name="f_GCMC",
            partner_id="COALESCE(NULLIF(f_LWDWID, ''), NULLIF(SKDWID, ''))",
            partner_name="COALESCE(NULLIF(f_LWDWMC, ''), NULLIF(LWGS, ''), NULLIF(SKDW, ''))",
            contract_id="COALESCE(NULLIF(Id, ''), NULLIF(GLYHTID, ''))",
            contract_no="COALESCE(NULLIF(f_HTBH, ''), NULLIF(GLYHTBH, ''), NULLIF(DJBH, ''))",
            contract_name="COALESCE(NULLIF(HTMC, ''), NULLIF(f_LWHT, ''), NULLIF(f_HTNR, ''))",
            work_scope="COALESCE(NULLIF(f_HTNR, ''), NULLIF(f_BZMC, ''), NULLIF(BZ, ''))",
            work_part="SGBWMC",
            department="COALESCE(NULLIF(JBBM, ''), NULLIF(BM, ''))",
            document_date="COALESCE(f_QDRQ, f_LRSJ)",
            start_date="f_QDRQ",
            end_date="QRRQ",
            created_time="f_LRSJ",
            creator_name="f_LRR",
            creator_id="LRRID",
            amount_total="ZJE",
            amount_contract="ZJE",
            amount_settlement="0",
            amount_payable="0",
            amount_deduction="0",
            tax_rate="SLV",
            bank_name="''",
            bank_account="''",
            attachment="''",
            note="COALESCE(NULLIF(f_BZ, ''), NULLIF(BZ, ''))",
            active_expr="COALESCE(CONVERT(varchar(max), DEL), '0') IN ('0', '', 'False', 'false')",
            from_sql="FROM dbo.LW_BZHTGL",
        ),
        select_clause(
            table="LW_LWHTGL_SP",
            fact_type="labor_contract",
            id_expr="Id",
            pid_expr="Pid",
            source_dataset="SJBMC",
            document_no="DJBH",
            document_state="DJZT",
            project_id="f_XMID",
            project_name="''",
            partner_id="f_LWDWID",
            partner_name="f_LWDWMC",
            contract_id="Id",
            contract_no="COALESCE(NULLIF(f_HTBH, ''), NULLIF(DJBH, ''))",
            contract_name="f_HTNR",
            work_scope="f_HTNR",
            work_part="''",
            department="f_JSDW",
            document_date="COALESCE(f_QDRQ, f_LRSJ)",
            start_date="f_QDRQ",
            end_date="f_SDSJ",
            created_time="f_LRSJ",
            creator_name="f_LRR",
            creator_id="LRRID",
            amount_total="f_HTJE",
            amount_contract="f_HTJE",
            amount_settlement="0",
            amount_payable="0",
            amount_deduction="0",
            tax_rate="SLV",
            bank_name="''",
            bank_account="''",
            attachment="FJ",
            note="COALESCE(NULLIF(f_BZ, ''), NULLIF(f_SDYJ, ''))",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.LW_LWHTGL_SP",
        ),
        select_clause(
            table="SGGL_FBGL_FBHT",
            fact_type="subcontract_contract",
            id_expr="Id",
            pid_expr="pid",
            source_dataset="SJBMC",
            document_no="DJBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_id="FBDWID",
            partner_name="FBDW",
            contract_id="Id",
            contract_no="COALESCE(NULLIF(HTBH, ''), NULLIF(DJBH, ''))",
            contract_name="COALESCE(NULLIF(HTMC, ''), NULLIF(FBNR, ''))",
            work_scope="FBNR",
            work_part="SGBWMC",
            department="''",
            document_date="COALESCE(QDSJ, LRSJ)",
            start_date="QDSJ",
            end_date="FHHTSJ",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            amount_total="JE",
            amount_contract="JE",
            amount_settlement="0",
            amount_payable="0",
            amount_deduction="0",
            tax_rate="SLV",
            bank_name="KHH",
            bank_account="YHZH",
            attachment="FJ",
            note="COALESCE(NULLIF(BZ, ''), NULLIF(BZ1, ''))",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.SGGL_FBGL_FBHT",
        ),
        select_clause(
            table="LW_Base_FDGL",
            fact_type="subcontract_settlement",
            id_expr="Id",
            pid_expr="Pid",
            source_dataset="SJBMC",
            document_no="DJBH",
            document_state="DJZT",
            project_id="COALESCE(NULLIF(XMID, ''), NULLIF(f_XMID, ''))",
            project_name="COALESCE(NULLIF(XMMC, ''), NULLIF(f_GCMC, ''))",
            partner_id="COALESCE(NULLIF(LWDWID, ''), NULLIF(SKDWID, ''), NULLIF(WFDWID, ''))",
            partner_name="COALESCE(NULLIF(f_LWDW, ''), NULLIF(SKDW, ''), NULLIF(WFDW, ''))",
            contract_id="LWHTID",
            contract_no="COALESCE(NULLIF(LWHTDH, ''), NULLIF(f_BZHTBH, ''), NULLIF(DJBH, ''))",
            contract_name="COALESCE(NULLIF(HTMC, ''), NULLIF(BZZXM, ''), NULLIF(GZ, ''))",
            work_scope="COALESCE(NULLIF(GZ, ''), NULLIF(BZ, ''), NULLIF(HTMC, ''))",
            work_part="SGBWMC",
            department="SQBM",
            document_date="COALESCE(DJRQ, JSZZRQ, f_LRSJ)",
            start_date="JSQSRQ",
            end_date="JSZZRQ",
            created_time="f_LRSJ",
            creator_name="f_LRR",
            creator_id="LRRID",
            amount_total="ZJE",
            amount_contract="0",
            amount_settlement="ZJE",
            amount_payable="YFJE",
            amount_deduction="0",
            tax_rate="SLV",
            bank_name="KHH",
            bank_account="YHZH",
            attachment="''",
            note="COALESCE(NULLIF(f_BZ, ''), NULLIF(BZ, ''), NULLIF(QKYJ, ''))",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.LW_Base_FDGL",
        ),
        select_clause(
            table="SGGL_LWGL_LXYG",
            fact_type="labor_usage",
            id_expr="Id",
            pid_expr="pid",
            source_dataset="SJBMC",
            document_no="DJBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_id="COALESCE(NULLIF(SGDWID, ''), NULLIF(LWDWID, ''))",
            partner_name="SGDWMC",
            contract_id="''",
            contract_no="HTBH",
            contract_name="BT",
            work_scope="COALESCE(NULLIF(BT, ''), NULLIF(BZ, ''))",
            work_part="SGBWMC",
            department="ZDBM",
            document_date="DJRQ",
            start_date="DJRQ",
            end_date="DJRQ",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            amount_total="ZJE",
            amount_contract="0",
            amount_settlement="ZJE",
            amount_payable="0",
            amount_deduction="0",
            tax_rate="0",
            bank_name="KHH",
            bank_account="KHZH",
            attachment="FJ",
            note="BZ",
            active_expr="COALESCE(CONVERT(varchar(max), DEL), '0') IN ('0', '', 'False', 'false')",
            from_sql="FROM dbo.SGGL_LWGL_LXYG",
        ),
        select_clause(
            table="T_JS_LWJSD",
            fact_type="labor_settlement",
            id_expr="Id",
            pid_expr="pid",
            source_dataset="SJBMC",
            document_no="DJBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_id="JSDWID",
            partner_name="COALESCE(NULLIF(GYDW, ''), NULLIF(SKDWM, ''))",
            contract_id="LWHTID",
            contract_no="HTBH",
            contract_name="JSSM",
            work_scope="COALESCE(NULLIF(JSSM, ''), NULLIF(TYPE, ''), NULLIF(GJC, ''))",
            work_part="''",
            department="BM",
            document_date="COALESCE(JSRQ, LRSJ)",
            start_date="QSJSRQ",
            end_date="ZZJSRQ",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            amount_total="ZJE",
            amount_contract="HTJE",
            amount_settlement="ZJE",
            amount_payable="SYWFKJE",
            amount_deduction="ZKJE",
            tax_rate="0",
            bank_name="''",
            bank_account="''",
            attachment="FJ",
            note="JSSM",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.T_JS_LWJSD",
        ),
        select_clause(
            table="T_JS_CLJSD",
            fact_type="subcontract_settlement",
            id_expr="Id",
            pid_expr="pid",
            source_dataset="SJBMC",
            document_no="DJBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_id="JSDWID",
            partner_name="GYDW",
            contract_id="''",
            contract_no="COALESCE(NULLIF(HTBH, ''), NULLIF(HTBH_2, ''))",
            contract_name="JSSM",
            work_scope="JSSM",
            work_part="''",
            department="''",
            document_date="COALESCE(JSRQ, LRSJ)",
            start_date="QSJSRQ",
            end_date="ZZJSRQ",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            amount_total="ZJE",
            amount_contract="0",
            amount_settlement="ZJE",
            amount_payable="YFJE",
            amount_deduction="ZKJE",
            tax_rate="0",
            bank_name="''",
            bank_account="''",
            attachment="FJ",
            note="JSSM",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.T_JS_CLJSD",
        ),
        select_clause(
            table="GLFY_GLFYJSD",
            fact_type="subcontract_settlement",
            id_expr="Id",
            pid_expr="PID",
            source_dataset="SJBMC",
            document_no="DJBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_id="JSDWID",
            partner_name="JSDW",
            contract_id="HTID",
            contract_no="''",
            contract_name="BT",
            work_scope="COALESCE(NULLIF(BT, ''), NULLIF(BZ, ''))",
            work_part="''",
            department="''",
            document_date="COALESCE(DJRQ, LRSJ)",
            start_date="DJRQ",
            end_date="DJRQ",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            amount_total="JSHJJE",
            amount_contract="0",
            amount_settlement="JSHJJE",
            amount_payable="0",
            amount_deduction="ZKJE",
            tax_rate="0",
            bank_name="''",
            bank_account="''",
            attachment="FJ",
            note="BZ",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.GLFY_GLFYJSD",
        ),
        select_clause(
            table="GLFY_XMFYBXD",
            fact_type="expense_claim",
            id_expr="Id",
            pid_expr="pid",
            source_dataset="SJBMC",
            document_no="DJBH",
            document_state="CONVERT(varchar(max), DJZT)",
            project_id="XMID",
            project_name="XMMC",
            partner_id="BXDWID",
            partner_name="COALESCE(NULLIF(BXDW, ''), NULLIF(SKR, ''))",
            contract_id="''",
            contract_no="''",
            contract_name="YWMC",
            work_scope="COALESCE(NULLIF(YWMC, ''), NULLIF(BXZL, ''), NULLIF(BZ, ''))",
            work_part="''",
            department="BM",
            document_date="LRSJ",
            start_date="LRSJ",
            end_date="XGSJ",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            amount_total="COALESCE(SJBXJE, HJ)",
            amount_contract="0",
            amount_settlement="COALESCE(SJBXJE, HJ)",
            amount_payable="SQBXJE",
            amount_deduction="HXJE",
            tax_rate="SLV",
            bank_name="KHYH",
            bank_account="SKZH",
            attachment="FJ",
            note="BZ",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.GLFY_XMFYBXD",
        ),
        select_clause(
            table="SGGL_LWGL_LXYG_CB",
            fact_type="labor_usage",
            id_expr="Id",
            pid_expr="pid",
            source_dataset="SJBMC",
            document_no="ZBID",
            document_state="''",
            project_id="''",
            project_name="XMMC",
            partner_id="ZRDWID",
            partner_name="ZRDW",
            contract_id="ZBID",
            contract_no="ZBID",
            contract_name="SGNR",
            work_scope="SGNR",
            work_part="SGBW",
            department="''",
            document_date="RQ",
            start_date="QZSJ_KS",
            end_date="QZSJ_JZ",
            created_time="RQ",
            creator_name="SGY",
            creator_id="''",
            amount_total="JE",
            amount_contract="0",
            amount_settlement="JE",
            amount_payable="GRHJ",
            amount_deduction="0",
            tax_rate="0",
            bank_name="''",
            bank_account="''",
            attachment="FJL",
            note="BZ",
            active_expr="1 = 1",
            from_sql="FROM dbo.SGGL_LWGL_LXYG_CB",
        ),
        select_clause(
            table="GLFY_Bill",
            fact_type="expense_claim",
            id_expr="Id",
            pid_expr="''",
            source_dataset="SJBMC",
            document_no="COALESCE(NULLIF(DJBH, ''), NULLIF(handBillCode, ''))",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_id="FKDWID",
            partner_name="FKDW",
            contract_id="''",
            contract_no="''",
            contract_name="BT",
            work_scope="COALESCE(NULLIF(BT, ''), NULLIF(note, ''))",
            work_part="SGBWMC",
            department="ZDBM",
            document_date="COALESCE(recordDate, createDate)",
            start_date="recordDate",
            end_date="modifyDate",
            created_time="createDate",
            creator_name="createUserName",
            creator_id="CONVERT(varchar(max), createUserID)",
            amount_total="ZJE",
            amount_contract="0",
            amount_settlement="ZJE",
            amount_payable="0",
            amount_deduction="CZJE",
            tax_rate="SLV",
            bank_name="''",
            bank_account="''",
            attachment="FJ",
            note="note",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.GLFY_Bill",
        ),
    ]
    return "SET NOCOUNT ON;\n" + "\nUNION ALL\n".join(parts) + "\nORDER BY source_table, document_date, legacy_record_id;"


def write_csv_payload() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
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


def csv_summary() -> dict[str, object]:
    amount_total = Decimal("0")
    active_rows = 0
    source_counts: dict[str, int] = {}
    fact_type_counts: dict[str, int] = {}
    with OUTPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            source_counts[row["source_table"]] = source_counts.get(row["source_table"], 0) + 1
            fact_type_counts[row["fact_type"]] = fact_type_counts.get(row["fact_type"], 0) + 1
            if row.get("active") == "1":
                active_rows += 1
            try:
                amount_total += Decimal(row.get("amount_total") or "0")
            except InvalidOperation:
                pass
    return {
        "active_rows": active_rows,
        "amount_total_sum": str(amount_total),
        "source_counts": source_counts,
        "fact_type_counts": fact_type_counts,
    }


def main() -> int:
    rows = write_csv_payload()
    summary = csv_summary()
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_labor_subcontract_replay_adapter",
        "total_rows": rows,
        "active_rows": summary["active_rows"],
        "amount_total_sum": summary["amount_total_sum"],
        "source_counts": summary["source_counts"],
        "fact_type_counts": summary["fact_type_counts"],
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_labor_subcontract_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_LABOR_SUBCONTRACT_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
