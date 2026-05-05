"""Build a unified SCBS residual register for上线审计.

The register records facts intentionally not written into operational target
models, with reason and next handling condition. It is an audit artifact, not a
business write.
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
        if candidate.exists():
            return candidate
    return Path("artifacts/migration")


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


def amount_sum(records) -> float:
    return sum(records.mapped("amount_total"))


def row_from_fact(fact, category: str, reason: str, target: str, next_condition: str) -> dict[str, object]:
    return {
        "category": category,
        "fact_family": fact.fact_family,
        "source_table": fact.source_table,
        "legacy_record_id": fact.legacy_record_id,
        "document_no": fact.document_no or "",
        "document_date": fact.document_date or "",
        "project_id": fact.project_id.id if fact.project_id else "",
        "project_name": fact.project_id.display_name if fact.project_id else "",
        "business_entity_id": fact.business_entity_id.id if fact.business_entity_id else "",
        "business_entity_name": fact.business_entity_id.display_name if fact.business_entity_id else "",
        "partner_id": fact.partner_id.id if fact.partner_id else "",
        "partner_name": fact.partner_id.display_name if fact.partner_id else (fact.legacy_partner_name or ""),
        "amount_total": fact.amount_total or 0.0,
        "residual_reason": reason,
        "target_model": target,
        "next_condition": next_condition,
        "active": fact.active,
    }


def main() -> None:
    artifacts = artifact_root()
    detail_csv = artifacts / "scbs_unified_residual_register_v1.csv"
    summary_csv = artifacts / "scbs_unified_residual_summary_v1.csv"
    md_path = artifacts / "scbs_unified_residual_register_v1.md"
    result_json = artifacts / "scbs_unified_residual_register_result_v1.json"

    Fact = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)  # noqa: F821
    base_domain = [
        ("import_batch", "=", "scbs_fact_staging_v1"),
        ("active", "=", True),
        ("mapping_gate_state", "=", "projection_ready"),
    ]
    rows: list[dict[str, object]] = []
    Adjustment = env["sc.legacy.payment.adjustment.fact"].sudo().with_context(active_test=False)  # noqa: F821
    adjusted_negative_payment_ids = {
        row["legacy_record_id"]
        for row in Adjustment.search_read(
            [
                ("legacy_source_model", "=", "sc.legacy.scbs.fact.staging"),
                ("legacy_source_table", "=", "T_FK_Supplier"),
            ],
            ["legacy_record_id"],
        )
    }
    EnterpriseFact = env["sc.legacy.enterprise.business.fact"].sudo().with_context(active_test=False)  # noqa: F821
    enterprise_no_project_keys = {
        (row["legacy_source_table"], row["legacy_record_id"])
        for row in EnterpriseFact.search_read(
            [
                ("legacy_source_model", "=", "sc.legacy.scbs.fact.staging"),
                ("document_scope", "=", "enterprise_no_project"),
            ],
            ["legacy_source_table", "legacy_record_id"],
        )
    }

    groups = [
        (
            "payment_no_project",
            base_domain + [("fact_family", "=", "payment"), ("project_id", "=", False)],
            "no_source_project_clue",
            "sc.legacy.enterprise.business.fact",
            "Write to enterprise no-project carrier unless source-chain evidence identifies a real project.",
        ),
        (
            "payment_negative_project_confirmed",
            base_domain + [("fact_family", "=", "payment"), ("project_id", "!=", False), ("amount_total", "<", 0)],
            "negative_payment_requires_refund_or_reversal_target",
            "none",
            "Write only after refund/reversal or historical adjustment target semantics are defined.",
        ),
        (
            "supplier_contract_no_project",
            base_domain + [("fact_family", "=", "supplier_contract"), ("project_id", "=", False)],
            "no_source_project_clue",
            "sc.legacy.enterprise.business.fact",
            "Write to enterprise no-project carrier unless source-chain evidence identifies a real project.",
        ),
        (
            "stock_in_zero_amount_no_line",
            base_domain + [("fact_family", "=", "stock_in")],
            "zero_amount_no_legacy_lines",
            "none",
            "Keep as audit residual; do not create empty material inbound documents.",
        ),
    ]

    # Stock-in zero no-line rows are identified by the latest projection residual artifact.
    stock_zero_ids = set()
    residual_csv = artifacts / "scbs_stock_in_projection_residual_v1.csv"
    if residual_csv.exists():
        with residual_csv.open(encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                if row.get("reason") == "missing_legacy_lines" and float(row.get("line_amount") or 0) == 0:
                    stock_zero_ids.add(row.get("legacy_record_id"))

    summary_rows: list[dict[str, object]] = []
    for category, domain, reason, target, next_condition in groups:
        records = Fact.search(domain, order="document_date, id")
        if category == "stock_in_zero_amount_no_line":
            records = records.filtered(lambda rec: rec.legacy_record_id in stock_zero_ids)
        if category == "payment_negative_project_confirmed":
            records = records.filtered(lambda rec: rec.legacy_record_id not in adjusted_negative_payment_ids)
        if category in ("payment_no_project", "supplier_contract_no_project"):
            records = records.filtered(lambda rec: (rec.source_table, rec.legacy_record_id) not in enterprise_no_project_keys)
        for fact in records:
            rows.append(row_from_fact(fact, category, reason, target, next_condition))
        summary_rows.append(
            {
                "category": category,
                "rows": len(records),
                "amount_total": amount_sum(records),
                "residual_reason": reason,
                "target_model": target,
                "next_condition": next_condition,
            }
        )

    inactive = Fact.search(
        [
            ("import_batch", "=", "scbs_fact_staging_v1"),
            ("active", "=", False),
        ],
        order="fact_family, document_date, id",
    )
    for fact in inactive:
        rows.append(
            row_from_fact(
                fact,
                "inactive_non_business_or_dirty_residual",
                "archived_from_projection_pool",
                "none",
                "Do not project unless business reclassifies the source row as real operational fact.",
            )
        )
    summary_rows.append(
        {
            "category": "inactive_non_business_or_dirty_residual",
            "rows": len(inactive),
            "amount_total": amount_sum(inactive),
            "residual_reason": "archived_from_projection_pool",
            "target_model": "none",
            "next_condition": "Do not project unless business reclassifies the source row as real operational fact.",
        }
    )

    detail_fields = [
        "category",
        "fact_family",
        "source_table",
        "legacy_record_id",
        "document_no",
        "document_date",
        "project_id",
        "project_name",
        "business_entity_id",
        "business_entity_name",
        "partner_id",
        "partner_name",
        "amount_total",
        "residual_reason",
        "target_model",
        "next_condition",
        "active",
    ]
    write_csv(detail_csv, rows, detail_fields)
    write_csv(
        summary_csv,
        summary_rows,
        ["category", "rows", "amount_total", "residual_reason", "target_model", "next_condition"],
    )

    md_lines = [
        "# SCBS Unified Residual Register",
        "",
        "## Summary",
        "",
        "| Category | Rows | Amount | Reason | Target |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for row in summary_rows:
        md_lines.append(
            "| {category} | {rows} | {amount_total:.2f} | {residual_reason} | {target_model} |".format(**row)
        )
    md_lines.extend(
        [
            "",
            "## Policy",
            "",
            "- Residual rows are not discarded; they remain source-identifiable audit facts.",
            "- No-project rows are not forced into direct projects without source-chain evidence.",
            "- No-project payment/contract rows written to `sc.legacy.enterprise.business.fact` are no longer residual rows.",
            "- Negative payment rows are not written into the non-negative payment execution model.",
            "- Negative payment rows written to `sc.legacy.payment.adjustment.fact` are no longer residual rows.",
            "- Fund daily rows are now enterprise business documents and are not residual rows.",
            "- Zero-amount stock-in headers without legacy lines do not create empty inbound documents.",
            "",
            "Detail CSV: `artifacts/migration/%s`" % detail_csv.name,
        ]
    )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    payload = {
        "status": "PASS",
        "database": env.cr.dbname,  # noqa: F821
        "detail_csv": str(detail_csv),
        "summary_csv": str(summary_csv),
        "md_path": str(md_path),
        "summary": summary_rows,
        "total_rows": len(rows),
        "total_amount": sum(float(row["amount_total"] or 0) for row in rows),
    }
    write_json(result_json, payload)
    print("SCBS_UNIFIED_RESIDUAL_REGISTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
