#!/usr/bin/env python3
"""Check SCBS stock-in material lines against the target material catalog.

This report intentionally does not promote legacy materials into products.
For construction-enterprise material management, `sc.material.catalog` is the
business control dimension used for cost statistics, budget comparison, and
management control. `product.product` promotion is outside this SCBS acceptance
path unless a later business process explicitly requires inventory-product
control.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
from collections import Counter
from pathlib import Path


SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-scbs")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyScbs20260417")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
PG_CONTAINER = os.getenv("ODOO_PG_CONTAINER", "sc-backend-odoo-prod-sim-db-1")
PG_DATABASE = os.getenv("ODOO_DATABASE", "sc_prod_sim")
PG_USER = os.getenv("ODOO_PG_USER", "odoo")
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))


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


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def target_catalog_by_legacy_id(legacy_ids: list[str]) -> dict[str, dict[str, str]]:
    if not legacy_ids:
        return {}
    result: dict[str, dict[str, str]] = {}
    batch_size = 500
    for offset in range(0, len(legacy_ids), batch_size):
        batch = legacy_ids[offset : offset + batch_size]
        values_sql = ",".join(f"({sql_literal(value)})" for value in batch)
        rows = parse_rows(
            run_psql(
                f"""
WITH input(legacy_material_id) AS (VALUES {values_sql})
SELECT
  i.legacy_material_id,
  COALESCE(c.id::text, '') material_catalog_id,
  COALESCE(c.name, '') catalog_name,
  COALESCE(c.spec_model, '') spec_model,
  COALESCE(c.uom_text, '') uom_text,
  COALESCE(c.promoted_product_id::text, '') promoted_product_id
FROM input i
LEFT JOIN sc_material_catalog c ON c.legacy_material_id = i.legacy_material_id
ORDER BY i.legacy_material_id;
"""
            ),
            [
                "legacy_material_id",
                "material_catalog_id",
                "catalog_name",
                "spec_model",
                "uom_text",
                "promoted_product_id",
            ],
        )
        for row in rows:
            result[row["legacy_material_id"]] = row
    return result


def target_catalog_by_business_key(line_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    keys = []
    seen = set()
    for index, row in enumerate(line_rows):
        name = row["material_name"].strip()
        spec = row["spec_model"].strip()
        uom = row["uom_text"].strip()
        if not name:
            continue
        key = (name, spec, uom)
        if key in seen:
            continue
        seen.add(key)
        keys.append((str(index), name, spec, uom))
    result: dict[str, dict[str, str]] = {}
    batch_size = 300
    for offset in range(0, len(keys), batch_size):
        batch = keys[offset : offset + batch_size]
        values_sql = ",".join(
            "(%s,%s,%s,%s)"
            % (sql_literal(row_key), sql_literal(name), sql_literal(spec), sql_literal(uom))
            for row_key, name, spec, uom in batch
        )
        rows = parse_rows(
            run_psql(
                f"""
WITH input(row_key, material_name, spec_model, uom_text) AS (VALUES {values_sql}),
exact_text AS (
  SELECT
    i.row_key,
    MIN(c.id)::text material_catalog_id,
    COUNT(*)::text match_count
  FROM input i
  JOIN sc_material_catalog c
    ON btrim(COALESCE(c.name, '')) = i.material_name
   AND btrim(COALESCE(c.spec_model, '')) = i.spec_model
   AND btrim(COALESCE(c.uom_text, '')) = i.uom_text
  GROUP BY i.row_key
),
name_spec AS (
  SELECT
    i.row_key,
    MIN(c.id)::text material_catalog_id,
    COUNT(*)::text match_count
  FROM input i
  JOIN sc_material_catalog c
    ON btrim(COALESCE(c.name, '')) = i.material_name
   AND btrim(COALESCE(c.spec_model, '')) = i.spec_model
  GROUP BY i.row_key
)
SELECT
  i.row_key,
  COALESCE(e.material_catalog_id, '') exact_text_catalog_id,
  COALESCE(e.match_count, '0') exact_text_match_count,
  COALESCE(ns.material_catalog_id, '') name_spec_catalog_id,
  COALESCE(ns.match_count, '0') name_spec_match_count
FROM input i
LEFT JOIN exact_text e ON e.row_key = i.row_key
LEFT JOIN name_spec ns ON ns.row_key = i.row_key
ORDER BY i.row_key;
"""
            ),
            [
                "row_key",
                "exact_text_catalog_id",
                "exact_text_match_count",
                "name_spec_catalog_id",
                "name_spec_match_count",
            ],
        )
        for row in rows:
            result[row["row_key"]] = row
    by_tuple = {}
    for index, row in enumerate(line_rows):
        key = (row["material_name"].strip(), row["spec_model"].strip(), row["uom_text"].strip())
        if not key[0]:
            continue
        if key not in by_tuple and str(index) in result:
            by_tuple["|".join(key)] = result[str(index)]
    return by_tuple


def main() -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    line_sql = """
SET NOCOUNT ON;
SELECT
  ISNULL(NULLIF(LTRIM(RTRIM(l.CLID)),''), '') legacy_material_id,
  ISNULL(NULLIF(LTRIM(RTRIM(l.CLMC)),''), '') material_name,
  ISNULL(NULLIF(LTRIM(RTRIM(l.GGXH)),''), '') spec_model,
  ISNULL(NULLIF(LTRIM(RTRIM(l.DW)),''), '') uom_text,
  COUNT(*) line_rows,
  COUNT(DISTINCT h.ID) header_rows,
  CAST(SUM(ISNULL(l.SL,0)) AS decimal(18,4)) qty,
  CAST(SUM(ISNULL(l.HJ,0)) AS decimal(18,2)) amount
FROM dbo.T_RK_RKD h
JOIN dbo.T_RK_RKDCB l ON l.ZBID=h.ID
WHERE ISNULL(h.DEL,0)=0
GROUP BY
  NULLIF(LTRIM(RTRIM(l.CLID)),''),
  NULLIF(LTRIM(RTRIM(l.CLMC)),''),
  NULLIF(LTRIM(RTRIM(l.GGXH)),''),
  NULLIF(LTRIM(RTRIM(l.DW)),'')
ORDER BY SUM(ISNULL(l.HJ,0)) DESC;
"""
    line_rows = parse_rows(
        run_sqlcmd(line_sql),
        [
            "legacy_material_id",
            "material_name",
            "spec_model",
            "uom_text",
            "line_rows",
            "header_rows",
            "qty",
            "amount",
        ],
    )

    legacy_ids = sorted({row["legacy_material_id"] for row in line_rows if row["legacy_material_id"]})
    catalog_by_legacy = target_catalog_by_legacy_id(legacy_ids)
    catalog_by_text = target_catalog_by_business_key(line_rows)

    review_rows = []
    counters: Counter[str] = Counter()
    amount_by_state: Counter[str] = Counter()
    for row in line_rows:
        target = catalog_by_legacy.get(row["legacy_material_id"], {})
        text_key = "|".join([row["material_name"].strip(), row["spec_model"].strip(), row["uom_text"].strip()])
        text_target = catalog_by_text.get(text_key, {})
        has_catalog = bool(target.get("material_catalog_id"))
        has_promoted_product = bool(target.get("promoted_product_id"))
        if not row["legacy_material_id"]:
            state = "missing_legacy_material_id"
        elif has_catalog:
            state = "catalog_ready_by_legacy_id"
        elif text_target.get("exact_text_catalog_id"):
            state = "catalog_candidate_exact_text"
        elif text_target.get("name_spec_catalog_id"):
            state = "catalog_candidate_name_spec"
        else:
            state = "catalog_missing"
        counters[state] += 1
        amount_by_state[state] += float(row["amount"] or 0)
        review_rows.append(
            {
                **row,
                "coverage_state": state,
                "target_material_catalog_id": target.get("material_catalog_id", ""),
                "target_catalog_name": target.get("catalog_name", ""),
                "target_spec_model": target.get("spec_model", ""),
                "target_uom_text": target.get("uom_text", ""),
                "exact_text_catalog_id": text_target.get("exact_text_catalog_id", ""),
                "exact_text_match_count": text_target.get("exact_text_match_count", "0"),
                "name_spec_catalog_id": text_target.get("name_spec_catalog_id", ""),
                "name_spec_match_count": text_target.get("name_spec_match_count", "0"),
                "has_promoted_product": "yes" if has_promoted_product else "no",
            }
        )

    target_counts = parse_rows(
        run_psql(
            """
SELECT 'sc_material_catalog' metric, count(*)::text rows FROM sc_material_catalog
UNION ALL
SELECT 'sc_material_catalog_legacy' metric, count(*)::text rows
FROM sc_material_catalog WHERE legacy_material_id IS NOT NULL
UNION ALL
SELECT 'product_template_legacy_material' metric, count(*)::text rows
FROM product_template WHERE legacy_material_detail_id IS NOT NULL
UNION ALL
SELECT 'product_product_total' metric, count(*)::text rows FROM product_product;
"""
        ),
        ["metric", "rows"],
    )

    result = {
        "status": "PASS" if counters.get("catalog_missing", 0) == 0 else "WARN",
        "database": SQL_DATABASE,
        "target_database": PG_DATABASE,
        "business_policy": "material_catalog_control_without_product_promotion",
        "distinct_line_material_groups": len(line_rows),
        "distinct_legacy_material_ids": len(legacy_ids),
        "coverage_counts": dict(counters),
        "coverage_amounts": {key: round(value, 2) for key, value in amount_by_state.items()},
        "target_counts": target_counts,
        "decision": (
            "SCBS stock-in should use target material catalog as the control "
            "dimension; do not promote legacy materials into product library for this slice."
        ),
    }

    json_path = ARTIFACT_ROOT / "scbs_stock_in_material_catalog_coverage_report_v1.json"
    csv_path = ARTIFACT_ROOT / "scbs_stock_in_material_catalog_coverage_v1.csv"
    md_path = ARTIFACT_ROOT / "scbs_stock_in_material_catalog_coverage_report_v1.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "coverage_state",
            "legacy_material_id",
            "material_name",
            "spec_model",
            "uom_text",
            "line_rows",
            "header_rows",
            "qty",
            "amount",
            "target_material_catalog_id",
            "target_catalog_name",
            "target_spec_model",
            "target_uom_text",
            "exact_text_catalog_id",
            "exact_text_match_count",
            "name_spec_catalog_id",
            "name_spec_match_count",
            "has_promoted_product",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(review_rows)

    lines = [
        "# SCBS Stock-In Material Catalog Coverage Report",
        "",
        "## Business Policy",
        "",
        "SCBS stock-in material facts use `sc.material.catalog` as the management-control dimension.",
        "This slice should not promote historical materials into a product library.",
        "",
        "## Summary",
        "",
        f"- distinct line material groups: {len(line_rows)}",
        f"- distinct legacy material IDs: {len(legacy_ids)}",
        f"- coverage counts: `{json.dumps(dict(counters), ensure_ascii=False, sort_keys=True)}`",
        f"- coverage amounts: `{json.dumps({key: round(value, 2) for key, value in amount_by_state.items()}, ensure_ascii=False, sort_keys=True)}`",
        "",
        "## Target Baseline",
        "",
        "| Metric | Rows |",
        "| --- | ---: |",
        *[f"| {row['metric']} | {row['rows']} |" for row in target_counts],
        "",
        "## Projection Rule",
        "",
        "- Use `material_catalog_id` as the business fact dimension for cost statistics, budget comparison, and control reports.",
        "- Do not run product promotion for SCBS stock-in acceptance.",
        "- Legacy material ID matching is preferred, but this SCBS slice may use a different legacy ID namespace from the existing target catalog; text candidates are review suggestions only.",
        "- If a formal model still requires `product_id`, use the existing system-default material only as a technical placeholder and keep `material_catalog_id` as the source of truth.",
        "- Any future product promotion must be a separate operational decision, not a migration prerequisite.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path}`",
        f"- CSV: `{csv_path}`",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("SCBS_STOCK_IN_MATERIAL_CATALOG_COVERAGE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
