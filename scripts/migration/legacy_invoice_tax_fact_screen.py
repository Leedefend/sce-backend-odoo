#!/usr/bin/env python3
"""Screen legacy invoice and tax business facts before assetization."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/invoice_tax_fact_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_invoice_tax_fact_screen_v1.json"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_invoice_tax_fact_screen_v1.md")

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
  SELECT 'C_JXXP_ZYFPJJD_CB' AS source_table, CONVERT(nvarchar(max), c.Id) AS legacy_id,
    CONVERT(nvarchar(max), h.DJBH) AS document_no, CONVERT(nvarchar(max), h.XMID) AS project_id,
    CONVERT(nvarchar(max), h.XMMC) AS project_name, CONVERT(nvarchar(max), c.GYSID) AS partner_id,
    CONVERT(nvarchar(max), c.GYSMC) AS partner_name, CONVERT(nvarchar(max), c.GYSSH) AS partner_tax_no,
    CONVERT(nvarchar(max), c.HJJE) AS amount, CONVERT(nvarchar(max), c.JXSE) AS tax_amount,
    CONVERT(nvarchar(max), h.DJRQ, 120) AS document_date, CONVERT(nvarchar(max), h.DJZT) AS state,
    CONVERT(nvarchar(max), h.DEL) AS deleted, CONVERT(nvarchar(max), c.FPLX) AS invoice_type,
    CONVERT(nvarchar(max), c.JE_NO) AS amount_untaxed, CONVERT(nvarchar(max), c.FPHM) AS invoice_no,
    CONVERT(nvarchar(max), COALESCE(NULLIF(c.D_SCBSJS_FPGSLX, ''), h.D_SCBSJS_FPGSLX)) AS invoice_company_type,
    CONVERT(nvarchar(max), c.KPDW) AS invoice_issue_company,
    CONVERT(nvarchar(max), c.GYSMC) AS invoice_provider_name,
    CONVERT(nvarchar(max), h.D_SCBSJS_IsPush) AS push_result,
    CONVERT(nvarchar(max), h.OTHER_SYSTEM_CODE) AS kingdee_document_no,
    CONVERT(nvarchar(max), h.LRRID) AS creator_legacy_user_id,
    CONVERT(nvarchar(max), h.LRR) AS creator_name,
    CONVERT(nvarchar(max), h.LRSJ, 120) AS created_time,
    CONVERT(nvarchar(max), COALESCE(NULLIF(c.D_SCBSJS_FPBZ, ''), NULLIF(c.BZ, ''), h.BZ)) AS note,
    CONVERT(nvarchar(max), c.pid) AS pid,
    'input_invoice_handover' AS family, 'input_invoice' AS direction, 'C_JXXP_ZYFPJJD_CB.HJJE' AS amount_field
  FROM dbo.C_JXXP_ZYFPJJD_CB c
  JOIN dbo.C_JXXP_ZYFPJJD h ON h.Id = c.ZBID
  UNION ALL
  SELECT 'C_JXXP_XXKPDJ', CONVERT(nvarchar(max), h.Id), CONVERT(nvarchar(max), h.DJBH),
    CONVERT(nvarchar(max), h.XMID), CONVERT(nvarchar(max), h.XMMC), CONVERT(nvarchar(max), h.D_BYK_KFDWID),
    CONVERT(nvarchar(max), h.SPFMC), CONVERT(nvarchar(max), h.D_BYK_SPF_NSSBH),
    CONVERT(nvarchar(max), CASE WHEN child.child_rows > 0 THEN child.amount_total ELSE h.KPZJE END),
    CONVERT(nvarchar(max), CASE WHEN child.child_rows > 0 THEN child.tax_amount ELSE h.ZSE END),
    CONVERT(nvarchar(max), h.SQRQ, 120),
    CONVERT(nvarchar(max), h.DJZT), CONVERT(nvarchar(max), h.DEL), CONVERT(nvarchar(max), h.FPZL),
    CONVERT(nvarchar(max), CASE WHEN child.child_rows > 0 THEN child.amount_total - child.tax_amount ELSE h.KPZJE - h.ZSE END),
    CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), NULL),
    CONVERT(nvarchar(max), h.SPFMC), CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), h.OTHER_SYSTEM_CODE),
    CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), NULL),
    CONVERT(nvarchar(max), h.BZ), CONVERT(nvarchar(max), h.pid), 'output_invoice_register',
    'output_invoice',
    CASE WHEN child.child_rows > 0 THEN 'C_JXXP_XXKPDJ_CB.JE_SUM' ELSE 'KPZJE' END
  FROM dbo.C_JXXP_XXKPDJ h
  OUTER APPLY (
    SELECT
      COUNT(c.Id) AS child_rows,
      SUM(ISNULL(c.JE, 0)) AS amount_total,
      SUM(ISNULL(c.SE, 0)) AS tax_amount
    FROM dbo.C_JXXP_XXKPDJ_CB c
    WHERE c.ZBID = h.Id
  ) child
  UNION ALL
  SELECT 'C_JXXP_KJFPSQ', CONVERT(nvarchar(max), Id), CONVERT(nvarchar(max), DJBH),
    CONVERT(nvarchar(max), XMID), CONVERT(nvarchar(max), XMMC), CONVERT(nvarchar(max), NULL),
    CONVERT(nvarchar(max), SPF_MC), CONVERT(nvarchar(max), SPF_SBH),
    CONVERT(nvarchar(max), BCKP_JE), CONVERT(nvarchar(max), BCYJ_JE), CONVERT(nvarchar(max), SQRQ, 120),
    CONVERT(nvarchar(max), DJZT), CONVERT(nvarchar(max), DEL), CONVERT(nvarchar(max), KPF_FPZL),
    CONVERT(nvarchar(max), BCKP_JE - BCYJ_JE), CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), NULL),
    CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), SPF_MC), CONVERT(nvarchar(max), NULL),
    CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), NULL),
    CONVERT(nvarchar(max), NULL),
    CONVERT(nvarchar(max), BZ), CONVERT(nvarchar(max), pid), 'invoice_issue_request',
    'output_invoice', 'BCKP_JE'
  FROM dbo.C_JXXP_KJFPSQ
  UNION ALL
  SELECT 'C_JXXP_YJSKDJ', CONVERT(nvarchar(max), Id), CONVERT(nvarchar(max), DJBH),
    CONVERT(nvarchar(max), XMID), CONVERT(nvarchar(max), XMMC), CONVERT(nvarchar(max), PersonId),
    CONVERT(nvarchar(max), SPFMC), CONVERT(nvarchar(max), NULL),
    CONVERT(nvarchar(max), COALESCE(NULLIF(KPZJE, 0), NULLIF(KPZJE_NO, 0), NULLIF(KPSE, 0))),
    CONVERT(nvarchar(max), KPSE), CONVERT(nvarchar(max), SQRQ, 120),
    CONVERT(nvarchar(max), DJZT), CONVERT(nvarchar(max), DEL), CONVERT(nvarchar(max), SJBMC),
    CONVERT(nvarchar(max), KPZJE_NO), CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), NULL),
    CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), SPFMC), CONVERT(nvarchar(max), NULL),
    CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), NULL),
    CONVERT(nvarchar(max), NULL),
    CONVERT(nvarchar(max), NULL), CONVERT(nvarchar(max), pid), 'prepaid_tax_register',
    'prepaid_tax', 'KPZJE_OR_KPZJE_NO_OR_KPSE'
  FROM dbo.C_JXXP_YJSKDJ
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(source_table, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(legacy_id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(document_no, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(project_id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(project_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(partner_id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(partner_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(partner_tax_no, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(amount, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(tax_amount, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(document_date, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(state, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(deleted, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(invoice_type, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(amount_untaxed, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(invoice_no, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(invoice_company_type, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(invoice_issue_company, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(invoice_provider_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(push_result, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(kingdee_document_no, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(creator_legacy_user_id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(creator_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(created_time, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(note, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(pid, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(family, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(direction, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(amount_field, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY source_table, legacy_id;
"""

SQL_COLUMNS = [
    "source_table",
    "legacy_id",
    "document_no",
    "project_id",
    "project_name",
    "partner_id",
    "partner_name",
    "partner_tax_no",
    "amount",
    "tax_amount",
    "document_date",
    "state",
    "deleted",
    "invoice_type",
    "amount_untaxed",
    "invoice_no",
    "invoice_company_type",
    "invoice_issue_company",
    "invoice_provider_name",
    "push_result",
    "kingdee_document_no",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "note",
    "pid",
    "family",
    "direction",
    "amount_field",
]


class InvoiceTaxScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvoiceTaxScreenError(message)


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
    container = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-sqlserver")
    sqlcmd = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
    database = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
    password = os.getenv("LEGACY_MSSQL_SA_PASSWORD")
    password_expr = '"$SA_PASSWORD"' if password is None else shlex.quote(password)
    cmd = [
        "docker",
        "exec",
        "-i",
        container,
        "bash",
        "-lc",
        (
            f"{shlex.quote(sqlcmd)} -S localhost -U sa -P {password_expr} "
            f"-C -d {shlex.quote(database)} -s '|' -y 0 -Y 0"
        ),
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
    require(rows, "no invoice/tax source rows returned")
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
    manifest = load_json(asset_root / "manifest/partner_external_id_manifest_v1.json")
    refs = {
        clean(row.get("legacy_partner_id"))
        for row in manifest.get("records", [])
        if row.get("status") == "loadable" and clean(row.get("legacy_partner_id"))
    }
    return refs


def classify_row(row: dict[str, str], project_refs: set[str]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not clean(row.get("legacy_id")):
        reasons.append("missing_legacy_id")
    if clean(row.get("deleted")) in {"1", "true", "True"}:
        reasons.append("deleted")
    project_id = clean(row.get("project_id"))
    if not project_id:
        reasons.append("missing_project_id")
    elif project_id not in project_refs:
        reasons.append("project_not_assetized")
    if parse_amount(row.get("amount", "")) == 0 and parse_amount(row.get("tax_amount", "")) == 0:
        reasons.append("amount_and_tax_missing_or_zero")
    if not clean(row.get("partner_name")) and not clean(row.get("partner_tax_no")):
        reasons.append("missing_counterparty_evidence")
    return ("loadable_candidate" if not reasons else "blocked", reasons)


def screen(asset_root: Path) -> dict[str, Any]:
    rows = parse_sql_rows(run_sql())
    project_refs = load_project_refs(asset_root)
    partner_refs = load_partner_refs(asset_root)
    route_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    table_counts: Counter[str] = Counter()
    table_loadable: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    direction_counts: Counter[str] = Counter()
    invoice_type_counts: Counter[str] = Counter()
    partner_anchor_counts: Counter[str] = Counter()
    samples: dict[str, list[dict[str, str]]] = {"loadable_candidate": [], "blocked": []}

    for row in rows:
        route, reasons = classify_row(row, project_refs)
        route_counts[route] += 1
        table = clean(row.get("source_table")) or "missing_source_table"
        family = clean(row.get("family")) or "missing_family"
        table_counts[table] += 1
        family_counts[family] += 1
        direction_counts[clean(row.get("direction")) or "missing_direction"] += 1
        invoice_type_counts[clean(row.get("invoice_type")) or "missing_invoice_type"] += 1
        if route == "loadable_candidate":
            table_loadable[table] += 1
        for reason in reasons:
            reason_counts[reason] += 1
        partner_id = clean(row.get("partner_id"))
        if partner_id and partner_id in partner_refs:
            partner_anchor_counts["partner_id_assetized"] += 1
        elif partner_id:
            partner_anchor_counts["partner_id_not_assetized"] += 1
        elif clean(row.get("partner_tax_no")):
            partner_anchor_counts["partner_tax_no_text"] += 1
        elif clean(row.get("partner_name")):
            partner_anchor_counts["partner_name_text"] += 1
        else:
            partner_anchor_counts["partner_missing"] += 1
        if len(samples[route]) < 20:
            samples[route].append(
                {
                    "source_table": table,
                    "legacy_id": clean(row.get("legacy_id")),
                    "document_no": clean(row.get("document_no")),
                    "project_id": clean(row.get("project_id")),
                    "project_name": clean(row.get("project_name")),
                    "partner_name": clean(row.get("partner_name")),
                    "partner_tax_no": clean(row.get("partner_tax_no")),
                    "amount": clean(row.get("amount")),
                    "tax_amount": clean(row.get("tax_amount")),
                    "family": family,
                    "direction": clean(row.get("direction")),
                    "invoice_type": clean(row.get("invoice_type")),
                    "reasons": ",".join(reasons),
                }
            )

    recommendation = next_lane_recommendation(table_loadable, route_counts)
    return {
        "status": "PASS",
        "raw_rows": len(rows),
        "loadable_rows": route_counts["loadable_candidate"],
        "blocked_rows": route_counts["blocked"],
        "route_counts": dict(route_counts),
        "blocked_reason_counts": dict(reason_counts.most_common()),
        "source_table_counts": dict(table_counts.most_common()),
        "source_table_loadable_counts": dict(table_loadable.most_common()),
        "family_counts": dict(family_counts.most_common()),
        "direction_counts": dict(direction_counts.most_common()),
        "invoice_type_counts": dict(invoice_type_counts.most_common(20)),
        "partner_anchor_counts": dict(partner_anchor_counts.most_common()),
        "samples": samples,
        "next_lane_recommendation": recommendation,
        "db_writes": 0,
        "odoo_shell": False,
    }


def next_lane_recommendation(table_loadable: Counter[str], route_counts: Counter[str]) -> dict[str, Any]:
    if not route_counts["loadable_candidate"]:
        return {"lane": "invoice_tax_model_design_blocked", "reason": "no loadable invoice/tax rows with project and amount"}
    table, count = table_loadable.most_common(1)[0]
    return {
        "lane": "legacy_invoice_tax_fact_carrier",
        "source_table_priority": table,
        "loadable_rows": count,
        "reason": "screen found project-anchored invoice/tax facts; design a neutral carrier before XML generation",
    }


def write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Legacy Invoice Tax Fact Screen v1",
        "",
        "Status: `PASS`",
        "",
        "This is a read-only screen for invoice and tax-related legacy facts.",
        "",
        "## Result",
        "",
        f"- raw rows: `{result['raw_rows']}`",
        f"- loadable rows: `{result['loadable_rows']}`",
        f"- blocked rows: `{result['blocked_rows']}`",
        "- DB writes: `0`",
        "- Odoo shell: `false`",
        "",
        "## Source table readiness",
        "",
        "| Source table | Raw rows | Loadable candidates |",
        "|---|---:|---:|",
    ]
    loadable_by_table = result["source_table_loadable_counts"]
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
    lines.extend(
        [
            "",
            "## Next lane recommendation",
            "",
            f"- lane: `{rec.get('lane', '')}`",
            f"- source table priority: `{rec.get('source_table_priority', '')}`",
            f"- loadable rows: `{rec.get('loadable_rows', 0)}`",
            f"- reason: {rec.get('reason', '')}",
            "",
            "## Boundary",
            "",
            "These rows are invoice and tax business facts, not accounting entries.",
            "A later carrier must not create `account.move`, payment, settlement, tax ledger, or approval runtime facts.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen legacy invoice/tax facts.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--output-json", default=str(OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(OUTPUT_MD))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = screen(Path(args.asset_root))
        write_json(Path(args.output_json), result)
        write_report(Path(args.output_md), result)
    except (InvoiceTaxScreenError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_INVOICE_TAX_FACT_SCREEN=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_INVOICE_TAX_FACT_SCREEN=" + json.dumps({
        "status": "PASS",
        "raw_rows": result["raw_rows"],
        "loadable_rows": result["loadable_rows"],
        "blocked_rows": result["blocked_rows"],
        "next_lane_recommendation": result["next_lane_recommendation"],
        "db_writes": 0,
        "odoo_shell": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
