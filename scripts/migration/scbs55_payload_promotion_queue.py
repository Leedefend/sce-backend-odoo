#!/usr/bin/env python3
"""Create a lane-level promotion queue from the SCBS55 replay gap report."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
GAP = ROOT / "docs/migration_alignment/scbs55_replay_payload_gap_report_v1.json"
OUTPUT_JSON = ROOT / "docs/migration_alignment/scbs55_payload_promotion_queue_v1.json"
OUTPUT_MD = ROOT / "docs/migration_alignment/scbs55_payload_promotion_queue_v1.md"


LANES = [
    ("foundation_manifest", 10, ("manifest_dry_run", "replay_payload_precheck")),
    (
        "user_security_context",
        20,
        (
            "legacy_user",
            "real_user",
            "user_rebuild",
            "legacy_task_evidence",
            "legacy_attendance",
            "legacy_personnel",
            "legacy_salary",
            "user_asset_verify",
        ),
    ),
    (
        "master_partner_project",
        30,
        (
            "partner",
            "project_anchor",
            "project_member",
            "project_lifecycle_continuity",
            "project_migration_field_continuity",
        ),
    ),
    ("contract_and_supplier", 40, ("contract", "supplier")),
    ("receipt_income", 50, ("receipt", "legacy_receipt", "receipt_income", "income_fact")),
    ("outflow_payment", 60, ("outflow", "actual_outflow", "payment")),
    (
        "finance_accounting",
        70,
        (
            "legacy_account",
            "legacy_invoice",
            "legacy_tax",
            "legacy_fund",
            "legacy_expense",
            "legacy_payment",
            "legacy_self_funding",
            "legacy_financing",
            "legacy_deduction",
        ),
    ),
    ("materials_tender_purchase", 80, ("legacy_material", "legacy_tender", "legacy_purchase", "legacy_labor", "legacy_equipment")),
    ("attachments_workflow", 90, ("legacy_file", "legacy_attachment", "legacy_workflow", "history_project_member_attachment")),
    ("formal_projections", 100, ("projection", "normalize", "treasury", "invoice", "construction", "fund", "office", "hr", "document")),
    ("runtime_probes", 110, ("probe", "usability")),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def lane_for_step(step: str, kind: str) -> str:
    for lane, _priority, markers in LANES:
        if any(marker in step for marker in markers):
            return lane
    if kind == "formal_projection":
        return "formal_projections"
    if kind == "probe":
        return "runtime_probes"
    return "unclassified"


def lane_priority(lane: str) -> int:
    for item, priority, _markers in LANES:
        if item == lane:
            return priority
    return 999


def build_queue() -> dict[str, Any]:
    gap = load_json(GAP)
    steps = gap.get("steps") if isinstance(gap.get("steps"), list) else []
    missing_by_step = defaultdict(list)
    for item in gap.get("missing_required_inputs", []):
        if isinstance(item, dict):
            missing_by_step[item.get("step")].append(item.get("path"))
    runtime_by_step = defaultdict(list)
    for item in gap.get("runtime_outputs_not_currently_packaged", []):
        if isinstance(item, dict):
            runtime_by_step[item.get("step")].append(item.get("path"))

    lane_rows: dict[str, dict[str, Any]] = {}
    for step in steps:
        if not isinstance(step, dict):
            continue
        lane = lane_for_step(str(step.get("step") or ""), str(step.get("kind") or ""))
        row = lane_rows.setdefault(
            lane,
            {
                "lane": lane,
                "priority": lane_priority(lane),
                "step_count": 0,
                "required_step_count": 0,
                "optional_step_count": 0,
                "missing_required_input_count": 0,
                "runtime_output_backlog_count": 0,
                "step_kinds": Counter(),
                "missing_required_inputs": [],
                "runtime_output_backlog": [],
                "sample_missing_inputs": [],
                "sample_runtime_outputs": [],
            },
        )
        row["step_count"] += 1
        if step.get("scope") == "required":
            row["required_step_count"] += 1
        else:
            row["optional_step_count"] += 1
        row["step_kinds"][step.get("kind") or "other"] += 1
        step_name = step.get("step")
        missing = missing_by_step.get(step_name, [])
        runtime = runtime_by_step.get(step_name, [])
        row["missing_required_input_count"] += len(missing)
        row["runtime_output_backlog_count"] += len(runtime)
        for path in missing:
            row["missing_required_inputs"].append({"step": step_name, "path": path})
            if len(row["sample_missing_inputs"]) < 10:
                row["sample_missing_inputs"].append({"step": step_name, "path": path})
        for path in runtime:
            row["runtime_output_backlog"].append({"step": step_name, "path": path})
            if len(row["sample_runtime_outputs"]) < 10:
                row["sample_runtime_outputs"].append({"step": step_name, "path": path})

    queue = []
    for row in lane_rows.values():
        row["step_kinds"] = dict(sorted(row["step_kinds"].items()))
        if row["missing_required_input_count"]:
            decision = "promote_required_inputs_first"
        elif row["runtime_output_backlog_count"]:
            decision = "promote_runtime_outputs_after_required_inputs"
        else:
            decision = "covered_in_current_workspace"
        row["decision"] = decision
        queue.append(row)
    queue.sort(key=lambda item: (item["priority"], item["lane"]))
    return {
        "queue_version": "scbs55_payload_promotion_queue_v1",
        "status": "PASS",
        "source_gap_report": str(GAP.relative_to(ROOT)),
        "lane_count": len(queue),
        "total_missing_required_inputs": sum(row["missing_required_input_count"] for row in queue),
        "total_runtime_output_backlog": sum(row["runtime_output_backlog_count"] for row in queue),
        "queue": queue,
        "decision": "promote payloads lane-by-lane in priority order; release-package verification remains the blocking gate",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    rows = []
    for row in payload["queue"]:
        rows.append(
            "| {priority} | {lane} | {step_count} | {missing_required_input_count} | {runtime_output_backlog_count} | {decision} |".format(
                **row
            )
        )
    details = []
    for row in payload["queue"]:
        details.append(f"### {row['priority']} {row['lane']}")
        details.append("")
        details.append(f"- steps: `{row['step_count']}`")
        details.append(f"- missing required inputs: `{row['missing_required_input_count']}`")
        details.append(f"- runtime output backlog: `{row['runtime_output_backlog_count']}`")
        if row["sample_missing_inputs"]:
            details.append("- sample missing inputs:")
            details.extend(f"  - `{item['step']}` `{item['path']}`" for item in row["sample_missing_inputs"][:5])
        if row["sample_runtime_outputs"]:
            details.append("- sample runtime outputs:")
            details.extend(f"  - `{item['step']}` `{item['path']}`" for item in row["sample_runtime_outputs"][:5])
        details.append("")
    return f"""# SCBS55 Payload Promotion Queue v1

Status: `{payload["status"]}`

Source: `{payload["source_gap_report"]}`

## Summary

- lanes: `{payload["lane_count"]}`
- missing required inputs: `{payload["total_missing_required_inputs"]}`
- runtime output backlog: `{payload["total_runtime_output_backlog"]}`

## Queue

| Priority | Lane | Steps | Missing required inputs | Runtime output backlog | Decision |
|---:|---|---:|---:|---:|---|
{chr(10).join(rows)}

## Lane Details

{chr(10).join(details)}
## Decision

`{payload["decision"]}`
"""


def main() -> int:
    payload = build_queue()
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(
        "SCBS55_PAYLOAD_PROMOTION_QUEUE="
        + json.dumps(
            {
                "status": payload["status"],
                "lanes": payload["lane_count"],
                "missing_required_inputs": payload["total_missing_required_inputs"],
                "runtime_output_backlog": payload["total_runtime_output_backlog"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
