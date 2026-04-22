#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GEN_DIR = ROOT / "docs" / "architecture" / "scene-governance" / "assets" / "generated"
SOURCE_CSV = GEN_DIR / "high_priority_family_user_flow_closure_current_v1.csv"
OUT_CSV = GEN_DIR / "product_workflow_readiness_current_v1.csv"


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


def _build_workflow_readiness(row: dict[str, str]) -> tuple[str, str]:
    acceptance_status = _clean(row.get("acceptance_status"))
    user_entry = _clean(row.get("user_entry"))
    final_scene = _clean(row.get("final_scene"))
    primary_action = _clean(row.get("primary_action"))
    required_provider = _clean(row.get("required_provider"))

    if not user_entry or not final_scene or not primary_action:
        return "blocked", "entry_scene_or_action_missing"
    if not required_provider or required_provider == "provider_tbd":
        return "blocked", "provider_not_explicit"
    if acceptance_status == "guarded_ready":
        return "ready", "guarded_ready"
    if acceptance_status == "guarded_with_residual_compat":
        return "ready_with_residual_compat", "residual_compat"
    if acceptance_status == "guarded_missing_provider":
        return "blocked", "missing_provider"
    return "blocked", "acceptance_not_ready"


def main() -> int:
    rows = _read_csv(SOURCE_CSV)
    output_rows: list[dict[str, str]] = []
    for row in rows:
        workflow_readiness, blocker_reason = _build_workflow_readiness(row)
        output_rows.append(
            {
                "family": _clean(row.get("family")),
                "user_entry": _clean(row.get("user_entry")),
                "final_scene": _clean(row.get("final_scene")),
                "primary_action": _clean(row.get("primary_action")),
                "required_provider": _clean(row.get("required_provider")),
                "fallback_strategy": _clean(row.get("fallback_strategy")),
                "acceptance_status": _clean(row.get("acceptance_status")),
                "workflow_readiness": workflow_readiness,
                "blocker_reason": blocker_reason,
            }
        )

    fieldnames = [
        "family",
        "user_entry",
        "final_scene",
        "primary_action",
        "required_provider",
        "fallback_strategy",
        "acceptance_status",
        "workflow_readiness",
        "blocker_reason",
    ]
    _write_csv(OUT_CSV, fieldnames, output_rows)

    ready_count = sum(1 for row in output_rows if row["workflow_readiness"] == "ready")
    residual_count = sum(1 for row in output_rows if row["workflow_readiness"] == "ready_with_residual_compat")
    blocked_count = sum(1 for row in output_rows if row["workflow_readiness"] == "blocked")

    print("[scene_governance_product_workflow_readiness_export] PASS")
    print(f"family_rows={len(output_rows)}")
    print(f"ready={ready_count}")
    print(f"ready_with_residual_compat={residual_count}")
    print(f"blocked={blocked_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
