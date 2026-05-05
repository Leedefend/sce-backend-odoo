"""Build SCBS staging blocker worklists by missing/conflict mapping dimension."""

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


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rows(query: str) -> list[dict[str, object]]:
    env.cr.execute(query)  # noqa: F821
    columns = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def md_table(items: list[dict[str, object]], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for item in items:
        lines.append("| " + " | ".join(str(item.get(column, "")) for column in columns) + " |")
    return lines


def main() -> None:
    artifacts = artifact_root()
    result_json = artifacts / "scbs_fact_staging_blocker_report_result_v1.json"
    summary_csv = artifacts / "scbs_fact_staging_blocker_summary_v1.csv"
    missing_csv = artifacts / "scbs_fact_staging_missing_mapping_worklist_v1.csv"
    conflict_csv = artifacts / "scbs_fact_staging_conflict_mapping_worklist_v1.csv"
    report_md = artifacts / "scbs_fact_staging_blocker_report_v1.md"

    summary = rows(
        """
        SELECT source_table, fact_family, mapping_gate_state,
               COUNT(*) AS row_count,
               ROUND(SUM(amount_total)::numeric, 2) AS amount_total,
               COUNT(*) FILTER (WHERE legacy_xmid IS NOT NULL AND legacy_xmid <> '' AND business_entity_map_id IS NULL) AS missing_entity_map,
               COUNT(*) FILTER (WHERE legacy_gcmc IS NOT NULL AND legacy_gcmc <> '' AND project_map_id IS NULL) AS missing_project_map,
               COUNT(*) FILTER (WHERE legacy_partner_name IS NOT NULL AND legacy_partner_name <> '' AND partner_map_id IS NULL) AS missing_partner_map,
               COUNT(*) FILTER (WHERE business_entity_mapping_state = 'conflict') AS conflict_entity_map,
               COUNT(*) FILTER (WHERE project_mapping_state = 'conflict') AS conflict_project_map,
               COUNT(*) FILTER (WHERE partner_mapping_state = 'conflict') AS conflict_partner_map
          FROM sc_legacy_scbs_fact_staging
         WHERE import_batch = 'scbs_fact_staging_v1'
         GROUP BY source_table, fact_family, mapping_gate_state
         ORDER BY source_table, mapping_gate_state
        """
    )
    missing = rows(
        """
        WITH missing AS (
            SELECT 'business_entity' AS dimension, source_table, fact_family,
                   legacy_xmid AS legacy_key, legacy_xmmc AS legacy_name,
                   COUNT(*) AS row_count, ROUND(SUM(amount_total)::numeric, 2) AS amount_total
              FROM sc_legacy_scbs_fact_staging
             WHERE import_batch = 'scbs_fact_staging_v1'
               AND legacy_xmid IS NOT NULL AND legacy_xmid <> ''
               AND business_entity_map_id IS NULL
             GROUP BY source_table, fact_family, legacy_xmid, legacy_xmmc
            UNION ALL
            SELECT 'project', source_table, fact_family,
                   legacy_gcmc, legacy_gcmc,
                   COUNT(*), ROUND(SUM(amount_total)::numeric, 2)
              FROM sc_legacy_scbs_fact_staging
             WHERE import_batch = 'scbs_fact_staging_v1'
               AND legacy_gcmc IS NOT NULL AND legacy_gcmc <> ''
               AND project_map_id IS NULL
             GROUP BY source_table, fact_family, legacy_gcmc
            UNION ALL
            SELECT 'partner', source_table, fact_family,
                   COALESCE(NULLIF(legacy_partner_tax_code, ''), legacy_partner_name), legacy_partner_name,
                   COUNT(*), ROUND(SUM(amount_total)::numeric, 2)
              FROM sc_legacy_scbs_fact_staging
             WHERE import_batch = 'scbs_fact_staging_v1'
               AND legacy_partner_name IS NOT NULL AND legacy_partner_name <> ''
               AND partner_map_id IS NULL
             GROUP BY source_table, fact_family, COALESCE(NULLIF(legacy_partner_tax_code, ''), legacy_partner_name), legacy_partner_name
        )
        SELECT * FROM missing ORDER BY amount_total DESC NULLS LAST, row_count DESC LIMIT 300
        """
    )
    conflict = rows(
        """
        WITH conflict AS (
            SELECT 'project' AS dimension, source_table, fact_family,
                   legacy_gcmc AS legacy_key, legacy_gcmc AS legacy_name,
                   project_mapping_state AS mapping_state,
                   COUNT(*) AS row_count, ROUND(SUM(amount_total)::numeric, 2) AS amount_total
              FROM sc_legacy_scbs_fact_staging
             WHERE import_batch = 'scbs_fact_staging_v1'
               AND project_mapping_state = 'conflict'
             GROUP BY source_table, fact_family, legacy_gcmc, project_mapping_state
            UNION ALL
            SELECT 'partner', source_table, fact_family,
                   COALESCE(NULLIF(legacy_partner_tax_code, ''), legacy_partner_name), legacy_partner_name,
                   partner_mapping_state,
                   COUNT(*), ROUND(SUM(amount_total)::numeric, 2)
              FROM sc_legacy_scbs_fact_staging
             WHERE import_batch = 'scbs_fact_staging_v1'
               AND partner_mapping_state = 'conflict'
             GROUP BY source_table, fact_family, COALESCE(NULLIF(legacy_partner_tax_code, ''), legacy_partner_name), legacy_partner_name, partner_mapping_state
        )
        SELECT * FROM conflict ORDER BY amount_total DESC NULLS LAST, row_count DESC LIMIT 300
        """
    )
    totals = rows(
        """
        SELECT COUNT(*) FILTER (WHERE mapping_gate_state = 'blocked') AS blocked_rows,
               ROUND(SUM(CASE WHEN mapping_gate_state = 'blocked' THEN amount_total ELSE 0 END)::numeric, 2) AS blocked_amount,
               COUNT(*) FILTER (WHERE mapping_gate_state = 'conflict') AS conflict_rows,
               ROUND(SUM(CASE WHEN mapping_gate_state = 'conflict' THEN amount_total ELSE 0 END)::numeric, 2) AS conflict_amount
          FROM sc_legacy_scbs_fact_staging
         WHERE import_batch = 'scbs_fact_staging_v1'
        """
    )[0]

    payload = {
        "status": "PASS",
        "database": env.cr.dbname,  # noqa: F821
        "totals": totals,
        "summary_csv": str(summary_csv),
        "missing_worklist_csv": str(missing_csv),
        "conflict_worklist_csv": str(conflict_csv),
        "report_md": str(report_md),
    }
    write_json(result_json, payload)
    write_csv(
        summary_csv,
        [
            "source_table",
            "fact_family",
            "mapping_gate_state",
            "row_count",
            "amount_total",
            "missing_entity_map",
            "missing_project_map",
            "missing_partner_map",
            "conflict_entity_map",
            "conflict_project_map",
            "conflict_partner_map",
        ],
        summary,
    )
    write_csv(missing_csv, ["dimension", "source_table", "fact_family", "legacy_key", "legacy_name", "row_count", "amount_total"], missing)
    write_csv(conflict_csv, ["dimension", "source_table", "fact_family", "legacy_key", "legacy_name", "mapping_state", "row_count", "amount_total"], conflict)

    lines = [
        "# SCBS Fact Staging Blocker Report",
        "",
        f"Database: `{payload['database']}`",
        "",
        "## Totals",
        "",
    ]
    lines.extend(md_table([totals], ["blocked_rows", "blocked_amount", "conflict_rows", "conflict_amount"]))
    lines.extend(["", "## By Source And Gate", ""])
    lines.extend(
        md_table(
            summary,
            [
                "source_table",
                "fact_family",
                "mapping_gate_state",
                "row_count",
                "amount_total",
                "missing_entity_map",
                "missing_project_map",
                "missing_partner_map",
                "conflict_project_map",
                "conflict_partner_map",
            ],
        )
    )
    lines.extend(["", "## Top Missing Mapping Worklist", ""])
    lines.extend(md_table(missing[:30], ["dimension", "source_table", "legacy_name", "row_count", "amount_total"]))
    lines.extend(["", "## Top Conflict Mapping Worklist", ""])
    lines.extend(md_table(conflict[:30], ["dimension", "source_table", "legacy_name", "row_count", "amount_total"]))
    lines.append("")
    report_md.write_text("\n".join(lines), encoding="utf-8")
    print("SCBS_FACT_STAGING_BLOCKER_REPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
