#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GEN_DIR = ROOT / "docs" / "architecture" / "scene-governance" / "assets" / "generated"
AUTHORITY_CSV = GEN_DIR / "scene_authority_matrix_current_v1.csv"
FAMILY_CSV = GEN_DIR / "scene_family_inventory_current_v1.csv"
MENU_CSV = GEN_DIR / "menu_scene_mapping_current_v1.csv"
PROVIDER_CSV = GEN_DIR / "provider_completeness_current_v1.csv"
OUT_CSV = GEN_DIR / "family_priority_score_current_v1.csv"

HIGH_FREQUENCY_FAMILIES = {
    "projects": 5,
    "tasks": 5,
    "finance_center": 5,
    "payment_entry": 5,
    "payment_approval": 5,
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_scores() -> list[dict[str, str | int]]:
    authority_rows = _read_csv(AUTHORITY_CSV)
    family_rows = _read_csv(FAMILY_CSV)
    menu_rows = _read_csv(MENU_CSV)
    provider_rows = _read_csv(PROVIDER_CSV)

    family_state = {
        str(row.get("family") or "").strip(): {
            "family": str(row.get("family") or "").strip(),
            "scene_count": int(str(row.get("scene_count") or "0") or "0"),
            "verify_status": str(row.get("verify_status") or "").strip(),
            "governance_status": str(row.get("governance_status") or "").strip(),
        }
        for row in family_rows
        if str(row.get("family") or "").strip()
    }

    scene_to_family = {
        str(row.get("scene_key") or "").strip(): str(row.get("family") or "").strip()
        for row in authority_rows
        if str(row.get("scene_key") or "").strip() and str(row.get("family") or "").strip()
    }

    bucket: dict[str, dict[str, int | str]] = {}
    for family, state in family_state.items():
        bucket[family] = {
            "family": family,
            "canonical_gap_score": 0,
            "compatibility_score": 0,
            "provider_gap_score": 0,
            "high_frequency_weight": HIGH_FREQUENCY_FAMILIES.get(family, 0),
            "closed_discount": -5 if state.get("governance_status") == "stage_closed" else 0,
            "total_score": 0,
        }

    for row in authority_rows:
        family = str(row.get("family") or "").strip()
        if not family:
            continue
        entry = bucket.setdefault(
            family,
            {
                "family": family,
                "canonical_gap_score": 0,
                "compatibility_score": 0,
                "provider_gap_score": 0,
                "high_frequency_weight": HIGH_FREQUENCY_FAMILIES.get(family, 0),
                "closed_discount": 0,
                "total_score": 0,
            },
        )
        canonical_entry = str(row.get("canonical_entry") or "").strip()
        native_fallback = str(row.get("native_fallback") or "").strip().lower()
        if not canonical_entry:
            entry["canonical_gap_score"] += 8
        if "compat" in native_fallback or "shared" in native_fallback:
            entry["compatibility_score"] += 4
        elif native_fallback and native_fallback not in {"none", "action", "menu_only"}:
            entry["compatibility_score"] += 2

    for row in provider_rows:
        family = scene_to_family.get(str(row.get("scene_key") or "").strip(), "")
        if not family:
            continue
        completeness = str(row.get("completeness_status") or "").strip()
        if completeness == "missing":
            bucket[family]["provider_gap_score"] += 6
        elif completeness == "fallback_only":
            bucket[family]["provider_gap_score"] += 2

    for row in menu_rows:
        if str(row.get("compatibility_used") or "").strip().lower() != "true":
            continue
        scene_key = str(row.get("resolved_scene_key") or "").strip()
        family = scene_to_family.get(scene_key, "")
        if family:
            bucket[family]["compatibility_score"] += 1

    rows: list[dict[str, str | int]] = []
    for family, row in bucket.items():
        total = (
            int(row["canonical_gap_score"])
            + int(row["compatibility_score"])
            + int(row["provider_gap_score"])
            + int(row["high_frequency_weight"])
            + int(row["closed_discount"])
        )
        row["total_score"] = total
        rows.append(row)

    rows.sort(key=lambda item: (-int(item["total_score"]), str(item["family"])))
    return rows


def main() -> int:
    try:
        rows = build_scores()
        _write_csv(
            OUT_CSV,
            [
                "family",
                "canonical_gap_score",
                "compatibility_score",
                "provider_gap_score",
                "high_frequency_weight",
                "closed_discount",
                "total_score",
            ],
            rows,
        )
    except Exception as exc:
        print("[scene_governance_family_priority_score] FAIL")
        print(f"- {exc}")
        return 1

    print("[scene_governance_family_priority_score] PASS")
    print(f"family_rows={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
