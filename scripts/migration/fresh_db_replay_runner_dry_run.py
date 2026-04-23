#!/usr/bin/env python3
"""Dry-run validator for the fresh database replay manifest.

This script never creates databases and never executes migration write scripts.
It validates that declared source files, scripts, and artifacts exist, and that
no high-risk lane is marked as default-run.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path.cwd()
MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_replay_manifest_v1.json"
RESULT = REPO_ROOT / "artifacts/migration/fresh_db_replay_runner_dry_run_result_v1.json"
REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_replay_manifest_runner_dry_run_v1.md"


def exists_all(paths: list[str]) -> tuple[list[str], list[str]]:
    present: list[str] = []
    missing: list[str] = []
    for item in paths:
        if (REPO_ROOT / item).exists():
            present.append(item)
        else:
            missing.append(item)
    return present, missing


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(payload: dict[str, object]) -> None:
    lines = [
        "# Fresh DB Replay Manifest Runner Dry Run v1",
        "",
        f"Status: {payload['status']}",
        "",
        "Task: `ITER-2026-04-15-FRESH-DB-REPLAY-MANIFEST-RUNNER-DRY-RUN`",
        "",
        "## Scope",
        "",
        "Validate the fresh database replay manifest without creating a database,",
        "executing write scripts, or mutating business data.",
        "",
        "## Lane Counts",
        "",
        "```json",
        json.dumps(payload["lane_status_counts"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Result",
        "",
        f"- lanes: `{payload['lane_count']}`",
        f"- default-run lanes: `{payload['default_run_lanes']}`",
        f"- missing references: `{len(payload['missing_references'])}`",
        f"- high-risk default violations: `{len(payload['high_risk_default_violations'])}`",
        f"- database operations: `0`",
        "",
        "## Decision",
        "",
        f"`{payload['decision']}`",
        "",
        "## Next",
        "",
        payload["next_step"],
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not MANIFEST.exists():
        raise RuntimeError({"missing_manifest": str(MANIFEST)})
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing_references: list[dict[str, object]] = []
    high_risk_default_violations: list[str] = []
    status_counts: Counter[str] = Counter()
    default_run_lanes = 0

    for lane in manifest.get("lanes", []):
        lane_id = lane["lane_id"]
        status_counts[lane["status"]] += 1
        if lane.get("default_run"):
            default_run_lanes += 1
        if lane.get("layer") == "L4_high_risk" and lane.get("default_run"):
            high_risk_default_violations.append(lane_id)
        for key in ["source_files", "write_scripts", "aggregate_artifacts", "replay_payloads"]:
            _, missing = exists_all(lane.get(key, []))
            if missing:
                missing_references.append({"lane_id": lane_id, "kind": key, "missing": missing})

    blocking_missing = [
        item
        for item in missing_references
        if item["kind"] in {"source_files", "aggregate_artifacts"}
    ]
    status = "PASS" if not blocking_missing and not high_risk_default_violations else "FAIL"
    adapter_gaps = status_counts.get("needs_adapter", 0) + status_counts.get("design_only", 0)
    next_step = (
        "open a dedicated fresh database operation contract; keep default_run disabled until that contract exists"
        if status == "PASS" and adapter_gaps == 0
        else "open fresh database operation contract only after replay adapters are implemented for needs_adapter/design_only lanes"
    )
    payload = {
        "status": status,
        "mode": "fresh_db_replay_runner_dry_run",
        "db_writes": 0,
        "database_operations": 0,
        "write_scripts_executed": 0,
        "manifest": str(MANIFEST),
        "lane_count": len(manifest.get("lanes", [])),
        "lane_status_counts": dict(sorted(status_counts.items())),
        "default_run_lanes": default_run_lanes,
        "missing_references": missing_references,
        "blocking_missing_references": blocking_missing,
        "high_risk_default_violations": high_risk_default_violations,
        "decision": "manifest_dry_run_valid" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "next_step": next_step,
    }
    write_json(RESULT, payload)
    write_report(payload)
    print(
        "FRESH_DB_REPLAY_RUNNER_DRY_RUN="
        + json.dumps(
            {
                "status": status,
                "lanes": payload["lane_count"],
                "default_run_lanes": default_run_lanes,
                "missing_references": len(missing_references),
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
