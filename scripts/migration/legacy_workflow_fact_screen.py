#!/usr/bin/env python3
"""Screen legacy S_Execute_Approval facts before workflow assetization."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/workflow_fact_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_workflow_fact_screen_v1.json"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_workflow_fact_screen_v1.md")
EXPECTED_RAW_ROWS = 163245

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
  CONVERT(nvarchar(max), Id) AS Id,
  CONVERT(nvarchar(max), SJBMC) AS SJBMC,
  CONVERT(nvarchar(max), DJID) AS DJID,
  CONVERT(nvarchar(max), business_Id) AS business_Id,
  CONVERT(nvarchar(max), f_SPZT) AS f_SPZT,
  CONVERT(nvarchar(max), f_Back_YJLX) AS f_Back_YJLX,
  CONVERT(nvarchar(max), f_SPYJ) AS f_SPYJ,
  CONVERT(nvarchar(max), f_LRRId) AS f_LRRId,
  CONVERT(nvarchar(max), f_LRR) AS f_LRR,
  CONVERT(nvarchar(max), f_SPSJ, 120) AS f_SPSJ,
  CONVERT(nvarchar(max), RecevieTime, 120) AS RecevieTime,
  CONVERT(nvarchar(max), pid) AS pid,
  CONVERT(nvarchar(max), SPLX) AS SPLX
FROM dbo.S_Execute_Approval
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SJBMC, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DJID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(business_Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_SPZT, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_Back_YJLX, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_SPYJ, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_LRRId, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_LRR, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_SPSJ, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(RecevieTime, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(pid, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SPLX, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY Id;
"""

SQL_COLUMNS = ["Id", "SJBMC", "DJID", "business_Id", "f_SPZT", "f_Back_YJLX", "f_SPYJ", "f_LRRId", "f_LRR", "f_SPSJ", "RecevieTime", "pid", "SPLX"]


class WorkflowFactScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise WorkflowFactScreenError(message)


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
    index: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
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
                if value:
                    item = {
                        "lane": lane,
                        "source_table": source_table,
                        "target_model": target_model,
                        "external_id": external_id,
                        "key_path": key_path,
                    }
                    index[(source_table, value)].append(item)
                    any_index[value].append(item)
    require(index, "workflow target index is empty")
    require(any_index, "workflow any-target index is empty")
    return index, any_index


def normalize_source_table(value: str) -> str:
    text = clean(value)
    aliases = {
        "T_ProjectContract_OutInfo": "T_ProjectContract_Out",
        "ProjectContract_Out": "T_ProjectContract_Out",
        "C_JFHKLR_CB_FP": "C_JFHKLR_CB",
    }
    return aliases.get(text, text)


def workflow_action(row: dict[str, str]) -> str:
    status = clean(row.get("f_SPZT"))
    back_type = clean(row.get("f_Back_YJLX"))
    if back_type and back_type not in {"0", "-1"}:
        return "reject_or_back"
    if status in {"1", "2", "3"}:
        return "approve"
    if status in {"-1", "4", "5"}:
        return "reject_or_cancel"
    return "unknown"


def screen(asset_root: Path) -> dict[str, Any]:
    rows = parse_sql_rows(run_sql())
    target_index, any_target_index = build_target_index(asset_root)
    source_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    route_counts: Counter[str] = Counter()
    lane_counts: Counter[str] = Counter()
    unmatched_source_counts: Counter[str] = Counter()
    ambiguous_rows = 0
    matched_targets: set[str] = set()
    samples: list[dict[str, Any]] = []

    for row in rows:
        source_table = normalize_source_table(row.get("SJBMC", ""))
        djid = clean(row.get("DJID"))
        business_id = clean(row.get("business_Id"))
        source_counts[source_table or "missing_source_table"] += 1
        action_counts[workflow_action(row)] += 1
        if not djid and not business_id:
            route_counts["blocked_missing_source_or_business_id"] += 1
            continue
        matches = []
        match_key = ""
        if djid:
            matches = any_target_index.get(djid, [])
            match_key = "DJID"
        if not matches and source_table and business_id:
            matches = target_index.get((source_table, business_id), [])
            match_key = "SJBMC_business_Id"
        if not matches and business_id:
            matches = any_target_index.get(business_id, [])
            match_key = "business_Id_any"
        if not matches:
            route_counts["blocked_target_not_assetized_or_not_loadable"] += 1
            unmatched_source_counts[source_table] += 1
            continue
        lanes = {match["lane"] for match in matches}
        targets = {match["external_id"] for match in matches}
        if len(targets) > 1:
            ambiguous_rows += 1
            route_counts["blocked_ambiguous_target"] += 1
            continue
        route_counts["loadable_historical_approval_fact"] += 1
        lane = next(iter(lanes))
        lane_counts[lane] += 1
        matched_targets.add(f"{lane}:{next(iter(targets))}")
        if len(samples) < 80:
            samples.append(
                {
                    "legacy_workflow_id": clean(row.get("Id")),
                    "source_table": source_table,
                    "business_id": business_id,
                    "djid": djid,
                    "match_key": match_key,
                    "lane": lane,
                    "target_model": matches[0]["target_model"],
                    "target_external_id": matches[0]["external_id"],
                    "action": workflow_action(row),
                    "actor": clean(row.get("f_LRR")),
                    "approved_at": clean(row.get("f_SPSJ")),
                }
            )

    loadable = route_counts["loadable_historical_approval_fact"]
    decision = "new_historical_workflow_audit_carrier_required" if loadable else "workflow_assetization_blocked_no_targets"
    return {
        "status": "PASS",
        "source_table": "S_Execute_Approval",
        "raw_rows": len(rows),
        "loadable_rows": loadable,
        "blocked_rows": len(rows) - loadable,
        "matched_target_records": len(matched_targets),
        "ambiguous_rows": ambiguous_rows,
        "source_counts": dict(source_counts.most_common()),
        "action_counts": dict(sorted(action_counts.items())),
        "route_counts": dict(sorted(route_counts.items())),
        "lane_counts": dict(sorted(lane_counts.items())),
        "unmatched_source_counts": dict(unmatched_source_counts.most_common(30)),
        "carrier_decision": decision,
        "rejected_carriers": {
            "sc.workflow.instance": "runtime current workflow state; would fabricate active process truth",
            "sc.workflow.workitem": "runtime todo/completion carrier; not historical audit-safe",
            "sc.workflow.log": "requires runtime instance and node references; cannot preserve source rows independently",
            "sc.business.evidence": "requires runtime integer business_id and restricted evidence types; not safe as XML carrier",
        },
        "samples": samples,
        "db_writes": 0,
        "odoo_shell": False,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    route_rows = "\n".join(f"| {key} | {value} |" for key, value in payload["route_counts"].items())
    lane_rows = "\n".join(f"| {key} | {value} |" for key, value in payload["lane_counts"].items()) or "| none | 0 |"
    action_rows = "\n".join(f"| {key} | {value} |" for key, value in payload["action_counts"].items())
    source_rows = "\n".join(f"| {key} | {value} |" for key, value in list(payload["source_counts"].items())[:30])
    return f"""# Legacy Workflow Fact Screen v1

Status: `{payload["status"]}`

This is a read-only screen for legacy approval facts from
`S_Execute_Approval`. It does not replay workflow runtime state.

## Result

- raw rows: `{payload["raw_rows"]}`
- loadable historical approval facts: `{payload["loadable_rows"]}`
- blocked rows: `{payload["blocked_rows"]}`
- matched target records: `{payload["matched_target_records"]}`
- ambiguous rows: `{payload["ambiguous_rows"]}`
- carrier decision: `{payload["carrier_decision"]}`
- DB writes: `0`
- Odoo shell: `false`

## Routes

| Route | Rows |
|---|---:|
{route_rows}

## Target Lane Coverage

| Lane | Approval rows |
|---|---:|
{lane_rows}

## Action Classification

| Action | Rows |
|---|---:|
{action_rows}

## Source Table Top Counts

| SJBMC | Rows |
|---|---:|
{source_rows}

## Rejected Existing Carriers

- `sc.workflow.instance`: runtime current workflow state; would fabricate active process truth.
- `sc.workflow.workitem`: runtime todo/completion carrier; not historical audit-safe.
- `sc.workflow.log`: requires runtime instance and node references; cannot preserve source rows independently.
- `sc.business.evidence`: requires runtime integer business_id and restricted evidence types; not safe as XML carrier.

## Decision

`{payload["carrier_decision"]}`
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen legacy approval workflow facts.")
    parser.add_argument("--asset-root", default=str(ASSET_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload = screen(Path(args.asset_root))
        write_json(OUTPUT_JSON, payload)
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    except (WorkflowFactScreenError, json.JSONDecodeError, OSError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("WORKFLOW_FACT_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print(
        "WORKFLOW_FACT_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "raw_rows": payload["raw_rows"],
                "loadable_rows": payload["loadable_rows"],
                "blocked_rows": payload["blocked_rows"],
                "matched_target_records": payload["matched_target_records"],
                "carrier_decision": payload["carrier_decision"],
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
