#!/usr/bin/env python3
"""Promote legacy material detail rows into product templates in controlled batches."""

from __future__ import annotations

import json
import os
from pathlib import Path


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",")
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


def scalar(sql: str, params: list[object] | None = None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def product_type_value() -> dict[str, str]:
    fields = env["product.template"]._fields  # noqa: F821
    if "detailed_type" in fields:
        return {"detailed_type": "consu"}
    return {"type": "consu"}


def normalize_limit() -> int:
    raw = (os.getenv("MIGRATION_MATERIAL_PRODUCT_LIMIT") or "1000").strip()
    try:
        value = int(raw)
    except ValueError:
        raise RuntimeError({"invalid_material_product_limit": raw})
    if value <= 0:
        raise RuntimeError({"invalid_material_product_limit": raw, "reason": "must_be_positive"})
    return min(value, 50000)


ensure_allowed_db()
artifact_root = resolve_artifact_root()
output_json = artifact_root / "fresh_db_material_product_projection_write_result_v1.json"
limit = normalize_limit()

LegacyMaterial = env["sc.legacy.material.detail"].sudo().with_context(active_test=False)  # noqa: F821
ProductTemplate = env["product.template"].sudo().with_context(active_test=False)  # noqa: F821
unit_uom = env.ref("uom.product_uom_unit", raise_if_not_found=False)  # noqa: F821

legacy_total = int(scalar("SELECT COUNT(*) FROM sc_legacy_material_detail") or 0)
promoted_before = int(scalar("SELECT COUNT(*) FROM sc_legacy_material_detail WHERE promotion_state = 'promoted'") or 0)
product_before = int(scalar("SELECT COUNT(*) FROM product_template WHERE legacy_material_detail_id IS NOT NULL") or 0)

records = LegacyMaterial.search(
    [
        ("active", "=", True),
        ("promotion_state", "!=", "promoted"),
        ("promoted_product_tmpl_id", "=", False),
    ],
    limit=limit,
    order="legacy_material_id,id",
)

detail_ids = records.ids
legacy_ids = [value for value in records.mapped("legacy_material_id") if value]
existing_templates = ProductTemplate.browse()
if detail_ids:
    existing_templates |= ProductTemplate.search([("legacy_material_detail_id", "in", detail_ids)])
if legacy_ids:
    existing_templates |= ProductTemplate.search([("legacy_material_id", "in", legacy_ids)])

existing_by_detail = {template.legacy_material_detail_id.id: template for template in existing_templates if template.legacy_material_detail_id}
existing_by_legacy = {template.legacy_material_id: template for template in existing_templates if template.legacy_material_id}

default_codes = [record.code for record in records if record.code]
conflicting_templates = ProductTemplate.search(
    [
        ("default_code", "in", default_codes),
        ("legacy_material_detail_id", "=", False),
        ("legacy_material_id", "=", False),
    ]
) if default_codes else ProductTemplate.browse()
conflicting_default_codes = set(conflicting_templates.mapped("default_code"))

created = 0
linked_existing = 0
skipped_conflict = []
failed = []
template_ids = []
type_value = product_type_value()

for record in records:
    try:
        template = existing_by_detail.get(record.id) or existing_by_legacy.get(record.legacy_material_id)
        if not template and record.code and record.code in conflicting_default_codes:
            skipped_conflict.append(
                {
                    "legacy_material_id": record.legacy_material_id,
                    "code": record.code,
                    "reason": "default_code_exists_without_legacy_trace",
                }
            )
            continue
        vals = {
            "name": record.name,
            "default_code": record.code or record.legacy_material_id,
            "list_price": record.planned_price or 0.0,
            "standard_price": record.internal_price or 0.0,
            "uom_id": unit_uom.id if unit_uom else False,
            "uom_po_id": unit_uom.id if unit_uom else False,
            "legacy_material_detail_id": record.id,
            "legacy_material_id": record.legacy_material_id,
        }
        vals.update(type_value)
        if template:
            template.write(
                {
                    "legacy_material_detail_id": record.id,
                    "legacy_material_id": record.legacy_material_id,
                }
            )
            linked_existing += 1
        else:
            template = ProductTemplate.create(vals)
            created += 1
        record.write(
            {
                "promoted_product_tmpl_id": template.id,
                "promoted_product_id": template.product_variant_id.id,
                "promotion_state": "promoted",
            }
        )
        template_ids.append(template.id)
        if len(template_ids) % 500 == 0:
            env.cr.commit()  # noqa: F821
    except Exception as exc:
        failed.append(
            {
                "legacy_material_id": record.legacy_material_id,
                "error": "%s: %s" % (type(exc).__name__, str(exc)[:240]),
            }
        )

env.cr.commit()  # noqa: F821

promoted_after = int(scalar("SELECT COUNT(*) FROM sc_legacy_material_detail WHERE promotion_state = 'promoted'") or 0)
product_after = int(scalar("SELECT COUNT(*) FROM product_template WHERE legacy_material_detail_id IS NOT NULL") or 0)
product_variant_after = int(
    scalar(
        """
        SELECT COUNT(*)
        FROM product_product pp
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        WHERE pt.legacy_material_detail_id IS NOT NULL
        """
    )
    or 0
)
remaining_active = int(
    scalar(
        """
        SELECT COUNT(*)
        FROM sc_legacy_material_detail
        WHERE active
          AND COALESCE(promotion_state, 'archived') <> 'promoted'
          AND promoted_product_tmpl_id IS NULL
        """
    )
    or 0
)

payload = {
    "status": "PASS" if not failed else "WARN",
    "mode": "fresh_db_material_product_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "limit": limit,
    "legacy_total": legacy_total,
    "selected": len(records),
    "created": created,
    "linked_existing": linked_existing,
    "skipped_conflict_count": len(skipped_conflict),
    "failed_count": len(failed),
    "promoted_before": promoted_before,
    "promoted_after": promoted_after,
    "promoted_delta": promoted_after - promoted_before,
    "product_templates_before": product_before,
    "product_templates_after": product_after,
    "product_templates_delta": product_after - product_before,
    "product_variants_after": product_variant_after,
    "remaining_active_unpromoted": remaining_active,
    "sample_template_ids": template_ids[:20],
    "skipped_conflicts": skipped_conflict[:20],
    "failures": failed[:20],
}
write_json(output_json, payload)
print("MATERIAL_PRODUCT_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
