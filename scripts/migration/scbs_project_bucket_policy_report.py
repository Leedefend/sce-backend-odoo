#!/usr/bin/env python3
"""Report SCBS active facts that need a project bucket for formal projection."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


PG_CONTAINER = os.getenv("ODOO_PG_CONTAINER", "sc-backend-odoo-prod-sim-db-1")
PG_DATABASE = os.getenv("ODOO_DATABASE", "sc_prod_sim")
PG_USER = os.getenv("ODOO_PG_USER", "odoo")
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))


def run_psql(sql: str) -> list[str]:
    cmd = [
        "docker",
        "exec",
        "-i",
        PG_CONTAINER,
        "psql",
        "-U",
        PG_USER,
        "-d",
        PG_DATABASE,
        "-t",
        "-A",
        "-F",
        "|",
        "-c",
        sql,
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=True)
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def parse_rows(lines: list[str], fields: list[str]) -> list[dict[str, str]]:
    rows = []
    for line in lines:
        parts = line.split("|")
        if len(parts) != len(fields):
            raise RuntimeError({"unexpected_row": line, "expected_fields": fields})
        rows.append(dict(zip(fields, parts)))
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main() -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)

    summary = parse_rows(
        run_psql(
            """
SELECT fact_family,
       source_table,
       COUNT(*)::text AS rows,
       ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2)::text AS amount_total,
       COUNT(*) FILTER (WHERE business_entity_id IS NOT NULL)::text AS with_business_entity,
       COUNT(DISTINCT business_entity_id)::text AS business_entity_count,
       COUNT(*) FILTER (WHERE partner_id IS NOT NULL)::text AS with_partner,
       COUNT(DISTINCT partner_id)::text AS partner_count
  FROM sc_legacy_scbs_fact_staging
 WHERE import_batch = 'scbs_fact_staging_v1'
   AND active IS TRUE
   AND mapping_gate_state = 'projection_ready'
   AND project_id IS NULL
   AND fact_family IN ('payment', 'supplier_contract', 'stock_in')
 GROUP BY fact_family, source_table
 ORDER BY fact_family;
"""
        ),
        [
            "fact_family",
            "source_table",
            "rows",
            "amount_total",
            "with_business_entity",
            "business_entity_count",
            "with_partner",
            "partner_count",
        ],
    )
    by_entity = parse_rows(
        run_psql(
            """
SELECT s.fact_family,
       COALESCE(be.name, '[NO_BUSINESS_ENTITY]') AS business_entity,
       COUNT(*)::text AS rows,
       ROUND(COALESCE(SUM(s.amount_total), 0)::numeric, 2)::text AS amount_total,
       COUNT(DISTINCT s.partner_id)::text AS partner_count,
       COUNT(DISTINCT COALESCE(NULLIF(s.legacy_partner_name, ''), '[NO_PARTNER_TEXT]'))::text AS legacy_partner_text_count
  FROM sc_legacy_scbs_fact_staging s
  LEFT JOIN sc_business_entity be ON be.id = s.business_entity_id
 WHERE s.import_batch = 'scbs_fact_staging_v1'
   AND s.active IS TRUE
   AND s.mapping_gate_state = 'projection_ready'
   AND s.project_id IS NULL
   AND s.fact_family IN ('payment', 'supplier_contract', 'stock_in')
 GROUP BY s.fact_family, COALESCE(be.name, '[NO_BUSINESS_ENTITY]')
 ORDER BY s.fact_family, SUM(s.amount_total) DESC NULLS LAST;
"""
        ),
        [
            "fact_family",
            "business_entity",
            "rows",
            "amount_total",
            "partner_count",
            "legacy_partner_text_count",
        ],
    )
    top_partner = parse_rows(
        run_psql(
            """
SELECT s.fact_family,
       COALESCE(be.name, '[NO_BUSINESS_ENTITY]') AS business_entity,
       COALESCE(rp.name, NULLIF(s.legacy_partner_name, ''), '[NO_PARTNER]') AS partner_name,
       COUNT(*)::text AS rows,
       ROUND(COALESCE(SUM(s.amount_total), 0)::numeric, 2)::text AS amount_total
  FROM sc_legacy_scbs_fact_staging s
  LEFT JOIN sc_business_entity be ON be.id = s.business_entity_id
  LEFT JOIN res_partner rp ON rp.id = s.partner_id
 WHERE s.import_batch = 'scbs_fact_staging_v1'
   AND s.active IS TRUE
   AND s.mapping_gate_state = 'projection_ready'
   AND s.project_id IS NULL
   AND s.fact_family IN ('payment', 'supplier_contract', 'stock_in')
 GROUP BY s.fact_family, COALESCE(be.name, '[NO_BUSINESS_ENTITY]'), COALESCE(rp.name, NULLIF(s.legacy_partner_name, ''), '[NO_PARTNER]')
 ORDER BY SUM(s.amount_total) DESC NULLS LAST
 LIMIT 100;
"""
        ),
        ["fact_family", "business_entity", "partner_name", "rows", "amount_total"],
    )

    summary_csv = ARTIFACT_ROOT / "scbs_project_bucket_policy_summary_v1.csv"
    entity_csv = ARTIFACT_ROOT / "scbs_project_bucket_policy_by_entity_v1.csv"
    partner_csv = ARTIFACT_ROOT / "scbs_project_bucket_policy_top_partners_v1.csv"
    report_md = ARTIFACT_ROOT / "scbs_project_bucket_policy_report_v1.md"
    result_json = ARTIFACT_ROOT / "scbs_project_bucket_policy_report_result_v1.json"

    write_csv(
        summary_csv,
        summary,
        [
            "fact_family",
            "source_table",
            "rows",
            "amount_total",
            "with_business_entity",
            "business_entity_count",
            "with_partner",
            "partner_count",
        ],
    )
    write_csv(
        entity_csv,
        by_entity,
        ["fact_family", "business_entity", "rows", "amount_total", "partner_count", "legacy_partner_text_count"],
    )
    write_csv(partner_csv, top_partner, ["fact_family", "business_entity", "partner_name", "rows", "amount_total"])

    lines = [
        "# SCBS Project Bucket Policy Report",
        "",
        "This report covers active SCBS facts that have no confirmed project but need `project_id` for formal target models.",
        "",
        "## Summary",
        "",
        "| Fact Family | Rows | Amount | Business Entity Count | Partner Count |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in summary:
        lines.append(
            "| {fact_family} | {rows} | {amount_total} | {business_entity_count} | {partner_count} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Recommended Policy",
            "",
            "- Do not merge these rows into existing real projects without source evidence.",
            "- Create source-tagged project buckets only if formal models must represent every historical fact as an operational row.",
            "- Recommended bucket grain: one `SCBS未指定项目` project per confirmed business entity; rows without business entity stay reporting-only until entity evidence is found.",
            "- Mark bucket projects as historical migration buckets in notes/source fields so they are not treated as real user-created projects.",
            "",
            "## By Business Entity",
            "",
            "| Fact Family | Business Entity | Rows | Amount | Partner Count | Legacy Partner Text Count |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in by_entity[:80]:
        lines.append(
            "| {fact_family} | {business_entity} | {rows} | {amount_total} | {partner_count} | {legacy_partner_text_count} |".format(
                **row
            )
        )
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload = {
        "status": "PASS",
        "database": PG_DATABASE,
        "summary_csv": str(summary_csv),
        "entity_csv": str(entity_csv),
        "partner_csv": str(partner_csv),
        "report_md": str(report_md),
        "rows": sum(int(row["rows"]) for row in summary),
        "amount_total": str(sum(float(row["amount_total"]) for row in summary)),
        "recommended_policy": "one_SCBS_unassigned_project_bucket_per_confirmed_business_entity",
    }
    result_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCBS_PROJECT_BUCKET_POLICY_REPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
