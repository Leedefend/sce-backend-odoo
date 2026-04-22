#!/usr/bin/env python3
"""Screen remaining legacy business fact candidates after current assets."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/remaining_business_fact_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_remaining_business_fact_screen_v1.json"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_remaining_business_fact_screen_v1.md")
EXPECTED_RAW_ROWS = 163245

BASE_TARGET_SPECS = [
    ("project", "BASE_SYSTEM_PROJECT", "manifest/project_external_id_manifest_v1.json", ["legacy_key", "target_lookup.value"]),
    ("contract", "T_ProjectContract_Out", "manifest/contract_external_id_manifest_v1.json", ["legacy_contract_id"]),
    ("receipt", "C_JFHKLR", "manifest/receipt_external_id_manifest_v1.json", ["legacy_receipt_id"]),
    ("outflow_request", "C_ZFSQGL", "manifest/outflow_request_external_id_manifest_v1.json", ["legacy_outflow_id"]),
    ("actual_outflow", "T_FK_Supplier", "manifest/actual_outflow_external_id_manifest_v1.json", ["legacy_actual_outflow_id"]),
    ("supplier_contract", "T_GYSHT_INFO", "manifest/supplier_contract_external_id_manifest_v1.json", ["legacy_supplier_contract_id"]),
    ("outflow_request_line", "C_ZFSQGL_CB", "manifest/outflow_request_line_external_id_manifest_v1.json", ["legacy_outflow_line_id"]),
    ("receipt_invoice_line", "C_JFHKLR_CB", "manifest/receipt_invoice_line_external_id_manifest_v1.json", ["legacy_receipt_invoice_line_id", "attachment_candidate_keys.Id"]),
]
SOURCE_RECORD_MANIFESTS = [
    ("legacy_expense_deposit", "manifest/legacy_expense_deposit_external_id_manifest_v1.json"),
    ("legacy_invoice_tax", "manifest/legacy_invoice_tax_external_id_manifest_v1.json"),
    ("legacy_receipt_income", "manifest/legacy_receipt_income_external_id_manifest_v1.json"),
    ("legacy_financing_loan", "manifest/legacy_financing_loan_external_id_manifest_v1.json"),
    ("legacy_fund_daily_snapshot", "manifest/legacy_fund_daily_snapshot_external_id_manifest_v1.json"),
]

FAMILY_RULES = [
    ("payment_request_residual", ("支付申请", "付款申请", "往来单位付款", "工程款支付审批")),
    ("supplier_or_purchase_residual", ("供货商材料合同", "供货合同", "一般供应商", "采购")),
    ("document_admin_residual", ("文件批阅", "承办笺", "印章使用", "资料图片", "存档资料")),
    ("attendance_hr_residual", ("请假", "休假", "外出申请", "绩效")),
    ("tender_registration_residual", ("投标报名", "报名管理")),
    ("fund_daily_or_loan_residual", ("资金日报", "贷款登记", "借款")),
    ("unknown_or_unmapped_family", ("",)),
]

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
SELECT
  CONVERT(nvarchar(max), a.Id) AS Id,
  CONVERT(nvarchar(max), a.SJBMC) AS SJBMC,
  CONVERT(nvarchar(max), a.DJID) AS DJID,
  CONVERT(nvarchar(max), a.business_Id) AS business_Id,
  CONVERT(nvarchar(max), a.f_SPZT) AS f_SPZT,
  CONVERT(nvarchar(max), a.f_LRRId) AS f_LRRId,
  CONVERT(nvarchar(max), a.f_LRR) AS f_LRR,
  CONVERT(nvarchar(max), a.f_SPSJ, 120) AS f_SPSJ,
  CONVERT(nvarchar(max), st.f_BZMC) AS setup_step_name,
  CONVERT(nvarchar(max), tm.f_MBMC) AS template_name,
  CONVERT(nvarchar(max), tm.f_S_setup_business_Name) AS template_business_name,
  CONVERT(nvarchar(max), tm.SJBMC) AS template_source_table,
  CONVERT(nvarchar(max), b.f_YWMC) AS setup_business_name,
  CONVERT(nvarchar(max), b.f_BMC) AS setup_business_table,
  CONVERT(nvarchar(max), b.f_BDLJ) AS setup_business_path
FROM dbo.S_Execute_Approval a
LEFT JOIN dbo.S_Setup_Step st ON a.S_Setup_Step_Id = st.Id
LEFT JOIN dbo.S_Setup_Template tm ON a.S_Setup_Template_Id = tm.Id
LEFT JOIN dbo.S_Setup_Business b ON tm.f_S_setup_business_Id = b.Id
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SJBMC, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DJID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(business_Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_SPZT, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_LRRId, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_LRR, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_SPSJ, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(setup_step_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(template_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(template_business_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(template_source_table, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(setup_business_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(setup_business_table, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(setup_business_path, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY Id;
"""

SQL_COLUMNS = [
    "Id", "SJBMC", "DJID", "business_Id", "f_SPZT", "f_LRRId", "f_LRR", "f_SPSJ",
    "setup_step_name", "template_name", "template_business_name", "template_source_table",
    "setup_business_name", "setup_business_table", "setup_business_path",
]


class RemainingBusinessFactScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RemainingBusinessFactScreenError(message)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def deep_get(row: dict[str, Any], path: str) -> str:
    value: Any = row
    for part in path.split("."):
        if not isinstance(value, dict):
            return ""
        value = value.get(part)
    return clean(value)


def normalize_source_table(value: str) -> str:
    aliases = {"T_ProjectContract_OutInfo": "T_ProjectContract_Out", "ProjectContract_Out": "T_ProjectContract_Out", "C_JFHKLR_CB_FP": "C_JFHKLR_CB"}
    text = clean(value)
    return aliases.get(text, text)


def run_sql() -> str:
    cmd = ["docker", "exec", "-i", "legacy-sqlserver", "bash", "-lc", "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P \"$SA_PASSWORD\" -C -d LegacyDb -s '|' -y 0 -Y 0"]
    completed = subprocess.run(cmd, input=SQL, text=True, capture_output=True, check=False)
    require(completed.returncode == 0, completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def parse_sql_rows(output: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        text = line.strip()
        if not text or text == "rowdata" or set(text) <= {"-"}:
            continue
        parts = [part.strip() for part in text.split("|")]
        if len(parts) != len(SQL_COLUMNS):
            continue
        rows.append(dict(zip(SQL_COLUMNS, parts)))
    require(len(rows) == EXPECTED_RAW_ROWS, f"workflow row count drifted: {len(rows)} != {EXPECTED_RAW_ROWS}")
    return rows


def add_index(index: dict[tuple[str, str], str], any_index: dict[str, set[str]], source_table: str, key: str, lane: str) -> None:
    key = clean(key)
    if not key:
        return
    index[(source_table, key)] = lane
    any_index[key].add(lane)


def build_coverage_indexes(asset_root: Path) -> tuple[dict[tuple[str, str], str], dict[str, set[str]]]:
    source_index: dict[tuple[str, str], str] = {}
    any_index: dict[str, set[str]] = defaultdict(set)
    for lane, source_table, rel_path, key_paths in BASE_TARGET_SPECS:
        manifest = load_json(asset_root / rel_path)
        for row in manifest.get("records", []):
            if row.get("status") != "loadable":
                continue
            for key_path in key_paths:
                value = deep_get(row, key_path)
                add_index(source_index, any_index, source_table, value, lane)
    for lane, rel_path in SOURCE_RECORD_MANIFESTS:
        manifest = load_json(asset_root / rel_path)
        for row in manifest.get("records", []):
            if row.get("status") != "loadable":
                continue
            add_index(source_index, any_index, clean(row.get("legacy_source_table")), clean(row.get("legacy_record_id")), lane)
    require(source_index and any_index, "coverage indexes are empty")
    return source_index, any_index


def covered_lane(row: dict[str, str], source_index: dict[tuple[str, str], str], any_index: dict[str, set[str]]) -> str:
    source_table = normalize_source_table(row.get("SJBMC", ""))
    djid = clean(row.get("DJID"))
    business_id = clean(row.get("business_Id"))
    if djid and djid in any_index and len(any_index[djid]) == 1:
        return next(iter(any_index[djid]))
    if source_table and business_id and (source_table, business_id) in source_index:
        return source_index[(source_table, business_id)]
    if business_id and business_id in any_index and len(any_index[business_id]) == 1:
        return next(iter(any_index[business_id]))
    return ""


def classify_family(row: dict[str, str]) -> str:
    values = [row.get("template_business_name", ""), row.get("template_name", ""), row.get("setup_business_name", ""), row.get("setup_business_table", ""), row.get("setup_business_path", ""), row.get("setup_step_name", "")]
    haystack = " ".join(clean(value) for value in values if clean(value))
    for family, tokens in FAMILY_RULES:
        if family == "unknown_or_unmapped_family":
            continue
        if any(token in haystack for token in tokens):
            return family
    return "unknown_or_unmapped_family"


def screen(asset_root: Path) -> dict[str, Any]:
    rows = parse_sql_rows(run_sql())
    source_index, any_index = build_coverage_indexes(asset_root)
    covered: Counter[str] = Counter()
    remaining_family: Counter[str] = Counter()
    remaining_template_business: Counter[str] = Counter()
    remaining_template: Counter[str] = Counter()
    remaining_table: Counter[str] = Counter()
    family_table_counts: dict[str, Counter[str]] = defaultdict(Counter)
    samples: dict[str, list[dict[str, str]]] = defaultdict(list)
    remaining_rows = 0
    for row in rows:
        lane = covered_lane(row, source_index, any_index)
        if lane:
            covered[lane] += 1
            continue
        remaining_rows += 1
        family = classify_family(row)
        remaining_family[family] += 1
        remaining_template_business[clean(row.get("template_business_name")) or "missing_template_business"] += 1
        remaining_template[clean(row.get("template_name")) or "missing_template"] += 1
        table_name = clean(row.get("setup_business_table")) or clean(row.get("SJBMC")) or "missing_source_table"
        remaining_table[table_name] += 1
        family_table_counts[family][table_name] += 1
        if len(samples[family]) < 10:
            samples[family].append({
                "workflow_id": clean(row.get("Id")),
                "source_table": clean(row.get("SJBMC")),
                "djid": clean(row.get("DJID")),
                "business_id": clean(row.get("business_Id")),
                "template_business_name": clean(row.get("template_business_name")),
                "template_name": clean(row.get("template_name")),
                "setup_business_table": clean(row.get("setup_business_table")),
            })
    recommendation = next_recommendation(remaining_family, family_table_counts)
    return {
        "status": "PASS",
        "raw_rows": len(rows),
        "covered_rows": sum(covered.values()),
        "remaining_rows": remaining_rows,
        "covered_by_lane_counts": dict(covered.most_common()),
        "remaining_family_counts": dict(remaining_family.most_common()),
        "remaining_template_business_counts": dict(remaining_template_business.most_common(30)),
        "remaining_template_counts": dict(remaining_template.most_common(30)),
        "remaining_setup_table_counts": dict(remaining_table.most_common(30)),
        "remaining_family_table_counts": {
            family: dict(counter.most_common(10)) for family, counter in sorted(family_table_counts.items())
        },
        "samples": samples,
        "next_lane_recommendation": recommendation,
        "db_writes": 0,
        "odoo_shell": False,
    }


def next_recommendation(family_counts: Counter[str], family_table_counts: dict[str, Counter[str]]) -> dict[str, Any]:
    actionable = [(family, count) for family, count in family_counts.most_common() if family != "unknown_or_unmapped_family"]
    if not actionable:
        return {"lane": "remaining_business_fact_review", "reason": "only unknown/unmapped workflow-linked rows remain"}
    family, count = actionable[0]
    table_counts = family_table_counts.get(family, Counter())
    table, table_count = table_counts.most_common(1)[0] if table_counts else ("", 0)
    return {"lane": family, "remaining_rows": count, "top_source_table": table, "top_source_table_rows": table_count, "reason": "largest remaining classified business family after current asset bus coverage"}


def write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Legacy Remaining Business Fact Screen v1",
        "",
        "Status: `PASS`",
        "",
        "This is a read-only screen after the current migration asset bus.",
        "",
        "## Result",
        "",
        f"- raw workflow rows: `{result['raw_rows']}`",
        f"- covered rows: `{result['covered_rows']}`",
        f"- remaining rows: `{result['remaining_rows']}`",
        "- DB writes: `0`",
        "- Odoo shell: `false`",
        "",
        "## Remaining Families",
        "",
        "| Family | Rows |",
        "|---|---:|",
    ]
    for family, count in result["remaining_family_counts"].items():
        lines.append(f"| {family} | {count} |")
    lines.extend(["", "## Covered By Lane", "", "| Lane | Rows |", "|---|---:|"])
    for lane, count in result["covered_by_lane_counts"].items():
        lines.append(f"| {lane} | {count} |")
    lines.extend(["", "## Top Remaining Source Tables", "", "| Source table | Rows |", "|---|---:|"])
    for table, count in result["remaining_setup_table_counts"].items():
        lines.append(f"| {table} | {count} |")
    lines.extend(["", "## Top Remaining Template Business Names", "", "| Template business | Rows |", "|---|---:|"])
    for name, count in result["remaining_template_business_counts"].items():
        lines.append(f"| {name} | {count} |")
    rec = result["next_lane_recommendation"]
    lines.extend([
        "",
        "## Next lane recommendation",
        "",
        f"- lane: `{rec.get('lane', '')}`",
        f"- remaining rows: `{rec.get('remaining_rows', 0)}`",
        f"- top source table: `{rec.get('top_source_table', '')}`",
        f"- top source table rows: `{rec.get('top_source_table_rows', 0)}`",
        f"- reason: {rec.get('reason', '')}",
        "",
        "## Boundary",
        "",
        "This report is a prioritization map. It does not prove each remaining row is loadable.",
        "The next lane still needs direct source-table completeness screening before model or XML work.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen remaining legacy business fact candidates.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--output-json", default=str(OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(OUTPUT_MD))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = screen(Path(args.asset_root))
        write_json(Path(args.output_json), result)
        write_report(Path(args.output_md), result)
    except (RemainingBusinessFactScreenError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_REMAINING_BUSINESS_FACT_SCREEN=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_REMAINING_BUSINESS_FACT_SCREEN=" + json.dumps({
        "status": "PASS",
        "raw_rows": result["raw_rows"],
        "covered_rows": result["covered_rows"],
        "remaining_rows": result["remaining_rows"],
        "next_lane_recommendation": result["next_lane_recommendation"],
        "db_writes": 0,
        "odoo_shell": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
