#!/usr/bin/env python3
"""Refresh replay manifest lanes for construction contract visible-surface delivery."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path.cwd()
MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_replay_manifest_v1.json"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_construction_contract_replay_manifest_refresh_result_v1.json"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_construction_contract_replay_manifest_refresh_v1.md"

LANES = [
    {
        "lane_id": "construction_contract_income_count_alignment",
        "status": "replay_ready_candidate",
        "layer": "L2_user_visible_business",
        "default_run": False,
        "target_model": "construction.contract",
        "write_scripts": [
            "scripts/migration/fresh_db_construction_contract_income_count_alignment_write.py",
            "scripts/migration/fresh_db_new_construction_contract_xlsx_income_write.py",
            "scripts/migration/fresh_db_income_fact_project_stub_write.py",
        ],
        "source_files": [
            "tmp/raw/contract/contract.csv",
            "tmp/new_construction_contract_income.xlsx",
        ],
        "aggregate_artifacts": [
            "artifacts/migration/fresh_db_construction_contract_income_count_alignment_write_result_v1.json",
            "artifacts/migration/fresh_db_new_construction_contract_xlsx_income_write_result_v1.json",
            "artifacts/migration/fresh_db_income_fact_project_stub_write_result_v1.json",
            "artifacts/migration/fresh_db_construction_contract_income_count_probe_result_v1.json",
        ],
        "expected_current_result": {
            "project_income_contracts": 1730,
            "general_income_contracts": 2,
            "income_contract_ledger_rows": 1732,
            "remaining_income_fact_projects_without_contract": 0,
        },
    },
    {
        "lane_id": "construction_contract_visible_surface",
        "status": "replay_ready_candidate",
        "layer": "L2_user_visible_business",
        "default_run": False,
        "target_model": "construction.contract",
        "write_scripts": ["scripts/migration/fresh_db_construction_contract_visible_surface_write.py"],
        "source_files": ["artifacts/migration/source_extracts/construction_contract_visible_surface.xlsx"],
        "aggregate_artifacts": ["artifacts/migration/fresh_db_construction_contract_visible_surface_write_result_v1.json"],
        "expected_current_result": {"visible_surface_mismatch_count": 0},
    },
    {
        "lane_id": "construction_contract_visible_business_fact",
        "status": "replay_ready_candidate",
        "layer": "L2_user_visible_business",
        "default_run": False,
        "target_model": "construction.contract",
        "write_scripts": ["scripts/migration/fresh_db_construction_contract_visible_business_fact_write.py"],
        "source_files": ["artifacts/migration/source_extracts/construction_contract_visible_surface.xlsx"],
        "aggregate_artifacts": ["artifacts/migration/fresh_db_construction_contract_visible_business_fact_write_result_v1.json"],
        "expected_current_result": {"status": "PASS"},
    },
    {
        "lane_id": "construction_contract_visible_trace",
        "status": "replay_ready_candidate",
        "layer": "L2_user_visible_business",
        "default_run": False,
        "target_model": "sc.contract.event",
        "write_scripts": ["scripts/migration/fresh_db_construction_contract_visible_trace_write.py"],
        "source_files": [
            "artifacts/migration/source_extracts/construction_contract_visible_surface.xlsx",
            "artifacts/migration/fresh_db_legacy_file_index_replay_payload_v1.csv",
        ],
        "aggregate_artifacts": ["artifacts/migration/fresh_db_construction_contract_visible_trace_write_result_v1.json"],
        "expected_current_result": {"approval_event_count": 20, "visible_surface_attachment_count": 0},
    },
    {
        "lane_id": "construction_contract_full_attachment",
        "status": "replay_ready_candidate",
        "layer": "L3_relation_custody",
        "default_run": False,
        "target_model": "ir.attachment",
        "write_scripts": ["scripts/migration/fresh_db_construction_contract_attachment_write.py"],
        "source_files": [
            "artifacts/migration/source_extracts/T_ProjectContract_Out_contract.csv",
            "artifacts/migration/fresh_db_legacy_file_index_replay_payload_v1.csv",
        ],
        "aggregate_artifacts": [
            "artifacts/migration/fresh_db_construction_contract_attachment_write_result_v1.json",
            "artifacts/migration/fresh_db_construction_contract_attachment_probe_result_v1.json",
        ],
        "expected_current_result": {
            "target_contract_rows": 1532,
            "full_attachment_count": 3728,
            "visible_surface_attachment_count": 0,
            "approval_event_count": 20,
        },
    },
]


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {
            "manifest_id": "fresh_db_replay_manifest_v1",
            "status": "runtime_anchor_for_packaged_replay",
            "lanes": [],
            "default_policy": {
                "execute_database_operations": False,
                "execute_write_scripts": False,
                "include_high_risk_lanes": False,
            },
        }
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(payload: dict[str, object]) -> None:
    lines = [
        "# Fresh DB Construction Contract Replay Manifest Refresh v1",
        "",
        f"Status: {payload['status']}",
        "",
        "## Scope",
        "",
        "Refresh replay manifest lanes for construction contract user-visible delivery.",
        "This script writes manifest metadata only and performs no database operations.",
        "",
        "## Result",
        "",
        f"- refreshed lanes: `{payload['refreshed_lanes']}`",
        f"- missing references: `{len(payload['missing_references'])}`",
        f"- default-run lanes: `{payload['default_run_lanes']}`",
        "- DB writes: `0`",
        "",
        "## Decision",
        "",
        f"`{payload['decision']}`",
    ]
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    manifest = read_json(MANIFEST)
    existing = {lane.get("lane_id"): lane for lane in manifest.get("lanes", [])}
    for lane in LANES:
        existing[lane["lane_id"]] = dict(lane)
    manifest["lanes"] = list(existing.values())
    manifest["status"] = "CONSTRUCTION_CONTRACT_REPLAY_READY_CANDIDATE"
    manifest["certification_status"] = "CONSTRUCTION_CONTRACT_VISIBLE_SURFACE_READY_CANDIDATE"
    manifest.setdefault("default_policy", {})
    manifest["default_policy"]["execute_database_operations"] = False
    manifest["default_policy"]["execute_write_scripts"] = False
    manifest["default_policy"]["include_high_risk_lanes"] = False

    missing: list[dict[str, str]] = []
    for lane in LANES:
        for key in ("source_files", "write_scripts", "aggregate_artifacts"):
            for rel_path in lane.get(key, []):
                if not (REPO_ROOT / rel_path).exists():
                    missing.append({"lane_id": lane["lane_id"], "kind": key, "missing": rel_path})

    default_run_lanes = sum(1 for lane in manifest["lanes"] if lane.get("default_run"))
    status = "PASS" if not missing and default_run_lanes == 0 else "FAIL"
    payload = {
        "status": status,
        "mode": "fresh_db_construction_contract_replay_manifest_refresh",
        "db_writes": 0,
        "database_operations": 0,
        "write_scripts_executed": 0,
        "refreshed_lanes": len(LANES),
        "missing_references": missing,
        "default_run_lanes": default_run_lanes,
        "decision": "construction_contract_replay_manifest_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    }
    write_json(MANIFEST, manifest)
    write_json(OUTPUT_JSON, payload)
    write_report(payload)
    print(
        "FRESH_DB_CONSTRUCTION_CONTRACT_REPLAY_MANIFEST_REFRESH="
        + json.dumps(
            {
                "status": status,
                "refreshed_lanes": len(LANES),
                "missing_references": len(missing),
                "default_run_lanes": default_run_lanes,
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
