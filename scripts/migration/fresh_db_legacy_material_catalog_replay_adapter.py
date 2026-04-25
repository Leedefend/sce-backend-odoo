#!/usr/bin/env python3
"""Build replay payloads for legacy material catalog facts from LegacyDb."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
CATEGORY_CSV = ARTIFACT_DIR / "fresh_db_legacy_material_category_replay_payload_v1.csv"
DETAIL_CSV = ARTIFACT_DIR / "fresh_db_legacy_material_detail_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_material_catalog_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

CATEGORY_FIELDS = [
    "legacy_category_id",
    "legacy_guid",
    "code",
    "name",
    "parent_legacy_category_id",
    "legacy_project_id",
    "depth",
    "uom_text",
    "source_table",
    "note",
    "active",
]
DETAIL_FIELDS = [
    "legacy_material_id",
    "code",
    "name",
    "category_legacy_id",
    "parent_legacy_material_id",
    "uom_text",
    "aux_uom_text",
    "planned_price",
    "internal_price",
    "legacy_project_id",
    "depth",
    "spec_model",
    "pinyin",
    "short_pinyin",
    "import_time",
    "remark",
    "active",
]


def clean_sql(field: str) -> str:
    return f"REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), {field}), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"


def run_sql(sql: str) -> str:
    cmd = [
        "docker",
        "exec",
        SQL_CONTAINER,
        SQLCMD,
        "-S",
        "localhost",
        "-U",
        "sa",
        "-P",
        SQL_PASSWORD,
        "-C",
        "-d",
        SQL_DATABASE,
        "-W",
        "-s",
        "\t",
        "-h",
        "-1",
        "-Q",
        sql,
    ]
    return subprocess.check_output(cmd, text=True)


def sqlcmd(sql: str) -> list[str]:
    return [
        "docker",
        "exec",
        SQL_CONTAINER,
        SQLCMD,
        "-S",
        "localhost",
        "-U",
        "sa",
        "-P",
        SQL_PASSWORD,
        "-C",
        "-d",
        SQL_DATABASE,
        "-W",
        "-s",
        "\t",
        "-h",
        "-1",
        "-Q",
        sql,
    ]


def parse_rows(raw: str, fields: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("(") and stripped.endswith("rows affected)"):
            continue
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) != len(fields):
            raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(fields), "line": line[:500]})
        rows.append(dict(zip(fields, parts)))
    return rows


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_sql_csv(path: Path, fields: list[str], sql: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with subprocess.Popen(sqlcmd(sql), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
        if proc.stdout is None:
            raise RuntimeError("sqlcmd stdout unavailable")
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(fields)
            for line in proc.stdout:
                stripped = line.strip()
                if not stripped or stripped.startswith("(") and stripped.endswith("rows affected)"):
                    continue
                parts = line.rstrip("\r\n").split("\t")
                if len(parts) != len(fields):
                    raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(fields), "line": line[:500]})
                writer.writerow(parts)
                count += 1
        return_code = proc.wait()
    if return_code != 0:
        raise RuntimeError({"sqlcmd_failed": return_code, "path": str(path)})
    return count


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cost_category_rows() -> list[dict[str, str]]:
    sql = f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("Id")} AS legacy_category_id,
  {clean_sql("Guid")} AS legacy_guid,
  {clean_sql("f_Tree_Code")} AS code,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(f_Tree_Name)), ''), Id)")} AS name,
  {clean_sql("f_Tree_Parentid")} AS parent_legacy_category_id,
  {clean_sql("f_Tree_XMID")} AS legacy_project_id,
  {clean_sql("f_depth")} AS depth,
  {clean_sql("f_tree_dw")} AS uom_text,
  'C_Base_CBFL' AS source_table,
  {clean_sql("'source_table=C_Base_CBFL; project_name=' + COALESCE(XMMC, '') + '; remark=' + COALESCE(f_Tree_remark, '')")} AS note,
  CASE WHEN ISNULL(f_Tree_del, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_Base_CBFL
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
ORDER BY Id;
"""
    return parse_rows(run_sql(sql), CATEGORY_FIELDS)


def material_class_rows() -> list[dict[str, str]]:
    sql = f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("CONVERT(varchar(80), Guid)")} AS legacy_category_id,
  {clean_sql("CONVERT(varchar(80), Guid)")} AS legacy_guid,
  {clean_sql("f_Tree_BuildMaterClassCode")} AS code,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(f_Tree_BuildMaterClassName)), ''), CONVERT(varchar(80), Guid))")} AS name,
  '' AS parent_legacy_category_id,
  '' AS legacy_project_id,
  '' AS depth,
  '' AS uom_text,
  'T_Base_BuildMaterialClass' AS source_table,
  {clean_sql("'source_table=T_Base_BuildMaterialClass; parent=' + COALESCE(SJBMC, '') + '; remark=' + COALESCE(f_Tree_remark, '')")} AS note,
  CASE WHEN ISNULL(f_Tree_del, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.T_Base_BuildMaterialClass
WHERE Guid IS NOT NULL
ORDER BY f_Tree_BuildMaterClassCode, Guid;
"""
    return parse_rows(run_sql(sql), CATEGORY_FIELDS)


def orphan_detail_category_rows() -> list[dict[str, str]]:
    sql = f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("d.f_Tree_BuildMaterialClassid")} AS legacy_category_id,
  {clean_sql("d.f_Tree_BuildMaterialClassid")} AS legacy_guid,
  '' AS code,
  {clean_sql("'旧库未建档物料分类 ' + d.f_Tree_BuildMaterialClassid")} AS name,
  '' AS parent_legacy_category_id,
  '' AS legacy_project_id,
  '' AS depth,
  '' AS uom_text,
  'T_Base_MaterialDetail' AS source_table,
  {clean_sql("'source_table=T_Base_MaterialDetail; orphan_category_key=1; referenced_rows=' + CONVERT(varchar(40), COUNT_BIG(*))")} AS note,
  '1' AS active
FROM dbo.T_Base_MaterialDetail d
WHERE NULLIF(LTRIM(RTRIM(d.ID)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(d.f_Tree_BuildMaterialClassid)), '') IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM dbo.T_Base_BuildMaterialClass c
    WHERE CONVERT(varchar(80), c.Guid) = d.f_Tree_BuildMaterialClassid
  )
GROUP BY d.f_Tree_BuildMaterialClassid
ORDER BY d.f_Tree_BuildMaterialClassid;
"""
    return parse_rows(run_sql(sql), CATEGORY_FIELDS)


def category_rows() -> list[dict[str, str]]:
    return material_class_rows() + orphan_detail_category_rows() + cost_category_rows()


def detail_rows() -> list[dict[str, str]]:
    raise RuntimeError("detail_rows is intentionally streamed by write_detail_csv")


def write_detail_csv() -> int:
    sql = f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("ID")} AS legacy_material_id,
  {clean_sql("f_Tree_Code")} AS code,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(f_Tree_BuildMaterDetailName)), ''), ID)")} AS name,
  {clean_sql("f_Tree_BuildMaterialClassid")} AS category_legacy_id,
  {clean_sql("f_Tree_Parentid")} AS parent_legacy_material_id,
  {clean_sql("f_Tree_DW")} AS uom_text,
  {clean_sql("f_Tree_FZDW")} AS aux_uom_text,
  CONVERT(varchar(80), COALESCE(f_Tree_JHDJ, 0)) AS planned_price,
  CONVERT(varchar(80), COALESCE(NBJHJ, 0)) AS internal_price,
  {clean_sql("XMID")} AS legacy_project_id,
  {clean_sql("Depth")} AS depth,
  {clean_sql("XH")} AS spec_model,
  {clean_sql("PY")} AS pinyin,
  {clean_sql("JP")} AS short_pinyin,
  COALESCE(CONVERT(varchar(23), f_Tree_importTime, 121), '') AS import_time,
  {clean_sql("f_Tree_remark")} AS remark,
  CASE WHEN ISNULL(f_Tree_del, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.T_Base_MaterialDetail
WHERE NULLIF(LTRIM(RTRIM(ID)), '') IS NOT NULL
ORDER BY ID;
"""
    return write_sql_csv(DETAIL_CSV, DETAIL_FIELDS, sql)


def main() -> int:
    categories = category_rows()
    write_csv(CATEGORY_CSV, CATEGORY_FIELDS, categories)
    detail_count = write_detail_csv()
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_material_catalog_replay_adapter",
        "category_rows": len(categories),
        "detail_rows": detail_count,
        "category_csv": str(CATEGORY_CSV),
        "detail_csv": str(DETAIL_CSV),
        "decision": "legacy_material_catalog_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_MATERIAL_CATALOG_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
