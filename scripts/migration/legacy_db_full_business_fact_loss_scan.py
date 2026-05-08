#!/usr/bin/env python3
"""Scan the full legacy database for business fact tables not yet replayed."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration/business_fact_upgrade"))
OUTPUT_JSON = ARTIFACT_ROOT / "legacy_db_full_business_fact_loss_scan_v1.json"
OUTPUT_MD = ARTIFACT_ROOT / "legacy_db_full_business_fact_loss_scan_v1.md"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD") or os.getenv("LEGACY_MSSQL_PASSWORD") or "LegacyRestore!2026"
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")

KNOWN_COVERED_TABLES = {
    "BASE_SYSTEM_FILE",
    "BASE_SYSTEM_PROJECT",
    "BASE_SYSTEM_PROJECT_USER",
    "BASE_SYSTEM_USER",
    "BASE_SYSTEM_USER_ROLE",
    "BASE_ORGANIZATION_DEPARTMENT",
    "BGGL_JHK_HKDJ",
    "BGGL_JHK_JKSQ",
    "BGGL_XZ_GZ",
    "BGGL_XZ_GZ_CB",
    "C_Base_ZHSZ",
    "C_CWSFK_GSCWSR",
    "C_CWSFK_GSCWZC",
    "C_FKGL_ZHJZJWL",
    "C_FKGL_YJDJ",
    "C_JXXP_DKDJ_New",
    "C_JXXP_DKDJ_CB",
    "C_JXXP_FPKPMXB",
    "C_JXXP_FPKPMXB_CB",
    "C_JXXP_GLHTB",
    "C_JXXP_JXZC_CB",
    "C_JXXP_KJFPSQ",
    "C_JXXP_KJFPSQ_CB",
    "C_JFHKLR",
    "C_JFHKLR_CB",
    "C_JFHKLR_TH",
    "C_JFHKLR_TH_ZCDF_CB",
    "C_JXXP_YJSKDJ",
    "C_JXXP_YJSKDJ_CB",
    "C_JXXP_XXKPDJ",
    "C_JXXP_XXKPDJ_CB",
    "C_JXXP_ZYFPJJD",
    "C_JXXP_ZYFPJJD_CB",
    "C_ZJSWGL_BASE_SKPFSZ",
    "C_ZFSQGL",
    "C_ZFSQGL_BZJKD",
    "C_ZFSQGL_CB",
    "C_ZFSQGL_GZ_CB",
    "C_ZFSQGL_KKD",
    "C_ZFSQGL_KKD_CB",
    "C_ZFSQGL_SD",
    "C_ZFSQGL_SJ_CB",
    "C_ZFSQGL_SJ_TP",
    "CheckInData",
    "CWGL_FYBX",
    "CWGL_FYBX_CB",
    "D_SCBSJS_ZJGL_ZJSZ_ZJRBB",
    "D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB",
    "GLFY_Bill",
    "GLFY_GLFYJSD",
    "GLFY_XMFYBXD",
    "HTGL_ZLHT_ZLDW",
    "HTGL_ZLHT_ZLHT",
    "HTGL_ZLHT_ZLHT_JX",
    "LW_Base_FDGL",
    "LW_BZHTGL",
    "LW_LWHTGL_SP",
    "P_ZTB_GCBMGL",
    "S_Execute_Approval",
    "SGGL_FBGL_FBHT",
    "SGGL_LWGL_LXYG",
    "SGGL_LWGL_LXYG_CB",
    "SGZL_RZRJ",
    "SGZL_RZRJ_CB",
    "A_SCBS_CLRKD",
    "T_BILL_FILE",
    "T_CGHT_INFO",
    "T_CK_CKD",
    "T_CK_CKDCB",
    "T_FK_Supplier",
    "T_FK_Supplier_CB",
    "T_GYSHT_INFO",
    "T_GYSHT_INFO_CB",
    "T_JS_CLJSD",
    "T_JS_LWJSD",
    "T_KK_SJDJB",
    "T_KK_SJDJB_CB",
    "T_KK_SJTHB",
    "T_KK_SJTHB_CB",
    "T_ProjectContract_Out",
    "T_ProjectContract_Out_CB",
    "T_RK_RKD",
    "T_RK_RKDCB",
    "T_ZL_HZD",
    "T_ZL_MachineShift",
    "T_ZL_ZLJH_ZLSQ",
    "T_ZL_ZLJSD",
    "T_ZL_ZLJSD_JX",
    "T_ZL_ZRD",
    "T_ZL_ZRD_JX",
    "T_ZL_ZZCLZJTD",
    "T_Base_CooperatCompany",
    "T_Base_MaterialDetail",
    "T_Base_BuildMaterialClass",
    "T_Base_SupplierInfo",
    "T_Base_SupplierInfoAndXMGL",
    "T_BASE_TASKDONE",
    "T_System_UserAndXXGL",
    "T_System_UserAndXXGL_History",
    "tr_RoleToUser",
    "tr_user",
    "View_Select_ts_system_loginData",
    "View_Select_XMCKXX_BS",
    "YT_JGZS_NKJCGXB",
    "YT_JGZS_NKKMB",
    "YT_JGZS_NKKMB_QD",
    "YT_JGZS_SGLKYSZB_CB1",
    "YT_JGZS_SGLKYSZB_QD_CB1",
    "XMGL_JJSB_ZLD_LXYG",
    "ZYJX_ZY_T_WZJJF_SBHZD",
    "ZYJX_ZY_T_WZJJF_SBZLD",
    "ZYJX_ZY_T_WZJJF_ZLHT",
    "ZJGL_BZJGL_Branch_SBZJDJ",
    "ZJGL_BZJGL_Branch_SBZJTH",
    "ZJGL_BZJGL_Pay_FBZJ",
    "ZJGL_BZJGL_Pay_FBZJTH",
    "ZJGL_BZJGL_Pay_FBZJTHSQ",
    "ZJGL_CWGL_FBXMJSFP",
    "ZJGL_CWGL_FBXMJSFP_CB",
    "ZJGL_SZQR_DKQRB",
    "ZJGL_SZQR_DKQRB_CB",
    "ZJGL_SZQR_ZFQRB_CB",
    "ZJGL_SZQR_ZFQRB",
    "ZJGL_SWGL_SJSWLXSZ",
    "ZJGL_SWGL_SJSWLXSZ_Templet",
    "ZJGL_WJZ_WJZDJB",
    "ZJGL_ZSJYGL",
    "ZJGL_ZCDFSZ_FXJK_HK",
    "ZJGL_ZCDFSZ_FXJK_JK",
    "ZJGL_ZJSZ_DKGL_DKDJ",
    "ZJGL_ZJSZ_DKGL_HKDJ",
}

KNOWN_ASSETIZED_PREFIXES = (
    "BASE_SYSTEM_",
    "S_Execute_",
)

SYSTEM_NAME_PATTERNS = re.compile(
    r"(^BASE_LOWCODE_|^BASE_SYSTEM_(API|LOG|MENU|MOBILE|SHARING|KEYVALUE)|^S_Setup_|^T_System_|^ts_|^tr_|"
    r"History$|_History$|_bak$|_BAK|_Record|LOG|Log|Click|LOGIN|PUSH|Template|Config|Function|Role|Menu)",
    re.IGNORECASE,
)
IMPORT_OR_REFERENCE_PATTERNS = re.compile(r"(^T_Base_Import_|BuildMaterialDetail|Dictionary|REGION|Type$|_Type$|_Base_|JCSZ|CLK|KMB|QDKM)", re.IGNORECASE)
AMOUNT_COL = re.compile(r"(JE|AMOUNT|MONEY|PRICE|ZJE|FKJE|SKJE|YSJE|YFJE|SE|TAX|BALANCE|JHJE|SFJE|ZSJE|YJJE|ZLBZJ)", re.IGNORECASE)
DATE_COL = re.compile(r"(RQ|DATE|SJ|TIME|LRR?Q|CREATE|UPDATE|FKSJ|SPSJ)", re.IGNORECASE)
PROJECT_COL = re.compile(r"(^XMID$|PROJECT|f_XMID|LYXMID|TSXMID|XMMC|PROJECT_ID)", re.IGNORECASE)
PARTNER_COL = re.compile(r"(WLDW|GYS|SUPPLIER|PARTNER|DWID|f_GYSID|f_SupplierID|CBF|FBF|JSDW)", re.IGNORECASE)
CONTRACT_COL = re.compile(r"(HTID|CONTRACT|GYSHT|HTBH|HTMC)", re.IGNORECASE)
PARENT_COL = re.compile(r"(ZBID|ZFSQID|PID|PARENT|BILLID|business_Id|f_ZFSQGLId)", re.IGNORECASE)
DELETED_COL = re.compile(r"(^DEL$|SCRQ|SCRID|DELETED|ISDELETE)", re.IGNORECASE)

FAMILY_RULES = [
    ("bid_tender", re.compile(r"^(P_ZTB_|CGPT_T_Base_ZBXX|WS_ZBJGL_|WS_BDGL_|WS_HTGL_ZBHT)")),
    ("labor_subcontract", re.compile(r"^(LW_|SGGL_LWGL_|SGGL_FBGL_|T_JS_LWJSD|T_JS_CLJSD|GLFY_)")),
    ("lease_equipment", re.compile(r"^(HTGL_ZLHT_|T_ZL_|XMGL_JJSB_ZLD_)")),
    ("material_stock", re.compile(r"^(T_RK_|T_CK_|A_SCBS_CLRKD|YT_JGZS_|ZYJX_ZY_T_WZJJF_)")),
    ("income_invoice", re.compile(r"^(C_JXXP_|C_ZJSWGL_)")),
    ("payment_fund", re.compile(r"^(C_ZFSQGL_|ZJGL_|C_FKGL_)")),
    ("project_settlement", re.compile(r"^(XMGL_HTGL_|T_ProjectContract_|T_Project_|XM_SBBF)")),
    ("office_admin", re.compile(r"^(BGGL_)")),
]


@dataclass
class TableMeta:
    schema: str
    name: str
    row_count: int
    columns: list[str] = field(default_factory=list)
    types: dict[str, str] = field(default_factory=dict)


def run_sql(sql: str) -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        SQL_CONTAINER,
        "bash",
        "-lc",
        f"{SQLCMD} -S localhost -U sa -P {shell_quote(SQL_PASSWORD)} -C -d {shell_quote(SQL_DATABASE)} -s '|' -y 0 -Y 0",
    ]
    completed = subprocess.run(cmd, input=sql, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError({"sqlcmd_failed": completed.returncode, "stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:]})
    return completed.stdout


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def load_metadata() -> list[TableMeta]:
    sql = """
SET NOCOUNT ON;
SELECT s.name, t.name, CONVERT(varchar(32), SUM(p.rows)), c.name, ty.name, CONVERT(varchar(16), c.column_id)
FROM sys.tables t
JOIN sys.schemas s ON s.schema_id=t.schema_id
JOIN sys.partitions p ON p.object_id=t.object_id AND p.index_id IN (0,1)
JOIN sys.columns c ON c.object_id=t.object_id
JOIN sys.types ty ON ty.user_type_id=c.user_type_id
GROUP BY s.name, t.name, c.name, ty.name, c.column_id
ORDER BY SUM(p.rows) DESC, t.name, c.column_id;
"""
    by_key: dict[tuple[str, str], TableMeta] = {}
    for raw in run_sql(sql).splitlines():
        parts = [part.strip() for part in raw.split("|")]
        if len(parts) != 6:
            continue
        schema, table, row_count_raw, column, col_type, _column_id = parts
        if not schema or not table:
            continue
        try:
            row_count = int(row_count_raw)
        except ValueError:
            continue
        key = (schema, table)
        meta = by_key.setdefault(key, TableMeta(schema=schema, name=table, row_count=row_count))
        meta.columns.append(column)
        meta.types[column] = col_type
    return list(by_key.values())


def has_any(columns: list[str], pattern: re.Pattern[str]) -> bool:
    return any(pattern.search(column) for column in columns)


def matching_columns(columns: list[str], pattern: re.Pattern[str]) -> list[str]:
    return [column for column in columns if pattern.search(column)]


def family_of(table_name: str) -> str:
    for family, pattern in FAMILY_RULES:
        if pattern.search(table_name):
            return family
    return table_name.split("_", 1)[0].lower() if "_" in table_name else "other"


def classify_table(meta: TableMeta) -> dict[str, Any]:
    name = meta.name
    columns = meta.columns
    signals = {
        "amount": matching_columns(columns, AMOUNT_COL)[:12],
        "date": matching_columns(columns, DATE_COL)[:12],
        "project": matching_columns(columns, PROJECT_COL)[:12],
        "partner": matching_columns(columns, PARTNER_COL)[:12],
        "contract": matching_columns(columns, CONTRACT_COL)[:12],
        "parent": matching_columns(columns, PARENT_COL)[:12],
        "deleted": matching_columns(columns, DELETED_COL)[:12],
    }
    signal_count = sum(1 for key in ("amount", "date", "project", "partner", "contract", "parent") if signals[key])
    is_system = bool(SYSTEM_NAME_PATTERNS.search(name))
    is_reference = bool(IMPORT_OR_REFERENCE_PATTERNS.search(name))
    is_covered = name in KNOWN_COVERED_TABLES
    if is_covered:
        classification = "known_replayed_or_assetized"
    elif is_system:
        classification = "system_or_audit_noise"
    elif is_reference and signal_count < 3:
        classification = "reference_or_import_catalog"
    elif signal_count >= 4 and meta.row_count > 0:
        classification = "candidate_effective_business_fact"
    elif signal_count >= 3 and meta.row_count > 0:
        classification = "candidate_secondary_business_fact"
    elif signal_count >= 2 and meta.row_count >= 100:
        classification = "candidate_needs_manual_screen"
    else:
        classification = "low_business_fact_signal"
    if name.startswith(KNOWN_ASSETIZED_PREFIXES) and classification == "candidate_needs_manual_screen":
        classification = "system_or_audit_noise"
    score = signal_count * 10
    if signals["amount"]:
        score += 20
    if signals["project"]:
        score += 15
    if signals["partner"]:
        score += 10
    if signals["contract"]:
        score += 10
    if meta.row_count >= 1000:
        score += 5
    if is_covered or is_system:
        score -= 50
    return {
        "schema": meta.schema,
        "table": meta.name,
        "row_count": meta.row_count,
        "column_count": len(meta.columns),
        "classification": classification,
        "family": family_of(meta.name),
        "business_signal_score": score,
        "signals": {key: value for key, value in signals.items() if value},
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    non_empty = [row for row in rows if int(row["row_count"]) > 0]
    candidates = [
        row
        for row in non_empty
        if row["classification"]
        in {"candidate_effective_business_fact", "candidate_secondary_business_fact", "candidate_needs_manual_screen"}
    ]
    by_class: dict[str, int] = {}
    by_class_rows: dict[str, int] = {}
    for row in rows:
        key = str(row["classification"])
        by_class[key] = by_class.get(key, 0) + 1
        by_class_rows[key] = by_class_rows.get(key, 0) + int(row["row_count"])
    by_family: dict[str, dict[str, Any]] = {}
    for row in candidates:
        family = str(row["family"])
        bucket = by_family.setdefault(
            family,
            {
                "family": family,
                "tables": 0,
                "rows": 0,
                "effective_tables": 0,
                "secondary_tables": 0,
                "top_tables": [],
            },
        )
        bucket["tables"] += 1
        bucket["rows"] += int(row["row_count"])
        if row["classification"] == "candidate_effective_business_fact":
            bucket["effective_tables"] += 1
        elif row["classification"] == "candidate_secondary_business_fact":
            bucket["secondary_tables"] += 1
        bucket["top_tables"].append(
            {
                "table": row["table"],
                "rows": row["row_count"],
                "classification": row["classification"],
                "score": row["business_signal_score"],
            }
        )
    family_summary = sorted(by_family.values(), key=lambda row: (-int(row["rows"]), -int(row["tables"]), str(row["family"])))
    for family in family_summary:
        family["top_tables"] = sorted(family["top_tables"], key=lambda row: (-int(row["score"]), -int(row["rows"]), str(row["table"])))[:10]
    return {
        "total_tables": len(rows),
        "non_empty_tables": len(non_empty),
        "candidate_tables": len(candidates),
        "candidate_rows": sum(int(row["row_count"]) for row in candidates),
        "classification_counts": by_class,
        "classification_row_counts": by_class_rows,
        "top_candidate_families": family_summary[:20],
        "top_candidates": sorted(candidates, key=lambda row: (-int(row["business_signal_score"]), -int(row["row_count"]), str(row["table"])))[:60],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    candidates = payload["summary"]["top_candidates"]
    rows = "\n".join(
        "| {table} | {row_count} | {classification} | {business_signal_score} | {signals} |".format(
            table=row["table"],
            row_count=row["row_count"],
            classification=row["classification"],
            business_signal_score=row["business_signal_score"],
            signals=", ".join(f"{key}:{'/'.join(value[:4])}" for key, value in row["signals"].items()),
        )
        for row in candidates
    )
    families = "\n".join(
        "| {family} | {tables} | {rows} | {effective_tables} | {top_tables} |".format(
            family=row["family"],
            tables=row["tables"],
            rows=row["rows"],
            effective_tables=row["effective_tables"],
            top_tables=", ".join(f"{item['table']}({item['rows']})" for item in row["top_tables"][:5]),
        )
        for row in payload["summary"]["top_candidate_families"][:20]
    )
    return f"""# Legacy DB Full Business Fact Loss Scan v1

Status: `{payload["status"]}`

Source: `{payload["source"]}`

## Summary

```json
{json.dumps(payload["summary"], ensure_ascii=False, indent=2)}
```

## Top Candidate Tables

| Table | Rows | Classification | Score | Signals |
|---|---:|---|---:|---|
{rows}

## Top Candidate Families

| Family | Tables | Rows | Effective Tables | Top Tables |
|---|---:|---:|---:|---|
{families}

## Boundary

- Read-only legacy DB scan
- DB writes: `0`
- This is a table/column signal screen; every candidate still needs lane-level SQL and replay mapping before ingestion.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan full legacy DB for possible unreplayed business facts.")
    parser.add_argument("--out", default=str(OUTPUT_JSON))
    parser.add_argument("--report", default=str(OUTPUT_MD))
    args = parser.parse_args()

    table_rows = [classify_table(meta) for meta in load_metadata()]
    payload = {
        "status": "PASS",
        "mode": "legacy_db_full_business_fact_loss_scan",
        "source": f"{SQL_CONTAINER}:{SQL_DATABASE}",
        "db_writes": 0,
        "summary": summarize(table_rows),
        "tables": table_rows,
        "decision": "full_legacy_business_fact_candidates_screened",
    }
    out = Path(args.out)
    report = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report.write_text(render_markdown(payload), encoding="utf-8")
    print(
        "LEGACY_DB_FULL_BUSINESS_FACT_LOSS_SCAN="
        + json.dumps(
            {
                "status": payload["status"],
                "non_empty_tables": payload["summary"]["non_empty_tables"],
                "candidate_tables": payload["summary"]["candidate_tables"],
                "candidate_rows": payload["summary"]["candidate_rows"],
                "top_candidate": (payload["summary"]["top_candidates"] or [{}])[0].get("table"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
