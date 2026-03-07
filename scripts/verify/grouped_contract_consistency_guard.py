#!/usr/bin/env python3
"""Guard grouped pagination contract baselines remain mutually consistent."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
FE_TREE_BASELINE = ROOT / "scripts" / "verify" / "baselines" / "fe_tree_grouped_signature.json"
E2E_BASELINE = ROOT / "scripts" / "verify" / "baselines" / "e2e_grouped_rows_signature.json"
FE_TREE_SMOKE = ROOT / "scripts" / "verify" / "fe_tree_view_smoke.js"
E2E_SMOKE = ROOT / "scripts" / "e2e" / "e2e_contract_smoke.py"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    errors: list[str] = []

    fe_tree = _load_json(FE_TREE_BASELINE)
    e2e = _load_json(E2E_BASELINE)
    fe_tree_smoke = _read(FE_TREE_SMOKE)
    e2e_smoke = _read(E2E_SMOKE)

    if not fe_tree:
        errors.append(f"missing or invalid baseline: {FE_TREE_BASELINE.relative_to(ROOT).as_posix()}")
    if not e2e:
        errors.append(f"missing or invalid baseline: {E2E_BASELINE.relative_to(ROOT).as_posix()}")

    smoke_markers = [
        "grouped_contract_fields:",
        "page_window: groupedHasPageWindow",
        "first_group_page_window_matches_range",
        "grouped_offset_replay_summary: groupedOffsetReplaySummary",
        "grouped_identity_summary: groupedIdentitySummary",
        "grouped_identity_key_matches_tuple",
        "grouped_identity_key_matches_flat",
        "grouped_identity_window_numbers_match_flat",
        "grouped_identity_total_match_flat",
        "grouped_identity_group_by_match_flat",
        "grouped_identity_page_meta_match_flat",
        "grouped_identity_range_numbers_match_flat",
        "grouped_identity_nav_match_flat",
        "grouped_identity_model_match_request",
    ]
    for marker in smoke_markers:
        if marker not in fe_tree_smoke:
            errors.append(f"fe_tree_view_smoke missing marker: {marker}")

    e2e_markers = [
        "def _build_grouped_semantic_signature",
        '"supports_page_window": grouped_semantic["supports_page_window"]',
        '"page_window_matches_range": grouped_semantic["page_window_matches_range"]',
    ]
    for marker in e2e_markers:
        if marker not in e2e_smoke:
            errors.append(f"e2e_contract_smoke missing marker: {marker}")

    grouped_fields = fe_tree.get("grouped_contract_fields") if isinstance(fe_tree.get("grouped_contract_fields"), dict) else {}
    for key in ("group_key", "page_has_prev", "page_has_next", "page_window"):
        if grouped_fields.get(key) is not True:
            errors.append(f"fe_tree grouped_contract_fields.{key} must be true")

    semantic = fe_tree.get("grouped_pagination_semantic_summary") if isinstance(fe_tree.get("grouped_pagination_semantic_summary"), dict) else {}
    identity = fe_tree.get("grouped_identity_summary") if isinstance(fe_tree.get("grouped_identity_summary"), dict) else {}
    consistency = semantic.get("consistency") if isinstance(semantic.get("consistency"), dict) else {}
    identity_consistency = identity.get("consistency") if isinstance(identity.get("consistency"), dict) else {}
    for key in (
        "request_offset_matches_observed",
        "request_offset_aligned_to_page_limit",
        "first_group_offset_aligned_to_page_limit",
        "first_group_page_window_matches_range",
    ):
        if not isinstance(consistency.get(key), bool):
            errors.append(f"fe_tree consistency.{key} must be bool")
    for key in (
        "has_window_id",
        "has_query_fingerprint",
        "query_fingerprint_hex",
        "has_window_digest",
        "window_digest_hex",
        "identity_object_present",
        "identity_object_matches_flat",
        "identity_version_present",
        "identity_algo_present",
        "identity_algo_supported",
        "identity_key_present",
        "identity_key_matches_tuple",
        "identity_key_matches_flat",
        "identity_window_numbers_present",
        "identity_window_numbers_match_flat",
        "identity_total_optional_typed",
        "identity_total_match_flat",
        "identity_model_match_request",
        "identity_group_by_match_flat",
        "identity_page_meta_present",
        "identity_page_meta_match_flat",
        "identity_range_numbers_present",
        "identity_range_numbers_match_flat",
        "identity_nav_present",
        "identity_nav_match_flat",
    ):
        if not isinstance(identity_consistency.get(key), bool):
            errors.append(f"fe_tree grouped_identity_summary.consistency.{key} must be bool")

    version = str(e2e.get("version") or "").strip()
    if version != "v0.4":
        errors.append(f"e2e grouped signature version must be v0.4, got {version or '-'}")

    grouped_cases = e2e.get("grouped_cases") if isinstance(e2e.get("grouped_cases"), list) else []
    if not grouped_cases:
        errors.append("e2e grouped_cases must be non-empty list")

    for idx, row in enumerate(grouped_cases):
        if not isinstance(row, dict):
            errors.append(f"e2e grouped_cases[{idx}] must be object")
            continue
        for key in (
            "case",
            "model",
            "group_by",
            "status",
            "has_group_summary",
            "has_grouped_rows",
            "supports_group_key",
            "supports_page_flags",
            "supports_page_window",
            "request_offset_matches_observed",
            "page_window_matches_range",
            "consistency_score",
            "response_keys",
        ):
            if key not in row:
                errors.append(f"e2e grouped_cases[{idx}] missing key: {key}")
        for key in (
            "has_group_summary",
            "has_grouped_rows",
            "supports_group_key",
            "supports_page_flags",
            "supports_page_window",
            "request_offset_matches_observed",
            "page_window_matches_range",
        ):
            if key in row and not isinstance(row.get(key), bool):
                errors.append(f"e2e grouped_cases[{idx}].{key} must be bool")
        if "response_keys" in row and not isinstance(row.get("response_keys"), list):
            errors.append(f"e2e grouped_cases[{idx}].response_keys must be list")
        consistency_score = row.get("consistency_score")
        if not isinstance(consistency_score, int):
            errors.append(f"e2e grouped_cases[{idx}].consistency_score must be int")
        elif consistency_score < 0 or consistency_score > 5:
            errors.append(f"e2e grouped_cases[{idx}].consistency_score must be in [0,5]")

        if row.get("status") == "ok" and row.get("has_grouped_rows") is True:
            if row.get("supports_group_key") is not True:
                errors.append(f"e2e grouped_cases[{idx}] grouped rows present but supports_group_key is not true")
            if row.get("supports_page_flags") is not True:
                errors.append(f"e2e grouped_cases[{idx}] grouped rows present but supports_page_flags is not true")
            if row.get("supports_page_window") is not True:
                errors.append(f"e2e grouped_cases[{idx}] grouped rows present but supports_page_window is not true")

    if errors:
        print("[grouped_contract_consistency_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[grouped_contract_consistency_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
