"""Bootstrap SCBS business entities from confirmed legacy mapping candidates.

Run through Odoo shell:

    odoo shell -c /path/to/odoo.conf -d DB < scripts/migration/scbs_business_entity_bootstrap.py

Dry-run by default. Set ``SCBS_BUSINESS_ENTITY_BOOTSTRAP_APPLY=1`` to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from odoo import fields


SOURCE_DOMAIN = "SCBS"
BATCH = "scbs_business_entity_bootstrap_v1"


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


def normalize_entity_type(value: str | None) -> str:
    return value if value in {"internal", "affiliate", "trade", "labor", "platform", "project_carrier", "unknown"} else "unknown"


def main() -> None:
    artifacts = artifact_root()
    apply = os.getenv("SCBS_BUSINESS_ENTITY_BOOTSTRAP_APPLY") == "1"
    limit = int(os.getenv("SCBS_BUSINESS_ENTITY_BOOTSTRAP_LIMIT") or "0")

    Map = env["sc.legacy.business.entity.map"].sudo()
    Entity = env["sc.business.entity"].sudo()

    domain = [
        ("source_domain", "=", SOURCE_DOMAIN),
        ("active", "=", True),
        ("mapping_state", "=", "candidate"),
    ]
    maps = Map.search(domain, order="rows_total desc, legacy_xmmc")
    if limit:
        maps = maps[:limit]

    plan_rows: list[dict[str, object]] = []
    rollback_rows: list[dict[str, object]] = []
    created = 0
    linked_by_legacy = 0
    confirmed_existing = 0
    skipped_no_name = 0

    for rec in maps:
        proposal = ""
        target = rec.business_entity_id
        if not rec.legacy_xmmc:
            proposal = "skip_no_legacy_name"
            skipped_no_name += 1
        elif target:
            proposal = "confirm_existing_target"
        else:
            existing = Entity.search(
                [
                    ("company_id", "=", rec.company_id.id),
                    ("legacy_xmid", "=", rec.legacy_xmid),
                    ("active", "=", True),
                ],
                limit=1,
            )
            if existing:
                target = existing
                proposal = "link_existing_by_legacy_xmid"
            else:
                proposal = "create_business_entity"

        plan_rows.append(
            {
                "map_id": rec.id,
                "legacy_xmid": rec.legacy_xmid,
                "legacy_xmmc": rec.legacy_xmmc,
                "legacy_company_name": rec.legacy_company_name,
                "company": rec.company_id.display_name,
                "suggested_entity_type": rec.suggested_entity_type,
                "rows_total": rec.rows_total,
                "amount_total": rec.amount_total,
                "proposal": proposal,
                "target_business_entity_id": target.id if target else "",
                "target_business_entity_name": target.display_name if target else "",
            }
        )

        if not apply or proposal == "skip_no_legacy_name":
            continue

        if proposal == "create_business_entity":
            target = Entity.create(
                {
                    "name": rec.legacy_xmmc,
                    "company_id": rec.company_id.id,
                    "partner_id": rec.partner_id.id if rec.partner_id else False,
                    "entity_type": normalize_entity_type(rec.suggested_entity_type),
                    "mapping_state": "confirmed",
                    "legacy_xmid": rec.legacy_xmid,
                    "legacy_xmmc": rec.legacy_xmmc,
                    "legacy_company_id": rec.legacy_company_id,
                    "legacy_company_name": rec.legacy_company_name,
                    "note": f"Created by {BATCH}; source_table={rec.source_table}; source_domain={rec.source_domain}.",
                }
            )
            created += 1
            rollback_rows.append(
                {
                    "business_entity_id": target.id,
                    "name": target.name,
                    "legacy_xmid": target.legacy_xmid,
                    "company": target.company_id.display_name,
                }
            )
        elif proposal == "link_existing_by_legacy_xmid":
            linked_by_legacy += 1
        elif proposal == "confirm_existing_target":
            confirmed_existing += 1

        if target:
            rec.write(
                {
                    "business_entity_id": target.id,
                    "mapping_state": "confirmed",
                    "reviewer_id": env.user.id,
                    "reviewed_at": fields.Datetime.now(),
                    "note": ((rec.note or "") + f"\n{BATCH}: {proposal}").strip(),
                }
            )

    result = {
        "mode": "apply" if apply else "dry_run",
        "processed_rows": len(maps),
        "plan_csv": str(artifacts / "scbs_business_entity_bootstrap_plan_v1.csv"),
        "rollback_csv": str(artifacts / "scbs_business_entity_bootstrap_rollback_targets_v1.csv"),
        "result_json": str(artifacts / "scbs_business_entity_bootstrap_result_v1.json"),
        "created_business_entities": created,
        "linked_existing_by_legacy_xmid": linked_by_legacy,
        "confirmed_existing_targets": confirmed_existing,
        "skipped_no_legacy_name": skipped_no_name,
        "remaining_candidate_maps": Map.search_count(domain),
        "remaining_conflict_maps": Map.search_count([("source_domain", "=", SOURCE_DOMAIN), ("mapping_state", "=", "conflict")]),
    }

    write_csv(
        artifacts / "scbs_business_entity_bootstrap_plan_v1.csv",
        plan_rows,
        [
            "map_id",
            "legacy_xmid",
            "legacy_xmmc",
            "legacy_company_name",
            "company",
            "suggested_entity_type",
            "rows_total",
            "amount_total",
            "proposal",
            "target_business_entity_id",
            "target_business_entity_name",
        ],
    )
    write_csv(
        artifacts / "scbs_business_entity_bootstrap_rollback_targets_v1.csv",
        rollback_rows,
        ["business_entity_id", "name", "legacy_xmid", "company"],
    )
    write_json(artifacts / "scbs_business_entity_bootstrap_result_v1.json", result)

    if apply:
        env.cr.commit()

    print("SCBS_BUSINESS_ENTITY_BOOTSTRAP=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
