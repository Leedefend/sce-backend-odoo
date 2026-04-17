#!/usr/bin/env python3
"""Screen legacy payment approval semantics from S_Execute_Approval."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from legacy_workflow_audit_asset_generator import (
    build_target_index,
    clean,
    normalize_source_table,
    parse_sql_rows,
    run_sql,
)


OUTPUT_JSON = Path("artifacts/migration/legacy_payment_approval_semantic_screen_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/legacy_payment_approval_semantic_screen_rows_v1.csv")
OUTPUT_MD = Path("docs/migration_alignment/legacy_payment_approval_semantic_screen_v1.md")

PAYMENT_TARGET_MODEL = "payment.request"
APPROVED_STATUSES = {"1", "2", "3"}
REJECTED_STATUSES = {"-1", "4", "5"}
EMPTY_OR_NEUTRAL_BACK_TYPES = {"", "0", "-1"}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "semantic_classification",
        "legacy_source_table",
        "target_lane",
        "legacy_status",
        "legacy_back_type",
        "legacy_detail_status_id",
        "legacy_detail_step_id",
        "legacy_setup_step_id",
        "legacy_template_id",
        "legacy_step_name",
        "legacy_template_name",
        "legacy_approval_type",
        "row_count",
        "distinct_targets",
        "sample_workflow_ids",
        "sample_target_external_ids",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in headers})


def _match_payment_target(row: dict[str, str], source_index, any_index) -> tuple[dict[str, str] | None, str]:
    source_table = normalize_source_table(row.get("SJBMC", ""))
    djid = clean(row.get("DJID"))
    business_id = clean(row.get("business_Id"))
    matches: list[dict[str, str]] = []
    match_key = ""
    if djid:
        matches = any_index.get(djid, [])
        match_key = "DJID"
    if not matches and source_table and business_id:
        matches = source_index.get((source_table, business_id), [])
        match_key = "SJBMC_business_Id"
    if not matches and business_id:
        matches = any_index.get(business_id, [])
        match_key = "business_Id_any"
    if not matches:
        return None, ""
    targets = {item["external_id"] for item in matches}
    if len(targets) > 1:
        return None, "ambiguous_target"
    match = matches[0]
    if match.get("target_model") != PAYMENT_TARGET_MODEL:
        return None, "non_payment_target"
    return match, match_key


def classify_legacy_row(row: dict[str, str]) -> str:
    status = clean(row.get("f_SPZT"))
    back_type = clean(row.get("f_Back_YJLX"))
    approved_at = clean(row.get("f_SPSJ"))
    received_at = clean(row.get("RecevieTime"))
    approval_note = clean(row.get("f_SPYJ"))
    actor = clean(row.get("f_LRR"))

    if back_type not in EMPTY_OR_NEUTRAL_BACK_TYPES:
        return "historical_rejected_or_back"
    if status in REJECTED_STATUSES:
        return "historical_rejected_or_back"
    if status in APPROVED_STATUSES:
        return "historical_approved"
    if status == "0":
        if approved_at and (actor or approval_note):
            return "workflow_trace_with_actor_time"
        if received_at:
            return "workflow_received_or_pending"
        return "workflow_status_zero_trace"
    return "unknown_or_unmapped"


def target_semantic(classes: Counter[str]) -> str:
    has_approved = bool(classes.get("historical_approved"))
    has_rejected = bool(classes.get("historical_rejected_or_back"))
    if has_approved and has_rejected:
        return "historical_mixed"
    if has_rejected:
        return "historical_rejected_or_back"
    if has_approved:
        return "historical_approved"
    if classes:
        return "historical_pending_or_trace_only"
    return "none"


def _combo_key(row: dict[str, str], match: dict[str, str], semantic: str) -> tuple[str, ...]:
    return (
        semantic,
        normalize_source_table(row.get("SJBMC", "")),
        clean(match.get("lane")),
        clean(row.get("f_SPZT")),
        clean(row.get("f_Back_YJLX")),
        clean(row.get("S_Execute_DetailStatus_Id")),
        clean(row.get("S_Execute_Detail_Step_Id")),
        clean(row.get("S_Setup_Step_Id")),
        clean(row.get("S_Setup_Template_Id")),
        clean(row.get("setup_step_name")),
        clean(row.get("template_name")) or clean(row.get("template_business_name")),
        clean(row.get("SPLX")),
    )


def _combo_row(key: tuple[str, ...], count: int, targets: set[str], workflow_ids: list[str], target_ids: list[str]) -> dict[str, Any]:
    return {
        "semantic_classification": key[0],
        "legacy_source_table": key[1],
        "target_lane": key[2],
        "legacy_status": key[3],
        "legacy_back_type": key[4],
        "legacy_detail_status_id": key[5],
        "legacy_detail_step_id": key[6],
        "legacy_setup_step_id": key[7],
        "legacy_template_id": key[8],
        "legacy_step_name": key[9],
        "legacy_template_name": key[10],
        "legacy_approval_type": key[11],
        "row_count": count,
        "distinct_targets": len(targets),
        "sample_workflow_ids": ";".join(workflow_ids[:5]),
        "sample_target_external_ids": ";".join(target_ids[:5]),
    }


def build_screen(asset_root: Path) -> dict[str, Any]:
    source_rows = parse_sql_rows(run_sql())
    source_index, any_index = build_target_index(asset_root)

    payment_rows = 0
    blocked = Counter()
    semantic_counts = Counter()
    lane_counts = Counter()
    status_counts = Counter()
    combo_counts = Counter()
    combo_targets: dict[tuple[str, ...], set[str]] = defaultdict(set)
    combo_workflow_samples: dict[tuple[str, ...], list[str]] = defaultdict(list)
    combo_target_samples: dict[tuple[str, ...], list[str]] = defaultdict(list)
    target_classes: dict[str, Counter[str]] = defaultdict(Counter)
    target_lanes: dict[str, str] = {}

    for row in source_rows:
        match, match_key = _match_payment_target(row, source_index, any_index)
        if not match:
            if match_key:
                blocked[match_key] += 1
            continue
        payment_rows += 1
        semantic = classify_legacy_row(row)
        target_external_id = clean(match.get("external_id"))
        lane = clean(match.get("lane"))
        semantic_counts[semantic] += 1
        lane_counts[lane] += 1
        status_counts[(clean(row.get("f_SPZT")), clean(row.get("f_Back_YJLX")), semantic)] += 1
        target_classes[target_external_id][semantic] += 1
        target_lanes[target_external_id] = lane

        key = _combo_key(row, match, semantic)
        combo_counts[key] += 1
        combo_targets[key].add(target_external_id)
        if len(combo_workflow_samples[key]) < 5:
            combo_workflow_samples[key].append(clean(row.get("Id")))
        if len(combo_target_samples[key]) < 5:
            combo_target_samples[key].append(target_external_id)

    target_semantic_counts = Counter(target_semantic(classes) for classes in target_classes.values())
    target_semantic_by_lane: dict[str, Counter[str]] = defaultdict(Counter)
    for target_id, classes in target_classes.items():
        target_semantic_by_lane[target_lanes.get(target_id, "")][target_semantic(classes)] += 1

    combo_rows = [
        _combo_row(
            key,
            count,
            combo_targets[key],
            combo_workflow_samples[key],
            combo_target_samples[key],
        )
        for key, count in combo_counts.most_common()
    ]

    summary = {
        "raw_workflow_rows": len(source_rows),
        "payment_target_rows": payment_rows,
        "payment_distinct_targets": len(target_classes),
        "semantic_row_counts": dict(sorted(semantic_counts.items())),
        "lane_row_counts": dict(sorted(lane_counts.items())),
        "target_semantic_counts": dict(sorted(target_semantic_counts.items())),
        "target_semantic_by_lane": {
            lane: dict(sorted(counter.items()))
            for lane, counter in sorted(target_semantic_by_lane.items())
        },
        "status_back_semantic_counts": [
            {
                "legacy_status": key[0],
                "legacy_back_type": key[1],
                "semantic_classification": key[2],
                "row_count": count,
            }
            for key, count in status_counts.most_common(30)
        ],
        "blocked_match_counts": dict(sorted(blocked.items())),
        "safe_mapping_rules": [
            {
                "rule": "f_Back_YJLX not in ['', '0', '-1'] or f_SPZT in [-1, 4, 5]",
                "semantic": "historical_rejected_or_back",
                "confidence": "high",
            },
            {
                "rule": "f_SPZT in [1, 2, 3]",
                "semantic": "historical_approved",
                "confidence": "high",
            },
            {
                "rule": "f_SPZT = 0 and f_Back_YJLX in ['', '0', '-1']",
                "semantic": "historical_pending_or_trace_only",
                "confidence": "safe_non_approved",
            },
        ],
        "top_combo_rows": combo_rows[:30],
    }
    payload = {"status": "PASS", "summary": summary, "db_writes": 0}
    write_json(OUTPUT_JSON, payload)
    write_csv(OUTPUT_CSV, combo_rows)
    write_report(OUTPUT_MD, payload)
    return payload


def write_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Legacy Payment Approval Semantic Screen v1",
        "",
        "## Scope",
        "- Source: `LegacyDb.dbo.S_Execute_Approval` joined with setup step/template names.",
        "- Target: rows that resolve to imported `payment.request` assets through migration manifests.",
        "- Mode: read-only semantic screen; no Odoo business records are mutated.",
        "",
        "## Counts",
        f"- Raw workflow rows: {summary['raw_workflow_rows']}",
        f"- Payment-target workflow rows: {summary['payment_target_rows']}",
        f"- Payment distinct targets: {summary['payment_distinct_targets']}",
        f"- Row semantics: `{json.dumps(summary['semantic_row_counts'], ensure_ascii=False, sort_keys=True)}`",
        f"- Target semantics: `{json.dumps(summary['target_semantic_counts'], ensure_ascii=False, sort_keys=True)}`",
        "",
        "## Safe Interpretation",
        "- `f_SPZT in [1, 2, 3]` is treated as historical approval.",
        "- Non-neutral `f_Back_YJLX` or rejected status values are treated as historical reject/back.",
        "- `f_SPZT = 0` with neutral back type is not treated as approval; it remains pending/trace-only.",
        "",
        "## Key Finding",
        "Most payment-target rows are legacy workflow traces with `f_SPZT=0` and neutral back type. They prove workflow existence, not final approval.",
        "",
        "## Next Decision",
        "A future write batch may surface target-level `historical_approved` or `historical_pending_or_trace_only`, but should not convert trace-only rows into current workflow approval.",
        "",
        "## Top Field Combinations",
    ]
    for row in summary["top_combo_rows"][:10]:
        lines.append(
            "- {semantic} / lane={lane} / status={status} / back={back} / rows={rows} / targets={targets} / step={step}".format(
                semantic=row["semantic_classification"],
                lane=row["target_lane"],
                status=row["legacy_status"],
                back=row["legacy_back_type"],
                rows=row["row_count"],
                targets=row["distinct_targets"],
                step=row["legacy_step_name"] or "-",
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen legacy payment approval semantics.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload = build_screen(Path(args.asset_root))
    except Exception as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0}
        write_json(OUTPUT_JSON, result)
        print("LEGACY_PAYMENT_APPROVAL_SEMANTIC_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_PAYMENT_APPROVAL_SEMANTIC_SCREEN=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
