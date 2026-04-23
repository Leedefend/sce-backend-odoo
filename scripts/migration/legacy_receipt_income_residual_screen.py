#!/usr/bin/env python3
"""Screen legacy receipt and income residual business facts."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/receipt_income_residual_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_receipt_income_residual_screen_v1.json"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_receipt_income_residual_screen_v1.md")

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
  SELECT 'C_JFHKLR' AS source_table, CONVERT(nvarchar(max), Id) AS legacy_id,
    CONVERT(nvarchar(max), DJBH) AS document_no, CONVERT(nvarchar(max), COALESCE(NULLIF(XMID, ''), NULLIF(LYXMID, ''), NULLIF(TSXMID, ''))) AS project_id,
    CONVERT(nvarchar(max), COALESCE(NULLIF(XMMC, ''), NULLIF(LYXM, ''), NULLIF(TSXMMC, ''))) AS project_name,
    CONVERT(nvarchar(max), WLDWID) AS partner_id, CONVERT(nvarchar(max), WLDWMC) AS partner_name,
    CONVERT(nvarchar(max), f_JE) AS amount, CONVERT(nvarchar(max), f_RQ, 120) AS document_date,
    CONVERT(nvarchar(max), DJZT) AS state, CONVERT(nvarchar(max), DEL) AS deleted,
    CONVERT(nvarchar(max), f_SRLBName) AS income_category, CONVERT(nvarchar(max), f_BZ) AS note,
    CONVERT(nvarchar(max), PID) AS pid, 'customer_receipt' AS family, 'inflow' AS direction
  FROM dbo.C_JFHKLR
  UNION ALL
  SELECT 'ZJGL_SZQR_DKQRB', CONVERT(nvarchar(max), Id), CONVERT(nvarchar(max), DJBH),
    CONVERT(nvarchar(max), XMID), CONVERT(nvarchar(max), XMMC), CONVERT(nvarchar(max), NULL),
    CONVERT(nvarchar(max), SGD), CONVERT(nvarchar(max), COALESCE(NULLIF(KPSKQK_BQS, 0), NULLIF(BCKYZJYE_BQS, 0), NULLIF(SGDGCK_2, 0), NULLIF(YFSGDGCK_2, 0), NULLIF(SJZJ, 0))),
    CONVERT(nvarchar(max), SJ, 120), CONVERT(nvarchar(max), DJZT), CONVERT(nvarchar(max), DEL),
    CONVERT(nvarchar(max), '到款确认'), CONVERT(nvarchar(max), COALESCE(NULLIF(KPSKQK_BZ, ''), NULLIF(BCKYZJYE_BZ, ''), NULLIF(SQLCYE_BZ, ''))),
    CONVERT(nvarchar(max), pid), 'receipt_confirmation', 'inflow'
  FROM dbo.ZJGL_SZQR_DKQRB
  UNION ALL
  SELECT 'C_CWSFK_GSCWSR', CONVERT(nvarchar(max), Id), CONVERT(nvarchar(max), DJBH),
    CONVERT(nvarchar(max), XMID), CONVERT(nvarchar(max), XMMC), CONVERT(nvarchar(max), FKDWID),
    CONVERT(nvarchar(max), FKDW), CONVERT(nvarchar(max), JZJE), CONVERT(nvarchar(max), SKSJ, 120),
    CONVERT(nvarchar(max), DJZT), CONVERT(nvarchar(max), DEL), CONVERT(nvarchar(max), COALESCE(NULLIF(D_SCBSJS_CWSRLB, ''), NULLIF(SKLB, ''))),
    CONVERT(nvarchar(max), BZ), CONVERT(nvarchar(max), pid), 'company_financial_income', 'inflow'
  FROM dbo.C_CWSFK_GSCWSR
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(source_table, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(legacy_id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(document_no, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(project_id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(project_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(partner_id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(partner_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(amount, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(document_date, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(state, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(deleted, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(income_category, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(note, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(pid, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(family, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(direction, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY source_table, legacy_id;
"""

SQL_COLUMNS = [
    "source_table", "legacy_id", "document_no", "project_id", "project_name",
    "partner_id", "partner_name", "amount", "document_date", "state", "deleted",
    "income_category", "note", "pid", "family", "direction",
]


class ReceiptIncomeResidualScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptIncomeResidualScreenError(message)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_amount(value: str) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


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
    require(rows, "no receipt/income residual source rows returned")
    return rows


def load_project_refs(asset_root: Path) -> set[str]:
    manifest = load_json(asset_root / "manifest/project_external_id_manifest_v1.json")
    refs = set()
    for row in manifest.get("records", []):
        if row.get("status") == "loadable":
            refs.add(clean(row.get("legacy_key")))
            refs.add(clean((row.get("target_lookup") or {}).get("value")))
    refs.discard("")
    require(refs, "project refs are empty")
    return refs


def load_partner_refs(asset_root: Path) -> set[str]:
    refs: set[str] = set()
    for rel_path in ("manifest/partner_external_id_manifest_v1.json", "manifest/receipt_counterparty_partner_external_id_manifest_v1.json"):
        path = asset_root / rel_path
        if not path.exists():
            continue
        manifest = load_json(path)
        for row in manifest.get("records", []):
            if row.get("status") == "loadable":
                refs.add(clean(row.get("legacy_partner_id")))
    refs.discard("")
    return refs


def load_existing_receipts(asset_root: Path) -> set[str]:
    manifest = load_json(asset_root / "manifest/receipt_external_id_manifest_v1.json")
    refs = {
        clean(row.get("legacy_receipt_id"))
        for row in manifest.get("records", [])
        if row.get("status") == "loadable" and clean(row.get("legacy_receipt_id"))
    }
    return refs


def is_deleted(value: str) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y"}


def classify_row(row: dict[str, str], project_refs: set[str], existing_receipts: set[str]) -> tuple[str, list[str]]:
    if clean(row.get("source_table")) == "C_JFHKLR" and clean(row.get("legacy_id")) in existing_receipts:
        return "already_assetized_receipt", []
    reasons: list[str] = []
    if not clean(row.get("legacy_id")):
        reasons.append("missing_legacy_id")
    if is_deleted(row.get("deleted", "")):
        reasons.append("deleted")
    project_id = clean(row.get("project_id"))
    if not project_id:
        reasons.append("missing_project_id")
    elif project_id not in project_refs:
        reasons.append("project_not_assetized")
    if parse_amount(row.get("amount", "")) <= 0:
        reasons.append("amount_not_positive_or_missing")
    return ("residual_loadable_candidate" if not reasons else "blocked", reasons)


def screen(asset_root: Path) -> dict[str, Any]:
    rows = parse_sql_rows(run_sql())
    project_refs = load_project_refs(asset_root)
    partner_refs = load_partner_refs(asset_root)
    existing_receipts = load_existing_receipts(asset_root)
    route_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    table_counts: Counter[str] = Counter()
    table_loadable: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    partner_counts: Counter[str] = Counter()
    samples: dict[str, list[dict[str, str]]] = {
        "residual_loadable_candidate": [],
        "already_assetized_receipt": [],
        "blocked": [],
    }

    for row in rows:
        route, reasons = classify_row(row, project_refs, existing_receipts)
        route_counts[route] += 1
        table = clean(row.get("source_table")) or "missing_source_table"
        family = clean(row.get("family")) or "missing_family"
        table_counts[table] += 1
        family_counts[family] += 1
        category_counts[clean(row.get("income_category")) or "missing_income_category"] += 1
        if route == "residual_loadable_candidate":
            table_loadable[table] += 1
        for reason in reasons:
            reason_counts[reason] += 1
        partner_id = clean(row.get("partner_id"))
        partner_name = clean(row.get("partner_name"))
        if partner_id and partner_id in partner_refs:
            partner_counts["partner_id_assetized"] += 1
        elif partner_id:
            partner_counts["partner_id_not_assetized"] += 1
        elif partner_name:
            partner_counts["partner_name_text"] += 1
        else:
            partner_counts["partner_missing"] += 1
        if len(samples[route]) < 20:
            samples[route].append({
                "source_table": table,
                "legacy_id": clean(row.get("legacy_id")),
                "document_no": clean(row.get("document_no")),
                "project_id": clean(row.get("project_id")),
                "project_name": clean(row.get("project_name")),
                "partner_id": partner_id,
                "partner_name": partner_name,
                "amount": clean(row.get("amount")),
                "income_category": clean(row.get("income_category")),
                "family": family,
                "reasons": ",".join(reasons),
            })

    recommendation = next_lane_recommendation(table_loadable, route_counts)
    return {
        "status": "PASS",
        "raw_rows": len(rows),
        "already_assetized_rows": route_counts["already_assetized_receipt"],
        "residual_loadable_rows": route_counts["residual_loadable_candidate"],
        "blocked_rows": route_counts["blocked"],
        "route_counts": dict(route_counts),
        "blocked_reason_counts": dict(reason_counts.most_common()),
        "source_table_counts": dict(table_counts.most_common()),
        "source_table_residual_loadable_counts": dict(table_loadable.most_common()),
        "family_counts": dict(family_counts.most_common()),
        "income_category_counts": dict(category_counts.most_common(20)),
        "partner_anchor_counts": dict(partner_counts.most_common()),
        "samples": samples,
        "next_lane_recommendation": recommendation,
        "db_writes": 0,
        "odoo_shell": False,
    }


def next_lane_recommendation(table_loadable: Counter[str], route_counts: Counter[str]) -> dict[str, Any]:
    if not route_counts["residual_loadable_candidate"]:
        return {"lane": "receipt_income_residual_model_design_blocked", "reason": "no residual loadable rows with project and positive amount"}
    table, count = table_loadable.most_common(1)[0]
    return {
        "lane": "legacy_receipt_income_residual_fact_carrier",
        "source_table_priority": table,
        "residual_loadable_rows": count,
        "reason": "screen found project-anchored positive-amount income facts not already covered by receipt_sc_v1",
    }


def write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Legacy Receipt Income Residual Screen v1",
        "",
        "Status: `PASS`",
        "",
        "This is a read-only screen for receipt and income facts not already covered by `receipt_sc_v1`.",
        "",
        "## Result",
        "",
        f"- raw rows: `{result['raw_rows']}`",
        f"- already assetized rows: `{result['already_assetized_rows']}`",
        f"- residual loadable rows: `{result['residual_loadable_rows']}`",
        f"- blocked rows: `{result['blocked_rows']}`",
        "- DB writes: `0`",
        "- Odoo shell: `false`",
        "",
        "## Source table readiness",
        "",
        "| Source table | Raw rows | Residual loadable candidates |",
        "|---|---:|---:|",
    ]
    loadable_by_table = result["source_table_residual_loadable_counts"]
    for table, count in result["source_table_counts"].items():
        lines.append(f"| {table} | {count} | {loadable_by_table.get(table, 0)} |")
    lines.extend(["", "## Blocked Reasons", "", "| Reason | Rows |", "|---|---:|"])
    for reason, count in result["blocked_reason_counts"].items():
        lines.append(f"| {reason} | {count} |")
    lines.extend(["", "## Family Counts", "", "| Family | Rows |", "|---|---:|"])
    for family, count in result["family_counts"].items():
        lines.append(f"| {family} | {count} |")
    lines.extend(["", "## Partner Evidence", "", "| Route | Rows |", "|---|---:|"])
    for route, count in result["partner_anchor_counts"].items():
        lines.append(f"| {route} | {count} |")
    rec = result["next_lane_recommendation"]
    lines.extend([
        "",
        "## Next lane recommendation",
        "",
        f"- lane: `{rec.get('lane', '')}`",
        f"- source table priority: `{rec.get('source_table_priority', '')}`",
        f"- residual loadable rows: `{rec.get('residual_loadable_rows', 0)}`",
        f"- reason: {rec.get('reason', '')}",
        "",
        "## Boundary",
        "",
        "These rows are receipt or income business facts, not payment runtime, settlement, or accounting entries.",
        "A later carrier must not create `payment.request`, `account.move`, settlement state, or approval runtime facts.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen legacy receipt/income residual facts.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--output-json", default=str(OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(OUTPUT_MD))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = screen(Path(args.asset_root))
        write_json(Path(args.output_json), result)
        write_report(Path(args.output_md), result)
    except (ReceiptIncomeResidualScreenError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_RECEIPT_INCOME_RESIDUAL_SCREEN=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_RECEIPT_INCOME_RESIDUAL_SCREEN=" + json.dumps({
        "status": "PASS",
        "raw_rows": result["raw_rows"],
        "already_assetized_rows": result["already_assetized_rows"],
        "residual_loadable_rows": result["residual_loadable_rows"],
        "blocked_rows": result["blocked_rows"],
        "next_lane_recommendation": result["next_lane_recommendation"],
        "db_writes": 0,
        "odoo_shell": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
