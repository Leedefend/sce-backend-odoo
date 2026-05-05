"""Build read-only reconciliation reports for SCBS fact staging."""

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


def fetch_dicts(query: str) -> list[dict[str, object]]:
    env.cr.execute(query)  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


def formal_model_counts() -> list[dict[str, object]]:
    models = [
        ("res_company", "res.company"),
        ("project_project", "project.project"),
        ("res_partner", "res.partner"),
        ("construction_contract", "construction.contract"),
    ]
    rows = []
    for table_name, model_name in models:
        Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
        all_count = Model.search_count([])
        if "active" in Model._fields:
            active_count = Model.search_count([("active", "=", True)])
            inactive_count = Model.search_count([("active", "=", False)])
        else:
            active_count = all_count
            inactive_count = 0
        rows.append(
            {
                "model": table_name,
                "all_count": all_count,
                "active_count": active_count,
                "inactive_count": inactive_count,
            }
        )
    return rows


def md_table(rows: list[dict[str, object]], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return lines


def main() -> None:
    artifacts = artifact_root()
    result_json = artifacts / "scbs_fact_staging_reconciliation_result_v1.json"
    by_gate_csv = artifacts / "scbs_fact_staging_reconciliation_by_gate_v1.csv"
    by_source_csv = artifacts / "scbs_fact_staging_reconciliation_by_source_v1.csv"
    report_md = artifacts / "scbs_fact_staging_reconciliation_report_v1.md"

    by_gate = fetch_dicts(
        """
        SELECT fact_family,
               mapping_gate_state,
               COUNT(*) AS row_count,
               ROUND(SUM(amount_total)::numeric, 2) AS amount_total,
               COUNT(*) FILTER (WHERE business_entity_map_id IS NOT NULL) AS with_entity_map,
               COUNT(*) FILTER (WHERE project_map_id IS NOT NULL) AS with_project_map,
               COUNT(*) FILTER (WHERE partner_map_id IS NOT NULL) AS with_partner_map
          FROM sc_legacy_scbs_fact_staging
         WHERE import_batch = 'scbs_fact_staging_v1'
           AND active IS TRUE
         GROUP BY fact_family, mapping_gate_state
         ORDER BY fact_family, mapping_gate_state
        """
    )
    by_source = fetch_dicts(
        """
        SELECT source_table,
               fact_family,
               COUNT(*) AS row_count,
               ROUND(SUM(amount_total)::numeric, 2) AS amount_total,
               MIN(document_date) AS min_date,
               MAX(document_date) AS max_date
          FROM sc_legacy_scbs_fact_staging
         WHERE import_batch = 'scbs_fact_staging_v1'
           AND active IS TRUE
         GROUP BY source_table, fact_family
         ORDER BY source_table
        """
    )
    excluded_by_gate = fetch_dicts(
        """
        SELECT fact_family,
               mapping_gate_state,
               COUNT(*) AS row_count,
               ROUND(SUM(amount_total)::numeric, 2) AS amount_total
          FROM sc_legacy_scbs_fact_staging
         WHERE import_batch = 'scbs_fact_staging_v1'
           AND active IS NOT TRUE
         GROUP BY fact_family, mapping_gate_state
         ORDER BY fact_family, mapping_gate_state
        """
    )
    formal_counts = formal_model_counts()
    total = fetch_dicts(
        """
        SELECT COUNT(*) AS row_count,
               ROUND(SUM(amount_total)::numeric, 2) AS amount_total,
               COUNT(*) FILTER (WHERE business_entity_map_id IS NOT NULL) AS with_entity_map,
               COUNT(*) FILTER (WHERE project_map_id IS NOT NULL) AS with_project_map,
               COUNT(*) FILTER (WHERE partner_map_id IS NOT NULL) AS with_partner_map,
               COUNT(*) FILTER (WHERE mapping_gate_state = 'projection_ready') AS projection_ready,
               COUNT(*) FILTER (WHERE mapping_gate_state = 'staging_ready') AS staging_ready,
               COUNT(*) FILTER (WHERE mapping_gate_state = 'blocked') AS blocked,
               COUNT(*) FILTER (WHERE mapping_gate_state = 'conflict') AS conflict
          FROM sc_legacy_scbs_fact_staging
         WHERE import_batch = 'scbs_fact_staging_v1'
           AND active IS TRUE
        """
    )[0]
    inactive_total = fetch_dicts(
        """
        SELECT COUNT(*) AS row_count,
               ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount_total
          FROM sc_legacy_scbs_fact_staging
         WHERE import_batch = 'scbs_fact_staging_v1'
           AND active IS NOT TRUE
        """
    )[0]
    status = "STAGING_IMPORTED_PROJECTION_BLOCKED" if total["projection_ready"] == 0 else "HAS_PROJECTION_READY_ROWS"
    payload = {
        "status": status,
        "database": env.cr.dbname,  # noqa: F821
        "total": total,
        "by_gate_csv": str(by_gate_csv),
        "by_source_csv": str(by_source_csv),
        "report_md": str(report_md),
        "formal_counts": formal_counts,
        "inactive_total": inactive_total,
    }

    write_json(result_json, payload)
    write_csv(
        by_gate_csv,
        [
            "fact_family",
            "mapping_gate_state",
            "row_count",
            "amount_total",
            "with_entity_map",
            "with_project_map",
            "with_partner_map",
        ],
        by_gate,
    )
    write_csv(by_source_csv, ["source_table", "fact_family", "row_count", "amount_total", "min_date", "max_date"], by_source)
    lines = [
        "# SCBS Fact Staging Reconciliation",
        "",
        f"Database: `{payload['database']}`",
        f"Status: `{status}`",
        "",
        "## Total",
        "",
    ]
    lines.extend(md_table([total], list(total.keys())))
    lines.extend(["", "## Excluded Total", ""])
    lines.extend(md_table([inactive_total], list(inactive_total.keys())))
    lines.extend(["", "## By Gate", ""])
    lines.extend(md_table(by_gate, ["fact_family", "mapping_gate_state", "row_count", "amount_total", "with_entity_map", "with_project_map", "with_partner_map"]))
    lines.extend(["", "## Excluded By Gate", ""])
    lines.extend(md_table(excluded_by_gate, ["fact_family", "mapping_gate_state", "row_count", "amount_total"]))
    lines.extend(["", "## By Source", ""])
    lines.extend(md_table(by_source, ["source_table", "fact_family", "row_count", "amount_total", "min_date", "max_date"]))
    lines.extend(["", "## Formal Table Counts", ""])
    lines.extend(md_table(formal_counts, ["model", "all_count", "active_count", "inactive_count"]))
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            "SCBS facts are imported into staging only. Formal projection remains blocked because no staged row is projection-ready.",
            "",
        ]
    )
    report_md.write_text("\n".join(lines), encoding="utf-8")
    print("SCBS_FACT_STAGING_RECONCILIATION=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
