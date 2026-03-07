#!/usr/bin/env python3
"""Drift guard for grouped pagination semantic summary baseline."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / "scripts/verify/fe_tree_view_smoke.js"
BASELINE = ROOT / "scripts/verify/baselines/fe_tree_grouped_signature.json"


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

    if not SMOKE.is_file():
        errors.append(f"missing smoke file: {SMOKE.relative_to(ROOT).as_posix()}")
        smoke_text = ""
    else:
        smoke_text = SMOKE.read_text(encoding="utf-8", errors="ignore")

    baseline = _load_json(BASELINE)
    if not baseline:
        errors.append(f"missing or invalid baseline: {BASELINE.relative_to(ROOT).as_posix()}")

    smoke_markers = [
        "function buildGroupedPaginationSemanticSummary(groupedRows, requestPageLimit, requestOffset) {",
        "function buildGroupedOffsetReplaySummary(groupPaging, requestGroupOffset) {",
        "function buildGroupedIdentitySummary(groupPaging) {",
        "grouped_pagination_semantic_summary: groupedPaginationSemanticSummary,",
        "grouped_offset_replay_summary: groupedOffsetReplaySummary,",
        "grouped_identity_summary: groupedIdentitySummary,",
        "consistency:",
        "request_offset_matches_observed",
        "request_offset_aligned_to_page_limit",
        "first_group_offset_aligned_to_page_limit",
        "first_group_page_window_matches_range",
    ]
    for marker in smoke_markers:
        if marker not in smoke_text:
            errors.append(f"smoke missing marker: {marker}")

    summary = baseline.get("grouped_pagination_semantic_summary") if isinstance(baseline.get("grouped_pagination_semantic_summary"), dict) else {}
    offset_replay = baseline.get("grouped_offset_replay_summary") if isinstance(baseline.get("grouped_offset_replay_summary"), dict) else {}
    identity_summary = baseline.get("grouped_identity_summary") if isinstance(baseline.get("grouped_identity_summary"), dict) else {}
    grouped_contract_fields = baseline.get("grouped_contract_fields") if isinstance(baseline.get("grouped_contract_fields"), dict) else {}
    field_types = summary.get("field_types") if isinstance(summary.get("field_types"), dict) else {}
    consistency = summary.get("consistency") if isinstance(summary.get("consistency"), dict) else {}
    first_group = (
        summary.get("first_group_observation")
        if isinstance(summary.get("first_group_observation"), dict)
        else {}
    )
    offset_consistency = offset_replay.get("consistency") if isinstance(offset_replay.get("consistency"), dict) else {}
    identity_consistency = identity_summary.get("consistency") if isinstance(identity_summary.get("consistency"), dict) else {}

    if not summary:
        errors.append("baseline grouped_pagination_semantic_summary must be object")
    if grouped_contract_fields.get("group_key") is not True:
        errors.append("baseline grouped_contract_fields.group_key must be true")
    if grouped_contract_fields.get("page_has_prev") is not True:
        errors.append("baseline grouped_contract_fields.page_has_prev must be true")
    if grouped_contract_fields.get("page_has_next") is not True:
        errors.append("baseline grouped_contract_fields.page_has_next must be true")
    if grouped_contract_fields.get("page_window") is not True:
        errors.append("baseline grouped_contract_fields.page_window must be true")
    if field_types.get("request_offset_matches_observed") != "boolean":
        errors.append("baseline field_types.request_offset_matches_observed must be 'boolean'")
    if not offset_replay:
        errors.append("baseline grouped_offset_replay_summary must be object")
    if not identity_summary:
        errors.append("baseline grouped_identity_summary must be object")

    for key in (
        "request_offset_matches_observed",
        "request_offset_aligned_to_page_limit",
        "first_group_offset_aligned_to_page_limit",
        "first_group_page_window_matches_range",
    ):
        if not isinstance(consistency.get(key), bool):
            errors.append(f"baseline consistency.{key} must be bool")

    if not isinstance(first_group.get("offset_aligned_to_page_limit"), bool):
        errors.append("baseline first_group_observation.offset_aligned_to_page_limit must be bool")
    if not isinstance(first_group.get("page_window_matches_range"), bool):
        errors.append("baseline first_group_observation.page_window_matches_range must be bool")
    for key in ("offset_roundtrip_match", "prev_signal_typed", "next_signal_typed"):
        if not isinstance(offset_consistency.get(key), bool):
            errors.append(f"baseline grouped_offset_replay_summary.consistency.{key} must be bool")
    for key in ("has_window_id", "has_query_fingerprint", "query_fingerprint_hex"):
        if not isinstance(identity_consistency.get(key), bool):
            errors.append(f"baseline grouped_identity_summary.consistency.{key} must be bool")

    if errors:
        print("[grouped_pagination_semantic_drift_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[grouped_pagination_semantic_drift_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
