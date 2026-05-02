# -*- coding: utf-8 -*-
"""Read-only probe for legacy material product projection quality."""

from __future__ import annotations

import json
import os
from pathlib import Path


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


def rows(sql: str, params: list[object] | None = None) -> list[tuple[object, ...]]:
    env.cr.execute(sql, params or [])  # noqa: F821
    return env.cr.fetchall()  # noqa: F821


artifact_root = resolve_artifact_root()
output_json = artifact_root / "material_product_projection_probe_result_v1.json"

counts = {
    "legacy_material_detail_rows": int(scalar("SELECT COUNT(*) FROM sc_legacy_material_detail") or 0),
    "legacy_material_detail_active_rows": int(scalar("SELECT COUNT(*) FROM sc_legacy_material_detail WHERE active") or 0),
    "legacy_material_detail_promoted": int(
        scalar("SELECT COUNT(*) FROM sc_legacy_material_detail WHERE promotion_state = 'promoted'") or 0
    ),
    "legacy_material_detail_promoted_with_template": int(
        scalar(
            """
            SELECT COUNT(*)
            FROM sc_legacy_material_detail
            WHERE promotion_state = 'promoted'
              AND promoted_product_tmpl_id IS NOT NULL
            """
        )
        or 0
    ),
    "product_templates_from_legacy_material": int(
        scalar("SELECT COUNT(*) FROM product_template WHERE legacy_material_detail_id IS NOT NULL") or 0
    ),
    "product_variants_from_legacy_material": int(
        scalar(
            """
            SELECT COUNT(*)
            FROM product_product pp
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pt.legacy_material_detail_id IS NOT NULL
            """
        )
        or 0
    ),
    "legacy_product_templates_missing_variant": int(
        scalar(
            """
            SELECT COUNT(*)
            FROM product_template pt
            WHERE pt.legacy_material_detail_id IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM product_product pp WHERE pp.product_tmpl_id = pt.id
              )
            """
        )
        or 0
    ),
    "duplicate_product_legacy_material_ids": int(
        scalar(
            """
            SELECT COUNT(*)
            FROM (
              SELECT legacy_material_id
              FROM product_template
              WHERE legacy_material_id IS NOT NULL AND legacy_material_id <> ''
              GROUP BY legacy_material_id
              HAVING COUNT(*) > 1
            ) dup
            """
        )
        or 0
    ),
}

samples = {
    "projected_products": [
        {
            "template_id": row[0],
            "legacy_material_id": row[1],
            "default_code": row[2],
            "name": row[3],
            "variant_count": int(row[4]),
        }
        for row in rows(
            """
            SELECT pt.id, pt.legacy_material_id, pt.default_code, pt.name,
                   COUNT(pp.id) AS variant_count
            FROM product_template pt
            LEFT JOIN product_product pp ON pp.product_tmpl_id = pt.id
            WHERE pt.legacy_material_detail_id IS NOT NULL
            GROUP BY pt.id, pt.legacy_material_id, pt.default_code, pt.name
            ORDER BY pt.id DESC
            LIMIT 10
            """
        )
    ],
}

gaps = {
    "missing_legacy_material_detail": counts["legacy_material_detail_rows"] == 0,
    "missing_product_projection": counts["legacy_material_detail_rows"] > 0
    and counts["product_templates_from_legacy_material"] == 0,
    "promoted_without_template": counts["legacy_material_detail_promoted"]
    != counts["legacy_material_detail_promoted_with_template"],
    "projected_template_missing_variant": counts["legacy_product_templates_missing_variant"] > 0,
    "duplicate_legacy_material_id": counts["duplicate_product_legacy_material_ids"] > 0,
}
failing_gaps = [key for key, value in gaps.items() if value]

payload = {
    "status": "PASS" if not failing_gaps else "FAIL",
    "mode": "material_product_projection_probe",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "counts": counts,
    "samples": samples,
    "gaps": gaps,
    "decision": "material_product_projection_ready" if not failing_gaps else "material_product_projection_gap",
}
write_json(output_json, payload)
print("MATERIAL_PRODUCT_PROJECTION_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
