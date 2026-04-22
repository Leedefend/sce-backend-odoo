#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GEN_DIR = ROOT / "docs" / "architecture" / "scene-governance" / "assets" / "generated"
SOURCE_CSV = GEN_DIR / "high_priority_family_user_flow_closure_current_v1.csv"
OUT_CSV = GEN_DIR / "runtime_eligibility_current_v1.csv"


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


def _build_runtime_eligibility(row: dict[str, str]) -> tuple[str, str]:
    acceptance_status = _clean(row.get("acceptance_status"))
    required_provider = _clean(row.get("required_provider"))
    final_scene = _clean(row.get("final_scene"))
    primary_action = _clean(row.get("primary_action"))

    if not final_scene or not primary_action:
        return "blocked", "missing_scene_or_primary_action"
    if not required_provider or required_provider == "provider_tbd":
        return "blocked", "provider_not_explicit"
    if acceptance_status == "guarded_ready":
        return "eligible", "guarded_ready"
    if acceptance_status == "guarded_with_residual_compat":
        return "conditional", "residual_compat"
    if acceptance_status == "guarded_missing_provider":
        return "blocked", "missing_provider"
    return "blocked", "acceptance_not_ready"


def main() -> int:
    rows = _read_csv(SOURCE_CSV)
    output_rows: list[dict[str, str]] = []
    for row in rows:
        runtime_eligibility, blocker_reason = _build_runtime_eligibility(row)
        output_rows.append(
            {
                "family": _clean(row.get("family")),
                "user_entry": _clean(row.get("user_entry")),
                "final_scene": _clean(row.get("final_scene")),
                "primary_action": _clean(row.get("primary_action")),
                "required_provider": _clean(row.get("required_provider")),
                "fallback_strategy": _clean(row.get("fallback_strategy")),
                "acceptance_status": _clean(row.get("acceptance_status")),
                "runtime_eligibility": runtime_eligibility,
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
        "runtime_eligibility",
        "blocker_reason",
    ]
    _write_csv(OUT_CSV, fieldnames, output_rows)

    eligible_count = sum(1 for row in output_rows if row["runtime_eligibility"] == "eligible")
    conditional_count = sum(1 for row in output_rows if row["runtime_eligibility"] == "conditional")
    blocked_count = sum(1 for row in output_rows if row["runtime_eligibility"] == "blocked")

    print("[scene_governance_runtime_eligibility_export] PASS")
    print(f"family_rows={len(output_rows)}")
    print(f"eligible={eligible_count}")
    print(f"conditional={conditional_count}")
    print(f"blocked={blocked_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
