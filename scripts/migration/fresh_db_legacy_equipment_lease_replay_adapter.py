#!/usr/bin/env python3
"""Build replay payload for legacy equipment and lease facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_equipment_lease_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_equipment_lease_replay_adapter_result_v1.json"

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
    "contract_legacy_id",
    "contract_no",
    "equipment_legacy_id",
    "equipment_name",
    "equipment_spec",
    "equipment_uom",
    "work_part",
    "department_name",
    "document_date",
    "start_date",
    "end_date",
    "created_time",
    "creator_name",
    "creator_legacy_user_id",
    "qty",
    "unit_price",
    "amount_total",
    "amount_no_tax",
    "tax_amount",
    "tax_rate",
    "amount_payable",
    "amount_deduction",
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
    project_id: str,
    project_name: str,
    partner_id: str,
    partner_name: str,
    contract_id: str,
    contract_no: str,
    equipment_id: str,
    equipment_name: str,
    equipment_spec: str = "''",
    equipment_uom: str = "''",
    work_part: str = "''",
    department: str = "''",
    document_date: str,
    start_date: str = "NULL",
    end_date: str = "NULL",
    created_time: str,
    creator_name: str,
    creator_id: str,
    qty: str = "0",
    unit_price: str = "0",
    amount_total: str,
    amount_no_tax: str = "0",
    tax_amount: str = "0",
    tax_rate: str = "0",
    amount_payable: str = "0",
    amount_deduction: str = "0",
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
  {text_sql(contract_id)} AS contract_legacy_id,
  {text_sql(contract_no)} AS contract_no,
  {text_sql(equipment_id)} AS equipment_legacy_id,
  {text_sql(equipment_name)} AS equipment_name,
  {text_sql(equipment_spec)} AS equipment_spec,
  {text_sql(equipment_uom)} AS equipment_uom,
  {text_sql(work_part)} AS work_part,
  {text_sql(department)} AS department_name,
  {date_sql(document_date)} AS document_date,
  {date_sql(start_date)} AS start_date,
  {date_sql(end_date)} AS end_date,
  {date_sql(created_time)} AS created_time,
  {text_sql(creator_name)} AS creator_name,
  {text_sql(creator_id)} AS creator_legacy_user_id,
  {text_sql(qty)} AS qty,
  {text_sql(unit_price)} AS unit_price,
  {text_sql(amount_total)} AS amount_total,
  {text_sql(amount_no_tax)} AS amount_no_tax,
  {text_sql(tax_amount)} AS tax_amount,
  {text_sql(tax_rate)} AS tax_rate,
  {text_sql(amount_payable)} AS amount_payable,
  {text_sql(amount_deduction)} AS amount_deduction,
  {text_sql(bank_name)} AS bank_name,
  {text_sql(bank_account)} AS bank_account,
  {text_sql(attachment)} AS attachment_ref,
  {text_sql(note)} AS note,
  CASE WHEN {active_expr} THEN '1' ELSE '0' END AS active
{from_sql}
"""


def payload_sql() -> str:
    contract_common = {
        "fact_type": "lease_contract",
        "id_expr": "Id",
        "pid_expr": "pid",
        "document_no": "COALESCE(NULLIF(DJBH, ''), NULLIF(HTBH, ''))",
        "document_state": "DJZT",
        "project_id": "XMID",
        "project_name": "XMMC",
        "partner_id": "COALESCE(NULLIF(FBDWID, ''), NULLIF(SKDWID, ''), NULLIF(WFDWID, ''))",
        "partner_name": "COALESCE(NULLIF(FBDW, ''), NULLIF(SKDW, ''), NULLIF(WFDW, ''))",
        "contract_id": "Id",
        "contract_no": "HTBH",
        "equipment_id": "FBNRID",
        "equipment_name": "COALESCE(NULLIF(FBNR, ''), NULLIF(HTBT, ''), NULLIF(BT, ''))",
        "work_part": "SGBWMC",
        "department": "JBBM",
        "document_date": "COALESCE(QDSJ, LRSJ)",
        "start_date": "QDSJ",
        "end_date": "FHHTSJ",
        "created_time": "LRSJ",
        "creator_name": "LRR",
        "creator_id": "LRRID",
        "qty": "ZSL",
        "unit_price": "0",
        "amount_total": "COALESCE(ZJE, JE)",
        "amount_no_tax": "ZJE_NO",
        "tax_amount": "SE",
        "tax_rate": "SLV",
        "bank_name": "KHH",
        "bank_account": "YHZH",
        "attachment": "FJ",
        "note": "COALESCE(CONVERT(varchar(max), BZ), NULLIF(BZ1, ''))",
        "active_expr": "ISNULL(DEL, 0) = 0",
    }
    parts = [
        select_clause(table="HTGL_ZLHT_ZLHT_JX", from_sql="FROM dbo.HTGL_ZLHT_ZLHT_JX", **contract_common),
        select_clause(table="HTGL_ZLHT_ZLHT", from_sql="FROM dbo.HTGL_ZLHT_ZLHT", **contract_common),
        select_clause(
            table="T_ZL_ZRD_JX",
            fact_type="equipment_transfer",
            id_expr="ID",
            pid_expr="Pid",
            document_no="COALESCE(NULLIF(DJBH, ''), NULLIF(f_ZRDH, ''))",
            document_state="DJZT",
            project_id="f_XMID",
            project_name="ProjectName",
            partner_id="COALESCE(NULLIF(f_Supplier_ID, ''), NULLIF(f_Lldw_ID, ''))",
            partner_name="COALESCE(NULLIF(f_SupplierName, ''), NULLIF(f_LldwName, ''))",
            contract_id="f_HT_ID",
            contract_no="f_HTBH",
            equipment_id="f_GLZRDId",
            equipment_name="BT",
            work_part="SGBWMC",
            document_date="COALESCE(f_DJRQ, f_LRSJ)",
            created_time="f_LRSJ",
            creator_name="f_LRR",
            creator_id="LRRID",
            amount_total="FYXJE",
            amount_payable="ZLYJ",
            tax_rate="SLV",
            attachment="FJ",
            note="f_BZ",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.T_ZL_ZRD_JX",
        ),
        select_clause(
            table="T_ZL_ZRD",
            fact_type="equipment_transfer",
            id_expr="ID",
            pid_expr="Pid",
            document_no="COALESCE(NULLIF(DJBH, ''), NULLIF(f_ZRDH, ''))",
            document_state="DJZT",
            project_id="f_XMID",
            project_name="ProjectName",
            partner_id="COALESCE(NULLIF(f_Supplier_ID, ''), NULLIF(f_Lldw_ID, ''))",
            partner_name="COALESCE(NULLIF(f_SupplierName, ''), NULLIF(f_LldwName, ''))",
            contract_id="f_HT_ID",
            contract_no="f_HTBH",
            equipment_id="f_GLZRDId",
            equipment_name="BT",
            work_part="SGBW",
            document_date="COALESCE(f_DJRQ, f_LRSJ)",
            created_time="f_LRSJ",
            creator_name="f_LRR",
            creator_id="LRRID",
            amount_total="FYXJE",
            amount_payable="ZLYJ",
            tax_rate="SLV",
            attachment="FJ",
            note="f_BZ",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.T_ZL_ZRD",
        ),
        select_clause(
            table="T_ZL_HZD",
            fact_type="lease_summary",
            id_expr="ID",
            pid_expr="Pid",
            document_no="COALESCE(NULLIF(DJBH, ''), NULLIF(f_HZDH, ''))",
            document_state="DJZT",
            project_id="f_XMID",
            project_name="XMMC",
            partner_id="COALESCE(NULLIF(f_Supplier_ID, ''), NULLIF(f_Lldw_ID, ''))",
            partner_name="COALESCE(NULLIF(f_SupplierName, ''), NULLIF(f_LldwName, ''))",
            contract_id="f_HT_ID",
            contract_no="f_HTBH",
            equipment_id="f_GLZRDID",
            equipment_name="BT",
            work_part="SGBWMC",
            document_date="COALESCE(f_DJRQ, f_LRSJ)",
            created_time="f_LRSJ",
            creator_name="f_LRR",
            creator_id="LRRID",
            amount_total="f_JSJE",
            amount_payable="DKJE",
            amount_deduction="COALESCE(f_PCF, 0) + COALESCE(f_WXF, 0) + COALESCE(f_JCCF, 0) + COALESCE(PSXFY, 0) + COALESCE(QTFYX, 0)",
            attachment="FJ",
            note="f_BZ",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.T_ZL_HZD",
        ),
        select_clause(
            table="T_ZL_MachineShift",
            fact_type="equipment_shift",
            id_expr="Id",
            pid_expr="pid",
            document_no="DJBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_id="COALESCE(NULLIF(ZLDWID, ''), NULLIF(SYDWID, ''))",
            partner_name="COALESCE(NULLIF(ZLDW, ''), NULLIF(SYDW, ''))",
            contract_id="''",
            contract_no="''",
            equipment_id="''",
            equipment_name="BT",
            work_part="SGBW",
            document_date="COALESCE(DJRQ, LRSJ)",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            amount_total="D_BQJT_ZJE",
            attachment="FJ",
            note="BZ",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.T_ZL_MachineShift",
        ),
        select_clause(
            table="HTGL_ZLHT_ZLDW",
            fact_type="lease_partner",
            id_expr="Id",
            pid_expr="pid",
            document_no="FBDWBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_id="Id",
            partner_name="FBDW",
            contract_id="''",
            contract_no="''",
            equipment_id="''",
            equipment_name="GCZYLX",
            department="LX",
            document_date="COALESCE(DJSJ, LRSJ)",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            amount_total="0",
            tax_rate="SLV",
            bank_name="KHH",
            bank_account="YHZH",
            attachment="COALESCE(NULLIF(YYZZ_FJ, ''), NULLIF(ZZZS_FJ, ''), NULLIF(AQSCXKZ_FJ, ''))",
            note="BZ",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.HTGL_ZLHT_ZLDW",
        ),
        select_clause(
            table="T_ZL_ZLJSD",
            fact_type="lease_settlement",
            id_expr="Id",
            pid_expr="PID",
            document_no="DJBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_id="COALESCE(NULLIF(JSDWID, ''), NULLIF(SYDWID, ''))",
            partner_name="COALESCE(NULLIF(JSDW, ''), NULLIF(SYDW, ''))",
            contract_id="''",
            contract_no="''",
            equipment_id="''",
            equipment_name="BT",
            document_date="COALESCE(DJRQ, LRSJ)",
            start_date="QSJSRQ",
            end_date="ZZJSRQ",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            amount_total="ZJE",
            amount_payable="DZJE",
            amount_deduction="ZKJE",
            attachment="FJ",
            note="BZ",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.T_ZL_ZLJSD",
        ),
        select_clause(
            table="T_ZL_ZLJSD_JX",
            fact_type="lease_settlement",
            id_expr="Id",
            pid_expr="PID",
            document_no="DJBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_id="COALESCE(NULLIF(JSDWID, ''), NULLIF(SYDWID, ''))",
            partner_name="COALESCE(NULLIF(JSDW, ''), NULLIF(SYDW, ''))",
            contract_id="''",
            contract_no="SGDH",
            equipment_id="''",
            equipment_name="BT",
            document_date="COALESCE(DJRQ, LRSJ)",
            start_date="QSJSRQ",
            end_date="ZZJSRQ",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            amount_total="COALESCE(ZJE, f_ZJE, JSZJ)",
            amount_payable="YFJE",
            amount_deduction="ZKJE",
            attachment="FJ",
            note="COALESCE(NULLIF(BZ, ''), NULLIF(JSSM, ''))",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.T_ZL_ZLJSD_JX",
        ),
        select_clause(
            table="XMGL_JJSB_ZLD_LXYG",
            fact_type="equipment_shift",
            id_expr="Id",
            pid_expr="pid",
            document_no="DJBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_id="SGDWID",
            partner_name="SGDWMC",
            contract_id="''",
            contract_no="''",
            equipment_id="''",
            equipment_name="BT",
            department="ZDBM",
            document_date="COALESCE(DJRQ, LRSJ)",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            amount_total="ZJE",
            bank_name="KHH",
            bank_account="KHZH",
            attachment="FJ",
            note="BZ",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.XMGL_JJSB_ZLD_LXYG",
        ),
        select_clause(
            table="T_ZL_ZLJH_ZLSQ",
            fact_type="lease_request",
            id_expr="Id",
            pid_expr="pid",
            document_no="DJBH",
            document_state="DJZT",
            project_id="XMID",
            project_name="XMMC",
            partner_id="COALESCE(NULLIF(ZLDWID, ''), NULLIF(SYDWID, ''))",
            partner_name="COALESCE(NULLIF(ZLDW, ''), NULLIF(SYDW, ''))",
            contract_id="''",
            contract_no="''",
            equipment_id="''",
            equipment_name="''",
            document_date="COALESCE(DJRQ, LRSJ)",
            created_time="LRSJ",
            creator_name="LRR",
            creator_id="LRRID",
            amount_total="GZZJE",
            attachment="FJ",
            note="BZ",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.T_ZL_ZLJH_ZLSQ",
        ),
        select_clause(
            table="T_ZL_ZZCLZJTD",
            fact_type="equipment_transfer",
            id_expr="ID",
            pid_expr="Pid",
            document_no="COALESCE(NULLIF(DJBH, ''), NULLIF(f_ZRDH, ''))",
            document_state="DJZT",
            project_id="f_XMID",
            project_name="''",
            partner_id="COALESCE(NULLIF(f_Supplier_ID, ''), NULLIF(f_Lldw_ID, ''))",
            partner_name="COALESCE(NULLIF(f_SupplierName, ''), NULLIF(f_LldwName, ''))",
            contract_id="f_HT_ID",
            contract_no="f_HTBH",
            equipment_id="f_GLZRDId",
            equipment_name="f_ZRDH",
            document_date="COALESCE(f_DJRQ, f_LRSJ)",
            created_time="f_LRSJ",
            creator_name="f_LRR",
            creator_id="LRRID",
            amount_total="0",
            note="f_BZ",
            active_expr="ISNULL(DEL, 0) = 0",
            from_sql="FROM dbo.T_ZL_ZZCLZJTD",
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
        "mode": "fresh_db_legacy_equipment_lease_replay_adapter",
        "total_rows": rows,
        "active_rows": summary["active_rows"],
        "amount_total_sum": summary["amount_total_sum"],
        "source_counts": summary["source_counts"],
        "fact_type_counts": summary["fact_type_counts"],
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_equipment_lease_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_EQUIPMENT_LEASE_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
