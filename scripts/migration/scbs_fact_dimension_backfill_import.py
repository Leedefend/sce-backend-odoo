"""Backfill low-weight SCBS dimension mapping candidates from staged facts.

This creates review mapping rows only:

- ``sc.legacy.business.entity.map`` rows for staged facts that have a legacy
  carrier but no business-entity map.
- ``sc.legacy.project.map`` rows for staged facts that have a legacy project
  name but no project map.

It does not create business entities, companies, projects, partners, or formal
business facts.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path("/tmp")


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fetch_missing_entities() -> list[dict[str, object]]:
    env.cr.execute(  # noqa: F821
        """
        SELECT legacy_xmid,
               MAX(legacy_xmmc) AS legacy_xmmc,
               COUNT(*) AS fact_rows,
               ROUND(SUM(amount_total)::numeric, 2) AS amount_total,
               STRING_AGG(DISTINCT source_table, ', ' ORDER BY source_table) AS source_tables,
               STRING_AGG(DISTINCT fact_family, ', ' ORDER BY fact_family) AS fact_families
          FROM sc_legacy_scbs_fact_staging s
         WHERE import_batch = 'scbs_fact_staging_v1'
           AND legacy_xmid IS NOT NULL AND legacy_xmid <> ''
           AND business_entity_map_id IS NULL
         GROUP BY legacy_xmid
         ORDER BY SUM(amount_total) DESC, COUNT(*) DESC
        """
    )
    columns = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def fetch_missing_projects() -> list[dict[str, object]]:
    env.cr.execute(  # noqa: F821
        """
        SELECT legacy_gcmc,
               COUNT(*) AS fact_rows,
               ROUND(SUM(amount_total)::numeric, 2) AS amount_total,
               STRING_AGG(DISTINCT source_table, ', ' ORDER BY source_table) AS source_tables,
               STRING_AGG(DISTINCT fact_family, ', ' ORDER BY fact_family) AS fact_families,
               MIN(document_date) AS min_date,
               MAX(document_date) AS max_date
          FROM sc_legacy_scbs_fact_staging s
         WHERE import_batch = 'scbs_fact_staging_v1'
           AND legacy_gcmc IS NOT NULL AND legacy_gcmc <> ''
           AND project_map_id IS NULL
         GROUP BY legacy_gcmc
         ORDER BY SUM(amount_total) DESC, COUNT(*) DESC
        """
    )
    columns = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def entity_type(name: str) -> str:
    if name == "公司综合平台":
        return "platform"
    if "劳务" in name:
        return "labor"
    if "商贸" in name or "建材销售" in name:
        return "trade"
    return "unknown"


def main() -> None:
    ensure_allowed_db()
    mode = os.getenv("SCBS_FACT_DIMENSION_BACKFILL_MODE", "dry-run")
    write_mode = mode == "write"
    if mode not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_mode": mode, "expected": ["dry-run", "write"]})

    artifacts = artifact_root()
    result_json = artifacts / "scbs_fact_dimension_backfill_result_v1.json"
    preview_csv = artifacts / "scbs_fact_dimension_backfill_preview_v1.csv"
    rollback_csv = artifacts / "scbs_fact_dimension_backfill_rollback_targets_v1.csv"

    EntityMap = env["sc.legacy.business.entity.map"]  # noqa: F821
    ProjectMap = env["sc.legacy.project.map"]  # noqa: F821
    entity_rows = fetch_missing_entities()
    project_rows = fetch_missing_projects()
    preview_rows: list[dict[str, object]] = []
    rollback_rows: list[dict[str, object]] = []
    created_entity_maps = 0
    updated_entity_maps = 0
    created_project_maps = 0
    updated_project_maps = 0

    for row in entity_rows:
        legacy_xmid = str(row["legacy_xmid"] or "").strip()
        legacy_xmmc = str(row["legacy_xmmc"] or "").strip()
        target_type = entity_type(legacy_xmmc)
        mapping = EntityMap.search(
            [("source_table", "=", "SCBS_FACT_BUSINESS_ENTITY_CANDIDATE"), ("legacy_xmid", "=", legacy_xmid)],
            limit=1,
        )
        vals = {
            "source_table": "SCBS_FACT_BUSINESS_ENTITY_CANDIDATE",
            "source_domain": "SCBS",
            "legacy_xmid": legacy_xmid,
            "legacy_xmmc": legacy_xmmc,
            "company_id": env.company.id,  # noqa: F821
            "mapping_state": "conflict" if "测试" in legacy_xmmc else "candidate",
            "suggested_entity_type": target_type,
            "source_count": 1,
            "rows_total": int(row["fact_rows"] or 0),
            "amount_total": float(row["amount_total"] or 0),
            "confidence": 0.25 if "测试" not in legacy_xmmc else 0.05,
            "evidence": json.dumps(
                {
                    "source": "scbs_fact_staging_v1_missing_entity_backfill",
                    "source_tables": row["source_tables"],
                    "fact_families": row["fact_families"],
                    "fact_rows": int(row["fact_rows"] or 0),
                    "amount_total": float(row["amount_total"] or 0),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        }
        preview_rows.append(
            {
                "dimension": "business_entity",
                "legacy_key": legacy_xmid,
                "legacy_name": legacy_xmmc,
                "action": "update" if mapping else "create",
                "mapping_state": vals["mapping_state"],
                "rows_total": vals["rows_total"],
                "amount_total": vals["amount_total"],
            }
        )
        if write_mode:
            if mapping:
                mapping.write(vals)
                updated_entity_maps += 1
            else:
                mapping = EntityMap.create(vals)
                created_entity_maps += 1
            rollback_rows.append({"model": "sc.legacy.business.entity.map", "id": mapping.id, "legacy_key": legacy_xmid, "name": legacy_xmmc})

    for row in project_rows:
        legacy_gcmc = str(row["legacy_gcmc"] or "").strip()
        mapping = ProjectMap.search(
            [("source_table", "=", "SCBS_FACT_PROJECT_CANDIDATE"), ("legacy_gcmc", "=", legacy_gcmc)],
            limit=1,
        )
        vals = {
            "source_table": "SCBS_FACT_PROJECT_CANDIDATE",
            "source_domain": "SCBS",
            "legacy_gcmc": legacy_gcmc,
            "company_id": env.company.id,  # noqa: F821
            "mapping_state": "ignored" if "测试" in legacy_gcmc else "candidate",
            "suggested_state": "ignored_test_candidate" if "测试" in legacy_gcmc else "single_source_project_candidate",
            "match_method": "none",
            "source_count": 1,
            "rows_total": int(row["fact_rows"] or 0),
            "amount_total": float(row["amount_total"] or 0),
            "min_date": row["min_date"] or False,
            "max_date": row["max_date"] or False,
            "confidence": 0.05 if "测试" in legacy_gcmc else 0.25,
            "evidence": json.dumps(
                {
                    "source": "scbs_fact_staging_v1_missing_project_backfill",
                    "source_tables": row["source_tables"],
                    "fact_families": row["fact_families"],
                    "fact_rows": int(row["fact_rows"] or 0),
                    "amount_total": float(row["amount_total"] or 0),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        }
        preview_rows.append(
            {
                "dimension": "project",
                "legacy_key": legacy_gcmc,
                "legacy_name": legacy_gcmc,
                "action": "update" if mapping else "create",
                "mapping_state": vals["mapping_state"],
                "rows_total": vals["rows_total"],
                "amount_total": vals["amount_total"],
            }
        )
        if write_mode:
            if mapping:
                mapping.write(vals)
                updated_project_maps += 1
            else:
                mapping = ProjectMap.create(vals)
                created_project_maps += 1
            rollback_rows.append({"model": "sc.legacy.project.map", "id": mapping.id, "legacy_key": legacy_gcmc, "name": legacy_gcmc})

    write_csv(preview_csv, ["dimension", "legacy_key", "legacy_name", "action", "mapping_state", "rows_total", "amount_total"], preview_rows)
    write_csv(rollback_csv, ["model", "id", "legacy_key", "name"], rollback_rows)
    if write_mode:
        env.cr.commit()  # noqa: F821
    payload = {
        "status": "PASS",
        "mode": mode,
        "database": env.cr.dbname,  # noqa: F821
        "entity_candidate_rows": len(entity_rows),
        "project_candidate_rows": len(project_rows),
        "created_entity_maps": created_entity_maps,
        "updated_entity_maps": updated_entity_maps,
        "created_project_maps": created_project_maps,
        "updated_project_maps": updated_project_maps,
        "preview_csv": str(preview_csv),
        "rollback_csv": str(rollback_csv),
    }
    write_json(result_json, payload)
    print("SCBS_FACT_DIMENSION_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
