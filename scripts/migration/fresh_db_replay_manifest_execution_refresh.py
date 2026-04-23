#!/usr/bin/env python3
"""Refresh fresh DB replay manifest with execution results."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path.cwd()
MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_replay_manifest_v1.json"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_replay_manifest_execution_refresh_result_v1.json"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_replay_manifest_execution_refresh_report_v1.md"
TASK_ID = "ITER-2026-04-15-FRESH-DB-REPLAY-MANIFEST-RECEIPT-LANE-NORMALIZE"

RESULTS = {
    "partner_l4_anchor_completed": {
        "path": "artifacts/migration/fresh_db_partner_l4_replay_write_result_v1.json",
        "status": "fresh_replay_executed",
        "expected_key": "created_rows",
        "expected_value": 4797,
    },
    "project_anchor_completed": {
        "path": "artifacts/migration/fresh_db_project_anchor_replay_write_result_v1.json",
        "status": "fresh_replay_executed",
        "expected_key": "created_rows",
        "expected_value": 755,
    },
    "project_member_neutral_completed": {
        "path": "artifacts/migration/fresh_db_project_member_neutral_replay_write_result_v1.json",
        "status": "fresh_replay_executed",
        "expected_key": "created_rows",
        "expected_value": 7389,
    },
    "contract_partner_source_12_anchor_design": {
        "path": "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_recovery_write_result_v1.json",
        "status": "fresh_replay_executed",
        "expected_key": "resolved_anchor_count",
        "expected_value": 12,
    },
    "contract_header_completed_1332": {
        "path": "artifacts/migration/fresh_db_contract_remaining_write_result_v1.json",
        "status": "fresh_replay_executed",
        "expected_key": "created_rows",
        "expected_value": 1332,
    },
    "receipt_header_pending": {
        "path": "artifacts/migration/fresh_db_receipt_core_write_result_v1.json",
        "status": "fresh_replay_executed",
        "expected_key": "created_rows",
        "expected_value": 1683,
    },
}
PREREQUISITES = {
    "core_tax_prerequisite": {
        "path": "artifacts/migration/fresh_db_core_tax_prereq_materialize_result_v1.json",
        "expected_key": "missing_required_taxes",
        "expected_value": [],
    }
}
ADDITIONAL_RESULTS = {
    "contract_header_retry_57": {
        "path": "artifacts/migration/fresh_db_contract_57_retry_write_result_v1.json",
        "expected_key": "created_rows",
        "expected_value": 57,
    },
    "contract_missing_partner_anchors": {
        "path": "artifacts/migration/fresh_db_contract_missing_partner_anchor_write_result_v1.json",
        "expected_key": "resolved_anchor_count",
        "expected_value": 95,
    },
    "receipt_core_receive_requests": {
        "path": "artifacts/migration/fresh_db_receipt_core_write_result_v1.json",
        "expected_key": "created_rows",
        "expected_value": 1683,
    },
}


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Fresh DB Replay Manifest Execution Refresh Report V1

Status: {payload["status"]}

Task: `{TASK_ID}`

## Scope

Refresh the replay manifest with already completed fresh database execution
results. This batch performs no database reads or writes.

## Result

- execution lanes refreshed: `{payload["execution_lanes_refreshed"]}`
- prerequisite results attached: `{payload["prerequisites_attached"]}`
- contract header historical rows: `{payload["contract_header_historical_rows"]}`
- contract header retry rows: `{payload["contract_header_retry_rows"]}`
- contract header total rows: `{payload["contract_header_total_rows"]}`
- receipt core rows: `{payload["receipt_core_rows"]}`
- manifest default-run lanes: `{payload["default_run_lanes"]}`
- DB writes: `0`

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    manifest = read_json(MANIFEST)
    lanes = {lane["lane_id"]: lane for lane in manifest.get("lanes", [])}
    errors: list[dict[str, object]] = []
    refreshed = 0
    contract_header_historical_rows = 0

    for lane_id, spec in RESULTS.items():
        lane = lanes.get(lane_id)
        if not lane:
            errors.append({"lane_id": lane_id, "error": "missing_manifest_lane"})
            continue
        result_path = REPO_ROOT / spec["path"]
        if not result_path.exists():
            errors.append({"lane_id": lane_id, "error": "missing_result", "path": spec["path"]})
            continue
        result = read_json(result_path)
        if result.get("status") != "PASS":
            errors.append({"lane_id": lane_id, "error": "result_not_pass", "status": result.get("status")})
            continue
        if result.get(spec["expected_key"]) != spec["expected_value"]:
            errors.append(
                {
                    "lane_id": lane_id,
                    "error": "unexpected_result_count",
                    "key": spec["expected_key"],
                    "expected": spec["expected_value"],
                    "actual": result.get(spec["expected_key"]),
                }
            )
            continue
        lane["status"] = spec["status"]
        lane["default_run"] = False
        if lane_id == "contract_header_completed_1332":
            lane["fresh_db_execution_artifacts"] = [spec["path"]]
        else:
            lane.setdefault("fresh_db_execution_artifacts", [])
        if spec["path"] not in lane["fresh_db_execution_artifacts"]:
            lane["fresh_db_execution_artifacts"].append(spec["path"])
        lane.setdefault("fresh_db_execution_result", {})
        lane["fresh_db_execution_result"].update(
            {
                "database": result.get("database", "sc_migration_fresh"),
                spec["expected_key"]: spec["expected_value"],
                "db_writes": result.get("cumulative_created_rows", result.get("db_writes", result.get("created_rows", 0))),
                "demo_targets_executed": result.get("demo_targets_executed", 0),
            }
        )
        if lane_id == "contract_header_completed_1332":
            contract_header_historical_rows = spec["expected_value"]
            lane["fresh_db_execution_result"].pop("partial_of", None)
            lane["fresh_db_execution_result"].pop("remaining_rows", None)
        if lane_id == "receipt_header_pending":
            lane["target_model"] = "payment.request"
            lane["expected_current_result"] = {"receipt_core_rows": spec["expected_value"]}
            lane["reason"] = "core receipt rows replayed as draft receive requests; settlement/accounting remain out of scope"
        refreshed += 1

    prerequisites_attached = 0
    manifest.setdefault("fresh_db_prerequisites", {})
    for key, spec in PREREQUISITES.items():
        result_path = REPO_ROOT / spec["path"]
        if not result_path.exists():
            errors.append({"prerequisite": key, "error": "missing_result", "path": spec["path"]})
            continue
        result = read_json(result_path)
        if result.get("status") != "PASS" or result.get(spec["expected_key"]) != spec["expected_value"]:
            errors.append({"prerequisite": key, "error": "prerequisite_not_ready"})
            continue
        manifest["fresh_db_prerequisites"][key] = {
            "status": "materialized",
            "artifact": spec["path"],
            "database": result.get("database", "sc_migration_fresh"),
            "demo_targets_executed": result.get("demo_targets_executed", 0),
            "transaction_rows_created": result.get("transaction_rows_created", 0),
        }
        prerequisites_attached += 1

    additional_results_attached = 0
    contract_header_retry_rows = 0
    contract_missing_partner_anchor_rows = 0
    receipt_core_rows = 0
    manifest.setdefault("fresh_db_additional_results", {})
    for key, spec in ADDITIONAL_RESULTS.items():
        result_path = REPO_ROOT / spec["path"]
        if not result_path.exists():
            errors.append({"additional_result": key, "error": "missing_result", "path": spec["path"]})
            continue
        result = read_json(result_path)
        if result.get("status") != "PASS" or result.get(spec["expected_key"]) != spec["expected_value"]:
            errors.append({"additional_result": key, "error": "additional_result_not_ready"})
            continue
        manifest["fresh_db_additional_results"][key] = {
            "status": "executed",
            "artifact": spec["path"],
            "database": result.get("database", "sc_migration_fresh"),
            spec["expected_key"]: spec["expected_value"],
            "demo_targets_executed": result.get("demo_targets_executed", 0),
        }
        if key == "contract_header_retry_57":
            contract_header_retry_rows = spec["expected_value"]
        if key == "contract_missing_partner_anchors":
            contract_missing_partner_anchor_rows = spec["expected_value"]
        if key == "receipt_core_receive_requests":
            receipt_core_rows = spec["expected_value"]
        additional_results_attached += 1

    manifest["status"] = "FRESH_DB_REPLAY_PARTIAL_EXECUTED"
    manifest["certification_status"] = "FRESH_DB_REPLAY_PARTIAL_EXECUTED_NO_DEMO"
    manifest["default_policy"]["execute_database_operations"] = False
    manifest["default_policy"]["execute_write_scripts"] = False
    manifest["default_policy"]["include_high_risk_lanes"] = False
    manifest["fresh_db_execution_summary"] = {
        "database": "sc_migration_fresh",
        "demo_modules_installed": False,
        "partner_l4_rows": 4797,
        "project_anchor_rows": 755,
        "project_member_neutral_rows": 7389,
        "contract_partner_anchor_rows": 12,
        "contract_missing_partner_anchor_rows": contract_missing_partner_anchor_rows,
        "contract_header_retry_rows": contract_header_retry_rows,
        "contract_header_historical_rows": contract_header_historical_rows,
        "contract_header_total_rows": contract_header_historical_rows + contract_header_retry_rows,
        "contract_header_full_target_rows": 1332,
        "contract_header_remaining_rows": 0,
        "receipt_core_rows": receipt_core_rows,
        "receipt_core_target_model": "payment.request",
        "receipt_core_target_type": "receive",
        "contract_line_rows": 0,
        "payment_rows": 0,
        "settlement_rows": 0,
        "accounting_rows": 0,
    }

    default_run_lanes = sum(1 for lane in manifest.get("lanes", []) if lane.get("default_run"))
    contract_replay_coverage_overstated = (contract_header_historical_rows, contract_header_retry_rows) != (1332, 57)
    status = (
        "PASS"
        if refreshed == len(RESULTS)
        and prerequisites_attached == len(PREREQUISITES)
        and additional_results_attached == len(ADDITIONAL_RESULTS)
        and not errors
        and default_run_lanes == 0
        and not contract_replay_coverage_overstated
        else "FAIL"
    )
    payload = {
        "status": status,
        "mode": "fresh_db_replay_manifest_execution_refresh",
        "db_writes": 0,
        "database_operations": 0,
        "write_scripts_executed": 0,
        "execution_lanes_refreshed": refreshed,
        "prerequisites_attached": prerequisites_attached,
        "additional_results_attached": additional_results_attached,
        "contract_header_historical_rows": contract_header_historical_rows,
        "contract_header_retry_rows": contract_header_retry_rows,
        "contract_header_total_rows": contract_header_historical_rows + contract_header_retry_rows,
        "receipt_core_rows": receipt_core_rows,
        "partial_contract_replay_rows": 0,
        "default_run_lanes": default_run_lanes,
        "contract_replay_coverage_overstated": contract_replay_coverage_overstated,
        "errors": errors,
        "decision": "fresh_db_replay_manifest_execution_refreshed" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "next_step": "open next migration lane after receipt core replay",
    }
    write_json(MANIFEST, manifest)
    write_json(OUTPUT_JSON, payload)
    write_report(payload)
    print(
        "FRESH_DB_REPLAY_MANIFEST_EXECUTION_REFRESH="
        + json.dumps(
            {
                "status": status,
                "execution_lanes_refreshed": refreshed,
                "prerequisites_attached": prerequisites_attached,
                "additional_results_attached": additional_results_attached,
                "contract_header_total_rows": contract_header_historical_rows + contract_header_retry_rows,
                "receipt_core_rows": receipt_core_rows,
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
