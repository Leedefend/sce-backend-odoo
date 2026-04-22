#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GEN_DIR = ROOT / "docs" / "architecture" / "scene-governance" / "assets" / "generated"
RUNTIME_ELIGIBILITY_CSV = GEN_DIR / "runtime_eligibility_current_v1.csv"
WORKFLOW_READINESS_CSV = GEN_DIR / "product_workflow_readiness_current_v1.csv"
OUT_CSV = GEN_DIR / "governed_runtime_mapping_current_v1.csv"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _clean(value: object) -> str:
    return str(value or "").strip()


def _runtime_mode(runtime_eligibility: str, workflow_readiness: str) -> tuple[str, str, str]:
    if runtime_eligibility == "eligible" and workflow_readiness == "ready":
        return "governed_user_flow", "family_runtime_consumer", "direct"
    return "governed_user_flow", "family_runtime_consumer", "orchestration"


def _runtime_acceptance_status(runtime_eligibility: str, workflow_readiness: str) -> str:
    if runtime_eligibility == "eligible" and workflow_readiness == "ready":
        return "runtime_ready"
    if runtime_eligibility == "conditional" or workflow_readiness == "ready_with_residual_compat":
        return "runtime_ready_with_conditions"
    return "runtime_blocked"


def main() -> int:
    runtime_rows = _read_csv(RUNTIME_ELIGIBILITY_CSV)
    workflow_rows = _read_csv(WORKFLOW_READINESS_CSV)
    workflow_by_family = {_clean(row.get("family")): row for row in workflow_rows if _clean(row.get("family"))}

    output_rows: list[dict[str, str]] = []
    for row in runtime_rows:
        family = _clean(row.get("family"))
        workflow_row = workflow_by_family.get(family, {})
        runtime_eligibility = _clean(row.get("runtime_eligibility"))
        workflow_readiness = _clean(workflow_row.get("workflow_readiness"))
        runtime_entry_type, runtime_consumer, runtime_mode = _runtime_mode(
            runtime_eligibility,
            workflow_readiness,
        )
        runtime_acceptance_status = _runtime_acceptance_status(
            runtime_eligibility,
            workflow_readiness,
        )
        output_rows.append(
            {
                "family": family,
                "user_entry": _clean(row.get("user_entry")),
                "final_scene": _clean(row.get("final_scene")),
                "runtime_entry_type": runtime_entry_type,
                "runtime_consumer": runtime_consumer,
                "primary_action": _clean(row.get("primary_action")),
                "required_provider": _clean(row.get("required_provider")),
                "fallback_runtime_policy": _clean(row.get("fallback_strategy")),
                "runtime_mode": runtime_mode,
                "runtime_acceptance_status": runtime_acceptance_status,
                "rollout_candidate": "yes" if runtime_acceptance_status == "runtime_ready" else "no",
                "blocking_reason": _clean(row.get("blocker_reason")) if runtime_acceptance_status != "runtime_ready" else "none",
                "recommended_next_action": "enter_workflow_rollout_wave" if runtime_acceptance_status == "runtime_ready" else "hold_for_runtime_review",
            }
        )

    fieldnames = [
        "family",
        "user_entry",
        "final_scene",
        "runtime_entry_type",
        "runtime_consumer",
        "primary_action",
        "required_provider",
        "fallback_runtime_policy",
        "runtime_mode",
        "runtime_acceptance_status",
        "rollout_candidate",
        "blocking_reason",
        "recommended_next_action",
    ]
    _write_csv(OUT_CSV, fieldnames, output_rows)

    direct_count = sum(1 for row in output_rows if row["runtime_mode"] == "direct")
    orchestration_count = sum(1 for row in output_rows if row["runtime_mode"] == "orchestration")
    rollout_count = sum(1 for row in output_rows if row["rollout_candidate"] == "yes")

    print("[scene_governance_governed_runtime_mapping_export] PASS")
    print(f"family_rows={len(output_rows)}")
    print(f"direct={direct_count}")
    print(f"orchestration={orchestration_count}")
    print(f"rollout_candidate={rollout_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
