#!/usr/bin/env python3
"""Mine residual SCBS facts without project_id for project clues."""

from __future__ import annotations

import csv
import json
import os
import subprocess
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
    escaped = sql.replace('"', '\\"')
    cmd = [
        "docker",
        "exec",
        SQL_CONTAINER,
        "bash",
        "-lc",
        f"printf \"%s\" \"{escaped}\" | {SQLCMD} -S localhost -U sa -P \"$MSSQL_SA_PASSWORD\" -C -d {SQL_DATABASE} -h -1 -W -s '|' -i /dev/stdin",
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


def residual_ids(source_table: str) -> list[str]:
    rows = parse_rows(
        run_psql(
            f"""
SELECT legacy_record_id
  FROM sc_legacy_scbs_fact_staging
 WHERE import_batch = 'scbs_fact_staging_v1'
   AND active IS TRUE
   AND mapping_gate_state = 'projection_ready'
   AND project_id IS NULL
   AND source_table = '{source_table}'
 ORDER BY legacy_record_id;
"""
        ),
        ["legacy_record_id"],
    )
    return [row["legacy_record_id"].replace("'", "''") for row in rows if row["legacy_record_id"]]


def values_clause(ids: list[str]) -> str:
    return ",".join(f"('{item}')" for item in ids)


def query_batches(ids: list[str], sql_template: str, fields: list[str], batch_size: int = 600) -> list[dict[str, str]]:
    all_rows: list[dict[str, str]] = []
    for offset in range(0, len(ids), batch_size):
        batch = ids[offset : offset + batch_size]
        if not batch:
            continue
        sql = sql_template.format(values=values_clause(batch))
        all_rows.extend(parse_rows(run_sqlcmd(sql), fields))
    return all_rows


def nonempty(value: str) -> bool:
    normalized = str(value or "").strip()
    return bool(normalized and normalized.upper() != "NULL")


def summarize(rows: list[dict[str, str]], family: str, fields: list[str]) -> list[dict[str, object]]:
    summary = []
    for field in fields:
        values = [row.get(field, "") for row in rows if nonempty(row.get(field, ""))]
        summary.append(
            {
                "fact_family": family,
                "field": field,
                "rows_with_value": len(values),
                "distinct_values": len(set(values)),
                "sample_values": " / ".join(list(dict.fromkeys(values))[:8]),
            }
        )
    return summary


def group_rows(rows: list[dict[str, str]], family: str, field: str) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    for row in rows:
        value = str(row.get(field) or "").strip() or "[EMPTY]"
        bucket = grouped.setdefault(
            value,
            {
                "fact_family": family,
                "field": field,
                "value": value,
                "rows": 0,
                "amount_total": 0.0,
            },
        )
        bucket["rows"] = int(bucket["rows"]) + 1
        try:
            bucket["amount_total"] = float(bucket["amount_total"]) + float(row.get("amount") or 0)
        except Exception:
            pass
    return sorted(grouped.values(), key=lambda item: (-float(item["amount_total"]), -int(item["rows"]), str(item["value"])))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main() -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    payment_ids = residual_ids("T_FK_Supplier")
    contract_ids = residual_ids("T_GYSHT_INFO")

    payment_fields = [
        "legacy_record_id",
        "document_no",
        "amount",
        "f_xmid",
        "xmmc",
        "tsxmid",
        "tsxmmc",
        "lyxmid",
        "lyxm",
        "gcmc",
        "bm",
        "sjs_company",
        "supplier_name",
        "remark",
    ]
    payment_rows = query_batches(
        payment_ids,
        """
SET NOCOUNT ON;
WITH ids(ID) AS (SELECT * FROM (VALUES {values}) AS v(ID))
SELECT p.Id,
       ISNULL(p.DJBH, ''),
       CAST(ISNULL(p.f_FKJE, 0) AS decimal(18,2)),
       ISNULL(p.f_XMID, ''),
       ISNULL(p.XMMC, ''),
       ISNULL(p.TSXMID, ''),
       ISNULL(p.TSXMMC, ''),
       ISNULL(p.f_LYXMID, ''),
       ISNULL(p.f_LYXM, ''),
       ISNULL(p.GCMC, ''),
       ISNULL(p.f_BM, ''),
       ISNULL(p.D_LYXM_SJSKDW, ''),
       ISNULL(p.f_SupplierName, ''),
       ISNULL(p.Remark, '')
  FROM dbo.T_FK_Supplier p
  JOIN ids i ON i.ID = p.Id
 ORDER BY p.f_FKJE DESC;
""",
        payment_fields,
    )

    contract_fields = [
        "legacy_record_id",
        "document_no",
        "amount",
        "xmid",
        "project_name",
        "gcmc",
        "jbbm",
        "wfdw",
        "zbdhjbt",
        "zmbtext",
        "supplier_name",
        "contract_name",
    ]
    contract_rows = query_batches(
        contract_ids,
        """
SET NOCOUNT ON;
WITH ids(ID) AS (SELECT * FROM (VALUES {values}) AS v(ID))
SELECT c.Id,
       ISNULL(c.DJBH, ''),
       CAST(ISNULL(c.ZJE, 0) AS decimal(18,2)),
       ISNULL(c.XMID, ''),
       ISNULL(c.ProjectName, ''),
       ISNULL(c.GCMC, ''),
       ISNULL(c.JBBM, ''),
       ISNULL(c.WFDW, ''),
       ISNULL(c.ZBDHJBT, ''),
       ISNULL(c.ZMBTEXT, ''),
       ISNULL(c.f_GYSName, ''),
       ISNULL(c.HTMC, '')
  FROM dbo.T_GYSHT_INFO c
  JOIN ids i ON i.ID = c.Id
 ORDER BY c.ZJE DESC;
""",
        contract_fields,
    )

    summary_rows = []
    summary_rows.extend(
        summarize(payment_rows, "payment", [field for field in payment_fields if field not in {"legacy_record_id", "amount"}])
    )
    summary_rows.extend(
        summarize(contract_rows, "supplier_contract", [field for field in contract_fields if field not in {"legacy_record_id", "amount"}])
    )

    summary_csv = ARTIFACT_ROOT / "scbs_residual_project_clue_summary_v1.csv"
    payment_csv = ARTIFACT_ROOT / "scbs_residual_project_clue_payment_examples_v1.csv"
    contract_csv = ARTIFACT_ROOT / "scbs_residual_project_clue_contract_examples_v1.csv"
    group_csv = ARTIFACT_ROOT / "scbs_residual_project_clue_grouping_v1.csv"
    result_json = ARTIFACT_ROOT / "scbs_residual_project_clue_result_v1.json"

    write_csv(summary_csv, summary_rows, ["fact_family", "field", "rows_with_value", "distinct_values", "sample_values"])
    write_csv(payment_csv, payment_rows, payment_fields)
    write_csv(contract_csv, contract_rows, contract_fields)
    group_summary = []
    group_summary.extend(group_rows(payment_rows, "payment", "bm"))
    group_summary.extend(group_rows(payment_rows, "payment", "supplier_name"))
    group_summary.extend(group_rows(contract_rows, "supplier_contract", "zmbtext"))
    group_summary.extend(group_rows(contract_rows, "supplier_contract", "supplier_name"))
    write_csv(group_csv, group_summary, ["fact_family", "field", "value", "rows", "amount_total"])

    strong_payment_clue_rows = sum(1 for row in payment_rows if nonempty(row.get("f_xmid")) or nonempty(row.get("xmmc")) or nonempty(row.get("tsxmid")) or nonempty(row.get("tsxmmc")) or nonempty(row.get("lyxmid")) or nonempty(row.get("lyxm")))
    strong_contract_clue_rows = sum(1 for row in contract_rows if nonempty(row.get("xmid")) or nonempty(row.get("project_name")) or nonempty(row.get("gcmc")))

    payload = {
        "status": "PASS",
        "database": PG_DATABASE,
        "legacy_database": SQL_DATABASE,
        "summary_csv": str(summary_csv),
        "payment_examples_csv": str(payment_csv),
        "contract_examples_csv": str(contract_csv),
        "grouping_csv": str(group_csv),
        "payment_rows": len(payment_rows),
        "contract_rows": len(contract_rows),
        "payment_rows_with_project_clue": strong_payment_clue_rows,
        "contract_rows_with_project_clue": strong_contract_clue_rows,
    }
    result_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCBS_RESIDUAL_PROJECT_CLUE_REPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
