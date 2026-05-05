#!/usr/bin/env python3
"""Preflight policy gates before projecting SCBS facts into formal models.

This host-side script reads the simulated production PostgreSQL database and,
for stock-in line checks, the restored SCBS SQL Server database. It does not
write business data.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
from decimal import Decimal
from pathlib import Path


PG_CONTAINER = os.getenv("ODOO_PG_CONTAINER", "sc-backend-odoo-prod-sim-db-1")
PG_DATABASE = os.getenv("ODOO_DATABASE", "sc_prod_sim")
PG_USER = os.getenv("ODOO_PG_USER", "odoo")
SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-scbs")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyScbs20260417")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
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


def run_sqlcmd(sql: str) -> list[str]:
    cmd = [
        "docker",
        "exec",
        "-i",
        SQL_CONTAINER,
        "bash",
        "-lc",
        (
            f"{SQLCMD} -S localhost -U sa -P \"$MSSQL_SA_PASSWORD\" "
            f"-C -d {SQL_DATABASE} -h -1 -W -s '|' -i /dev/stdin"
        ),
    ]
    proc = subprocess.run(cmd, input=sql, text=True, capture_output=True, check=True)
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def parse_rows(lines: list[str], fields: list[str]) -> list[dict[str, str]]:
    rows = []
    for line in lines:
        parts = line.split("|")
        if len(parts) != len(fields):
            raise RuntimeError({"unexpected_row": line, "expected_fields": fields})
        rows.append(dict(zip(fields, parts)))
    return rows


def decimal_text(value: object) -> str:
    if value is None or value == "":
        return "0.00"
    return str(Decimal(str(value)).quantize(Decimal("0.01")))


def active_summary() -> list[dict[str, str]]:
    return parse_rows(
        run_psql(
            """
SELECT fact_family,
       source_table,
       COUNT(*)::text AS active_rows,
       ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2)::text AS amount_total,
       COUNT(*) FILTER (WHERE project_id IS NOT NULL)::text AS with_project,
       COUNT(*) FILTER (WHERE partner_id IS NOT NULL)::text AS with_partner,
       COUNT(*) FILTER (WHERE business_entity_id IS NOT NULL)::text AS with_business_entity
  FROM sc_legacy_scbs_fact_staging
 WHERE import_batch = 'scbs_fact_staging_v1'
   AND active IS TRUE
   AND mapping_gate_state = 'projection_ready'
 GROUP BY fact_family, source_table
 ORDER BY fact_family, source_table;
"""
        ),
        [
            "fact_family",
            "source_table",
            "active_rows",
            "amount_total",
            "with_project",
            "with_partner",
            "with_business_entity",
        ],
    )


def single_metric(sql: str, fields: list[str]) -> dict[str, str]:
    rows = parse_rows(run_psql(sql), fields)
    return rows[0] if rows else {field: "0" for field in fields}


def active_legacy_ids(source_table: str) -> list[str]:
    rows = parse_rows(
        run_psql(
            f"""
SELECT legacy_record_id
  FROM sc_legacy_scbs_fact_staging
 WHERE import_batch = 'scbs_fact_staging_v1'
   AND active IS TRUE
   AND mapping_gate_state = 'projection_ready'
   AND source_table = '{source_table}'
 ORDER BY legacy_record_id;
"""
        ),
        ["legacy_record_id"],
    )
    return [row["legacy_record_id"].replace("'", "''") for row in rows if row["legacy_record_id"]]


def stock_in_line_metrics(active_ids: list[str]) -> dict[str, str]:
    if not active_ids:
        return {
            "active_headers": "0",
            "active_lines": "0",
            "line_amount": "0.00",
            "mismatch_headers": "0",
            "mismatch_amount_abs": "0.00",
            "headers_without_lines": "0",
            "headers_without_lines_amount": "0.00",
        }
    values_rows = ",".join(f"('{legacy_id}')" for legacy_id in active_ids)
    rows = parse_rows(
        run_sqlcmd(
            f"""
SET NOCOUNT ON;
WITH active_ids(ID) AS (SELECT * FROM (VALUES {values_rows}) AS v(ID)),
s AS (
  SELECT
    h.ID,
    CAST(ISNULL(h.RK_ZJE,0) AS decimal(18,2)) header_amount,
    CAST(COALESCE(SUM(ISNULL(l.HJ,0)), 0) AS decimal(18,2)) line_amount,
    COUNT(l.ID) line_count
  FROM dbo.T_RK_RKD h
  JOIN active_ids a ON a.ID = h.ID
  LEFT JOIN dbo.T_RK_RKDCB l ON l.ZBID = h.ID
  WHERE ISNULL(h.DEL,0)=0
  GROUP BY h.ID,h.RK_ZJE
)
SELECT COUNT(*) active_headers,
       CAST(SUM(line_count) AS varchar(32)) active_lines,
       CAST(SUM(line_amount) AS decimal(18,2)) line_amount,
       SUM(CASE WHEN ABS(line_amount-header_amount)>0.01 THEN 1 ELSE 0 END) mismatch_headers,
       CAST(SUM(CASE WHEN ABS(line_amount-header_amount)>0.01 THEN ABS(line_amount-header_amount) ELSE 0 END) AS decimal(18,2)) mismatch_amount_abs,
       SUM(CASE WHEN line_count = 0 THEN 1 ELSE 0 END) headers_without_lines,
       CAST(SUM(CASE WHEN line_count = 0 THEN header_amount ELSE 0 END) AS decimal(18,2)) headers_without_lines_amount
FROM s;
"""
        ),
        [
            "active_headers",
            "active_lines",
            "line_amount",
            "mismatch_headers",
            "mismatch_amount_abs",
            "headers_without_lines",
            "headers_without_lines_amount",
        ],
    )
    return rows[0]


def stock_in_mismatch_examples(active_ids: list[str]) -> list[dict[str, str]]:
    if not active_ids:
        return []
    values_rows = ",".join(f"('{legacy_id}')" for legacy_id in active_ids)
    return parse_rows(
        run_sqlcmd(
            f"""
SET NOCOUNT ON;
WITH active_ids(ID) AS (SELECT * FROM (VALUES {values_rows}) AS v(ID)),
s AS (
  SELECT
    h.ID,
    ISNULL(h.RKDH, '') RKDH,
    CONVERT(varchar(10), h.DJRQ, 120) DJRQ,
    ISNULL(h.SupplierName, '') SupplierName,
    ISNULL(h.GCMC, '') GCMC,
    CAST(ISNULL(h.RK_ZJE,0) AS decimal(18,2)) header_amount,
    CAST(COALESCE(SUM(ISNULL(l.HJ,0)), 0) AS decimal(18,2)) line_amount,
    COUNT(l.ID) line_count
  FROM dbo.T_RK_RKD h
  JOIN active_ids a ON a.ID = h.ID
  LEFT JOIN dbo.T_RK_RKDCB l ON l.ZBID=h.ID
  WHERE ISNULL(h.DEL,0)=0
  GROUP BY h.ID,h.RKDH,h.DJRQ,h.SupplierName,h.GCMC,h.RK_ZJE
)
SELECT TOP 50 ID,RKDH,DJRQ,SupplierName,GCMC,header_amount,line_amount,
       CAST(line_amount-header_amount AS decimal(18,2)) diff,line_count
FROM s
WHERE ABS(line_amount-header_amount)>0.01
ORDER BY ABS(line_amount-header_amount) DESC;
"""
        ),
        [
            "legacy_record_id",
            "document_no",
            "date",
            "supplier_name",
            "project_name",
            "header_amount",
            "line_amount",
            "diff",
            "line_count",
        ],
    )


def stock_in_missing_line_examples(active_ids: list[str]) -> list[dict[str, str]]:
    if not active_ids:
        return []
    values_rows = ",".join(f"('{legacy_id}')" for legacy_id in active_ids)
    return parse_rows(
        run_sqlcmd(
            f"""
SET NOCOUNT ON;
WITH active_ids(ID) AS (SELECT * FROM (VALUES {values_rows}) AS v(ID))
SELECT TOP 50
       h.ID,
       ISNULL(h.RKDH, '') RKDH,
       CONVERT(varchar(10), h.DJRQ, 120) DJRQ,
       ISNULL(h.SupplierName, '') SupplierName,
       ISNULL(h.GCMC, '') GCMC,
       CAST(ISNULL(h.RK_ZJE,0) AS decimal(18,2)) header_amount
FROM dbo.T_RK_RKD h
JOIN active_ids a ON a.ID = h.ID
WHERE ISNULL(h.DEL,0)=0
  AND NOT EXISTS (SELECT 1 FROM dbo.T_RK_RKDCB l WHERE l.ZBID = h.ID)
ORDER BY ABS(ISNULL(h.RK_ZJE,0)) DESC;
"""
        ),
        [
            "legacy_record_id",
            "document_no",
            "date",
            "supplier_name",
            "project_name",
            "header_amount",
        ],
    )


def build_policy_rows(summary_rows: list[dict[str, str]], stock_metrics: dict[str, str]) -> list[dict[str, str]]:
    by_family = {row["fact_family"]: row for row in summary_rows}
    payment_exact = single_metric(
        """
SELECT COUNT(*)::text AS rows,
       ROUND(COALESCE(SUM(s.amount_total), 0)::numeric, 2)::text AS amount
  FROM sc_legacy_scbs_fact_staging s
  JOIN payment_request p
    ON p.project_id = s.project_id
   AND p.partner_id = s.partner_id
   AND p.date_request = s.document_date
   AND ROUND(p.amount::numeric, 2) = ROUND(s.amount_total::numeric, 2)
 WHERE s.import_batch = 'scbs_fact_staging_v1'
   AND s.active IS TRUE
   AND s.mapping_gate_state = 'projection_ready'
   AND s.source_table = 'T_FK_Supplier'
   AND s.project_id IS NOT NULL
   AND s.partner_id IS NOT NULL;
""",
        ["rows", "amount"],
    )
    payment_broad = single_metric(
        """
SELECT COUNT(*)::text AS rows,
       ROUND(COALESCE(SUM(s.amount_total), 0)::numeric, 2)::text AS amount
  FROM sc_legacy_scbs_fact_staging s
  JOIN payment_request p
    ON p.partner_id = s.partner_id
   AND ROUND(p.amount::numeric, 2) = ROUND(s.amount_total::numeric, 2)
 WHERE s.import_batch = 'scbs_fact_staging_v1'
   AND s.active IS TRUE
   AND s.mapping_gate_state = 'projection_ready'
   AND s.source_table = 'T_FK_Supplier'
   AND s.partner_id IS NOT NULL;
""",
        ["rows", "amount"],
    )
    supplier_legacy = single_metric(
        """
SELECT COUNT(*)::text AS rows,
       ROUND(COALESCE(SUM(s.amount_total), 0)::numeric, 2)::text AS amount
  FROM sc_legacy_scbs_fact_staging s
  JOIN sc_general_contract c
    ON c.legacy_source_model = 'sc.legacy.scbs.fact.staging'
   AND c.legacy_record_id = s.legacy_record_id
 WHERE s.import_batch = 'scbs_fact_staging_v1'
   AND s.active IS TRUE
   AND s.mapping_gate_state = 'projection_ready'
   AND s.source_table = 'T_GYSHT_INFO';
""",
        ["rows", "amount"],
    )
    supplier_doc_general = single_metric(
        """
SELECT COUNT(*)::text AS rows,
       ROUND(COALESCE(SUM(s.amount_total), 0)::numeric, 2)::text AS amount
  FROM sc_legacy_scbs_fact_staging s
  JOIN sc_general_contract c
    ON COALESCE(c.document_no, c.contract_no, '') <> ''
   AND COALESCE(c.document_no, c.contract_no, '') = s.document_no
 WHERE s.import_batch = 'scbs_fact_staging_v1'
   AND s.active IS TRUE
   AND s.mapping_gate_state = 'projection_ready'
   AND s.source_table = 'T_GYSHT_INFO'
   AND COALESCE(s.document_no, '') <> '';
""",
        ["rows", "amount"],
    )
    supplier_doc_construction = single_metric(
        """
SELECT COUNT(*)::text AS rows,
       ROUND(COALESCE(SUM(s.amount_total), 0)::numeric, 2)::text AS amount
  FROM sc_legacy_scbs_fact_staging s
  JOIN construction_contract c
    ON COALESCE(c.legacy_document_no, c.legacy_contract_no, '') <> ''
   AND COALESCE(c.legacy_document_no, c.legacy_contract_no, '') = s.document_no
 WHERE s.import_batch = 'scbs_fact_staging_v1'
   AND s.active IS TRUE
   AND s.mapping_gate_state = 'projection_ready'
   AND s.source_table = 'T_GYSHT_INFO'
   AND COALESCE(s.document_no, '') <> '';
""",
        ["rows", "amount"],
    )
    existing_payment_projection = single_metric(
        """
SELECT COUNT(*)::text AS rows
  FROM sc_payment_execution
 WHERE legacy_source_model = 'sc.legacy.scbs.fact.staging'
   AND legacy_source_table = 'T_FK_Supplier';
""",
        ["rows"],
    )
    existing_contract_projection = single_metric(
        """
SELECT COUNT(*)::text AS rows
  FROM sc_general_contract
 WHERE legacy_source_model = 'sc.legacy.scbs.fact.staging'
   AND legacy_source_table = 'T_GYSHT_INFO';
""",
        ["rows"],
    )
    existing_stock_projection = single_metric(
        """
SELECT COUNT(*)::text AS rows
  FROM sc_material_inbound
 WHERE legacy_fact_model = 'sc.legacy.scbs.fact.staging';
""",
        ["rows"],
    )

    def row_for(
        fact_family: str,
        target_model: str,
        existing_rows: str,
        blocker: str,
        recommended_policy: str,
        formal_gate: str,
        evidence: str,
    ) -> dict[str, str]:
        source = by_family.get(fact_family, {})
        return {
            "fact_family": fact_family,
            "source_table": source.get("source_table", ""),
            "active_rows": source.get("active_rows", "0"),
            "amount_total": decimal_text(source.get("amount_total", "0")),
            "missing_project_rows": str(int(source.get("active_rows", "0")) - int(source.get("with_project", "0"))),
            "missing_partner_rows": str(int(source.get("active_rows", "0")) - int(source.get("with_partner", "0"))),
            "missing_business_entity_rows": str(
                int(source.get("active_rows", "0")) - int(source.get("with_business_entity", "0"))
            ),
            "target_model": target_model,
            "existing_target_rows_by_source_key": existing_rows,
            "blocker": blocker,
            "recommended_policy": recommended_policy,
            "formal_gate": formal_gate,
            "evidence": evidence,
        }

    payment_gate = "READY_WITH_SOURCE_TAGGED_SUPPLEMENT_POLICY"
    payment_blocker = "none_strict; broad_overlap_is_company_level_possible_representation"
    if int(payment_exact["rows"]) > 0:
        payment_gate = "REVIEW_STRICT_DUPLICATES"
        payment_blocker = "strict_project_partner_date_amount_overlap"
    if int(by_family.get("payment", {}).get("active_rows", "0")) > int(by_family.get("payment", {}).get("with_project", "0")):
        payment_gate = "PROJECT_BUCKET_POLICY_REQUIRED"
        payment_blocker = "target_project_id_required_but_legacy_project_missing"

    supplier_gate = "READY_WITH_SOURCE_KEY_AND_SOFT_DOCUMENT_NO_POLICY"
    supplier_blocker = "none_strict; document_number_is_reference_not_identity"
    supplier_doc_rows = int(supplier_doc_general["rows"]) + int(supplier_doc_construction["rows"])
    if int(supplier_legacy["rows"]) > 0:
        supplier_gate = "REVIEW_SOURCE_KEY_DUPLICATES"
        supplier_blocker = "source_key_duplicate_exists"
    if int(by_family.get("supplier_contract", {}).get("active_rows", "0")) > int(
        by_family.get("supplier_contract", {}).get("with_project", "0")
    ):
        supplier_gate = "PROJECT_BUCKET_POLICY_REQUIRED"
        supplier_blocker = "target_project_id_required_but_legacy_project_missing"

    stock_gate = "READY_WITH_LINE_AMOUNT_AND_MISMATCH_AUDIT_POLICY"
    stock_blocker = "none; line_amount_is_business_fact_and_mismatches_are_audited"
    if int(stock_metrics["headers_without_lines"]) > 0 and Decimal(stock_metrics["headers_without_lines_amount"]) != Decimal("0.00"):
        stock_gate = "BLOCKED_BY_MISSING_LINES"
        stock_blocker = "active_headers_without_lines_with_nonzero_amount"
    if int(by_family.get("stock_in", {}).get("active_rows", "0")) > int(by_family.get("stock_in", {}).get("with_project", "0")):
        stock_gate = "PROJECT_BUCKET_POLICY_REQUIRED"
        stock_blocker = "target_project_id_required_but_legacy_project_missing"

    return [
        row_for(
            "payment",
            "sc.payment.execution",
            existing_payment_projection["rows"],
            payment_blocker,
            "create source-tagged SCBS payment execution as project-level supplement; do not merge into existing payment_request",
            payment_gate,
            (
                f"strict_exact_rows={payment_exact['rows']} strict_exact_amount={payment_exact['amount']}; "
                f"broad_partner_amount_rows={payment_broad['rows']} broad_partner_amount={payment_broad['amount']}"
            ),
        ),
        row_for(
            "supplier_contract",
            "sc.general.contract",
            existing_contract_projection["rows"],
            supplier_blocker,
            "use legacy_source_model+legacy_record_id as identity; keep document_no/contract_no as source reference only",
            supplier_gate,
            (
                f"source_key_existing_rows={supplier_legacy['rows']} source_key_amount={supplier_legacy['amount']}; "
                f"doc_reference_matches={supplier_doc_rows} "
                f"doc_reference_amount_general={supplier_doc_general['amount']} "
                f"doc_reference_amount_construction={supplier_doc_construction['amount']}"
            ),
        ),
        row_for(
            "stock_in",
            "sc.material.inbound",
            existing_stock_projection["rows"],
            stock_blocker,
            "create source-tagged inbound headers from active SCBS headers and lines; amount follows line total, header mismatch retained as audit note",
            stock_gate,
            (
                f"active_headers={stock_metrics['active_headers']} active_lines={stock_metrics['active_lines']} "
                f"line_amount={stock_metrics['line_amount']} mismatch_headers={stock_metrics['mismatch_headers']} "
                f"mismatch_amount_abs={stock_metrics['mismatch_amount_abs']} headers_without_lines={stock_metrics['headers_without_lines']} "
                f"headers_without_lines_amount={stock_metrics['headers_without_lines_amount']}"
            ),
        ),
        row_for(
            "fund_daily",
            "reporting_snapshot",
            "0",
            "no_operational_posting_target",
            "retain as reporting/balance snapshot attached to confirmed business entity until target semantics are defined",
            "REPORTING_ONLY_NOT_FORMAL_WRITE",
            "fund_daily is a balance snapshot, not an execution voucher",
        ),
    ]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_report(
    path: Path,
    rows: list[dict[str, str]],
    mismatch_examples: list[dict[str, str]],
    missing_line_examples: list[dict[str, str]],
) -> None:
    lines = [
        "# SCBS Formal Projection Policy Preflight",
        "",
        "This report checks active SCBS staging facts only. It does not write formal business documents.",
        "",
        "## Conclusion",
        "",
        "- Active dimension mapping is complete: formal blockers are now policy gates, not missing entity/project/partner/material mappings.",
        "- Some active facts have no legacy project, while the target formal models require `project_id`; these rows need an explicit project-bucket policy before full formal write.",
        "- Rows with a confirmed project can be projected as source-tagged SCBS facts under the supplement/reference policies below.",
        "- Stock-in must be projected from line detail with mismatch audit notes; it must not be projected from header totals alone.",
        "- Fund daily remains reporting-only because it is a balance snapshot, not an operational posting.",
        "",
        "## Gate Matrix",
        "",
        "| Fact Family | Rows | Amount | Target | Gate | Blocker | Evidence |",
        "| --- | ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {fact_family} | {active_rows} | {amount_total} | {target_model} | {formal_gate} | {blocker} | {evidence} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Recommended Projection Policies",
            "",
        ]
    )
    for row in rows:
        lines.append(f"- `{row['fact_family']}`: {row['recommended_policy']}")
    lines.extend(
        [
            "",
            "## Required Target Field Gaps",
            "",
            "| Fact Family | Missing Project | Missing Partner | Missing Business Entity |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            "| {fact_family} | {missing_project_rows} | {missing_partner_rows} | {missing_business_entity_rows} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Stock-In Mismatch Examples",
            "",
            "| Legacy ID | Document No | Date | Supplier | Project | Header Amount | Line Amount | Diff | Lines |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in mismatch_examples[:20]:
        lines.append(
            "| {legacy_record_id} | {document_no} | {date} | {supplier_name} | {project_name} | {header_amount} | {line_amount} | {diff} | {line_count} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Stock-In Headers Without Lines",
            "",
            "| Legacy ID | Document No | Date | Supplier | Project | Header Amount |",
            "| --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for row in missing_line_examples[:20]:
        lines.append(
            "| {legacy_record_id} | {document_no} | {date} | {supplier_name} | {project_name} | {header_amount} |".format(
                **row
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    summary_rows = active_summary()
    stock_ids = active_legacy_ids("T_RK_RKD")
    stock_metrics = stock_in_line_metrics(stock_ids)
    mismatch_examples = stock_in_mismatch_examples(stock_ids)
    missing_line_examples = stock_in_missing_line_examples(stock_ids)
    policy_rows = build_policy_rows(summary_rows, stock_metrics)

    policy_csv = ARTIFACT_ROOT / "scbs_formal_projection_policy_preflight_v1.csv"
    mismatch_csv = ARTIFACT_ROOT / "scbs_formal_projection_stock_in_mismatch_examples_v1.csv"
    missing_line_csv = ARTIFACT_ROOT / "scbs_formal_projection_stock_in_missing_line_examples_v1.csv"
    result_json = ARTIFACT_ROOT / "scbs_formal_projection_policy_preflight_result_v1.json"
    report_md = ARTIFACT_ROOT / "scbs_formal_projection_policy_preflight_v1.md"

    fieldnames = [
        "fact_family",
        "source_table",
        "active_rows",
        "amount_total",
        "missing_project_rows",
        "missing_partner_rows",
        "missing_business_entity_rows",
        "target_model",
        "existing_target_rows_by_source_key",
        "blocker",
        "recommended_policy",
        "formal_gate",
        "evidence",
    ]
    write_csv(policy_csv, policy_rows, fieldnames)
    write_csv(
        mismatch_csv,
        mismatch_examples,
        [
            "legacy_record_id",
            "document_no",
            "date",
            "supplier_name",
            "project_name",
            "header_amount",
            "line_amount",
            "diff",
            "line_count",
        ],
    )
    write_csv(
        missing_line_csv,
        missing_line_examples,
        [
            "legacy_record_id",
            "document_no",
            "date",
            "supplier_name",
            "project_name",
            "header_amount",
        ],
    )
    write_report(report_md, policy_rows, mismatch_examples, missing_line_examples)

    payload = {
        "status": "PASS",
        "database": PG_DATABASE,
        "legacy_database": SQL_DATABASE,
        "policy_csv": str(policy_csv),
        "mismatch_csv": str(mismatch_csv),
        "missing_line_csv": str(missing_line_csv),
        "report_md": str(report_md),
        "active_rows": sum(int(row["active_rows"]) for row in summary_rows),
        "formal_gates": {row["fact_family"]: row["formal_gate"] for row in policy_rows},
        "stock_metrics": stock_metrics,
    }
    result_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCBS_FORMAL_PROJECTION_POLICY_PREFLIGHT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
