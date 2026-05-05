"""Confirm low-risk SCBS project and partner mappings.

The script is intentionally narrow:

- project: candidate + existing target project + exact match only;
- partner: candidate + existing single target partner + exact-name/tax-code match
  and not a tax-code conflict.

It never creates target projects or partners.

Run through Odoo shell. Dry-run by default:

    odoo shell -c /path/to/odoo.conf -d DB < scripts/migration/scbs_safe_mapping_confirm.py

Set ``SCBS_SAFE_MAPPING_CONFIRM_APPLY=1`` to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from odoo import fields


BATCH = "scbs_safe_mapping_confirm_v1"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("artifacts/migration")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_note(rec, text: str) -> str:
    return ((rec.note or "") + "\n" + text).strip()


def main() -> None:
    artifacts = artifact_root()
    apply = os.getenv("SCBS_SAFE_MAPPING_CONFIRM_APPLY") == "1"

    ProjectMap = env["sc.legacy.project.map"].sudo()
    PartnerMap = env["sc.legacy.partner.map"].sudo()

    project_domain = [
        ("mapping_state", "=", "candidate"),
        ("project_id", "!=", False),
        ("match_method", "=", "exact"),
    ]
    partner_domain = [
        ("mapping_state", "=", "candidate"),
        ("partner_id", "!=", False),
        ("target_partner_count", "=", 1),
        ("match_method", "in", ["tax_code", "exact_name"]),
        ("suggested_state", "!=", "tax_code_conflict"),
    ]

    rows: list[dict[str, object]] = []
    counts = {
        "project_confirmed": 0,
        "partner_confirmed": 0,
    }

    for rec in ProjectMap.search(project_domain, order="amount_total desc, legacy_gcmc"):
        rows.append(
            {
                "dimension": "project",
                "map_id": rec.id,
                "legacy_key": rec.legacy_gcmc,
                "match_method": rec.match_method,
                "suggested_state": rec.suggested_state,
                "target_id": rec.project_id.id,
                "target_name": rec.project_id.display_name,
                "fact_rows": rec.rows_total,
                "amount_total": rec.amount_total,
                "action": "confirm",
            }
        )
        if apply:
            rec.write(
                {
                    "mapping_state": "confirmed",
                    "reviewer_id": env.user.id,
                    "reviewed_at": fields.Datetime.now(),
                    "note": append_note(rec, BATCH),
                }
            )
            counts["project_confirmed"] += 1

    for rec in PartnerMap.search(partner_domain, order="legacy_rows desc, legacy_partner_name"):
        rows.append(
            {
                "dimension": "partner",
                "map_id": rec.id,
                "legacy_key": rec.legacy_key,
                "legacy_name": rec.legacy_partner_name,
                "match_method": rec.match_method,
                "suggested_state": rec.suggested_state,
                "target_id": rec.partner_id.id,
                "target_name": rec.partner_id.display_name,
                "fact_rows": rec.legacy_rows,
                "amount_total": "",
                "action": "confirm",
            }
        )
        if apply:
            rec.write(
                {
                    "mapping_state": "confirmed",
                    "reviewer_id": env.user.id,
                    "reviewed_at": fields.Datetime.now(),
                    "note": append_note(rec, BATCH),
                }
            )
            counts["partner_confirmed"] += 1

    result = {
        "mode": "apply" if apply else "dry_run",
        "planned_rows": len(rows),
        "project_planned": sum(1 for row in rows if row["dimension"] == "project"),
        "partner_planned": sum(1 for row in rows if row["dimension"] == "partner"),
        "counts": counts,
        "remaining_project_candidates": ProjectMap.search_count([("mapping_state", "=", "candidate")]),
        "remaining_partner_candidates": PartnerMap.search_count([("mapping_state", "=", "candidate")]),
        "plan_csv": str(artifacts / "scbs_safe_mapping_confirm_plan_v1.csv"),
        "result_json": str(artifacts / "scbs_safe_mapping_confirm_result_v1.json"),
    }

    write_csv(
        artifacts / "scbs_safe_mapping_confirm_plan_v1.csv",
        rows,
        [
            "dimension",
            "map_id",
            "legacy_key",
            "legacy_name",
            "match_method",
            "suggested_state",
            "target_id",
            "target_name",
            "fact_rows",
            "amount_total",
            "action",
        ],
    )
    write_json(artifacts / "scbs_safe_mapping_confirm_result_v1.json", result)

    if apply:
        env.cr.commit()

    print("SCBS_SAFE_MAPPING_CONFIRM=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
