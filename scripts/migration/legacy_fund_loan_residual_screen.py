#!/usr/bin/env python3
"""Screen legacy fund daily and loan residual business facts."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/fund_loan_residual_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_fund_loan_residual_screen_v1.json"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_fund_loan_residual_screen_v1.md")

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
  SELECT 'D_SCBSJS_ZJGL_ZJSZ_ZJRBB' AS source_table,
    CONVERT(nvarchar(max), ID) AS legacy_id,
    CONVERT(nvarchar(max), PID) AS legacy_pid,
    CONVERT(nvarchar(max), DJBH) AS document_no,
    CONVERT(nvarchar(max), DJZT) AS state,
    CONVERT(nvarchar(max), DJRQ, 120) AS document_date,
    CONVERT(nvarchar(max), XMID) AS project_id,
    CONVERT(nvarchar(max), XMMC) AS project_name,
    CONVERT(nvarchar(max), '') AS counterparty_id,
    CONVERT(nvarchar(max), '') AS counterparty_name,
    CONVERT(nvarchar(max), ZHYEHJ) AS amount,
    CONVERT(nvarchar(max), ZHYHYEHJ) AS amount_secondary,
    CONVERT(nvarchar(max), YHXTCEHJ) AS amount_delta,
    CONVERT(nvarchar(max), 'fund_daily_balance_snapshot') AS family,
    CONVERT(nvarchar(max), BT) AS subject,
    CONVERT(nvarchar(max), '') AS due_date,
    CONVERT(nvarchar(max), BZ) AS note,
    CONVERT(nvarchar(max), DEL) AS deleted,
    CONVERT(nvarchar(max), '') AS extra_ref,
    CONVERT(nvarchar(max), '') AS extra_label
  FROM dbo.D_SCBSJS_ZJGL_ZJSZ_ZJRBB
  UNION ALL
  SELECT 'ZJGL_ZJSZ_DKGL_DKDJ',
    CONVERT(nvarchar(max), Id),
    CONVERT(nvarchar(max), pid),
    CONVERT(nvarchar(max), DJBH),
    CONVERT(nvarchar(max), DJZT),
    CONVERT(nvarchar(max), DKRQ, 120),
    CONVERT(nvarchar(max), XMID),
    CONVERT(nvarchar(max), XMMC),
    CONVERT(nvarchar(max), DKZHID),
    CONVERT(nvarchar(max), COALESCE(NULLIF(DKYH, ''), NULLIF(DKZH, ''))),
    CONVERT(nvarchar(max), DKJE),
    CONVERT(nvarchar(max), 0),
    CONVERT(nvarchar(max), 0),
    CONVERT(nvarchar(max), 'loan_registration'),
    CONVERT(nvarchar(max), D_SCBSJS_DQLX),
    CONVERT(nvarchar(max), HKRQ, 120),
    CONVERT(nvarchar(max), BZ),
    CONVERT(nvarchar(max), DEL),
    CONVERT(nvarchar(max), LXID),
    CONVERT(nvarchar(max), COALESCE(NULLIF(LX, ''), NULLIF(DKLL, ''), NULLIF(DKSJ, '')))
  FROM dbo.ZJGL_ZJSZ_DKGL_DKDJ
  UNION ALL
  SELECT 'ZJGL_ZCDFSZ_FXJK_JK',
    CONVERT(nvarchar(max), Id),
    CONVERT(nvarchar(max), pid),
    CONVERT(nvarchar(max), DJBH),
    CONVERT(nvarchar(max), DJZT),
    CONVERT(nvarchar(max), TXRQ, 120),
    CONVERT(nvarchar(max), XMID),
    CONVERT(nvarchar(max), XMMC),
    CONVERT(nvarchar(max), TXRID),
    CONVERT(nvarchar(max), COALESCE(NULLIF(JKR, ''), NULLIF(SKDW, ''), NULLIF(TXR, ''))),
    CONVERT(nvarchar(max), JKJE),
    CONVERT(nvarchar(max), JKLX),
    CONVERT(nvarchar(max), 0),
    CONVERT(nvarchar(max), 'borrowing_request'),
    CONVERT(nvarchar(max), YT),
    CONVERT(nvarchar(max), YDQX, 120),
    CONVERT(nvarchar(max), BZ),
    CONVERT(nvarchar(max), DEL),
    CONVERT(nvarchar(max), COALESCE(NULLIF(SKZHID, ''), NULLIF(WSZCZHID, ''))),
    CONVERT(nvarchar(max), COALESCE(NULLIF(SKZH, ''), NULLIF(WSZCZH, ''), NULLIF(BM, '')))
  FROM dbo.ZJGL_ZCDFSZ_FXJK_JK
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(source_table, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(legacy_id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(legacy_pid, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(document_no, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(state, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(document_date, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(project_id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(project_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(counterparty_id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(counterparty_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(amount, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(amount_secondary, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(amount_delta, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(family, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(subject, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(due_date, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(note, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(deleted, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(extra_ref, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(extra_label, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY source_table, legacy_id;
"""

SQL_COLUMNS = [
    "source_table",
    "legacy_id",
    "legacy_pid",
    "document_no",
    "state",
    "document_date",
    "project_id",
    "project_name",
    "counterparty_id",
    "counterparty_name",
    "amount",
    "amount_secondary",
    "amount_delta",
    "family",
    "subject",
    "due_date",
    "note",
    "deleted",
    "extra_ref",
    "extra_label",
]


class FundLoanResidualScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FundLoanResidualScreenError(message)


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
    require(rows, "no fund/loan source rows returned")
    return rows


def load_project_refs(asset_root: Path) -> set[str]:
    manifest = load_json(asset_root / "manifest/project_external_id_manifest_v1.json")
    refs: set[str] = set()
    for row in manifest.get("records", []):
        if row.get("status") == "loadable":
            refs.add(clean(row.get("legacy_key")))
            refs.add(clean((row.get("target_lookup") or {}).get("value")))
    refs.discard("")
    require(refs, "project refs are empty")
    return refs


def is_deleted(row: dict[str, str]) -> bool:
    return clean(row.get("deleted")) in {"1", "true", "True"}


def classify_row(row: dict[str, str], project_refs: set[str]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not clean(row.get("legacy_id")):
        reasons.append("missing_legacy_id")
    if is_deleted(row):
        reasons.append("deleted")
    if not clean(row.get("document_date")):
        reasons.append("missing_document_date")

    amount = parse_amount(row.get("amount", ""))
    family = clean(row.get("family"))
    if family == "fund_daily_balance_snapshot":
        if amount == 0 and parse_amount(row.get("amount_secondary", "")) == 0 and parse_amount(row.get("amount_delta", "")) == 0:
            reasons.append("missing_balance_amounts")
    elif amount <= 0:
        reasons.append("amount_not_positive_or_missing")

    project_id = clean(row.get("project_id"))
    project_resolved = project_id in project_refs if project_id else False
    if not project_id:
        reasons.append("missing_project_id")
    elif not project_resolved:
        reasons.append("project_not_assetized")

    if family == "fund_daily_balance_snapshot":
        return ("management_snapshot_candidate" if not reasons else "blocked", reasons)

    if not clean(row.get("counterparty_name")):
        reasons.append("missing_counterparty_name")
    if not reasons and project_resolved:
        return "project_anchored_financing_candidate", []
    if not reasons:
        return "company_level_financing_candidate", []
    return "blocked", reasons


def counter_to_dict(counter: Counter[str], limit: int | None = None) -> dict[str, int]:
    items = counter.most_common(limit)
    return {key: value for key, value in items}


def sample_row(row: dict[str, str], route: str, reasons: list[str]) -> dict[str, str]:
    return {
        "source_table": clean(row.get("source_table")),
        "legacy_id": clean(row.get("legacy_id")),
        "document_no": clean(row.get("document_no")),
        "document_date": clean(row.get("document_date")),
        "project_id": clean(row.get("project_id")),
        "project_name": clean(row.get("project_name")),
        "counterparty_name": clean(row.get("counterparty_name")),
        "amount": clean(row.get("amount")),
        "family": clean(row.get("family")),
        "route": route,
        "reasons": ",".join(reasons),
    }


def screen(asset_root: Path) -> dict[str, Any]:
    rows = parse_sql_rows(run_sql())
    project_refs = load_project_refs(asset_root)
    by_table: Counter[str] = Counter()
    by_family: Counter[str] = Counter()
    routes: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    route_by_table: dict[str, Counter[str]] = defaultdict(Counter)
    samples: dict[str, list[dict[str, str]]] = defaultdict(list)

    amount_by_route: dict[str, Decimal] = defaultdict(Decimal)
    active_rows = 0
    project_anchored_rows = 0
    counterparty_named_rows = 0

    for row in rows:
        source_table = clean(row.get("source_table"))
        family = clean(row.get("family"))
        by_table[source_table] += 1
        by_family[family] += 1
        if not is_deleted(row):
            active_rows += 1
        if clean(row.get("project_id")) in project_refs:
            project_anchored_rows += 1
        if clean(row.get("counterparty_name")):
            counterparty_named_rows += 1

        route, blocked_reasons = classify_row(row, project_refs)
        routes[route] += 1
        route_by_table[source_table][route] += 1
        amount_by_route[route] += parse_amount(row.get("amount", ""))
        for reason in blocked_reasons:
            reasons[reason] += 1
        if len(samples[route]) < 15:
            samples[route].append(sample_row(row, route, blocked_reasons))

    project_financing = routes["project_anchored_financing_candidate"]
    management_snapshots = routes["management_snapshot_candidate"]
    if project_financing:
        next_recommendation = "open_fund_loan_model_design_for_project_anchored_financing"
    elif management_snapshots:
        next_recommendation = "defer_management_snapshot_until_target_model_confirmed"
    else:
        next_recommendation = "no_assetization_lane"

    return {
        "status": "PASS",
        "raw_rows": len(rows),
        "active_rows": active_rows,
        "project_anchored_rows": project_anchored_rows,
        "counterparty_named_rows": counterparty_named_rows,
        "source_table_counts": counter_to_dict(by_table),
        "family_counts": counter_to_dict(by_family),
        "classification_counts": counter_to_dict(routes),
        "blocked_reason_counts": counter_to_dict(reasons),
        "classification_by_table": {table: counter_to_dict(counter) for table, counter in sorted(route_by_table.items())},
        "amount_by_classification": {key: str(value) for key, value in sorted(amount_by_route.items())},
        "samples": dict(samples),
        "next_recommendation": next_recommendation,
        "source_tables": [
            "D_SCBSJS_ZJGL_ZJSZ_ZJRBB",
            "ZJGL_ZJSZ_DKGL_DKDJ",
            "ZJGL_ZCDFSZ_FXJK_JK",
        ],
        "db_writes": 0,
        "odoo_shell": False,
    }


def write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Legacy Fund Loan Residual Screen v1",
        "",
        "Status: `PASS`",
        "",
        "This report screens old-system fund daily, loan registration, and borrowing rows before any model or XML asset decision.",
        "",
        "## Scope",
        "",
        "- source tables: `D_SCBSJS_ZJGL_ZJSZ_ZJRBB`, `ZJGL_ZJSZ_DKGL_DKDJ`, `ZJGL_ZCDFSZ_FXJK_JK`",
        "- DB writes: `0`",
        "- Odoo shell: `false`",
        "",
        "## Source Baseline",
        "",
        f"- raw rows: `{result['raw_rows']}`",
        f"- active rows: `{result['active_rows']}`",
        f"- project-anchored rows: `{result['project_anchored_rows']}`",
        f"- counterparty-named rows: `{result['counterparty_named_rows']}`",
        "",
        "### Source table counts",
        "",
        "| Source table | Rows |",
        "|---|---:|",
    ]
    for table, count in result["source_table_counts"].items():
        lines.append(f"| {table} | {count} |")

    lines.extend(
        [
            "",
            "## Business Fact Classification",
            "",
            "| Classification | Rows | Source amount sum |",
            "|---|---:|---:|",
        ]
    )
    for route, count in result["classification_counts"].items():
        lines.append(f"| {route} | {count} | {result['amount_by_classification'].get(route, '0')} |")

    lines.extend(["", "### Classification by source table", "", "| Source table | Classification counts |", "|---|---|"])
    for table, counts in result["classification_by_table"].items():
        lines.append(f"| {table} | `{json.dumps(counts, ensure_ascii=False, sort_keys=True)}` |")

    lines.extend(["", "### Blocked reasons", "", "| Reason | Rows |", "|---|---:|"])
    for reason, count in result["blocked_reason_counts"].items():
        lines.append(f"| {reason} | {count} |")

    lines.extend(["", "## Samples", ""])
    for route, rows in sorted(result["samples"].items()):
        lines.extend([f"### {route}", "", "```json"])
        lines.append(json.dumps(rows[:5], ensure_ascii=False, indent=2, sort_keys=True))
        lines.extend(["```", ""])

    lines.extend(
        [
            "## Next Recommendation",
            "",
            f"- recommendation: `{result['next_recommendation']}`",
            "- judgment: loan registration and borrowing rows with positive amount, document date, project anchor, and counterparty name are durable business facts.",
            "- judgment: fund daily rows are management balance snapshots, not payment or settlement transactions; they should not be forced into the payment model.",
            "- next lane: if accepted, open a model-design batch for a neutral legacy financing/loan fact carrier before XML asset generation.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen legacy fund and loan residual rows.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--output-json", default=str(OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(OUTPUT_MD))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = screen(Path(args.asset_root))
        write_json(Path(args.output_json), result)
        write_report(Path(args.output_md), result)
    except (FundLoanResidualScreenError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_FUND_LOAN_RESIDUAL_SCREEN=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print(
        "LEGACY_FUND_LOAN_RESIDUAL_SCREEN="
        + json.dumps(
            {
                "status": "PASS",
                "raw_rows": result["raw_rows"],
                "classification_counts": result["classification_counts"],
                "next_recommendation": result["next_recommendation"],
                "db_writes": 0,
                "odoo_shell": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
