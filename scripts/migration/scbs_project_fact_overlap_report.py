"""Report overlap risk between SCBS project-level facts and existing formal data."""

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


def fetch_dicts(query: str, params: tuple = ()) -> list[dict[str, object]]:
    env.cr.execute(query, params)  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    result_json = artifacts / "scbs_project_fact_overlap_report_result_v1.json"
    summary_csv = artifacts / "scbs_project_fact_overlap_summary_v1.csv"
    examples_csv = artifacts / "scbs_project_fact_overlap_examples_v1.csv"
    report_md = artifacts / "scbs_project_fact_overlap_report_v1.md"

    source_summary = fetch_dicts(
        """
        SELECT fact_family,
               source_table,
               COUNT(*) AS staged_rows,
               ROUND(SUM(amount_total)::numeric, 2) AS staged_amount,
               COUNT(*) FILTER (WHERE mapping_gate_state = 'projection_ready') AS projection_ready,
               COUNT(*) FILTER (WHERE mapping_gate_state = 'staging_ready') AS staging_ready,
               COUNT(*) FILTER (WHERE mapping_gate_state = 'conflict') AS conflict,
               COUNT(*) FILTER (WHERE mapping_gate_state = 'blocked') AS blocked
          FROM sc_legacy_scbs_fact_staging
         WHERE import_batch = 'scbs_fact_staging_v1'
         GROUP BY fact_family, source_table
         ORDER BY fact_family, source_table
        """
    )
    exact_contract = fetch_dicts(
        """
        SELECT COUNT(*) AS overlap_rows,
               ROUND(COALESCE(SUM(s.amount_total), 0)::numeric, 2) AS overlap_amount
          FROM sc_legacy_scbs_fact_staging s
          JOIN construction_contract c
            ON c.legacy_contract_id = s.legacy_record_id
         WHERE s.import_batch = 'scbs_fact_staging_v1'
           AND s.source_table = 'T_GYSHT_INFO'
        """
    )[0]
    contract_doc_match = fetch_dicts(
        """
        SELECT COUNT(*) AS overlap_rows,
               ROUND(COALESCE(SUM(s.amount_total), 0)::numeric, 2) AS overlap_amount
          FROM sc_legacy_scbs_fact_staging s
          JOIN construction_contract c
            ON c.legacy_document_no IS NOT NULL
           AND c.legacy_document_no <> ''
           AND c.legacy_document_no = s.document_no
         WHERE s.import_batch = 'scbs_fact_staging_v1'
           AND s.source_table = 'T_GYSHT_INFO'
           AND s.document_no IS NOT NULL
           AND s.document_no <> ''
        """
    )[0]
    payment_exact = fetch_dicts(
        """
        SELECT COUNT(*) AS overlap_rows,
               ROUND(COALESCE(SUM(s.amount_total), 0)::numeric, 2) AS overlap_amount
          FROM sc_legacy_scbs_fact_staging s
          JOIN payment_request p
            ON p.project_id = s.project_id
           AND p.partner_id = s.partner_id
           AND p.date_request = s.document_date
           AND ROUND(p.amount::numeric, 2) = ROUND(s.amount_total::numeric, 2)
         WHERE s.import_batch = 'scbs_fact_staging_v1'
           AND s.source_table = 'T_FK_Supplier'
           AND s.project_id IS NOT NULL
           AND s.partner_id IS NOT NULL
        """
    )[0]
    payment_amount_partner = fetch_dicts(
        """
        SELECT COUNT(*) AS overlap_rows,
               ROUND(COALESCE(SUM(s.amount_total), 0)::numeric, 2) AS overlap_amount
          FROM sc_legacy_scbs_fact_staging s
          JOIN payment_request p
            ON p.partner_id = s.partner_id
           AND ROUND(p.amount::numeric, 2) = ROUND(s.amount_total::numeric, 2)
         WHERE s.import_batch = 'scbs_fact_staging_v1'
           AND s.source_table = 'T_FK_Supplier'
           AND s.partner_id IS NOT NULL
        """
    )[0]
    material_inbound_count = fetch_dicts("SELECT COUNT(*) AS formal_rows FROM sc_material_inbound")[0]
    material_inbound_scbs = fetch_dicts(
        """
        SELECT COUNT(*) AS formal_rows,
               ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS formal_amount
          FROM sc_material_inbound
         WHERE legacy_fact_model = 'sc.legacy.scbs.fact.staging'
        """
    )[0]
    fund_target = fetch_dicts(
        """
        SELECT COUNT(*) AS formal_rows,
               COUNT(*) FILTER (WHERE business_entity_id IS NOT NULL) AS with_business_entity,
               COUNT(*) FILTER (WHERE project_id IS NOT NULL) AS with_project,
               ROUND(COALESCE(SUM(source_account_balance_total), 0)::numeric, 2) AS formal_amount
          FROM sc_legacy_fund_daily_snapshot_fact
         WHERE legacy_source_table = 'D_SCBSJS_ZJGL_ZJSZ_ZJRBB'
           AND import_batch = 'scbs_fund_daily_enterprise_v1'
        """
    )[0]

    summary_rows = []
    for row in source_summary:
        overlap_method = ""
        overlap_rows = 0
        overlap_amount = 0.0
        projection_policy = "review_required"
        if row["source_table"] == "T_GYSHT_INFO":
            overlap_method = "contract_legacy_id_exact"
            overlap_rows = exact_contract["overlap_rows"]
            overlap_amount = exact_contract["overlap_amount"]
            projection_policy = "block_duplicates_by_legacy_contract_id"
        elif row["source_table"] == "T_FK_Supplier":
            overlap_method = "payment_project_partner_date_amount_exact"
            overlap_rows = payment_exact["overlap_rows"]
            overlap_amount = payment_exact["overlap_amount"]
            projection_policy = "requires_payment_duplicate_review"
        elif row["source_table"] == "T_RK_RKD":
            overlap_method = "material_inbound_legacy_fact_id_unique"
            overlap_rows = material_inbound_scbs["formal_rows"]
            overlap_amount = material_inbound_scbs["formal_amount"]
            projection_policy = "formal_material_inbound_written_by_legacy_fact_id"
        elif row["source_table"] == "D_SCBSJS_ZJGL_ZJSZ_ZJRBB":
            overlap_method = "enterprise_fund_daily_source_id_unique"
            overlap_rows = fund_target["formal_rows"]
            overlap_amount = fund_target["formal_amount"]
            projection_policy = "enterprise_business_document_written_no_project_binding"
        summary_rows.append(
            {
                **row,
                "overlap_method": overlap_method,
                "overlap_rows": overlap_rows,
                "overlap_amount": overlap_amount,
                "projection_policy": projection_policy,
            }
        )

    examples = fetch_dicts(
        """
        SELECT 'supplier_contract_legacy_id' AS overlap_kind,
               s.source_table,
               s.legacy_record_id,
               s.document_no,
               s.legacy_partner_name,
               s.legacy_gcmc,
               s.amount_total,
               c.id AS target_id,
               c.name AS target_name
          FROM sc_legacy_scbs_fact_staging s
          JOIN construction_contract c
            ON c.legacy_contract_id = s.legacy_record_id
         WHERE s.import_batch = 'scbs_fact_staging_v1'
           AND s.source_table = 'T_GYSHT_INFO'
         LIMIT 50
        """
    )
    examples.extend(
        fetch_dicts(
            """
            SELECT 'supplier_contract_document_no' AS overlap_kind,
                   s.source_table,
                   s.legacy_record_id,
                   s.document_no,
                   s.legacy_partner_name,
                   s.legacy_gcmc,
                   s.amount_total,
                   c.id AS target_id,
                   c.name AS target_name
              FROM sc_legacy_scbs_fact_staging s
              JOIN construction_contract c
                ON c.legacy_document_no IS NOT NULL
               AND c.legacy_document_no <> ''
               AND c.legacy_document_no = s.document_no
             WHERE s.import_batch = 'scbs_fact_staging_v1'
               AND s.source_table = 'T_GYSHT_INFO'
               AND s.document_no IS NOT NULL
               AND s.document_no <> ''
             LIMIT 50
            """
        )
    )
    examples.extend(
        fetch_dicts(
            """
            SELECT 'payment_project_partner_date_amount' AS overlap_kind,
                   s.source_table,
                   s.legacy_record_id,
                   s.document_no,
                   s.legacy_partner_name,
                   s.legacy_gcmc,
                   s.amount_total,
                   p.id AS target_id,
                   p.name AS target_name
              FROM sc_legacy_scbs_fact_staging s
              JOIN payment_request p
                ON p.project_id = s.project_id
               AND p.partner_id = s.partner_id
               AND p.date_request = s.document_date
               AND ROUND(p.amount::numeric, 2) = ROUND(s.amount_total::numeric, 2)
             WHERE s.import_batch = 'scbs_fact_staging_v1'
               AND s.source_table = 'T_FK_Supplier'
               AND s.project_id IS NOT NULL
               AND s.partner_id IS NOT NULL
             LIMIT 50
            """
        )
    )
    examples.extend(
        fetch_dicts(
            """
            SELECT 'payment_partner_amount_possible' AS overlap_kind,
                   s.source_table,
                   s.legacy_record_id,
                   s.document_no,
                   s.legacy_partner_name,
                   s.legacy_gcmc,
                   s.amount_total,
                   p.id AS target_id,
                   p.name AS target_name
              FROM sc_legacy_scbs_fact_staging s
              JOIN payment_request p
                ON p.partner_id = s.partner_id
               AND ROUND(p.amount::numeric, 2) = ROUND(s.amount_total::numeric, 2)
             WHERE s.import_batch = 'scbs_fact_staging_v1'
               AND s.source_table = 'T_FK_Supplier'
               AND s.partner_id IS NOT NULL
             ORDER BY s.amount_total DESC
             LIMIT 100
            """
        )
    )

    write_csv(
        summary_csv,
        [
            "fact_family",
            "source_table",
            "staged_rows",
            "staged_amount",
            "projection_ready",
            "staging_ready",
            "conflict",
            "blocked",
            "overlap_method",
            "overlap_rows",
            "overlap_amount",
            "projection_policy",
        ],
        summary_rows,
    )
    write_csv(
        examples_csv,
        [
            "overlap_kind",
            "source_table",
            "legacy_record_id",
            "document_no",
            "legacy_partner_name",
            "legacy_gcmc",
            "amount_total",
            "target_id",
            "target_name",
        ],
        examples,
    )

    lines = [
        "# SCBS Project-Level Fact Overlap Report",
        "",
        "## Summary",
        "",
    ]
    lines.extend(
        md_table(
            summary_rows,
            [
                "source_table",
                "fact_family",
                "staged_rows",
                "staged_amount",
                "overlap_method",
                "overlap_rows",
                "overlap_amount",
                "projection_policy",
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Supplier contracts can be checked by exact legacy contract ID and document number.",
            "- Supplier payments have no direct formal legacy ID in `payment.request`; current check is approximate by project, partner, date, and amount.",
            "- Material inbound is formally written by legacy fact ID; duplicate risk is controlled by source identity.",
            "- Fund daily is now projected as enterprise business documents on business entity, not project; SCBS project binding must remain zero.",
            "",
        ]
    )
    report_md.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "status": "PASS",
        "database": env.cr.dbname,  # noqa: F821
        "summary_csv": str(summary_csv),
        "examples_csv": str(examples_csv),
        "report_md": str(report_md),
        "exact_contract_overlap": exact_contract,
        "contract_document_overlap": contract_doc_match,
        "payment_exact_overlap": payment_exact,
        "payment_amount_partner_overlap": payment_amount_partner,
        "material_inbound": material_inbound_count,
        "material_inbound_scbs": material_inbound_scbs,
        "fund_target": fund_target,
    }
    write_json(result_json, payload)
    print("SCBS_PROJECT_FACT_OVERLAP_REPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
