"""Build a dry-run formal projection plan for active SCBS staging facts.

This script does not write formal business documents. It checks the active
projection pool and target-model idempotency keys, then emits a plan for the
next projection stage.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


SOURCE_MODEL = "sc.legacy.scbs.fact.staging"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("artifacts/migration")


def fetch_dicts(query: str, params: tuple = ()) -> list[dict[str, object]]:
    env.cr.execute(query, params)  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def active_fact_summary() -> list[dict[str, object]]:
    return fetch_dicts(
        """
        SELECT fact_family,
               source_table,
               COUNT(*) AS active_rows,
               ROUND(SUM(amount_total)::numeric, 2) AS amount_total,
               COUNT(*) FILTER (WHERE project_id IS NOT NULL) AS with_project,
               COUNT(*) FILTER (WHERE partner_id IS NOT NULL) AS with_partner,
               COUNT(*) FILTER (WHERE business_entity_id IS NOT NULL) AS with_business_entity,
               MIN(document_date) AS min_date,
               MAX(document_date) AS max_date
          FROM sc_legacy_scbs_fact_staging
         WHERE import_batch = 'scbs_fact_staging_v1'
           AND active IS TRUE
           AND mapping_gate_state = 'projection_ready'
         GROUP BY fact_family, source_table
         ORDER BY fact_family, source_table
        """
    )


def target_existing_count(model_name: str, source_table: str) -> int:
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    if "legacy_source_model" in Model._fields:
        return Model.search_count([("legacy_source_model", "=", SOURCE_MODEL), ("legacy_source_table", "=", source_table)])
    if "legacy_fact_model" in Model._fields:
        return Model.search_count([("legacy_fact_model", "=", SOURCE_MODEL)])
    return 0


def target_model_for_family(fact_family: str) -> tuple[str, str, str]:
    if fact_family == "payment":
        return (
            "sc.payment.execution",
            "legacy_source_model + legacy_record_id",
            "READY_WITH_SOURCE_TAGGED_SUPPLEMENT_POLICY",
        )
    if fact_family == "supplier_contract":
        return (
            "sc.general.contract",
            "legacy_source_model + legacy_record_id",
            "READY_WITH_SOURCE_KEY_AND_SOFT_DOCUMENT_NO_POLICY",
        )
    if fact_family == "stock_in":
        return (
            "sc.material.inbound",
            "legacy_fact_model + legacy_fact_id",
            "READY_WITH_LINE_AMOUNT_AND_MISMATCH_AUDIT_POLICY",
        )
    if fact_family == "fund_daily":
        return (
            "reporting_snapshot",
            "source_table + legacy_record_id",
            "reporting_only_no_formal_write_target",
        )
    return ("", "", "unsupported_fact_family")


def main() -> None:
    artifacts = artifact_root()
    plan_csv = artifacts / "scbs_formal_projection_plan_v1.csv"
    result_json = artifacts / "scbs_formal_projection_plan_result_v1.json"
    report_md = artifacts / "scbs_formal_projection_plan_v1.md"

    summary = active_fact_summary()
    plan_rows: list[dict[str, object]] = []
    for row in summary:
        fact_family = str(row["fact_family"])
        source_table = str(row["source_table"])
        target_model, idempotency_key, projection_status = target_model_for_family(fact_family)
        existing = 0 if target_model == "reporting_snapshot" else target_existing_count(target_model, source_table)
        active_rows = int(row["active_rows"] or 0)
        with_project = int(row["with_project"] or 0)
        if target_model != "reporting_snapshot" and with_project < active_rows:
            projection_status = "PARTIAL_READY_PROJECT_BUCKET_POLICY_REQUIRED"
        plan_rows.append(
            {
                "fact_family": fact_family,
                "source_table": source_table,
                "active_rows": active_rows,
                "amount_total": row["amount_total"],
                "with_project": with_project,
                "with_partner": row["with_partner"],
                "with_business_entity": row["with_business_entity"],
                "min_date": row["min_date"],
                "max_date": row["max_date"],
                "target_model": target_model,
                "idempotency_key": idempotency_key,
                "existing_target_rows": existing,
                "new_projection_rows": max(active_rows - existing, 0),
                "projection_status": projection_status,
            }
        )

    write_csv(
        plan_csv,
        plan_rows,
        [
            "fact_family",
            "source_table",
            "active_rows",
            "amount_total",
            "with_project",
            "with_partner",
            "with_business_entity",
            "min_date",
            "max_date",
            "target_model",
            "idempotency_key",
            "existing_target_rows",
            "new_projection_rows",
            "projection_status",
        ],
    )

    lines = [
        "# SCBS Formal Projection Plan",
        "",
        "This is a dry-run plan. It does not create formal business documents.",
        "",
        "| Fact Family | Active Rows | Amount | Target Model | New Rows | Status |",
        "| --- | ---: | ---: | --- | ---: | --- |",
    ]
    for row in plan_rows:
        lines.append(
            "| {fact_family} | {active_rows} | {amount_total} | {target_model} | {new_projection_rows} | {projection_status} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Current Decision",
            "",
            "- Active staging facts are dimension-ready.",
            "- Payment, supplier-contract, and stock-in rows with confirmed projects are ready for source-tagged formal projection.",
            "- Rows without legacy project cannot be fully written to the current formal target models until a project-bucket policy is accepted.",
            "- Stock-in projection must use line amount and retain header/line differences as audit evidence.",
            "- Fund daily remains reporting snapshot until a formal target model is selected.",
            "",
        ]
    )
    report_md.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "status": "PASS",
        "database": env.cr.dbname,  # noqa: F821
        "plan_csv": str(plan_csv),
        "report_md": str(report_md),
        "fact_families": len(plan_rows),
        "active_rows": sum(int(row["active_rows"] or 0) for row in plan_rows),
        "new_projection_rows": sum(int(row["new_projection_rows"] or 0) for row in plan_rows if row["target_model"] != "reporting_snapshot"),
        "statuses": sorted({str(row["projection_status"]) for row in plan_rows}),
    }
    write_json(result_json, payload)
    print("SCBS_FORMAL_PROJECTION_PLAN=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
