#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GEN_DIR = ROOT / "docs" / "architecture" / "scene-governance" / "assets" / "generated"
MAPPING_CSV = GEN_DIR / "governed_runtime_mapping_current_v1.csv"
WORKFLOW_CSV = GEN_DIR / "product_workflow_readiness_current_v1.csv"
OUT_CSV = GEN_DIR / "product_workflow_rollout_candidates_current_v1.csv"


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


def _rollout_priority(row: dict[str, str]) -> str:
    family = _clean(row.get("family"))
    if family in {"projects", "finance_center", "tasks"}:
        return "wave_1"
    if family in {"contracts", "payment_approval", "payment_entry"}:
        return "wave_2"
    return "wave_3"


def main() -> int:
    mapping_rows = _read_csv(MAPPING_CSV)
    workflow_rows = _read_csv(WORKFLOW_CSV)
    workflow_by_family = {_clean(row.get("family")): row for row in workflow_rows if _clean(row.get("family"))}

    output_rows: list[dict[str, str]] = []
    for row in mapping_rows:
        family = _clean(row.get("family"))
        workflow_row = workflow_by_family.get(family, {})
        workflow_ready = _clean(workflow_row.get("workflow_readiness"))
        runtime_ready = _clean(row.get("runtime_acceptance_status"))
        runtime_mode = _clean(row.get("runtime_mode"))
        rollout_candidate = _clean(row.get("rollout_candidate"))
        output_rows.append(
            {
                "family": family,
                "workflow_ready": workflow_ready,
                "runtime_ready": runtime_ready,
                "rollout_priority": _rollout_priority(row),
                "canonical_entry": _clean(row.get("user_entry")),
                "primary_action": _clean(row.get("primary_action")),
                "fallback_strategy": _clean(row.get("fallback_runtime_policy")),
                "delivery_mode": "direct_delivery" if runtime_mode == "direct" else "orchestration_delivery",
                "recommended_rollout_wave": _rollout_priority(row),
                "rollout_candidate": rollout_candidate,
            }
        )

    fieldnames = [
        "family",
        "workflow_ready",
        "runtime_ready",
        "rollout_priority",
        "canonical_entry",
        "primary_action",
        "fallback_strategy",
        "delivery_mode",
        "recommended_rollout_wave",
        "rollout_candidate",
    ]
    _write_csv(OUT_CSV, fieldnames, output_rows)

    candidate_count = sum(1 for row in output_rows if row["rollout_candidate"] == "yes")
    direct_delivery_count = sum(1 for row in output_rows if row["delivery_mode"] == "direct_delivery")

    print("[scene_governance_product_workflow_rollout_candidates_export] PASS")
    print(f"family_rows={len(output_rows)}")
    print(f"rollout_candidate={candidate_count}")
    print(f"direct_delivery={direct_delivery_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
