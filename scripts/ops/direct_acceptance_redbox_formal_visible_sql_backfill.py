#!/usr/bin/env python3
"""Backfill acceptance-visible columns on formal business records with SQL batches.

Run with:
    DB_NAME=sc_demo MIGRATION_REPLAY_DB_ALLOWLIST=sc_demo DIRECT_ACCEPTANCE_REDBOX_APPLY=1 \
      bash scripts/ops/odoo_shell_exec.sh < scripts/ops/direct_acceptance_redbox_formal_visible_sql_backfill.py
"""

from __future__ import annotations

import json
import os
import zlib
from pathlib import Path
from typing import Any

from psycopg2 import sql
from psycopg2.extras import execute_batch


SOURCE_SYSTEM = "online_old_scbsly"
SOURCE_FACT_MODEL = "online_old_scbsly:direct_acceptance_fact"
SOURCE_DIRECT_MODEL = "online_old_scbsly:direct_acceptance"
OUTPUT_JSON_NAME = "direct_acceptance_redbox_formal_visible_sql_backfill_result_v1.json"
APPLY = os.getenv("DIRECT_ACCEPTANCE_REDBOX_APPLY") == "1"
LIMIT = int(os.getenv("DIRECT_ACCEPTANCE_REDBOX_LIMIT", "0") or "0")
PAGE_SIZE = int(os.getenv("DIRECT_ACCEPTANCE_REDBOX_SQL_PAGE_SIZE", "500") or "500")


SPECS: dict[str, dict[str, Any]] = {
    "材料计划": {"model": "project.material.plan", "mode": "legacy_fact"},
    "报价单": {"model": "sc.material.rfq", "mode": "legacy_fact"},
    "入库": {"model": "sc.material.inbound", "mode": "legacy_fact"},
    "方单": {"model": "sc.labor.usage", "mode": "legacy_fact"},
    "零星用工": {"model": "sc.labor.usage", "mode": "legacy_fact"},
    "分包方单": {"model": "sc.subcontract.request", "mode": "legacy_fact"},
    "机械台班记录": {"model": "sc.equipment.usage", "mode": "legacy_fact"},
    "租入": {"model": "sc.material.rental.order", "mode": "legacy_fact"},
    "还租": {"model": "sc.material.rental.order", "mode": "legacy_fact"},
    "管理人员工资表": {"model": "sc.hr.payroll.document", "mode": "legacy_source_payroll"},
    "油卡登记": {"model": "sc.fund.account.operation", "mode": "legacy_source_record"},
    "充值登记": {"model": "sc.fund.account.operation", "mode": "legacy_source_record"},
    "施工日志（新）": {"model": "sc.construction.diary", "mode": "legacy_source_record"},
}


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path(f"/tmp/direct_acceptance_redbox/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_test"
            probe.write_text("", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/direct_acceptance_redbox/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_visible_sql_backfill": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def clean(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return "" if text.lower() in {"false", "none", "null"} else text


def visible(fact, index: int) -> str:
    return clean(getattr(fact, f"legacy_visible_{index:02d}", ""))


def source_key(label: str, fact) -> int:
    token = f"{SOURCE_SYSTEM}:{label}:{fact.legacy_record_id or fact.id}".encode("utf-8")
    return zlib.crc32(token) & 0x7FFFFFFF


def source_facts(label: str):
    return env["sc.legacy.direct.acceptance.fact"].sudo().search(  # noqa: F821
        [("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", label), ("active", "=", True)],
        order="document_no,legacy_record_id,id",
        limit=LIMIT or None,
    )


def sql_columns(model_name: str) -> list[str]:
    fields = env[model_name]._fields  # noqa: F821
    names = ["legacy_acceptance_label"]
    names.extend(f"legacy_visible_{index:02d}" for index in range(1, 61))
    return [name for name in names if name in fields]


def update_query(table: str, columns: list[str], mode: str):
    assignments = [
        sql.SQL("{} = %s").format(sql.Identifier(column))
        for column in columns
    ]
    if mode == "legacy_fact":
        where = sql.SQL("legacy_fact_model = %s AND legacy_fact_id = %s")
    elif mode == "legacy_source_payroll":
        where = sql.SQL("legacy_source_table = %s AND legacy_source_id = %s")
    else:
        where = sql.SQL("legacy_source_model = %s AND legacy_source_table = %s AND legacy_record_id = %s")
    return sql.SQL("UPDATE {} SET {} WHERE {}").format(
        sql.Identifier(table),
        sql.SQL(", ").join(assignments),
        where,
    )


def row_for(label: str, mode: str, columns: list[str], fact) -> tuple:
    values_by_column = {"legacy_acceptance_label": label}
    values_by_column.update({f"legacy_visible_{index:02d}": visible(fact, index) for index in range(1, 61)})
    row = [values_by_column[column] for column in columns]
    if mode == "legacy_fact":
        row.extend([SOURCE_FACT_MODEL, source_key(label, fact)])
    elif mode == "legacy_source_payroll":
        row.extend([f"direct_acceptance:{label}", clean(fact.legacy_record_id) or str(fact.id)])
    else:
        row.extend([SOURCE_DIRECT_MODEL, f"direct_acceptance:{label}", f"{label}:{fact.legacy_record_id or fact.id}"])
    return tuple(row)


ensure_allowed_db()
results = []

for label, spec in SPECS.items():
    model_name = spec["model"]
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    columns = sql_columns(model_name)
    facts = source_facts(label)
    query = update_query(Model._table, columns, spec["mode"])
    rows = [row_for(label, spec["mode"], columns, fact) for fact in facts]
    updated = 0
    if APPLY and rows:
        before = env.cr.rowcount  # noqa: F821
        del before
        execute_batch(env.cr._obj, query, rows, page_size=PAGE_SIZE)  # noqa: F821
        updated = len(rows)
    formal_count = Model.search_count(
        [("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", f"direct_acceptance:{label}")]
        if spec["mode"] == "legacy_fact"
        else (
            [("legacy_source_table", "=", "direct_acceptance:管理人员工资表")]
            if spec["mode"] == "legacy_source_payroll"
            else [("legacy_source_model", "=", SOURCE_DIRECT_MODEL), ("legacy_source_table", "=", f"direct_acceptance:{label}")]
        )
    )
    results.append(
        {
            "label": label,
            "model": model_name,
            "source_count": len(facts),
            "formal_count": formal_count,
            "updated_rows_requested": updated,
            "visible_column_count": len(columns),
            "status": "PASS" if formal_count == len(facts) and columns else "REVIEW",
        }
    )

if APPLY:
    env.cr.commit()  # noqa: F821
else:
    env.cr.rollback()  # noqa: F821

payload = {
    "status": "PASS" if all(item["status"] == "PASS" for item in results) else "REVIEW",
    "mode": "direct_acceptance_redbox_formal_visible_sql_backfill",
    "apply": APPLY,
    "database": env.cr.dbname,  # noqa: F821
    "results": results,
}
out = artifact_root() / OUTPUT_JSON_NAME
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("DIRECT_ACCEPTANCE_REDBOX_FORMAL_VISIBLE_SQL_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
