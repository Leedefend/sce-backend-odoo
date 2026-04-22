#!/usr/bin/env python3
"""Generate implementation plan for fresh-db replay adapters."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path.cwd()
MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_replay_manifest_v1.json"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_replay_adapter_plan_v1.json"
OUTPUT_DOC = REPO_ROOT / "docs/migration_alignment/fresh_db_replay_adapter_plan_v1.md"


ADAPTER_STRATEGY = {
    "partner_l4_anchor_completed": {
        "adapter_task": "FRESH-DB-REPLAY-PARTNER-L4-ADAPTER",
        "adapter_type": "consolidated_anchor_replay",
        "write_policy": "idempotent_create_only_by_legacy_partner_key",
        "required_outputs": [
            "single partner anchor replay payload",
            "rollback targets",
            "aggregate source/target review",
            "discard/hold ledger"
        ],
        "batch_size_rule": "500-1000 anchors per low-risk batch after dry-run"
    },
    "project_anchor_completed": {
        "adapter_task": "FRESH-DB-REPLAY-PROJECT-ANCHOR-ADAPTER",
        "adapter_type": "consolidated_project_replay",
        "write_policy": "idempotent_create_only_by_legacy_project_id",
        "required_outputs": [
            "single project anchor replay payload",
            "rollback targets",
            "aggregate source/target review",
            "source-missing contract blocker ledger"
        ],
        "batch_size_rule": "500-1000 projects when precheck is clean"
    },
    "contract_partner_source_12_anchor_design": {
        "adapter_task": "FRESH-DB-REPLAY-CONTRACT-PARTNER-12-ANCHOR-ADAPTER",
        "adapter_type": "new_anchor_recovery_replay",
        "write_policy": "idempotent_create_only_by company::counterparty_text",
        "required_outputs": [
            "12 partner anchor write payload",
            "rollback targets",
            "post-write partner anchor review",
            "57 contract retry readiness packet"
        ],
        "batch_size_rule": "single 12-anchor batch"
    }
}


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_doc(payload: dict[str, object]) -> None:
    adapter_lines = []
    for adapter in payload["adapters"]:
        adapter_lines.extend(
            [
                f"### {adapter['lane_id']}",
                "",
                f"- status: `{adapter['source_status']}`",
                f"- adapter task: `{adapter['adapter_task']}`",
                f"- adapter type: `{adapter['adapter_type']}`",
                f"- write policy: `{adapter['write_policy']}`",
                f"- batch size: `{adapter['batch_size_rule']}`",
                f"- required outputs: `{', '.join(adapter['required_outputs'])}`",
                "",
            ]
        )
    text = f"""# Fresh DB Replay Adapter Plan v1

Status: {payload["status"]}

Task: `ITER-2026-04-15-FRESH-DB-REPLAY-ADAPTER-PLAN`

## Scope

Convert replay manifest gaps into adapter implementation tasks. This batch does
not create a database, execute write scripts, or mutate business data.

## Summary

- manifest lanes: `{payload["manifest_lane_count"]}`
- adapter lanes: `{payload["adapter_lane_count"]}`
- blocked high-risk lanes: `{payload["excluded_high_risk_lanes"]}`
- database operations: `0`

## Adapter Plan

{chr(10).join(adapter_lines)}
## Execution Order

1. Implement partner L4 consolidated replay adapter.
2. Implement project anchor consolidated replay adapter.
3. Implement 12-anchor contract partner recovery adapter.
4. Re-run manifest dry-run and mark certified adapters as `replay_ready_candidate`.
5. Open fresh database operation contract only after adapter dry-run passes.

## Stop Rules

- Do not include payment, settlement, accounting, ACL, manifest, or module
  install lanes.
- Do not run write scripts from adapter planning.
- Do not create/drop databases from adapter planning.
"""
    OUTPUT_DOC.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DOC.write_text(text, encoding="utf-8")


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    adapters = []
    excluded_high_risk = 0
    for lane in manifest["lanes"]:
        lane_id = lane["lane_id"]
        if lane["status"] == "excluded_high_risk":
            excluded_high_risk += 1
            continue
        if lane["status"] not in {"needs_adapter", "design_only"}:
            continue
        strategy = ADAPTER_STRATEGY.get(lane_id)
        if not strategy:
            adapters.append(
                {
                    "lane_id": lane_id,
                    "source_status": lane["status"],
                    "adapter_task": "UNDECLARED",
                    "blocking_error": "missing adapter strategy"
                }
            )
            continue
        adapters.append(
            {
                "lane_id": lane_id,
                "source_status": lane["status"],
                **strategy,
            }
        )

    errors = [adapter for adapter in adapters if adapter.get("blocking_error")]
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "mode": "fresh_db_replay_adapter_plan",
        "db_writes": 0,
        "database_operations": 0,
        "write_scripts_executed": 0,
        "manifest": str(MANIFEST),
        "manifest_lane_count": len(manifest["lanes"]),
        "adapter_lane_count": len(adapters),
        "excluded_high_risk_lanes": excluded_high_risk,
        "adapters": adapters,
        "errors": errors,
        "decision": "adapter_plan_ready" if not errors else "STOP_REVIEW_REQUIRED",
        "next_step": "implement partner L4 consolidated replay adapter first"
    }
    write_json(OUTPUT_JSON, payload)
    write_doc(payload)
    print(
        "FRESH_DB_REPLAY_ADAPTER_PLAN="
        + json.dumps(
            {
                "status": payload["status"],
                "adapter_lanes": payload["adapter_lane_count"],
                "excluded_high_risk_lanes": excluded_high_risk,
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
