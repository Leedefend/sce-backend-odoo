#!/usr/bin/env python3
"""Screen legacy user facts available for repository assetization."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = {"USERID", "LRR"}


class UserAssetScreenError(Exception):
    pass


def clean(value: object) -> str:
    return ("" if value is None else str(value)).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UserAssetScreenError(message)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    require(path.exists(), f"missing source csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def screen(member_path: Path, out_path: Path | None) -> dict[str, Any]:
    columns, rows = read_csv(member_path)
    missing_columns = sorted(REQUIRED_COLUMNS - set(columns))
    require(not missing_columns, f"missing user projection columns: {missing_columns}")

    names_by_user_ref: dict[str, Counter[str]] = defaultdict(Counter)
    rows_by_user_ref: Counter[str] = Counter()
    missing_user_ref = 0
    missing_name = 0

    for row in rows:
        user_ref = clean(row.get("USERID"))
        user_name = clean(row.get("LRR"))
        if not user_ref:
            missing_user_ref += 1
            continue
        rows_by_user_ref[user_ref] += 1
        if not user_name:
            missing_name += 1
        else:
            names_by_user_ref[user_ref][user_name] += 1

    conflicting_name_refs = {
        user_ref: dict(name_counts)
        for user_ref, name_counts in names_by_user_ref.items()
        if len(name_counts) > 1
    }
    canonical_candidates = []
    for user_ref, row_count in sorted(rows_by_user_ref.items()):
        name_counts = names_by_user_ref.get(user_ref, Counter())
        canonical_name = name_counts.most_common(1)[0][0] if name_counts else ""
        canonical_candidates.append(
            {
                "legacy_user_ref": user_ref,
                "candidate_login": user_ref,
                "candidate_name": canonical_name,
                "source_row_count": row_count,
                "name_variant_count": len(name_counts),
            }
        )

    source_sufficiency = "insufficient_for_authority_asset"
    can_generate_res_users_xml = False
    if rows_by_user_ref and not missing_user_ref and not missing_name and not conflicting_name_refs:
        source_sufficiency = "projection_only_not_authoritative"

    payload: dict[str, Any] = {
        "status": "PASS",
        "mode": "user_asset_screen",
        "db_writes": 0,
        "odoo_shell": False,
        "source_rows": len(rows),
        "source_fact_type": "project_member_user_projection",
        "target_model": "res.users",
        "authority_surface": True,
        "distinct_legacy_user_refs": len(rows_by_user_ref),
        "missing_legacy_user_ref_rows": missing_user_ref,
        "missing_user_name_rows": missing_name,
        "conflicting_name_user_refs": len(conflicting_name_refs),
        "can_generate_res_users_xml": can_generate_res_users_xml,
        "source_sufficiency": source_sufficiency,
        "blocking_reason": "authoritative_user_source_required",
        "next_required_source": {
            "source": "legacy user master table or approved user seed whitelist",
            "minimum_fields": ["legacy_user_ref", "name", "login"],
            "explicitly_deferred_fields": ["groups_id", "sc_role_profile", "department", "post", "manager"],
        },
        "project_member_dependency_resolution": {
            "required_asset_package": "user_sc_v1",
            "status": "blocked_until_user_asset_policy_freezes",
        },
        "candidate_count": len(canonical_candidates),
        "sample_candidates": canonical_candidates[:20],
        "conflicting_name_samples": dict(list(conflicting_name_refs.items())[:20]),
    }
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen available user facts for migration assetization.")
    parser.add_argument("--member", default="tmp/raw/project_member/project_member.csv", help="Legacy member CSV")
    parser.add_argument("--out", help="Optional runtime JSON output path")
    parser.add_argument("--check", action="store_true", help="Fail non-zero on screen errors")
    args = parser.parse_args()

    try:
        payload = screen(Path(args.member), Path(args.out) if args.out else None)
    except (UserAssetScreenError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("USER_ASSET_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "USER_ASSET_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "source_rows": payload["source_rows"],
                "distinct_legacy_user_refs": payload["distinct_legacy_user_refs"],
                "can_generate_res_users_xml": payload["can_generate_res_users_xml"],
                "source_sufficiency": payload["source_sufficiency"],
                "blocking_reason": payload["blocking_reason"],
                "db_writes": 0,
                "odoo_shell": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
