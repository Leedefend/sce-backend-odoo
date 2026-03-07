#!/usr/bin/env python3
"""Guard grouped pagination semantic summary fields and types remain stable."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / "scripts/verify/fe_tree_view_smoke.js"
BASELINE = ROOT / "scripts/verify/baselines/fe_tree_grouped_signature.json"


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8")


def _expect_dict(value: object, key: str, errors: list[str]) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    errors.append(f"{key} must be object")
    return {}


def _expect_type(value: object, expected: type | tuple[type, ...], key: str, errors: list[str]) -> None:
    if not isinstance(value, expected):
        expected_name = (
            "|".join(tp.__name__ for tp in expected) if isinstance(expected, tuple) else expected.__name__
        )
        errors.append(f"{key} must be {expected_name}")


def main() -> int:
    errors: list[str] = []
    try:
        smoke_text = _read(SMOKE)
        baseline_text = _read(BASELINE)
    except FileNotFoundError as exc:
        print("[FAIL] grouped_pagination_semantic_guard")
        print(f"- {exc}")
        return 1

    smoke_markers = [
        "function buildGroupedPaginationSemanticSummary(groupedRows, requestPageLimit, requestOffset) {",
        "function buildGroupedOffsetReplaySummary(groupPaging, requestGroupOffset) {",
        "function buildGroupedIdentitySummary(groupPaging) {",
        "grouped_pagination_semantic_summary: groupedPaginationSemanticSummary,",
        "grouped_offset_replay_summary: groupedOffsetReplaySummary,",
        "grouped_identity_summary: groupedIdentitySummary,",
        "grouped_pagination_normalized_offset:",
        "grouped_page_window_present:",
    ]
    for marker in smoke_markers:
        if marker not in smoke_text:
            errors.append(f"fe_tree_view_smoke missing marker: {marker}")

    try:
        baseline = json.loads(baseline_text)
    except json.JSONDecodeError as exc:
        errors.append(f"baseline JSON parse failed: {exc}")
        baseline = {}

    semantic = _expect_dict(baseline.get("grouped_pagination_semantic_summary"), "grouped_pagination_semantic_summary", errors)
    offset_replay = _expect_dict(
        baseline.get("grouped_offset_replay_summary"),
        "grouped_offset_replay_summary",
        errors,
    )
    identity_summary = _expect_dict(
        baseline.get("grouped_identity_summary"),
        "grouped_identity_summary",
        errors,
    )
    grouped_contract_fields = _expect_dict(
        baseline.get("grouped_contract_fields"),
        "grouped_contract_fields",
        errors,
    )
    formulas = _expect_dict(semantic.get("formulas"), "grouped_pagination_semantic_summary.formulas", errors)
    field_types = _expect_dict(semantic.get("field_types"), "grouped_pagination_semantic_summary.field_types", errors)
    request = _expect_dict(semantic.get("request"), "grouped_pagination_semantic_summary.request", errors)
    first_group = _expect_dict(
        semantic.get("first_group_observation"),
        "grouped_pagination_semantic_summary.first_group_observation",
        errors,
    )
    offset_formulas = _expect_dict(offset_replay.get("formulas"), "grouped_offset_replay_summary.formulas", errors)
    offset_request = _expect_dict(offset_replay.get("request"), "grouped_offset_replay_summary.request", errors)
    offset_response = _expect_dict(offset_replay.get("response"), "grouped_offset_replay_summary.response", errors)
    offset_consistency = _expect_dict(
        offset_replay.get("consistency"),
        "grouped_offset_replay_summary.consistency",
        errors,
    )
    identity_formulas = _expect_dict(identity_summary.get("formulas"), "grouped_identity_summary.formulas", errors)
    identity_response = _expect_dict(identity_summary.get("response"), "grouped_identity_summary.response", errors)
    identity_consistency = _expect_dict(
        identity_summary.get("consistency"),
        "grouped_identity_summary.consistency",
        errors,
    )

    for key in ("page_offset_normalize", "current_page", "total_pages", "page_range"):
        _expect_type(formulas.get(key), str, f"grouped_pagination_semantic_summary.formulas.{key}", errors)
    for key in ("offset_roundtrip", "prev_when_offset_positive", "next_signal_type"):
        _expect_type(offset_formulas.get(key), str, f"grouped_offset_replay_summary.formulas.{key}", errors)
    for key in ("window_id_shape", "query_fingerprint_shape", "window_digest_shape"):
        _expect_type(identity_formulas.get(key), str, f"grouped_identity_summary.formulas.{key}", errors)

    expected_field_types = {
        "page_limit": "number",
        "page_offset": "number",
        "current_page": "number",
        "total_pages": "number",
        "range_start": "number",
        "range_end": "number",
        "offset_aligned_to_page_limit": "boolean",
    }
    for key, expected in expected_field_types.items():
        value = field_types.get(key)
        if value != expected:
            errors.append(f"grouped_pagination_semantic_summary.field_types.{key} must be '{expected}'")

    if grouped_contract_fields.get("page_window") is not True:
        errors.append("grouped_contract_fields.page_window must be true")

    for key in ("page_limit", "request_offset", "normalized_request_offset"):
        _expect_type(request.get(key), int, f"grouped_pagination_semantic_summary.request.{key}", errors)
    _expect_type(offset_request.get("group_offset"), int, "grouped_offset_replay_summary.request.group_offset", errors)

    _expect_type(first_group.get("present"), bool, "grouped_pagination_semantic_summary.first_group_observation.present", errors)
    _expect_type(
        first_group.get("offset_aligned_to_page_limit"),
        bool,
        "grouped_pagination_semantic_summary.first_group_observation.offset_aligned_to_page_limit",
        errors,
    )
    _expect_type(
        first_group.get("page_window_matches_range"),
        bool,
        "grouped_pagination_semantic_summary.first_group_observation.page_window_matches_range",
        errors,
    )
    for key in (
        "count",
        "sample_rows_count",
        "page_limit",
        "page_offset",
        "current_page",
        "total_pages",
        "range_start",
        "range_end",
        "page_window_start",
        "page_window_end",
    ):
        _expect_type(first_group.get(key), int, f"grouped_pagination_semantic_summary.first_group_observation.{key}", errors)

    for key in ("group_offset", "group_count"):
        _expect_type(offset_response.get(key), int, f"grouped_offset_replay_summary.response.{key}", errors)
    _expect_type(offset_response.get("has_more"), bool, "grouped_offset_replay_summary.response.has_more", errors)
    _expect_type(
        offset_response.get("next_group_offset"),
        (int, type(None)),
        "grouped_offset_replay_summary.response.next_group_offset",
        errors,
    )
    _expect_type(
        offset_response.get("prev_group_offset"),
        (int, type(None)),
        "grouped_offset_replay_summary.response.prev_group_offset",
        errors,
    )
    for key in ("offset_roundtrip_match", "prev_signal_typed", "next_signal_typed"):
        _expect_type(offset_consistency.get(key), bool, f"grouped_offset_replay_summary.consistency.{key}", errors)
    _expect_type(identity_response.get("window_id"), str, "grouped_identity_summary.response.window_id", errors)
    _expect_type(
        identity_response.get("query_fingerprint"),
        str,
        "grouped_identity_summary.response.query_fingerprint",
        errors,
    )
    _expect_type(identity_response.get("window_digest"), str, "grouped_identity_summary.response.window_digest", errors)
    for key in ("has_window_id", "has_query_fingerprint", "query_fingerprint_hex", "has_window_digest", "window_digest_hex"):
        _expect_type(identity_consistency.get(key), bool, f"grouped_identity_summary.consistency.{key}", errors)

    if errors:
        print("[FAIL] grouped_pagination_semantic_guard")
        for line in errors:
            print(f"- {line}")
        return 1

    print("[OK] grouped_pagination_semantic_guard")
    print(f"- smoke: {SMOKE}")
    print(f"- baseline: {BASELINE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
