#!/usr/bin/env python3
"""Project legacy material categories into product.category in controlled batches."""

from __future__ import annotations

import json
import os
from pathlib import Path


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim,sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_limit() -> int:
    raw = (os.getenv("MIGRATION_MATERIAL_CATEGORY_LIMIT") or "200000").strip()
    try:
        value = int(raw)
    except ValueError:
        raise RuntimeError({"invalid_material_category_limit": raw})
    if value <= 0:
        raise RuntimeError({"invalid_material_category_limit": raw, "reason": "must_be_positive"})
    return min(value, 250000)


ensure_allowed_db()
artifact_root = resolve_artifact_root()
output_json = artifact_root / "fresh_db_material_category_projection_write_result_v1.json"
limit = normalize_limit()

LegacyCategory = env["sc.legacy.material.category"].sudo().with_context(active_test=False)  # noqa: F821
ProductCategory = env["product.category"].sudo().with_context(active_test=False)  # noqa: F821
IMD = env["ir.model.data"].sudo()  # noqa: F821
ROOT_PARENT_SENTINELS = {"0", "-1"}

records = LegacyCategory.search(
    [("legacy_category_id", "!=", False)],
    limit=limit,
    order="legacy_category_id,id",
)
existing = ProductCategory.search([("legacy_material_category_id", "in", records.ids)]) if records else ProductCategory.browse()
existing_by_legacy_id = {category.legacy_material_category_id.id: category for category in existing}

created = 0
updated = 0
category_by_legacy_key = {}
failures = []

for record in records:
    try:
        category = existing_by_legacy_id.get(record.id)
        vals = {
            "name": record.name or record.code or record.legacy_category_id,
            "legacy_material_category_id": record.id,
            "legacy_material_category_code": record.legacy_category_id,
        }
        if category:
            if category.name != vals["name"] or category.legacy_material_category_code != vals["legacy_material_category_code"]:
                category.write(vals)
            updated += 1
        else:
            category = ProductCategory.create(vals)
            created += 1
        category_by_legacy_key[record.legacy_category_id] = category
        xml_name = "legacy_material_category_%s" % record.legacy_category_id.replace("-", "_").replace(".", "_")
        if not IMD.search([("module", "=", "migration_assets"), ("name", "=", xml_name)], limit=1):
            IMD.create({"module": "migration_assets", "name": xml_name, "model": "product.category", "res_id": category.id})
        if (created + updated) % 1000 == 0:
            env.cr.commit()  # noqa: F821
    except Exception as exc:
        failures.append(
            {
                "legacy_category_id": record.legacy_category_id,
                "error": "%s: %s" % (type(exc).__name__, str(exc)[:240]),
            }
        )

parent_linked = 0
parent_missing = []
for record in records:
    parent_key = record.parent_legacy_category_id
    if not parent_key or parent_key in ROOT_PARENT_SENTINELS:
        continue
    category = category_by_legacy_key.get(record.legacy_category_id)
    parent = category_by_legacy_key.get(parent_key)
    if not category:
        continue
    if not parent:
        parent_missing.append({"legacy_category_id": record.legacy_category_id, "parent_legacy_category_id": parent_key})
        continue
    if category.parent_id != parent:
        try:
            category.write({"parent_id": parent.id})
            parent_linked += 1
        except Exception as exc:
            failures.append(
                {
                    "legacy_category_id": record.legacy_category_id,
                    "parent_legacy_category_id": parent_key,
                    "error": "%s: %s" % (type(exc).__name__, str(exc)[:240]),
                }
            )
    if parent_linked and (parent_linked % 1000) == 0:
        env.cr.commit()  # noqa: F821

env.cr.commit()  # noqa: F821

legacy_total = LegacyCategory.search_count([])
target_total = ProductCategory.search_count([("legacy_material_category_id", "!=", False)])
remaining = max(legacy_total - target_total, 0)
payload = {
    "status": "PASS" if not failures else "WARN",
    "mode": "fresh_db_material_category_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "limit": limit,
    "legacy_total": legacy_total,
    "selected": len(records),
    "created": created,
    "updated_or_seen": updated,
    "target_total": target_total,
    "remaining_unprojected": remaining,
    "parent_linked": parent_linked,
    "parent_missing_count": len(parent_missing),
    "failed_count": len(failures),
    "parent_missing_sample": parent_missing[:20],
    "failures": failures[:20],
    "db_writes": created + updated + parent_linked,
    "decision": "legacy_material_categories_projected_to_product_category",
}
write_json(output_json, payload)
print("MATERIAL_CATEGORY_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
