# -*- coding: utf-8 -*-
"""Probe business evidence behind the user-confirmed project name baseline.

This script is read-only. It checks whether names from
`user_project_name_strategy_20260520.csv` can be backed by existing project
records and strong business fact tables.
"""

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_SOURCE = "migration_assets/10_master/project/user_project_name_strategy_20260520.csv"

FACT_TABLES = [
    "construction_contract",
    "sc_general_contract",
    "payment_request",
    "sc_payment_execution",
    "sc_receipt_income",
    "sc_fund_account_operation",
    "sc_treasury_ledger",
    "sc_invoice_registration",
    "sc_material_inbound",
    "sc_material_inbound_line",
    "sc_material_stock_summary",
    "sc_settlement_order",
    "sc_legacy_purchase_contract_fact",
    "sc_legacy_labor_subcontract_fact",
    "sc_legacy_payment_residual_fact",
    "sc_legacy_receipt_income_fact",
    "sc_legacy_material_stock_fact",
    "sc_legacy_invoice_registration_line",
    "sc_legacy_expense_deposit_fact",
    "sc_legacy_financing_loan_fact",
    "sc_legacy_tender_registration_fact",
    "sc_legacy_scbs_fact_staging",
]

TEXT_SEARCH_TABLES = [
    ("sc_legacy_purchase_contract_fact", "project_name"),
    ("sc_legacy_labor_subcontract_fact", "project_name"),
    ("sc_legacy_payment_residual_fact", "project_name"),
    ("sc_legacy_receipt_income_fact", "legacy_project_name"),
    ("sc_legacy_material_stock_fact", "project_name"),
    ("sc_legacy_invoice_registration_line", "project_name"),
    ("sc_legacy_expense_deposit_fact", "legacy_project_name"),
    ("sc_legacy_financing_loan_fact", "legacy_project_name"),
    ("sc_legacy_tender_registration_fact", "project_name"),
    ("sc_legacy_construction_diary_line", "project_name"),
    ("sc_legacy_account_transaction_line", "project_name"),
    ("sc_legacy_fund_daily_line", "project_name"),
    ("sc_legacy_project_fund_balance_fact", "project_name"),
]


def normalize_name(value: object) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", "", text)
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("－", "-").replace("—", "-").replace("–", "-")
    return text.rstrip(".")


def source_path() -> Path:
    raw = os.getenv("MIGRATION_USER_PROJECT_STRATEGY_CSV") or DEFAULT_SOURCE
    path = Path(raw)
    if path.is_absolute():
        return path
    if raw.startswith("migration_assets/") and Path("/mnt/migration_assets").exists():
        return Path("/mnt/migration_assets") / raw[len("migration_assets/") :]
    return Path.cwd() / path


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("ARTIFACT_ROOT") or "/tmp/project_master_stabilization")
    root.mkdir(parents=True, exist_ok=True)
    return root


def fetch_dicts(query: str, params: tuple = ()) -> list[dict[str, object]]:
    env.cr.execute(query, params)  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


def table_exists(table: str) -> bool:
    rows = fetch_dicts("SELECT to_regclass(%s) AS reg", (table,))
    return bool(rows and rows[0]["reg"])


def table_has_column(table: str, column: str) -> bool:
    rows = fetch_dicts(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_schema = current_schema()
           AND table_name = %s
           AND column_name = %s
        """,
        (table, column),
    )
    return bool(rows)


def read_source(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def project_name(project) -> str:
    name = project.name
    if isinstance(name, dict):
        return name.get("zh_CN") or name.get("en_US") or next(iter(name.values()), "") or ""
    return str(name or "")


def main() -> None:
    source = source_path()
    source_rows = read_source(source)
    source_by_name = {(row.get("normalized_project_name") or normalize_name(row.get("project_name"))): row for row in source_rows}

    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    projects = Project.search([], order="id")
    projects_by_name = defaultdict(lambda: Project.browse())
    for project in projects:
        projects_by_name[normalize_name(project_name(project))] |= project

    project_fact_counts: dict[int, Counter[str]] = defaultdict(Counter)
    table_totals = {}
    for table in FACT_TABLES:
        if not table_exists(table) or not table_has_column(table, "project_id"):
            continue
        rows = fetch_dicts(
            f"SELECT project_id, COUNT(*) AS cnt FROM {table} WHERE project_id IS NOT NULL GROUP BY project_id"
        )
        table_totals[table] = sum(int(row["cnt"]) for row in rows)
        for row in rows:
            project_fact_counts[int(row["project_id"])][table] += int(row["cnt"])

    summary_rows = []
    missing_rows = []
    duplicate_names = 0
    matched_with_evidence = 0
    matched_without_evidence = 0

    for key, source_row in source_by_name.items():
        candidates = projects_by_name.get(key, Project.browse())
        if not candidates:
            missing_rows.append(source_row)
            continue
        if len(candidates) > 1:
            duplicate_names += 1
        evidence_total = sum(sum(project_fact_counts[project.id].values()) for project in candidates)
        if evidence_total:
            matched_with_evidence += 1
        else:
            matched_without_evidence += 1
        for project in candidates:
            counts = project_fact_counts[project.id]
            summary_rows.append(
                {
                    "source_project_name": source_row.get("project_name", ""),
                    "operation_strategy": source_row.get("operation_strategy", ""),
                    "project_id": project.id,
                    "db_project_name": project_name(project),
                    "active": bool(project.active),
                    "legacy_project_id": project.legacy_project_id or "",
                    "evidence_total": sum(counts.values()),
                    "evidence_tables": ";".join(f"{key}:{value}" for key, value in counts.most_common() if value),
                }
            )

    missing_text_rows = []
    for row in missing_rows:
        source_name = row.get("project_name", "")
        normalized = normalize_name(source_name)
        hits = []
        for table, column in TEXT_SEARCH_TABLES:
            if not table_exists(table) or not table_has_column(table, column):
                continue
            count_rows = fetch_dicts(
                f"""
                SELECT COUNT(*) AS cnt
                  FROM {table}
                 WHERE regexp_replace(
                         replace(replace(replace(coalesce({column}, ''), '（', '('), '）', ')'), '－', '-'),
                         '[[:space:]]', '', 'g'
                       ) = %s
                """,
                (normalized,),
            )
            count = int(count_rows[0]["cnt"]) if count_rows else 0
            if count:
                hits.append(f"{table}.{column}:{count}")
        missing_text_rows.append(
            {
                "source_project_name": source_name,
                "operation_strategy": row.get("operation_strategy", ""),
                "text_evidence_total": sum(int(hit.rsplit(":", 1)[1]) for hit in hits),
                "text_evidence_tables": ";".join(hits),
            }
        )

    root = artifact_root()
    summary_csv = root / "user_project_business_evidence_summary_20260520.csv"
    missing_csv = root / "user_project_missing_name_text_evidence_20260520.csv"
    result_json = root / "user_project_business_evidence_result_20260520.json"

    write_csv(
        summary_csv,
        summary_rows,
        [
            "source_project_name",
            "operation_strategy",
            "project_id",
            "db_project_name",
            "active",
            "legacy_project_id",
            "evidence_total",
            "evidence_tables",
        ],
    )
    write_csv(
        missing_csv,
        missing_text_rows,
        ["source_project_name", "operation_strategy", "text_evidence_total", "text_evidence_tables"],
    )

    payload = {
        "status": "PASS",
        "database": env.cr.dbname,  # noqa: F821
        "source_csv": str(source),
        "source_rows": len(source_rows),
        "source_counts": dict(Counter(row.get("operation_strategy") for row in source_rows)),
        "matched_source_names": len(source_rows) - len(missing_rows),
        "missing_source_names": len(missing_rows),
        "duplicate_source_names": duplicate_names,
        "matched_with_business_evidence": matched_with_evidence,
        "matched_without_business_evidence": matched_without_evidence,
        "missing_with_text_evidence": sum(1 for row in missing_text_rows if row["text_evidence_total"] > 0),
        "missing_without_text_evidence": sum(1 for row in missing_text_rows if row["text_evidence_total"] == 0),
        "fact_table_totals": table_totals,
        "summary_csv": str(summary_csv),
        "missing_text_csv": str(missing_csv),
        "readonly": True,
    }
    write_json(result_json, payload)
    print("USER_PROJECT_BUSINESS_EVIDENCE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
