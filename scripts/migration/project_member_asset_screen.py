#!/usr/bin/env python3
"""Screen legacy project-member rows for assetization readiness without DB access."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_MEMBER_COLUMNS = {"ID", "USERID", "XMID", "XMMC", "LRR"}


class ProjectMemberScreenError(Exception):
    pass


def clean(value: object) -> str:
    return ("" if value is None else str(value)).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProjectMemberScreenError(message)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    require(path.exists(), f"missing member source csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def project_external_ids(project_manifest: dict[str, Any]) -> set[str]:
    records = project_manifest.get("records", [])
    require(isinstance(records, list) and records, "project external manifest records must be non-empty")
    return {clean(row.get("target_lookup", {}).get("value")) for row in records if clean(row.get("target_lookup", {}).get("value"))}


def screen(member_path: Path, project_external_path: Path, out_path: Path | None) -> dict[str, Any]:
    columns, rows = read_csv(member_path)
    missing_columns = sorted(REQUIRED_MEMBER_COLUMNS - set(columns))
    require(not missing_columns, f"missing member source columns: {missing_columns}")

    project_ids = project_external_ids(load_json(project_external_path))
    counters: Counter[str] = Counter()
    member_ids: Counter[str] = Counter()
    relation_keys: Counter[tuple[str, str]] = Counter()
    user_refs: Counter[str] = Counter()

    for row in rows:
        legacy_member_id = clean(row.get("ID"))
        legacy_project_id = clean(row.get("XMID"))
        legacy_user_ref = clean(row.get("USERID"))
        if not legacy_member_id:
            counters["missing_legacy_member_id"] += 1
        else:
            member_ids[legacy_member_id] += 1
        if not legacy_project_id:
            counters["missing_legacy_project_id"] += 1
        elif legacy_project_id not in project_ids:
            counters["project_anchor_missing_from_asset"] += 1
        else:
            counters["project_anchor_ready"] += 1
        if not legacy_user_ref:
            counters["missing_legacy_user_ref"] += 1
        else:
            user_refs[legacy_user_ref] += 1
        relation_keys[(legacy_project_id, legacy_user_ref)] += 1

    duplicate_member_ids = sum(1 for count in member_ids.values() if count > 1)
    duplicate_relation_keys = sum(1 for count in relation_keys.values() if count > 1)
    rows_with_duplicate_relation = sum(count for count in relation_keys.values() if count > 1)
    project_anchor_ready = counters["project_anchor_ready"]
    missing_user_refs = counters["missing_legacy_user_ref"]
    loadable_without_user_asset = 0

    payload = {
        "status": "PASS",
        "mode": "project_member_asset_screen",
        "db_writes": 0,
        "odoo_shell": False,
        "source_rows": len(rows),
        "target_model": "sc.project.member.staging",
        "target_asset_layer": "30_relation",
        "target_dependency_order": ["project_sc_v1", "user_sc_v1", "project_member_sc_v1"],
        "project_anchor_ready_rows": project_anchor_ready,
        "project_anchor_missing_rows": counters["project_anchor_missing_from_asset"],
        "missing_legacy_project_id_rows": counters["missing_legacy_project_id"],
        "distinct_legacy_member_ids": len(member_ids),
        "duplicate_legacy_member_id_keys": duplicate_member_ids,
        "distinct_legacy_user_refs": len(user_refs),
        "missing_legacy_user_ref_rows": missing_user_refs,
        "distinct_project_user_relation_keys": len(relation_keys),
        "duplicate_project_user_relation_keys": duplicate_relation_keys,
        "rows_in_duplicate_project_user_relations": rows_with_duplicate_relation,
        "loadable_without_user_asset": loadable_without_user_asset,
        "blocking_dependency": "user_sc_v1",
        "next_required_asset": {
            "asset_package_id": "user_sc_v1",
            "reason": "sc.project.member.staging.user_id is required; legacy USERID must resolve to repository-tracked res.users external ids before member XML can load.",
        },
        "assetization_decision": {
            "project_member_xml_generation": "defer_until_user_asset_exists",
            "role_fact_status": "missing",
            "role_or_responsibility_promotion": "blocked_no_role_fact",
            "duplicate_relation_strategy": "preserve_as_neutral_evidence_not_project_responsibility",
        },
        "counters": dict(sorted(counters.items())),
    }
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen project-member migration asset readiness without DB access.")
    parser.add_argument("--member", default="tmp/raw/project_member/project_member.csv", help="Legacy project-member CSV")
    parser.add_argument(
        "--project-external",
        default="migration_assets/manifest/project_external_id_manifest_v1.json",
        help="Project external id manifest",
    )
    parser.add_argument("--out", help="Optional runtime JSON output path")
    parser.add_argument("--check", action="store_true", help="Fail non-zero on screen errors")
    args = parser.parse_args()

    try:
        payload = screen(
            Path(args.member),
            Path(args.project_external),
            Path(args.out) if args.out else None,
        )
    except (ProjectMemberScreenError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("PROJECT_MEMBER_ASSET_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "PROJECT_MEMBER_ASSET_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "source_rows": payload["source_rows"],
                "project_anchor_ready_rows": payload["project_anchor_ready_rows"],
                "project_anchor_missing_rows": payload["project_anchor_missing_rows"],
                "distinct_legacy_user_refs": payload["distinct_legacy_user_refs"],
                "loadable_without_user_asset": payload["loadable_without_user_asset"],
                "blocking_dependency": payload["blocking_dependency"],
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
