#!/usr/bin/env python3
"""Project all legacy material details into the formal material catalog model."""

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
        raise RuntimeError({"db_name_not_allowed_for_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def artifact_root() -> Path:
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


ensure_allowed_db()
output_json = artifact_root() / "fresh_db_material_catalog_projection_write_result_v1.json"
uid = env.uid  # noqa: F821

before = int(scalar("SELECT COUNT(*) FROM sc_material_catalog") or 0)
legacy_total = int(scalar("SELECT COUNT(*) FROM sc_legacy_material_detail") or 0)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_material_catalog (
      name, code, category_id, project_id, spec_model,
      uom_text, aux_uom_text, planned_price, internal_price,
      depth, pinyin, short_pinyin, remark, source_origin,
      legacy_material_detail_id, legacy_material_id, legacy_category_id,
      promoted_product_tmpl_id, promoted_product_id, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      COALESCE(NULLIF(l.name, ''), NULLIF(l.code, ''), l.legacy_material_id),
      NULLIF(l.code, ''),
      pc.id,
      l.project_id,
      NULLIF(l.spec_model, ''),
      NULLIF(l.uom_text, ''),
      NULLIF(l.aux_uom_text, ''),
      COALESCE(l.planned_price, 0.0),
      COALESCE(l.internal_price, 0.0),
      NULLIF(l.depth, ''),
      NULLIF(l.pinyin, ''),
      NULLIF(l.short_pinyin, ''),
      l.remark,
      'legacy',
      l.id,
      l.legacy_material_id,
      NULLIF(l.category_legacy_id, ''),
      l.promoted_product_tmpl_id,
      l.promoted_product_id,
      l.active,
      %s, NOW(), %s, NOW()
    FROM sc_legacy_material_detail l
    LEFT JOIN product_category pc ON pc.legacy_material_category_id = l.category_id
    ON CONFLICT (legacy_material_detail_id) DO UPDATE SET
      name = EXCLUDED.name,
      code = EXCLUDED.code,
      category_id = EXCLUDED.category_id,
      project_id = EXCLUDED.project_id,
      spec_model = EXCLUDED.spec_model,
      uom_text = EXCLUDED.uom_text,
      aux_uom_text = EXCLUDED.aux_uom_text,
      planned_price = EXCLUDED.planned_price,
      internal_price = EXCLUDED.internal_price,
      depth = EXCLUDED.depth,
      pinyin = EXCLUDED.pinyin,
      short_pinyin = EXCLUDED.short_pinyin,
      remark = EXCLUDED.remark,
      source_origin = EXCLUDED.source_origin,
      legacy_material_id = EXCLUDED.legacy_material_id,
      legacy_category_id = EXCLUDED.legacy_category_id,
      promoted_product_tmpl_id = EXCLUDED.promoted_product_tmpl_id,
      promoted_product_id = EXCLUDED.promoted_product_id,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)
affected = env.cr.rowcount  # noqa: F821
env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM sc_material_catalog") or 0)
legacy_carried = int(
    scalar("SELECT COUNT(*) FROM sc_material_catalog WHERE legacy_material_detail_id IS NOT NULL") or 0
)
with_category = int(
    scalar("SELECT COUNT(*) FROM sc_material_catalog WHERE legacy_material_detail_id IS NOT NULL AND category_id IS NOT NULL")
    or 0
)
with_project = int(
    scalar("SELECT COUNT(*) FROM sc_material_catalog WHERE legacy_material_detail_id IS NOT NULL AND project_id IS NOT NULL")
    or 0
)
with_product = int(
    scalar(
        """
        SELECT COUNT(*)
        FROM sc_material_catalog
        WHERE legacy_material_detail_id IS NOT NULL
          AND promoted_product_tmpl_id IS NOT NULL
        """
    )
    or 0
)

payload = {
    "status": "PASS" if legacy_carried == legacy_total else "FAIL",
    "mode": "fresh_db_material_catalog_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "legacy_total": legacy_total,
    "before": before,
    "after": after,
    "delta": after - before,
    "affected_rows": affected,
    "legacy_carried": legacy_carried,
    "remaining_unprojected": max(legacy_total - legacy_carried, 0),
    "with_category": with_category,
    "with_project": with_project,
    "with_promoted_product": with_product,
    "db_writes": affected,
    "decision": "legacy_material_details_projected_to_formal_material_catalog",
}
write_json(output_json, payload)
print("MATERIAL_CATALOG_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
