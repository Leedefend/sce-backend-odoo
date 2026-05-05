#!/usr/bin/env python3
"""Plan or apply SCBS material catalog bootstrap.

Run through Odoo shell. By default this is a dry-run and writes only artifacts.

Environment switches:

- SCBS_MATERIAL_BOOTSTRAP_APPLY=1 writes changes.
- SCBS_MATERIAL_BOOTSTRAP_LINK_EXACT=1 links exact text candidates.
- SCBS_MATERIAL_BOOTSTRAP_CREATE_MISSING=1 creates missing material catalog rows.
- SCBS_MATERIAL_BOOTSTRAP_LIMIT=N limits processed rows for trial runs.
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path


ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
OUTPUT_CSV = ARTIFACT_ROOT / "scbs_material_catalog_bootstrap_plan_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "scbs_material_catalog_bootstrap_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "scbs_material_catalog_bootstrap_rollback_targets_v1.csv"


def truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "y"}


APPLY = truthy("SCBS_MATERIAL_BOOTSTRAP_APPLY")
LINK_EXACT = truthy("SCBS_MATERIAL_BOOTSTRAP_LINK_EXACT")
CREATE_MISSING = truthy("SCBS_MATERIAL_BOOTSTRAP_CREATE_MISSING")
LIMIT = int(os.getenv("SCBS_MATERIAL_BOOTSTRAP_LIMIT", "0") or "0")


def catalog_code(material_map) -> str:
    if material_map.legacy_material_id:
        return "SCBS-%s" % material_map.legacy_material_id[:24]
    return "SCBS-GROUP-%s" % material_map.material_key[:24]


def proposed_action(material_map) -> str:
    if material_map.material_catalog_id:
        return "already_linked"
    if material_map.mapping_state == "ignored":
        return "ignored"
    if material_map.mapping_state == "conflict":
        return "blocked_conflict"
    if material_map.exact_text_catalog_id and material_map.exact_text_match_count == 1:
        return "link_existing_exact"
    if material_map.name_spec_catalog_id and material_map.name_spec_match_count == 1:
        return "review_name_spec_candidate"
    if material_map.material_name:
        return "create_catalog"
    return "blocked_missing_material_name"


def plan_row(material_map, action: str, target=None) -> dict[str, object]:
    return {
        "map_id": material_map.id,
        "material_key": material_map.material_key or "",
        "legacy_material_id": material_map.legacy_material_id or "",
        "material_name": material_map.material_name or "",
        "spec_model": material_map.spec_model or "",
        "uom_text": material_map.uom_text or "",
        "company_id": material_map.company_id.id,
        "company_name": material_map.company_id.display_name,
        "mapping_state": material_map.mapping_state,
        "coverage_state": material_map.coverage_state,
        "amount_total": material_map.amount_total,
        "line_rows": material_map.line_rows,
        "header_rows": material_map.header_rows,
        "proposed_action": action,
        "target_catalog_id": target.id if target else (material_map.material_catalog_id.id or ""),
        "target_catalog_name": target.display_name if target else (material_map.material_catalog_id.display_name or ""),
        "apply_status": "planned",
    }


def create_catalog(material_map):
    Catalog = env["sc.material.catalog"].sudo()  # noqa: F821
    legacy_id = material_map.legacy_material_id or False
    existing = False
    if legacy_id:
        existing = Catalog.search(
            [
                ("company_id", "=", material_map.company_id.id),
                ("legacy_material_id", "=", legacy_id),
            ],
            limit=1,
        )
    if not existing:
        existing = Catalog.search(
            [
                ("company_id", "=", material_map.company_id.id),
                ("name", "=", material_map.material_name),
                ("spec_model", "=", material_map.spec_model or False),
                ("uom_text", "=", material_map.uom_text or False),
            ],
            limit=1,
        )
    if existing:
        return existing, False
    catalog = Catalog.create(
        {
            "company_id": material_map.company_id.id,
            "name": material_map.material_name,
            "code": catalog_code(material_map),
            "spec_model": material_map.spec_model or False,
            "uom_text": material_map.uom_text or False,
            "source_origin": "legacy",
            "legacy_material_id": legacy_id,
            "remark": "SCBS material bootstrap; source_table=%s; material_key=%s"
            % (material_map.source_table or "", material_map.material_key or ""),
        }
    )
    return catalog, True


def main() -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    MaterialMap = env["sc.legacy.scbs.material.map"].sudo()  # noqa: F821
    domain = [("source_domain", "=", "SCBS")]
    records = MaterialMap.search(domain, order="mapping_state, review_priority, amount_total desc, id")
    if LIMIT:
        records = records[:LIMIT]

    rows = []
    rollback_rows = []
    counters: Counter[str] = Counter()
    applied_counters: Counter[str] = Counter()

    for material_map in records:
        action = proposed_action(material_map)
        target = None
        created = False
        apply_status = "dry_run"
        if action == "already_linked":
            target = material_map.material_catalog_id
            if APPLY and material_map.mapping_state != "confirmed":
                material_map.write({"mapping_state": "confirmed"})
                apply_status = "confirmed_existing_link"
                applied_counters[apply_status] += 1
            else:
                apply_status = "skipped_already_linked"
        elif action == "link_existing_exact":
            target = material_map.exact_text_catalog_id
            if APPLY and LINK_EXACT:
                material_map.write(
                    {
                        "material_catalog_id": target.id,
                        "mapping_state": "confirmed",
                    }
                )
                apply_status = "linked_exact"
                applied_counters[apply_status] += 1
            elif APPLY:
                apply_status = "skipped_link_exact_switch_off"
        elif action == "create_catalog":
            if APPLY and CREATE_MISSING:
                target, created = create_catalog(material_map)
                material_map.write(
                    {
                        "material_catalog_id": target.id,
                        "mapping_state": "confirmed",
                    }
                )
                apply_status = "created_catalog" if created else "linked_existing_by_business_key"
                applied_counters[apply_status] += 1
                if created:
                    rollback_rows.append(
                        {
                            "model": "sc.material.catalog",
                            "id": target.id,
                            "legacy_material_id": target.legacy_material_id or "",
                            "name": target.name,
                            "code": target.code or "",
                        }
                    )
            elif APPLY:
                apply_status = "skipped_create_missing_switch_off"

        row = plan_row(material_map, action, target)
        row["apply_status"] = apply_status
        rows.append(row)
        counters[action] += 1

    fieldnames = [
        "map_id",
        "material_key",
        "legacy_material_id",
        "material_name",
        "spec_model",
        "uom_text",
        "company_id",
        "company_name",
        "mapping_state",
        "coverage_state",
        "amount_total",
        "line_rows",
        "header_rows",
        "proposed_action",
        "target_catalog_id",
        "target_catalog_name",
        "apply_status",
    ]
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with ROLLBACK_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["model", "id", "legacy_material_id", "name", "code"])
        writer.writeheader()
        writer.writerows(rollback_rows)

    result = {
        "mode": "apply" if APPLY else "dry_run",
        "link_exact_enabled": LINK_EXACT,
        "create_missing_enabled": CREATE_MISSING,
        "processed_rows": len(rows),
        "proposal_counts": dict(sorted(counters.items())),
        "applied_counts": dict(sorted(applied_counters.items())),
        "output_csv": str(OUTPUT_CSV),
        "rollback_csv": str(ROLLBACK_CSV),
        "safe_next_step": (
            "review plan CSV; rerun with SCBS_MATERIAL_BOOTSTRAP_APPLY=1 and selected switches"
            if not APPLY
            else "run material coverage report again and review confirmed mappings"
        ),
    }
    if APPLY:
        env.cr.commit()  # noqa: F821
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


main()
