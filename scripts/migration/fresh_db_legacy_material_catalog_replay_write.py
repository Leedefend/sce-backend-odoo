#!/usr/bin/env python3
"""Bulk replay legacy material catalog facts into neutral carrier models."""

from __future__ import annotations

import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_legacy_material_catalog_replay_adapter_result_v1.json").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bulk_load(csv_path: Path, temp_table: str, columns: list[str]) -> None:
    env.cr.execute(f"DROP TABLE IF EXISTS {temp_table}")  # noqa: F821
    env.cr.execute(f"CREATE TEMP TABLE {temp_table} ({', '.join(f'{col} text' for col in columns)}) ON COMMIT DROP")  # noqa: F821
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        env.cr.copy_expert(  # noqa: F821
            f"COPY {temp_table} ({', '.join(columns)}) FROM STDIN WITH CSV HEADER",
            handle,
        )


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_material_catalog_replay_adapter_result_v1.json"
CATEGORY_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_material_category_replay_payload_v1.csv"
DETAIL_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_material_detail_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_material_catalog_replay_write_result_v1.json"

CATEGORY_COLUMNS = [
    "legacy_category_id",
    "legacy_guid",
    "code",
    "name",
    "parent_legacy_category_id",
    "legacy_project_id",
    "depth",
    "uom_text",
    "source_table",
    "note",
    "active",
]
DETAIL_COLUMNS = [
    "legacy_material_id",
    "code",
    "name",
    "category_legacy_id",
    "parent_legacy_material_id",
    "uom_text",
    "aux_uom_text",
    "planned_price",
    "internal_price",
    "legacy_project_id",
    "depth",
    "spec_model",
    "pinyin",
    "short_pinyin",
    "import_time",
    "remark",
    "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821

bulk_load(CATEGORY_CSV, "tmp_legacy_material_category", CATEGORY_COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_material_category")  # noqa: F821
category_before = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_material_detail")  # noqa: F821
detail_before = env.cr.fetchone()[0]  # noqa: F821
input_detail_rows = int(manifest.get("detail_rows") or 0)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_material_category (
      legacy_category_id, legacy_guid, code, name, parent_legacy_category_id,
      legacy_project_id, project_id, depth, uom_text, source_table, note, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_category_id,
      NULLIF(t.legacy_guid, ''),
      NULLIF(t.code, ''),
      COALESCE(NULLIF(t.name, ''), t.legacy_category_id),
      NULLIF(t.parent_legacy_category_id, ''),
      NULLIF(t.legacy_project_id, ''),
      p.id,
      NULLIF(t.depth, ''),
      NULLIF(t.uom_text, ''),
      COALESCE(NULLIF(t.source_table, ''), 'C_Base_CBFL'),
      NULLIF(t.note, ''),
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_material_category t
    LEFT JOIN project_project p ON p.legacy_project_id = NULLIF(t.legacy_project_id, '')
    ON CONFLICT (legacy_category_id) DO UPDATE SET
      legacy_guid = EXCLUDED.legacy_guid,
      code = EXCLUDED.code,
      name = EXCLUDED.name,
      parent_legacy_category_id = EXCLUDED.parent_legacy_category_id,
      legacy_project_id = EXCLUDED.legacy_project_id,
      project_id = EXCLUDED.project_id,
      depth = EXCLUDED.depth,
      uom_text = EXCLUDED.uom_text,
      source_table = EXCLUDED.source_table,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_legacy_material_category child
    SET parent_id = parent.id, write_uid = %s, write_date = NOW()
    FROM sc_legacy_material_category parent
    WHERE child.parent_legacy_category_id IS NOT NULL
      AND child.parent_legacy_category_id <> ''
      AND parent.legacy_category_id = child.parent_legacy_category_id
    """,
    [uid],
)

env.cr.execute("DROP TABLE IF EXISTS tmp_legacy_material_category_map")  # noqa: F821
env.cr.execute(  # noqa: F821
    """
    CREATE TEMP TABLE tmp_legacy_material_category_map AS
    SELECT legacy_category_id AS category_key, id
    FROM sc_legacy_material_category
    WHERE legacy_category_id IS NOT NULL
    UNION ALL
    SELECT LOWER(legacy_guid) AS category_key, id
    FROM sc_legacy_material_category
    WHERE legacy_guid IS NOT NULL AND legacy_guid <> ''
    """
)
env.cr.execute("CREATE INDEX tmp_legacy_material_category_map_key_idx ON tmp_legacy_material_category_map(category_key)")  # noqa: F821

if detail_before < input_detail_rows:
    bulk_load(DETAIL_CSV, "tmp_legacy_material_detail", DETAIL_COLUMNS)
    env.cr.execute(  # noqa: F821
        """
        INSERT INTO sc_legacy_material_detail (
          legacy_material_id, code, name, category_legacy_id, category_id,
          parent_legacy_material_id, uom_text, aux_uom_text, planned_price,
          internal_price, legacy_project_id, project_id, depth, spec_model, pinyin,
          short_pinyin, import_time, remark, source_table, active,
          create_uid, create_date, write_uid, write_date
        )
        SELECT
          t.legacy_material_id,
          NULLIF(t.code, ''),
          COALESCE(NULLIF(t.name, ''), t.legacy_material_id),
          NULLIF(t.category_legacy_id, ''),
          c.id,
          NULLIF(t.parent_legacy_material_id, ''),
          NULLIF(t.uom_text, ''),
          NULLIF(t.aux_uom_text, ''),
          COALESCE(NULLIF(t.planned_price, '')::numeric, 0),
          COALESCE(NULLIF(t.internal_price, '')::numeric, 0),
          NULLIF(t.legacy_project_id, ''),
          p.id,
          NULLIF(t.depth, ''),
          NULLIF(t.spec_model, ''),
          NULLIF(t.pinyin, ''),
          NULLIF(t.short_pinyin, ''),
          NULLIF(t.import_time, '')::timestamp,
          NULLIF(t.remark, ''),
          'T_Base_MaterialDetail',
          COALESCE(NULLIF(t.active, ''), '1') = '1',
          %s, NOW(), %s, NOW()
        FROM tmp_legacy_material_detail t
        LEFT JOIN tmp_legacy_material_category_map c ON c.category_key = LOWER(NULLIF(t.category_legacy_id, ''))
        LEFT JOIN project_project p ON p.legacy_project_id = NULLIF(t.legacy_project_id, '')
        ON CONFLICT (legacy_material_id) DO UPDATE SET
          code = EXCLUDED.code,
          name = EXCLUDED.name,
          category_legacy_id = EXCLUDED.category_legacy_id,
          category_id = EXCLUDED.category_id,
          parent_legacy_material_id = EXCLUDED.parent_legacy_material_id,
          uom_text = EXCLUDED.uom_text,
          aux_uom_text = EXCLUDED.aux_uom_text,
          planned_price = EXCLUDED.planned_price,
          internal_price = EXCLUDED.internal_price,
          legacy_project_id = EXCLUDED.legacy_project_id,
          project_id = EXCLUDED.project_id,
          depth = EXCLUDED.depth,
          spec_model = EXCLUDED.spec_model,
          pinyin = EXCLUDED.pinyin,
          short_pinyin = EXCLUDED.short_pinyin,
          import_time = EXCLUDED.import_time,
          remark = EXCLUDED.remark,
          active = EXCLUDED.active,
          write_uid = EXCLUDED.write_uid,
          write_date = NOW()
        """,
        [uid, uid],
    )

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_legacy_material_detail detail
    SET category_id = category_map.id, write_uid = %s, write_date = NOW()
    FROM tmp_legacy_material_category_map category_map
    WHERE category_map.category_key = LOWER(detail.category_legacy_id)
      AND detail.category_id IS DISTINCT FROM category_map.id
    """,
    [uid],
)

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_material_category")  # noqa: F821
category_after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_material_detail")  # noqa: F821
detail_after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_material_detail WHERE project_id IS NOT NULL")  # noqa: F821
detail_project_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_material_detail WHERE category_id IS NOT NULL")  # noqa: F821
detail_category_linked = env.cr.fetchone()[0]  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_material_catalog_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_category_rows": manifest.get("category_rows"),
    "input_detail_rows": manifest.get("detail_rows"),
    "category_before": category_before,
    "category_after": category_after,
    "category_delta": category_after - category_before,
    "detail_before": detail_before,
    "detail_after": detail_after,
    "detail_delta": detail_after - detail_before,
    "detail_project_linked": detail_project_linked,
    "detail_category_linked": detail_category_linked,
    "db_writes": max(category_after - category_before, 0) + max(detail_after - detail_before, 0),
    "decision": "legacy_material_catalog_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_MATERIAL_CATALOG_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
