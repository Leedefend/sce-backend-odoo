#!/usr/bin/env python3
"""Attach ready adapter payloads to the fresh database replay manifest."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path.cwd()
MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_replay_manifest_v1.json"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_replay_manifest_adapter_refresh_result_v1.json"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_replay_manifest_adapter_refresh_report_v1.md"

ADAPTERS = {
    "partner_l4_anchor_completed": {
        "result": "artifacts/migration/fresh_db_partner_l4_replay_adapter_result_v1.json",
        "payload": "artifacts/migration/fresh_db_partner_l4_replay_payload_v1.csv",
        "expected_payload_rows": 4797,
    },
    "project_anchor_completed": {
        "result": "artifacts/migration/fresh_db_project_anchor_replay_adapter_result_v1.json",
        "payload": "artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv",
        "expected_payload_rows": 755,
    },
    "contract_partner_source_12_anchor_design": {
        "result": "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_adapter_result_v1.json",
        "payload": "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_payload_v1.csv",
        "expected_payload_rows": 12,
    },
}


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Fresh DB Replay Manifest Adapter Refresh Report v1

Status: {payload["status"]}

Task: `ITER-2026-04-15-FRESH-DB-REPLAY-MANIFEST-ADAPTER-REFRESH`

## Scope

Attach ready adapter payloads to the fresh database replay manifest without
creating a database, executing write scripts, or mutating business data.

## Result

- refreshed lanes: `{payload["refreshed_lanes"]}`
- missing adapter references: `{len(payload["missing_adapter_references"])}`
- adapter failures: `{len(payload["adapter_failures"])}`
- default-run lanes: `{payload["default_run_lanes"]}`
- high-risk default violations: `{len(payload["high_risk_default_violations"])}`
- DB writes: `0`

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing_refs: list[dict[str, str]] = []
    adapter_failures: list[dict[str, object]] = []
    refreshed_lanes = 0

    for lane in manifest.get("lanes", []):
        lane_id = lane.get("lane_id")
        spec = ADAPTERS.get(lane_id)
        if not spec:
            continue
        result_path = REPO_ROOT / spec["result"]
        payload_path = REPO_ROOT / spec["payload"]
        if not result_path.exists():
            missing_refs.append({"lane_id": lane_id, "missing": spec["result"]})
            continue
        if not payload_path.exists():
            missing_refs.append({"lane_id": lane_id, "missing": spec["payload"]})
            continue
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("status") != "PASS" or result.get("replay_payload_rows") != spec["expected_payload_rows"]:
            adapter_failures.append(
                {
                    "lane_id": lane_id,
                    "status": result.get("status"),
                    "expected_payload_rows": spec["expected_payload_rows"],
                    "actual_payload_rows": result.get("replay_payload_rows"),
                }
            )
            continue
        lane["status"] = "replay_ready_candidate"
        lane["default_run"] = False
        lane["replay_payloads"] = [spec["payload"]]
        lane["adapter_result_artifacts"] = [spec["result"]]
        lane.setdefault("aggregate_artifacts", [])
        if spec["result"] not in lane["aggregate_artifacts"]:
            lane["aggregate_artifacts"].append(spec["result"])
        lane.setdefault("expected_current_result", {})
        lane["expected_current_result"]["replay_payload_rows"] = spec["expected_payload_rows"]
        refreshed_lanes += 1

    manifest["status"] = "ADAPTER_PAYLOADS_DRY_RUN_READY"
    manifest["certification_status"] = "DRY_RUN_ADAPTER_PAYLOADS_READY"
    manifest["default_policy"]["execute_database_operations"] = False
    manifest["default_policy"]["execute_write_scripts"] = False
    manifest["default_policy"]["include_high_risk_lanes"] = False

    default_run_lanes = sum(1 for lane in manifest.get("lanes", []) if lane.get("default_run"))
    high_risk_default_violations = [
        lane["lane_id"]
        for lane in manifest.get("lanes", [])
        if lane.get("layer") == "L4_high_risk" and lane.get("default_run")
    ]
    status = (
        "PASS"
        if refreshed_lanes == len(ADAPTERS)
        and not missing_refs
        and not adapter_failures
        and default_run_lanes == 0
        and not high_risk_default_violations
        else "FAIL"
    )
    result_payload = {
        "status": status,
        "mode": "fresh_db_replay_manifest_adapter_refresh",
        "db_writes": 0,
        "database_operations": 0,
        "write_scripts_executed": 0,
        "refreshed_lanes": refreshed_lanes,
        "missing_adapter_references": missing_refs,
        "adapter_failures": adapter_failures,
        "default_run_lanes": default_run_lanes,
        "high_risk_default_violations": high_risk_default_violations,
        "decision": "manifest_adapter_payloads_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "next_step": "run fresh database replay runner dry-run, then open a dedicated fresh database operation contract",
    }
    write_json(MANIFEST, manifest)
    write_json(OUTPUT_JSON, result_payload)
    write_report(result_payload)
    print(
        "FRESH_DB_REPLAY_MANIFEST_ADAPTER_REFRESH="
        + json.dumps(
            {
                "status": status,
                "refreshed_lanes": refreshed_lanes,
                "missing_adapter_references": len(missing_refs),
                "adapter_failures": len(adapter_failures),
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
