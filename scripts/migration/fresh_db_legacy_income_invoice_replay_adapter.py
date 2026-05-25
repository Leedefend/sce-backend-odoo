#!/usr/bin/env python3
"""Build replay payload for legacy income invoice facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_income_invoice_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_income_invoice_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_record_id",
    "legacy_parent_id",
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
    "partner_tax_no",
    "contract_legacy_id",
    "contract_no",
    "contract_name",
    "invoice_no",
    "invoice_code",
    "invoice_type",
    "invoice_content",
    "tax_method",
    "tax_type",
    "tax_certificate_no",
    "document_date",
    "invoice_date",
    "expected_receipt_date",
    "created_time",
    "creator_name",
    "creator_legacy_user_id",
    "qty",
    "unit_price",
    "amount_total",
    "amount_no_tax",
    "tax_amount",
    "tax_rate",
    "amount_contract",
    "amount_received",
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


def select_clause(
    *,
    table: str,
    fact_type: str,
    id_expr: str,
    parent_expr: str = "''",
    pid_expr: str = "''",
    source_dataset: str = "SJBMC",
    document_no: str = "DJBH",
    document_state: str = "DJZT",
    project_id: str = "''",
    project_name: str = "''",
    partner_id: str = "''",
    partner_name: str = "''",
    partner_tax_no: str = "''",
    contract_id: str = "''",
    contract_no: str = "''",
    contract_name: str = "''",
    invoice_no: str = "''",
    invoice_code: str = "''",
    invoice_type: str = "''",
    invoice_content: str = "''",
    tax_method: str = "''",
    tax_type: str = "''",
    tax_certificate_no: str = "''",
    document_date: str = "NULL",
    invoice_date: str = "NULL",
    expected_receipt_date: str = "NULL",
    created_time: str = "NULL",
    creator_name: str = "''",
    creator_id: str = "''",
    qty: str = "0",
    unit_price: str = "0",
    amount_total: str = "0",
    amount_no_tax: str = "0",
    tax_amount: str = "0",
    tax_rate: str = "0",
    amount_contract: str = "0",
    amount_received: str = "0",
    bank_name: str = "''",
    bank_account: str = "''",
    attachment: str = "''",
    note: str = "''",
    active_expr: str = "1 = 1",
    from_sql: str,
) -> str:
    return f"""
SELECT
  {text_sql(id_expr)} AS legacy_record_id,
  {text_sql(parent_expr)} AS legacy_parent_id,
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
  {text_sql(partner_tax_no)} AS partner_tax_no,
  {text_sql(contract_id)} AS contract_legacy_id,
  {text_sql(contract_no)} AS contract_no,
  {text_sql(contract_name)} AS contract_name,
  {text_sql(invoice_no)} AS invoice_no,
  {text_sql(invoice_code)} AS invoice_code,
  {text_sql(invoice_type)} AS invoice_type,
  {text_sql(invoice_content)} AS invoice_content,
  {text_sql(tax_method)} AS tax_method,
  {text_sql(tax_type)} AS tax_type,
  {text_sql(tax_certificate_no)} AS tax_certificate_no,
  {date_sql(document_date)} AS document_date,
  {date_sql(invoice_date)} AS invoice_date,
  {date_sql(expected_receipt_date)} AS expected_receipt_date,
  {date_sql(created_time)} AS created_time,
  {text_sql(creator_name)} AS creator_name,
  {text_sql(creator_id)} AS creator_legacy_user_id,
  {text_sql(qty)} AS qty,
  {text_sql(unit_price)} AS unit_price,
  {text_sql(amount_total)} AS amount_total,
  {text_sql(amount_no_tax)} AS amount_no_tax,
  {text_sql(tax_amount)} AS tax_amount,
  {text_sql(tax_rate)} AS tax_rate,
  {text_sql(amount_contract)} AS amount_contract,
  {text_sql(amount_received)} AS amount_received,
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
            table="C_JXXP_KJFPSQ",
            fact_type="invoice_application",
            id_expr="Id",
            pid_expr="pid",
            document_no="DJBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_id="MCID",
            partner_name="SPF_MC",
            partner_tax_no="SPF_SBH",
            contract_id="D_JCLY_GLHTID",
            contract_no="HTBH",
            contract_name="KPF_HTMC",
            invoice_type="COALESCE(NULLIF(FPZL, ''), NULLIF(KPF_FPZL, ''))",
            invoice_content="COALESCE(NULLIF(FPBT, ''), NULLIF(FB_YWFB, ''))",
            tax_method="KPF_JSFF",
            document_date="COALESCE(SQRQ, LRSJ)",
            expected_receipt_date="YJHKRQ",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            qty="BCSK_GCK",
            amount_total="COALESCE(BCKPJE, BCKP_JE, BCKP_ZS)",
            amount_no_tax="BCKP_JE",
            tax_amount="BCKP_ZS - BCKP_JE",
            amount_contract="HTE",
            amount_received="COALESCE(LJYSK, LJYJSK)",
            bank_name="SPF_KHYH",
            bank_account="SPF_YHZH",
            attachment="FJ",
            note="COALESCE(NULLIF(BZ, ''), NULLIF(SQYY, ''), NULLIF(FPBZ, ''))",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.C_JXXP_KJFPSQ",
        ),
        select_clause(
            table="C_JXXP_KJFPSQ_CB",
            fact_type="invoice_application_line",
            id_expr="l.Id",
            parent_expr="l.ZBID",
            pid_expr="l.PId",
            source_dataset="l.SJBMC",
            document_no="COALESCE(NULLIF(h.DJBH, ''), NULLIF(l.JDCZDJH, ''))",
            document_state="h.DJZT",
            project_id="h.XMID",
            project_name="h.XMMC",
            partner_id="h.MCID",
            partner_name="h.SPF_MC",
            partner_tax_no="h.SPF_SBH",
            contract_id="h.D_JCLY_GLHTID",
            contract_no="h.HTBH",
            contract_name="h.KPF_HTMC",
            invoice_type="COALESCE(NULLIF(h.FPZL, ''), NULLIF(h.KPF_FPZL, ''))",
            invoice_content="l.JDCZDJH",
            document_date="COALESCE(h.SQRQ, h.LRSJ)",
            expected_receipt_date="h.YJHKRQ",
            created_time="h.LRSJ",
            creator_name="h.LRR",
            creator_id="h.LRRID",
            qty="l.SL",
            unit_price="l.SJ",
            amount_total="COALESCE(l.SQKPJE, l.HDCZJE)",
            amount_no_tax="l.FBDKJE",
            tax_amount="0",
            amount_contract="0",
            amount_received="l.YJSKJE",
            attachment="COALESCE(NULLIF(l.FJ, ''), NULLIF(h.FJ, ''))",
            note="COALESCE(NULLIF(l.BZ, ''), NULLIF(h.BZ, ''))",
            active_expr="ISNULL(h.DEL, 0) = 0",
            from_sql="FROM dbo.C_JXXP_KJFPSQ_CB l LEFT JOIN dbo.C_JXXP_KJFPSQ h ON h.Id = l.ZBID",
        ),
        select_clause(
            table="C_ZJSWGL_BASE_SKPFSZ",
            fact_type="invoice_config",
            id_expr="Id",
            pid_expr="pid",
            document_no="HTBH",
            document_state="''",
            project_id="XMID",
            project_name="XMMC",
            partner_name="JFMC",
            partner_tax_no="SH",
            contract_id="JBXXID",
            contract_no="HTBH",
            contract_name="HTMC",
            invoice_type="FPLX",
            tax_method="JSFF",
            document_date="LRSJ",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            tax_rate="KPSL",
            bank_name="KHYH",
            bank_account="YHZH",
            note="SWJG",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.C_ZJSWGL_BASE_SKPFSZ",
        ),
        select_clause(
            table="C_JXXP_GLHTB",
            fact_type="invoice_contract_link",
            id_expr="Id",
            parent_expr="ZBID",
            pid_expr="pid",
            document_no="DJBH",
            document_state="''",
            project_id="XMID",
            contract_id="DJID",
            amount_total="BCGLKPJE",
            from_sql="FROM dbo.C_JXXP_GLHTB",
        ),
        select_clause(
            table="C_JXXP_YJSKDJ",
            fact_type="prepaid_tax",
            id_expr="Id",
            pid_expr="pid",
            document_no="DJBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_name="SPFMC",
            contract_id="C_JXXP_XXKPDJ_Id",
            invoice_date="FPKJRQ",
            document_date="COALESCE(SQRQ, LRSJ)",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            amount_total="KPZJE",
            amount_no_tax="KPZJE_NO",
            tax_amount="KPSE",
            amount_received="BCJSJE",
            attachment="FJ",
            note="BCJSBS",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.C_JXXP_YJSKDJ",
        ),
        select_clause(
            table="C_JXXP_YJSKDJ_CB",
            fact_type="prepaid_tax_line",
            id_expr="l.Id",
            parent_expr="l.ZBID",
            pid_expr="l.pid",
            source_dataset="l.SJBMC",
            document_no="h.DJBH",
            document_state="h.DJZT",
            project_id="h.XMID",
            project_name="h.XMMC",
            partner_name="h.SPFMC",
            contract_id="h.C_JXXP_XXKPDJ_Id",
            invoice_no="l.FBFPHM",
            invoice_code="l.FBFPDM",
            invoice_date="l.JNSJ",
            expected_receipt_date="h.FPKJRQ",
            document_date="COALESCE(h.SQRQ, h.LRSJ)",
            created_time="h.LRSJ",
            creator_name="h.LRR",
            creator_id="h.LRRID",
            qty="l.BS",
            amount_total="l.JE",
            amount_no_tax="l.FBFPBHSJE",
            tax_amount="l.BCFBDKSE",
            tax_rate="l.SLBL",
            tax_type="l.JSLX",
            tax_certificate_no="l.WSPZHM",
            amount_received="l.BCFBDKJE",
            attachment="h.FJ",
            note="l.BZ",
            active_expr="ISNULL(h.DEL, 0) = 0",
            from_sql="FROM dbo.C_JXXP_YJSKDJ_CB l LEFT JOIN dbo.C_JXXP_YJSKDJ h ON h.Id = l.ZBID",
        ),
        select_clause(
            table="C_JXXP_JXZC_CB",
            fact_type="tax_transfer_line",
            id_expr="Id",
            parent_expr="ZBID",
            pid_expr="pid",
            document_no="''",
            document_state="''",
            invoice_no="FPHM",
            invoice_code="FPDM",
            invoice_date="KPRQ",
            partner_id="KPDWID",
            partner_name="KPDW",
            amount_total="JE",
            amount_no_tax="JE_NO",
            tax_amount="SE",
            amount_received="DKJE",
            document_date="COALESCE(DKRQ, ZCRQ, KPRQ)",
            note="COALESCE(NULLIF(ZCSY, ''), NULLIF(FPDJXX, ''), NULLIF(DKDJXX, ''))",
            from_sql="FROM dbo.C_JXXP_JXZC_CB",
        ),
        select_clause(
            table="C_JXXP_FPKPMXB",
            fact_type="invoice_issue",
            id_expr="Id",
            pid_expr="pid",
            document_no="DJBH",
            document_state="''",
            project_id="XMID",
            project_name="XMMC",
            partner_name="GMF_MC",
            partner_tax_no="GMF_SBH",
            invoice_no="DH",
            invoice_content="BZ",
            document_date="LRSJ",
            invoice_date="LRSJ",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            bank_name="GMF_DH",
            bank_account="GMF_ZH",
            note="COALESCE(NULLIF(MMQ, ''), NULLIF(BZ, ''))",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.C_JXXP_FPKPMXB",
        ),
        select_clause(
            table="C_JXXP_FPKPMXB_CB",
            fact_type="invoice_issue_line",
            id_expr="l.Id",
            parent_expr="l.ZBID",
            pid_expr="l.pid",
            source_dataset="l.SJBMC",
            document_no="h.DJBH",
            document_state="''",
            project_id="h.XMID",
            project_name="h.XMMC",
            partner_name="h.GMF_MC",
            partner_tax_no="h.GMF_SBH",
            invoice_no="h.DH",
            invoice_type="l.f_SLV",
            invoice_content="l.MC",
            document_date="h.LRSJ",
            invoice_date="h.LRSJ",
            created_time="h.LRSJ",
            creator_name="h.LRR",
            creator_id="h.LRRID",
            qty="l.SL",
            unit_price="l.DJ",
            amount_total="l.JE",
            tax_amount="l.SE",
            tax_rate="l.SLV",
            note="l.GGXH",
            active_expr="ISNULL(h.DEL, 0) = 0",
            from_sql="FROM dbo.C_JXXP_FPKPMXB_CB l LEFT JOIN dbo.C_JXXP_FPKPMXB h ON h.Id = l.ZBID",
        ),
        select_clause(
            table="C_JXXP_DKDJ_New",
            fact_type="tax_deduction",
            id_expr="Id",
            pid_expr="pid",
            document_no="DJBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            contract_id="FPDJ_Id",
            document_date="COALESCE(DJRQ, LRSJ)",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            qty="D_SCBSJS_FJS",
            attachment="FJ",
            note="COALESCE(NULLIF(BZ, ''), NULLIF(SFYXQNR, ''))",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.C_JXXP_DKDJ_New",
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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def csv_summary() -> dict[str, object]:
    active_rows = 0
    amount_total = Decimal("0")
    tax_amount = Decimal("0")
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
            try:
                tax_amount += Decimal(row.get("tax_amount") or "0")
            except InvalidOperation:
                pass
    return {
        "active_rows": active_rows,
        "amount_total_sum": str(amount_total),
        "tax_amount_sum": str(tax_amount),
        "source_counts": source_counts,
        "fact_type_counts": fact_type_counts,
    }


def main() -> int:
    rows = write_csv_payload()
    summary = csv_summary()
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_income_invoice_replay_adapter",
        "total_rows": rows,
        "active_rows": summary["active_rows"],
        "amount_total_sum": summary["amount_total_sum"],
        "tax_amount_sum": summary["tax_amount_sum"],
        "source_counts": summary["source_counts"],
        "fact_type_counts": summary["fact_type_counts"],
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_income_invoice_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_INCOME_INVOICE_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
