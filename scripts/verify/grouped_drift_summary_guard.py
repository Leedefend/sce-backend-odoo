#!/usr/bin/env python3
"""Aggregate grouped drift signals across fe-tree baseline, e2e baseline, and evidence exporter."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
FE_TREE_BASELINE = ROOT / "scripts" / "verify" / "baselines" / "fe_tree_grouped_signature.json"
E2E_BASELINE = ROOT / "scripts" / "verify" / "baselines" / "e2e_grouped_rows_signature.json"
EVIDENCE_EXPORT = ROOT / "scripts" / "contract" / "export_evidence.py"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    errors: list[str] = []

    fe_tree = _load_json(FE_TREE_BASELINE)
    e2e = _load_json(E2E_BASELINE)
    export_text = EVIDENCE_EXPORT.read_text(encoding="utf-8", errors="ignore") if EVIDENCE_EXPORT.is_file() else ""

    if not fe_tree:
        errors.append(f"missing or invalid baseline: {FE_TREE_BASELINE.relative_to(ROOT).as_posix()}")
    if not e2e:
        errors.append(f"missing or invalid baseline: {E2E_BASELINE.relative_to(ROOT).as_posix()}")
    if not export_text:
        errors.append(f"missing evidence export script: {EVIDENCE_EXPORT.relative_to(ROOT).as_posix()}")

    grouped_fields = fe_tree.get("grouped_contract_fields") if isinstance(fe_tree.get("grouped_contract_fields"), dict) else {}
    for key in ("group_key", "page_has_prev", "page_has_next", "page_window"):
        if grouped_fields.get(key) is not True:
            errors.append(f"fe_tree grouped_contract_fields.{key} must be true")

    semantic = fe_tree.get("grouped_pagination_semantic_summary") if isinstance(fe_tree.get("grouped_pagination_semantic_summary"), dict) else {}
    consistency = semantic.get("consistency") if isinstance(semantic.get("consistency"), dict) else {}
    if not isinstance(consistency.get("first_group_page_window_matches_range"), bool):
        errors.append("fe_tree consistency.first_group_page_window_matches_range must be bool")

    grouped_cases = e2e.get("grouped_cases") if isinstance(e2e.get("grouped_cases"), list) else []
    if not grouped_cases:
        errors.append("e2e grouped_cases must be non-empty list")

    max_consistency_score = 0
    has_grouped_rows_case = False
    for idx, row in enumerate(grouped_cases):
        if not isinstance(row, dict):
            errors.append(f"e2e grouped_cases[{idx}] must be object")
            continue
        score = row.get("consistency_score")
        if not isinstance(score, int):
            errors.append(f"e2e grouped_cases[{idx}].consistency_score must be int")
            continue
        max_consistency_score = max(max_consistency_score, score)
        if row.get("has_grouped_rows") is True:
            has_grouped_rows_case = True

    if has_grouped_rows_case and max_consistency_score < 4:
        errors.append("e2e grouped cases include grouped_rows but max consistency_score < 4")

    export_markers = [
        '"grouped_pagination_contract": {',
        '"supports_page_window":',
        '"window_range_consistency":',
    ]
    for marker in export_markers:
        if marker not in export_text:
            errors.append(f"export_evidence missing marker: {marker}")

    if errors:
        print("[grouped_drift_summary_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[grouped_drift_summary_guard] PASS")
    print(f"- fe_tree_group_fields: {sorted(grouped_fields.keys())}")
    print(f"- e2e_cases: {len(grouped_cases)}")
    print(f"- e2e_max_consistency_score: {max_consistency_score}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
