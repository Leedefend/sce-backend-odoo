#!/usr/bin/env python3
"""Classify blocked legacy workflow approval rows by business family."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/workflow_blocked_family_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_workflow_blocked_family_screen_v1.json"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_workflow_blocked_family_screen_v1.md")
EXPECTED_RAW_ROWS = 163245
EXPECTED_BLOCKED_ROWS = 83543

TARGET_SPECS = [
    ("project", "BASE_SYSTEM_PROJECT", "project.project", "manifest/project_external_id_manifest_v1.json", ["legacy_key", "target_lookup.value"]),
    ("contract", "T_ProjectContract_Out", "construction.contract", "manifest/contract_external_id_manifest_v1.json", ["legacy_contract_id"]),
    ("receipt", "C_JFHKLR", "payment.request", "manifest/receipt_external_id_manifest_v1.json", ["legacy_receipt_id"]),
    ("outflow_request", "C_ZFSQGL", "payment.request", "manifest/outflow_request_external_id_manifest_v1.json", ["legacy_outflow_id"]),
    ("actual_outflow", "T_FK_Supplier", "payment.request", "manifest/actual_outflow_external_id_manifest_v1.json", ["legacy_actual_outflow_id"]),
    ("supplier_contract", "T_GYSHT_INFO", "construction.contract", "manifest/supplier_contract_external_id_manifest_v1.json", ["legacy_supplier_contract_id"]),
    ("outflow_request_line", "C_ZFSQGL_CB", "payment.request.line", "manifest/outflow_request_line_external_id_manifest_v1.json", ["legacy_outflow_line_id"]),
    ("receipt_invoice_line", "C_JFHKLR_CB", "sc.receipt.invoice.line", "manifest/receipt_invoice_line_external_id_manifest_v1.json", ["legacy_receipt_invoice_line_id", "attachment_candidate_keys.Id"]),
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
  CONVERT(nvarchar(max), a.SPLX) AS SPLX,
  CONVERT(nvarchar(max), st.f_BZMC) AS setup_step_name,
  CONVERT(nvarchar(max), st.f_BZXH) AS setup_step_sequence,
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
  ISNULL(REPLACE(REPLACE(REPLACE(SPLX, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(setup_step_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(setup_step_sequence, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
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
    "Id",
    "SJBMC",
    "DJID",
    "business_Id",
    "f_SPZT",
    "f_LRRId",
    "f_LRR",
    "f_SPSJ",
    "SPLX",
    "setup_step_name",
    "setup_step_sequence",
    "template_name",
    "template_business_name",
    "template_source_table",
    "setup_business_name",
    "setup_business_table",
    "setup_business_path",
]

FAMILY_RULES = [
    ("payment_request_residual", ("支付申请", "付款申请", "往来单位付款")),
    ("receipt_or_income_residual", ("工程款收入", "到款确认", "公司财务收入", "自筹垫付收入")),
    ("supplier_contract_residual", ("供货商材料合同", "供货合同", "一般供应商")),
    ("contract_residual", ("施工合同", "外部合同")),
    ("invoice_tax_family", ("进项上报", "销项开票")),
    ("expense_or_deposit_family", ("报销申请", "公司财务支出", "保证金", "垫付退回", "扣款实缴退回")),
    ("document_approval_family", ("文件批阅", "承办笺")),
]


class BlockedFamilyScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BlockedFamilyScreenError(message)


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
    text = clean(value)
    aliases = {
        "T_ProjectContract_OutInfo": "T_ProjectContract_Out",
        "ProjectContract_Out": "T_ProjectContract_Out",
        "C_JFHKLR_CB_FP": "C_JFHKLR_CB",
    }
    return aliases.get(text, text)


def classify_family(*values: str) -> str:
    haystack = " ".join(clean(value) for value in values if clean(value))
    for family, tokens in FAMILY_RULES:
        if any(token in haystack for token in tokens):
            return family
    return "unknown_or_unmapped_family"


def run_sql() -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        "legacy-sqlserver",
        "bash",
        "-lc",
        "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P \"$SA_PASSWORD\" -C -d LegacyDb -s '|' -y 0 -Y 0",
    ]
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


def build_target_index(asset_root: Path) -> tuple[dict[tuple[str, str], list[dict[str, str]]], dict[str, list[dict[str, str]]]]:
    source_index: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    any_index: dict[str, list[dict[str, str]]] = defaultdict(list)
    for lane, source_table, target_model, rel_path, key_paths in TARGET_SPECS:
        manifest = load_json(asset_root / rel_path)
        for row in manifest.get("records", []):
            if row.get("status") != "loadable":
                continue
            external_id = clean(row.get("external_id"))
            if not external_id:
                continue
            for key_path in key_paths:
                value = deep_get(row, key_path)
                if not value:
                    continue
                item = {"lane": lane, "source_table": source_table, "target_model": target_model, "external_id": external_id}
                source_index[(source_table, value)].append(item)
                any_index[value].append(item)
    require(source_index and any_index, "target indexes are empty")
    return source_index, any_index


def is_loadable(row: dict[str, str], source_index: dict[tuple[str, str], list[dict[str, str]]], any_index: dict[str, list[dict[str, str]]]) -> bool:
    source_table = normalize_source_table(row.get("SJBMC", ""))
    djid = clean(row.get("DJID"))
    business_id = clean(row.get("business_Id"))
    matches: list[dict[str, str]] = []
    if djid:
        matches = any_index.get(djid, [])
    if not matches and source_table and business_id:
        matches = source_index.get((source_table, business_id), [])
    if not matches and business_id:
        matches = any_index.get(business_id, [])
    return len({match["external_id"] for match in matches}) == 1


def screen(asset_root: Path) -> dict[str, Any]:
    rows = parse_sql_rows(run_sql())
    source_index, any_index = build_target_index(asset_root)
    blocked_rows = [row for row in rows if not is_loadable(row, source_index, any_index)]
    require(len(blocked_rows) == EXPECTED_BLOCKED_ROWS, f"blocked row count drifted: {len(blocked_rows)} != {EXPECTED_BLOCKED_ROWS}")

    family_counts: Counter[str] = Counter()
    template_business_counts: Counter[str] = Counter()
    template_counts: Counter[str] = Counter()
    setup_business_counts: Counter[str] = Counter()
    setup_table_counts: Counter[str] = Counter()
    step_counts: Counter[str] = Counter()
    actor_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    samples_by_family: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row in blocked_rows:
        family = classify_family(
            row.get("template_business_name", ""),
            row.get("template_name", ""),
            row.get("setup_business_name", ""),
            row.get("setup_business_table", ""),
            row.get("setup_business_path", ""),
            row.get("setup_step_name", ""),
        )
        family_counts[family] += 1
        template_business_counts[clean(row.get("template_business_name")) or "missing_template_business_name"] += 1
        template_counts[clean(row.get("template_name")) or "missing_template_name"] += 1
        setup_business_counts[clean(row.get("setup_business_name")) or "missing_setup_business_name"] += 1
        setup_table_counts[clean(row.get("setup_business_table")) or "missing_setup_business_table"] += 1
        step_counts[clean(row.get("setup_step_name")) or "missing_step_name"] += 1
        actor_counts["%s|%s" % (clean(row.get("f_LRR")) or "missing_actor", clean(row.get("f_LRRId")) or "missing_actor_id")] += 1
        source_counts[clean(row.get("SJBMC")) or "missing_source_table"] += 1
        if len(samples_by_family[family]) < 8:
            samples_by_family[family].append(
                {
                    "legacy_workflow_id": clean(row.get("Id")),
                    "djid": clean(row.get("DJID")),
                    "business_id": clean(row.get("business_Id")),
                    "template_business_name": clean(row.get("template_business_name")),
                    "template_name": clean(row.get("template_name")),
                    "setup_business_name": clean(row.get("setup_business_name")),
                    "setup_business_table": clean(row.get("setup_business_table")),
                    "step_name": clean(row.get("setup_step_name")),
                    "actor": clean(row.get("f_LRR")),
                    "approved_at": clean(row.get("f_SPSJ")),
                }
            )

    recommendation = next_lane_recommendation(family_counts)
    return {
        "status": "PASS",
        "raw_rows": len(rows),
        "blocked_rows": len(blocked_rows),
        "family_counts": dict(family_counts.most_common()),
        "template_business_counts": dict(template_business_counts.most_common(30)),
        "template_counts": dict(template_counts.most_common(30)),
        "setup_business_counts": dict(setup_business_counts.most_common(30)),
        "setup_table_counts": dict(setup_table_counts.most_common(30)),
        "step_counts": dict(step_counts.most_common(30)),
        "actor_counts": dict(actor_counts.most_common(20)),
        "source_counts": dict(source_counts.most_common(20)),
        "samples_by_family": dict(samples_by_family),
        "next_lane_recommendation": recommendation,
        "db_writes": 0,
        "odoo_shell": False,
    }


def next_lane_recommendation(family_counts: Counter[str]) -> dict[str, Any]:
    if not family_counts:
        return {"lane": "", "reason": "no blocked rows"}
    family, count = family_counts.most_common(1)[0]
    if family == "payment_request_residual":
        lane = "payment_request_residual_readiness"
        reason = "largest blocked family is still payment-request related; screen why these old payment approvals lack loadable payment.request anchors"
    elif family == "invoice_tax_family":
        lane = "invoice_tax_fact_lane"
        reason = "blocked rows point to old invoice/tax reporting facts that are not yet modeled as migration assets"
    elif family == "expense_or_deposit_family":
        lane = "expense_deposit_fact_lane"
        reason = "blocked rows point to reimbursement, financial expense, guarantee, or deposit facts not yet covered by current payment/request assets"
    elif family == "receipt_or_income_residual":
        lane = "receipt_income_residual_readiness"
        reason = "blocked rows point to income/receipt facts that may require residual receipt-family assetization"
    elif family == "supplier_contract_residual":
        lane = "supplier_contract_residual_readiness"
        reason = "blocked rows point to supplier contract facts that are not currently loadable"
    else:
        lane = "blocked_family_deep_probe"
        reason = "largest family is unmapped; inspect old setup business paths and target tables before implementation"
    return {"family": family, "blocked_rows": count, "lane": lane, "reason": reason}


def write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Legacy Workflow Blocked Family Screen v1",
        "",
        "Status: `PASS`",
        "",
        "This is a read-only screen for the blocked legacy approval audit rows.",
        "It does not generate XML assets and does not weaken target-anchor requirements.",
        "",
        "## Result",
        "",
        f"- raw rows: `{result['raw_rows']}`",
        f"- blocked rows: `{result['blocked_rows']}`",
        "- DB writes: `0`",
        "- Odoo shell: `false`",
        "",
        "## Top blocked business families",
        "",
        "| Family | Rows |",
        "|---|---:|",
    ]
    for family, count in result["family_counts"].items():
        lines.append(f"| {family} | {count} |")
    lines.extend(["", "## Top Template Business Names", "", "| Template business | Rows |", "|---|---:|"])
    for name, count in result["template_business_counts"].items():
        lines.append(f"| {name} | {count} |")
    lines.extend(["", "## Top Templates", "", "| Template | Rows |", "|---|---:|"])
    for name, count in result["template_counts"].items():
        lines.append(f"| {name} | {count} |")
    lines.extend(["", "## Setup Business Tables", "", "| Setup table | Rows |", "|---|---:|"])
    for name, count in result["setup_table_counts"].items():
        lines.append(f"| {name} | {count} |")
    rec = result["next_lane_recommendation"]
    lines.extend(
        [
            "",
            "## Next lane recommendation",
            "",
            f"- family: `{rec.get('family', '')}`",
            f"- blocked rows: `{rec.get('blocked_rows', 0)}`",
            f"- lane: `{rec.get('lane', '')}`",
            f"- reason: {rec.get('reason', '')}",
            "",
            "## Boundary",
            "",
            "Rows remain blocked until their target business records are assetized and loadable.",
            "Do not import these approval rows into `sc.legacy.workflow.audit` without a concrete target external id.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen blocked legacy workflow approval families.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--output-json", default=str(OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(OUTPUT_MD))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = screen(Path(args.asset_root))
        write_json(Path(args.output_json), result)
        write_report(Path(args.output_md), result)
    except (BlockedFamilyScreenError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_WORKFLOW_BLOCKED_FAMILY_SCREEN=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_WORKFLOW_BLOCKED_FAMILY_SCREEN=" + json.dumps({
        "status": "PASS",
        "blocked_rows": result["blocked_rows"],
        "next_lane_recommendation": result["next_lane_recommendation"],
        "db_writes": 0,
        "odoo_shell": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
