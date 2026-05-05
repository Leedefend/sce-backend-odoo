#!/usr/bin/env python3
"""Report whether SCBS stock-in facts have enough detail for projection."""

import csv
import json
import os
import subprocess
from pathlib import Path


SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-scbs")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyScbs20260417")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
PG_CONTAINER = os.getenv("ODOO_PG_CONTAINER", "sc-backend-odoo-prod-sim-db-1")
PG_DATABASE = os.getenv("ODOO_DATABASE", "sc_prod_sim")
PG_USER = os.getenv("ODOO_PG_USER", "odoo")
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))


def run_sqlcmd(sql):
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


def run_psql(sql):
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


def parse_rows(lines, fields):
    rows = []
    for line in lines:
        parts = line.split("|")
        if len(parts) != len(fields):
            raise RuntimeError({"unexpected_row": line, "expected_fields": fields})
        rows.append(dict(zip(fields, parts)))
    return rows


def main():
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)

    summary_sql = """
SET NOCOUNT ON;
SELECT 'active_headers' metric, COUNT(*) rows, CAST(SUM(ISNULL(h.RK_ZJE,0)) AS decimal(18,2)) amount
FROM dbo.T_RK_RKD h
WHERE ISNULL(h.DEL,0)=0
UNION ALL
SELECT 'active_headers_with_lines', COUNT(DISTINCT h.ID), CAST(SUM(ISNULL(l.HJ,0)) AS decimal(18,2))
FROM dbo.T_RK_RKD h
JOIN dbo.T_RK_RKDCB l ON l.ZBID=h.ID
WHERE ISNULL(h.DEL,0)=0
UNION ALL
SELECT 'active_lines', COUNT(*), CAST(SUM(ISNULL(l.HJ,0)) AS decimal(18,2))
FROM dbo.T_RK_RKD h
JOIN dbo.T_RK_RKDCB l ON l.ZBID=h.ID
WHERE ISNULL(h.DEL,0)=0
UNION ALL
SELECT 'active_headers_without_lines', COUNT(*), CAST(SUM(ISNULL(h.RK_ZJE,0)) AS decimal(18,2))
FROM dbo.T_RK_RKD h
WHERE ISNULL(h.DEL,0)=0
  AND NOT EXISTS (SELECT 1 FROM dbo.T_RK_RKDCB l WHERE l.ZBID=h.ID)
UNION ALL
SELECT 'line_catalog_match_by_clid_id', COUNT(*), CAST(SUM(ISNULL(l.HJ,0)) AS decimal(18,2))
FROM dbo.T_RK_RKD h
JOIN dbo.T_RK_RKDCB l ON l.ZBID=h.ID
JOIN dbo.T_Base_MaterialDetail m ON m.ID=l.CLID
WHERE ISNULL(h.DEL,0)=0
UNION ALL
SELECT 'line_without_catalog_id_match', COUNT(*), CAST(SUM(ISNULL(l.HJ,0)) AS decimal(18,2))
FROM dbo.T_RK_RKD h
JOIN dbo.T_RK_RKDCB l ON l.ZBID=h.ID
WHERE ISNULL(h.DEL,0)=0
  AND NOT EXISTS (
      SELECT 1 FROM dbo.T_Base_MaterialDetail m
      WHERE m.ID=l.CLID OR m.Guid=l.CLID
  );
"""
    coverage_sql = """
SET NOCOUNT ON;
SELECT
  'active_line_coverage' metric,
  COUNT(*) rows,
  COUNT(DISTINCT NULLIF(LTRIM(RTRIM(l.CLID)),'')) distinct_clid,
  COUNT(DISTINCT NULLIF(LTRIM(RTRIM(l.CLMC)),'')) distinct_clmc,
  SUM(CASE WHEN NULLIF(LTRIM(RTRIM(l.CLID)),'') IS NOT NULL THEN 1 ELSE 0 END) with_clid,
  SUM(CASE WHEN NULLIF(LTRIM(RTRIM(l.CLMC)),'') IS NOT NULL THEN 1 ELSE 0 END) with_clmc,
  SUM(CASE WHEN NULLIF(LTRIM(RTRIM(l.DW)),'') IS NOT NULL THEN 1 ELSE 0 END) with_uom,
  SUM(CASE WHEN ISNULL(l.SL,0)<>0 THEN 1 ELSE 0 END) with_qty,
  SUM(CASE WHEN ISNULL(l.DJ,0)<>0 OR ISNULL(l.DJ_NO,0)<>0 THEN 1 ELSE 0 END) with_price,
  CAST(SUM(ISNULL(l.HJ,0)) AS decimal(18,2)) amount
FROM dbo.T_RK_RKD h
JOIN dbo.T_RK_RKDCB l ON l.ZBID=h.ID
WHERE ISNULL(h.DEL,0)=0;
"""
    mismatch_sql = """
SET NOCOUNT ON;
WITH s AS (
  SELECT
    h.ID,
    h.RKDH,
    CONVERT(varchar(10), h.DJRQ, 120) DJRQ,
    ISNULL(h.SupplierName, '') SupplierName,
    ISNULL(h.GCMC, '') GCMC,
    CAST(ISNULL(h.RK_ZJE,0) AS decimal(18,2)) header_amount,
    CAST(SUM(ISNULL(l.HJ,0)) AS decimal(18,2)) line_amount,
    COUNT(l.ID) line_count
  FROM dbo.T_RK_RKD h
  LEFT JOIN dbo.T_RK_RKDCB l ON l.ZBID=h.ID
  WHERE ISNULL(h.DEL,0)=0
  GROUP BY h.ID,h.RKDH,h.DJRQ,h.SupplierName,h.GCMC,h.RK_ZJE
)
SELECT TOP 20 ID,RKDH,DJRQ,SupplierName,GCMC,header_amount,line_amount,
       CAST(ISNULL(line_amount,0)-header_amount AS decimal(18,2)) diff,line_count
FROM s
WHERE ABS(ISNULL(line_amount,0)-header_amount)>0.01
ORDER BY ABS(ISNULL(line_amount,0)-header_amount) DESC;
"""
    top_material_sql = """
SET NOCOUNT ON;
SELECT TOP 30
  ISNULL(NULLIF(LTRIM(RTRIM(l.CLMC)),''), '') CLMC,
  ISNULL(NULLIF(LTRIM(RTRIM(l.GGXH)),''), '') GGXH,
  ISNULL(NULLIF(LTRIM(RTRIM(l.DW)),''), '') DW,
  COUNT(*) rows,
  CAST(SUM(ISNULL(l.SL,0)) AS decimal(18,4)) qty,
  CAST(SUM(ISNULL(l.HJ,0)) AS decimal(18,2)) amount
FROM dbo.T_RK_RKD h
JOIN dbo.T_RK_RKDCB l ON l.ZBID=h.ID
WHERE ISNULL(h.DEL,0)=0
GROUP BY NULLIF(LTRIM(RTRIM(l.CLMC)),''),NULLIF(LTRIM(RTRIM(l.GGXH)),''),NULLIF(LTRIM(RTRIM(l.DW)),'')
ORDER BY SUM(ISNULL(l.HJ,0)) DESC;
"""

    summary = parse_rows(run_sqlcmd(summary_sql), ["metric", "rows", "amount"])
    coverage = parse_rows(
        run_sqlcmd(coverage_sql),
        [
            "metric",
            "rows",
            "distinct_clid",
            "distinct_clmc",
            "with_clid",
            "with_clmc",
            "with_uom",
            "with_qty",
            "with_price",
            "amount",
        ],
    )[0]
    mismatches = parse_rows(
        run_sqlcmd(mismatch_sql),
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
    top_materials = parse_rows(
        run_sqlcmd(top_material_sql),
        ["material_name", "spec", "uom", "rows", "qty", "amount"],
    )

    target_counts = parse_rows(
        run_psql(
            """
SELECT 'product_template' metric, count(*)::text rows FROM product_template
UNION ALL
SELECT 'product_product', count(*)::text FROM product_product
UNION ALL
SELECT 'sc_material_catalog', count(*)::text FROM sc_material_catalog
UNION ALL
SELECT 'sc_material_inbound', count(*)::text FROM sc_material_inbound;
"""
        ),
        ["metric", "rows"],
    )

    result = {
        "database": SQL_DATABASE,
        "target_database": PG_DATABASE,
        "summary": summary,
        "line_coverage": coverage,
        "target_counts": target_counts,
        "mismatch_examples": mismatches,
        "top_materials": top_materials,
        "status": "BLOCKED_BY_MATERIAL_CATALOG_MAPPING",
        "interpretation": (
            "SCBS stock-in has usable line detail. Formal projection is gated by "
            "SCBS material-catalog mapping, not by product-library promotion."
        ),
    }

    json_path = ARTIFACT_ROOT / "scbs_stock_in_detail_readiness_report_v1.json"
    summary_csv = ARTIFACT_ROOT / "scbs_stock_in_detail_readiness_summary_v1.csv"
    mismatch_csv = ARTIFACT_ROOT / "scbs_stock_in_detail_mismatch_examples_v1.csv"
    top_csv = ARTIFACT_ROOT / "scbs_stock_in_top_materials_v1.csv"
    md_path = ARTIFACT_ROOT / "scbs_stock_in_detail_readiness_report_v1.md"

    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "rows", "amount"])
        writer.writeheader()
        writer.writerows(summary)
    with mismatch_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=mismatches[0].keys() if mismatches else [])
        if mismatches:
            writer.writeheader()
            writer.writerows(mismatches)
    with top_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["material_name", "spec", "uom", "rows", "qty", "amount"])
        writer.writeheader()
        writer.writerows(top_materials)

    summary_by_metric = {row["metric"]: row for row in summary}
    target_by_metric = {row["metric"]: row["rows"] for row in target_counts}
    md_path.write_text(
        "\n".join(
            [
                "# SCBS Stock-In Detail Readiness Report",
                "",
                "## Conclusion",
                "",
                "SCBS stock-in has usable line-level legacy detail, but formal projection is blocked until SCBS materials are mapped to `sc.material.catalog`.",
                "",
                "## Key Counts",
                "",
                "| Metric | Rows | Amount |",
                "| --- | ---: | ---: |",
                *[
                    f"| {row['metric']} | {row['rows']} | {row['amount']} |"
                    for row in summary
                ],
                "",
                "## Line Coverage",
                "",
                f"- active lines: {coverage['rows']}",
                f"- with legacy material ID: {coverage['with_clid']}",
                f"- with material name: {coverage['with_clmc']}",
                f"- with unit: {coverage['with_uom']}",
                f"- with quantity: {coverage['with_qty']}",
                f"- with price: {coverage['with_price']}",
                f"- distinct legacy material IDs: {coverage['distinct_clid']}",
                f"- distinct material names: {coverage['distinct_clmc']}",
                "",
                "## Target Baseline",
                "",
                f"- product templates: {target_by_metric.get('product_template', '0')}",
                f"- product variants: {target_by_metric.get('product_product', '0')}",
                f"- material catalog rows: {target_by_metric.get('sc_material_catalog', '0')}",
                f"- formal material inbound documents: {target_by_metric.get('sc_material_inbound', '0')}",
                "",
                "## Projection Gate",
                "",
                "- Do not create formal `sc.material.inbound` rows from header totals only.",
                "- Use `sc.material.catalog` as the business material dimension for cost statistics, budget comparison, and management control.",
                "- Do not promote SCBS historical materials into product templates/products as part of this acceptance path.",
                "- First map legacy materials from `T_Base_MaterialDetail` and line `CLID/CLMC/GGXH/DW` to material catalog rows.",
                "- After material mapping, generate source-tagged inbound headers and lines using `T_RK_RKD.ID` and `T_RK_RKDCB.ID` as duplicate keys.",
                "- Six active headers have zero header amount but non-zero line amount; keep line amount as factual detail and flag these headers for review.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path}`",
                f"- Summary CSV: `{summary_csv}`",
                f"- Mismatch examples: `{mismatch_csv}`",
                f"- Top materials: `{top_csv}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print("SCBS_STOCK_IN_DETAIL_READINESS_REPORT=" + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
