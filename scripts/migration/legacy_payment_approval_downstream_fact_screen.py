#!/usr/bin/env python3
"""Screen approval evidence from downstream legacy payment business facts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from legacy_payment_approval_semantic_screen import (
    _match_payment_target,
    classify_legacy_row,
    target_semantic,
)
from legacy_workflow_audit_asset_generator import (
    build_target_index,
    clean,
    parse_sql_rows,
    run_sql,
)


OUTPUT_JSON = Path("artifacts/migration/legacy_payment_approval_downstream_fact_screen_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/legacy_payment_approval_downstream_fact_screen_rows_v1.csv")
OUTPUT_MD = Path("docs/migration_alignment/legacy_payment_approval_downstream_fact_screen_v1.md")


class DownstreamFactScreenError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DownstreamFactScreenError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "target_external_id",
        "target_lane",
        "final_approval_fact",
        "audit_semantic",
        "audit_rows",
        "audit_approved_rows",
        "workflow_trace_rows",
        "actual_outflow_count",
        "actual_outflow_amount",
        "outflow_detail_line_count",
        "receipt_invoice_line_count",
        "evidence_reason",
        "sample_downstream_external_ids",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in headers})


def money(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def _load_actual_outflow_evidence(asset_root: Path) -> dict[str, dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "amount": Decimal("0"), "samples": []})
    manifest = load_json(asset_root / "manifest/actual_outflow_external_id_manifest_v1.json")
    for row in manifest.get("records", []):
        if row.get("status") != "loadable":
            continue
        request_external_id = clean(row.get("request_external_id"))
        if not request_external_id:
            continue
        item = evidence[request_external_id]
        item["count"] += 1
        item["amount"] += money(row.get("amount"))
        if len(item["samples"]) < 5:
            item["samples"].append(clean(row.get("external_id")))
    return evidence


def _load_outflow_detail_counts(asset_root: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    manifest = load_json(asset_root / "manifest/outflow_request_line_external_id_manifest_v1.json")
    for row in manifest.get("records", []):
        if row.get("status") != "loadable":
            continue
        request_external_id = clean(row.get("outflow_request_external_id"))
        if request_external_id:
            counts[request_external_id] += 1
    return counts


def _load_receipt_invoice_counts(asset_root: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    manifest = load_json(asset_root / "manifest/receipt_invoice_line_external_id_manifest_v1.json")
    for row in manifest.get("records", []):
        if row.get("status") != "loadable":
            continue
        receipt_external_id = clean(row.get("receipt_external_id"))
        if receipt_external_id:
            counts[receipt_external_id] += 1
    return counts


def _format_amount(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def final_approval_fact(
    audit_semantic: str,
    target_lane: str,
    actual_outflow_count: int,
) -> tuple[str, str]:
    if audit_semantic in {"historical_approved", "historical_mixed"}:
        return "historical_approved", "explicit_legacy_audit_approval"
    if target_lane == "outflow_request" and actual_outflow_count > 0:
        return "historical_approved_by_downstream_business_fact", "actual_outflow_references_request"
    if audit_semantic == "historical_rejected_or_back":
        return "historical_rejected_or_back", "explicit_legacy_audit_reject_or_back"
    return "historical_pending_or_trace_only", "no_executed_downstream_business_fact"


def build_screen(asset_root: Path) -> dict[str, Any]:
    source_rows = parse_sql_rows(run_sql())
    source_index, any_index = build_target_index(asset_root)
    actual_outflow = _load_actual_outflow_evidence(asset_root)
    outflow_lines = _load_outflow_detail_counts(asset_root)
    receipt_invoice_lines = _load_receipt_invoice_counts(asset_root)

    target_classes: dict[str, Counter[str]] = defaultdict(Counter)
    target_lanes: dict[str, str] = {}
    blocked = Counter()

    for row in source_rows:
        match, match_key = _match_payment_target(row, source_index, any_index)
        if not match:
            if match_key:
                blocked[match_key] += 1
            continue
        target_external_id = clean(match.get("external_id"))
        target_classes[target_external_id][classify_legacy_row(row)] += 1
        target_lanes[target_external_id] = clean(match.get("lane"))

    evidence_rows: list[dict[str, Any]] = []
    final_counts: Counter[str] = Counter()
    final_by_lane: dict[str, Counter[str]] = defaultdict(Counter)
    downstream_approved = 0
    downstream_approved_trace_only = 0

    for target_external_id in sorted(target_classes):
        classes = target_classes[target_external_id]
        audit_semantic = target_semantic(classes)
        lane = target_lanes.get(target_external_id, "")
        actual = actual_outflow.get(target_external_id, {})
        actual_count = int(actual.get("count") or 0)
        final_fact, reason = final_approval_fact(audit_semantic, lane, actual_count)
        final_counts[final_fact] += 1
        final_by_lane[lane][final_fact] += 1
        if final_fact == "historical_approved_by_downstream_business_fact":
            downstream_approved += 1
            if audit_semantic == "historical_pending_or_trace_only":
                downstream_approved_trace_only += 1
        evidence_rows.append(
            {
                "target_external_id": target_external_id,
                "target_lane": lane,
                "final_approval_fact": final_fact,
                "audit_semantic": audit_semantic,
                "audit_rows": sum(classes.values()),
                "audit_approved_rows": classes.get("historical_approved", 0),
                "workflow_trace_rows": classes.get("workflow_trace_with_actor_time", 0)
                + classes.get("workflow_received_or_pending", 0)
                + classes.get("workflow_status_zero_trace", 0),
                "actual_outflow_count": actual_count,
                "actual_outflow_amount": _format_amount(actual.get("amount") or Decimal("0")),
                "outflow_detail_line_count": outflow_lines.get(target_external_id, 0),
                "receipt_invoice_line_count": receipt_invoice_lines.get(target_external_id, 0),
                "evidence_reason": reason,
                "sample_downstream_external_ids": ";".join(actual.get("samples") or []),
            }
        )

    rows_by_priority = sorted(
        evidence_rows,
        key=lambda row: (
            0 if row["final_approval_fact"] == "historical_approved_by_downstream_business_fact" else 1,
            row["target_lane"],
            row["target_external_id"],
        ),
    )

    summary = {
        "raw_workflow_rows": len(source_rows),
        "payment_distinct_targets": len(target_classes),
        "final_approval_fact_counts": dict(sorted(final_counts.items())),
        "final_approval_fact_by_lane": {
            lane: dict(sorted(counter.items()))
            for lane, counter in sorted(final_by_lane.items())
        },
        "downstream_business_fact_rule": {
            "rule": "target_lane=outflow_request and actual_outflow_count > 0",
            "semantic": "historical_approved_by_downstream_business_fact",
            "confidence": "high",
        },
        "downstream_approved_targets": downstream_approved,
        "downstream_approved_trace_only_targets": downstream_approved_trace_only,
        "structural_detail_only_policy": {
            "outflow_request_line": "not approval evidence by itself",
            "receipt_invoice_line": "not approval evidence by itself",
        },
        "blocked_match_counts": dict(sorted(blocked.items())),
        "top_evidence_rows": rows_by_priority[:50],
    }
    payload = {"status": "PASS", "summary": summary, "db_writes": 0}
    write_json(OUTPUT_JSON, payload)
    write_csv(OUTPUT_CSV, rows_by_priority)
    write_report(OUTPUT_MD, payload)
    return payload


def write_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Legacy Payment Approval Downstream Fact Screen v1",
        "",
        "## Scope",
        "- Source: legacy approval audit rows plus migration manifests for downstream payment facts.",
        "- Strong downstream evidence: actual outflow rows that reference an outflow payment request.",
        "- Structural detail rows are reported but not counted as approval evidence by themselves.",
        "- Mode: read-only screen; no Odoo business records are mutated.",
        "",
        "## Counts",
        f"- Raw workflow rows: {summary['raw_workflow_rows']}",
        f"- Payment distinct targets: {summary['payment_distinct_targets']}",
        f"- Final approval facts: `{json.dumps(summary['final_approval_fact_counts'], ensure_ascii=False, sort_keys=True)}`",
        f"- Downstream-approved targets: {summary['downstream_approved_targets']}",
        f"- Downstream-approved trace-only targets: {summary['downstream_approved_trace_only_targets']}",
        "",
        "## Safe Interpretation",
        "- Explicit old audit approval remains historical approval.",
        "- An outflow request referenced by actual outflow is historical approval by downstream business fact.",
        "- Outflow detail lines and receipt invoice lines are structural facts, not approval proof by themselves.",
        "",
        "## Key Finding",
        "Old audit status may be incomplete, but actual outflow rows provide direct business evidence that the referenced payment request passed approval and reached execution.",
        "",
        "## Top Downstream Evidence Rows",
    ]
    for row in summary["top_evidence_rows"][:10]:
        lines.append(
            "- {target} / lane={lane} / final={final} / audit={audit} / actual_outflows={count} / amount={amount}".format(
                target=row["target_external_id"],
                lane=row["target_lane"],
                final=row["final_approval_fact"],
                audit=row["audit_semantic"],
                count=row["actual_outflow_count"],
                amount=row["actual_outflow_amount"],
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen downstream business facts for legacy payment approval.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload = build_screen(Path(args.asset_root))
    except Exception as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0}
        write_json(OUTPUT_JSON, result)
        print("LEGACY_PAYMENT_APPROVAL_DOWNSTREAM_FACT_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_PAYMENT_APPROVAL_DOWNSTREAM_FACT_SCREEN=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
