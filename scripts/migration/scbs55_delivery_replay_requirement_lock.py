#!/usr/bin/env python3
"""Freeze delivery/release replay artifact requirements for SCBS55."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.migration import migration_asset_delivery_audit
from scripts.migration import migration_asset_release_package


REPLAY_GAP = ROOT / "docs/migration_alignment/scbs55_replay_payload_gap_report_v1.json"
OUTPUT_JSON = ROOT / "docs/migration_alignment/scbs55_delivery_replay_requirement_lock_v1.json"
OUTPUT_MD = ROOT / "docs/migration_alignment/scbs55_delivery_replay_requirement_lock_v1.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_lock() -> dict[str, Any]:
    gap = load_json(REPLAY_GAP)
    steps = gap.get("steps") if isinstance(gap.get("steps"), list) else []
    gap_required = sorted(
        {
            item.get("path")
            for step in steps
            if isinstance(step, dict) and step.get("scope") == "required"
            for item in step.get("input_artifacts", [])
            if isinstance(item, dict) and item.get("path")
        }
    )
    baseline_exclusions = sorted(set(migration_asset_delivery_audit.BASELINE_EXCLUDED_REQUIRED_ARTIFACTS) & set(gap_required))
    expected_required = sorted(set(gap_required) - set(baseline_exclusions))
    delivery_required = migration_asset_delivery_audit.required_replay_artifacts()
    release_required = migration_asset_release_package.required_replay_artifacts()
    errors = []
    if delivery_required != release_required:
        errors.append("delivery audit and release package required artifact sets differ")
    if delivery_required != expected_required:
        errors.append("delivery/release required artifact set does not match replay gap minus baseline exclusions")
    return {
        "lock_version": "scbs55_delivery_replay_requirement_lock_v1",
        "status": "FAIL" if errors else "PASS",
        "source_gap_report": str(REPLAY_GAP.relative_to(ROOT)),
        "gap_required_input_unique_path_count": len(gap_required),
        "baseline_excluded_required_path_count": len(baseline_exclusions),
        "delivery_required_replay_artifact_count": len(delivery_required),
        "release_required_replay_artifact_count": len(release_required),
        "baseline_excluded_required_paths": baseline_exclusions,
        "delivery_required_replay_artifacts": delivery_required,
        "release_required_replay_artifacts": release_required,
        "errors": errors,
        "decision": "delivery and release package gates must use this required replay artifact set; delivery audit reports may only replace this lock after package materialization",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    exclusions = "\n".join(f"- `{item}`" for item in payload["baseline_excluded_required_paths"]) or "- none"
    required = "\n".join(f"- `{item}`" for item in payload["delivery_required_replay_artifacts"]) or "- none"
    return f"""# SCBS55 Delivery Replay Requirement Lock v1

Status: `{payload["status"]}`

Source: `{payload["source_gap_report"]}`

## Summary

- gap required input unique paths: `{payload["gap_required_input_unique_path_count"]}`
- baseline excluded required paths: `{payload["baseline_excluded_required_path_count"]}`
- delivery required replay artifacts: `{payload["delivery_required_replay_artifact_count"]}`
- release required replay artifacts: `{payload["release_required_replay_artifact_count"]}`

## Baseline Exclusions

{exclusions}

## Required Replay Artifacts

{required}

## Decision

`{payload["decision"]}`
"""


def main() -> int:
    payload = build_lock()
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(
        "SCBS55_DELIVERY_REPLAY_REQUIREMENT_LOCK="
        + json.dumps(
            {
                "status": payload["status"],
                "gap_required": payload["gap_required_input_unique_path_count"],
                "baseline_excluded": payload["baseline_excluded_required_path_count"],
                "delivery_required": payload["delivery_required_replay_artifact_count"],
                "release_required": payload["release_required_replay_artifact_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 2 if payload["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
