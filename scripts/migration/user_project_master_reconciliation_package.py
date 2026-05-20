# -*- coding: utf-8 -*-
"""Build a replayable user project master reconciliation package.

This script is read-only. It classifies the user-confirmed project name and
operation-strategy baseline into:

- exact names with business evidence;
- exact names without business evidence;
- missing names that need create/alias review;
- duplicate project names with canonical-project candidates.

It intentionally does not create projects, merge projects, or relink business
facts. Later write scripts should consume the generated review package.
"""

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_SOURCE = "migration_assets/10_master/project/user_project_name_strategy_20260520.csv"
PACKAGE_ID = "user_project_master_reconciliation_20260520"

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
        rows = [dict(row) for row in csv.DictReader(handle)]
    required = {"project_name", "normalized_project_name", "operation_strategy"}
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        raise RuntimeError(f"source csv missing headers: {sorted(missing)}")
    duplicate_names = [
        key for key, count in Counter(row["normalized_project_name"] or normalize_name(row["project_name"]) for row in rows).items() if count > 1
    ]
    if duplicate_names:
        raise RuntimeError(f"source csv has duplicate normalized names: {duplicate_names[:20]}")
    return rows


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


def build_fact_counts() -> dict[int, Counter[str]]:
    counts_by_project: dict[int, Counter[str]] = defaultdict(Counter)
    for table in FACT_TABLES:
        if not table_exists(table) or not table_has_column(table, "project_id"):
            continue
        for row in fetch_dicts(
            f"SELECT project_id, COUNT(*) AS cnt FROM {table} WHERE project_id IS NOT NULL GROUP BY project_id"
        ):
            counts_by_project[int(row["project_id"])][table] += int(row["cnt"])
    return counts_by_project


def text_evidence_for_name(source_name: str) -> list[str]:
    normalized = normalize_name(source_name)
    hits = []
    for table, column in TEXT_SEARCH_TABLES:
        if not table_exists(table) or not table_has_column(table, column):
            continue
        rows = fetch_dicts(
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
        count = int(rows[0]["cnt"]) if rows else 0
        if count:
            hits.append(f"{table}.{column}:{count}")
    return hits


def pick_canonical(candidates) -> tuple[object, str]:
    ranked = sorted(
        candidates,
        key=lambda item: (
            item["evidence_total"],
            1 if item["active"] else 0,
            item["project_id"],
        ),
        reverse=True,
    )
    if not ranked:
        return None, ""
    top = ranked[0]
    second_total = ranked[1]["evidence_total"] if len(ranked) > 1 else -1
    if top["evidence_total"] > 0 and top["evidence_total"] > second_total:
        return top, "highest_business_evidence_total"
    active_with_evidence = [row for row in ranked if row["active"] and row["evidence_total"] > 0]
    if len(active_with_evidence) == 1:
        return active_with_evidence[0], "single_active_project_with_business_evidence"
    return None, "manual_review_required"


def candidate_payload(project, counts: Counter[str]) -> dict[str, object]:
    return {
        "project_id": project.id,
        "db_project_name": project_name(project),
        "active": bool(project.active),
        "legacy_project_id": project.legacy_project_id or "",
        "current_operation_strategy": project.operation_strategy or "",
        "evidence_total": sum(counts.values()),
        "evidence_tables": ";".join(f"{key}:{value}" for key, value in counts.most_common() if value),
    }


def main() -> None:
    source = source_path()
    source_rows = read_source(source)
    source_by_name = {(row.get("normalized_project_name") or normalize_name(row.get("project_name"))): row for row in source_rows}

    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    projects = Project.search([], order="id")
    projects_by_name = defaultdict(lambda: Project.browse())
    for project in projects:
        projects_by_name[normalize_name(project_name(project))] |= project

    fact_counts = build_fact_counts()
    package_rows = []
    missing_rows = []
    duplicate_rows = []
    no_evidence_rows = []

    for source_key, source_row in source_by_name.items():
        source_name = source_row.get("project_name", "")
        strategy = source_row.get("operation_strategy", "")
        candidates = projects_by_name.get(source_key, Project.browse())
        candidate_rows = [candidate_payload(project, fact_counts[project.id]) for project in candidates]
        total_evidence = sum(int(row["evidence_total"]) for row in candidate_rows)

        if not candidates:
            text_hits = text_evidence_for_name(source_name)
            status = "missing_with_text_evidence" if text_hits else "missing_no_business_evidence"
            action = "manual_alias_or_create_review"
            row = {
                "source_project_name": source_name,
                "operation_strategy": strategy,
                "status": status,
                "proposed_action": action,
                "canonical_project_id": "",
                "canonical_project_name": "",
                "canonical_reason": "",
                "candidate_count": 0,
                "evidence_total": 0,
                "evidence_tables": "",
                "legacy_project_id": "",
                "active": "",
                "text_evidence_tables": ";".join(text_hits),
                "review_note": "No exact project.project match; do not relink business facts by name.",
            }
            package_rows.append(row)
            missing_rows.append(row)
            continue

        if len(candidates) > 1:
            canonical, reason = pick_canonical(candidate_rows)
            status = "duplicate_with_canonical_candidate" if canonical else "duplicate_manual_review"
            action = "confirm_canonical_project_before_write"
            for candidate in candidate_rows:
                duplicate_rows.append(
                    {
                        "source_project_name": source_name,
                        "operation_strategy": strategy,
                        "candidate_project_id": candidate["project_id"],
                        "candidate_project_name": candidate["db_project_name"],
                        "candidate_active": candidate["active"],
                        "candidate_legacy_project_id": candidate["legacy_project_id"],
                        "candidate_operation_strategy": candidate["current_operation_strategy"],
                        "candidate_evidence_total": candidate["evidence_total"],
                        "candidate_evidence_tables": candidate["evidence_tables"],
                        "recommended": bool(canonical and candidate["project_id"] == canonical["project_id"]),
                        "recommend_reason": reason,
                    }
                )
            package_rows.append(
                {
                    "source_project_name": source_name,
                    "operation_strategy": strategy,
                    "status": status,
                    "proposed_action": action,
                    "canonical_project_id": canonical["project_id"] if canonical else "",
                    "canonical_project_name": canonical["db_project_name"] if canonical else "",
                    "canonical_reason": reason,
                    "candidate_count": len(candidate_rows),
                    "evidence_total": total_evidence,
                    "evidence_tables": "",
                    "legacy_project_id": "",
                    "active": "",
                    "text_evidence_tables": "",
                    "review_note": "Duplicate exact project names; choose canonical carrier before any alias/write.",
                }
            )
            continue

        only = candidate_rows[0]
        status = "exact_with_business_evidence" if only["evidence_total"] else "exact_without_business_evidence"
        action = "keep_confirmed" if only["evidence_total"] else "manual_business_evidence_review"
        row = {
            "source_project_name": source_name,
            "operation_strategy": strategy,
            "status": status,
            "proposed_action": action,
            "canonical_project_id": only["project_id"],
            "canonical_project_name": only["db_project_name"],
            "canonical_reason": "single_exact_project_name_match",
            "candidate_count": 1,
            "evidence_total": only["evidence_total"],
            "evidence_tables": only["evidence_tables"],
            "legacy_project_id": only["legacy_project_id"],
            "active": only["active"],
            "text_evidence_tables": "",
            "review_note": "",
        }
        package_rows.append(row)
        if not only["evidence_total"]:
            no_evidence_rows.append(row)

    root = artifact_root()
    package_csv = root / f"{PACKAGE_ID}_package.csv"
    missing_csv = root / f"{PACKAGE_ID}_missing_review.csv"
    duplicates_csv = root / f"{PACKAGE_ID}_duplicate_canonical_review.csv"
    no_evidence_csv = root / f"{PACKAGE_ID}_no_evidence_review.csv"
    result_json = root / f"{PACKAGE_ID}_result.json"

    package_fields = [
        "source_project_name",
        "operation_strategy",
        "status",
        "proposed_action",
        "canonical_project_id",
        "canonical_project_name",
        "canonical_reason",
        "candidate_count",
        "evidence_total",
        "evidence_tables",
        "legacy_project_id",
        "active",
        "text_evidence_tables",
        "review_note",
    ]
    write_csv(package_csv, package_rows, package_fields)
    write_csv(missing_csv, missing_rows, package_fields)
    write_csv(
        duplicates_csv,
        duplicate_rows,
        [
            "source_project_name",
            "operation_strategy",
            "candidate_project_id",
            "candidate_project_name",
            "candidate_active",
            "candidate_legacy_project_id",
            "candidate_operation_strategy",
            "candidate_evidence_total",
            "candidate_evidence_tables",
            "recommended",
            "recommend_reason",
        ],
    )
    write_csv(no_evidence_csv, no_evidence_rows, package_fields)

    status_counts = Counter(row["status"] for row in package_rows)
    action_counts = Counter(row["proposed_action"] for row in package_rows)
    payload = {
        "status": "PASS",
        "package_id": PACKAGE_ID,
        "database": env.cr.dbname,  # noqa: F821
        "source_csv": str(source),
        "source_rows": len(source_rows),
        "source_counts": dict(Counter(row.get("operation_strategy") for row in source_rows)),
        "status_counts": dict(status_counts),
        "action_counts": dict(action_counts),
        "package_csv": str(package_csv),
        "missing_review_csv": str(missing_csv),
        "duplicate_canonical_review_csv": str(duplicates_csv),
        "no_evidence_review_csv": str(no_evidence_csv),
        "readonly": True,
        "replay_boundary": "No project creation, merge, alias write, project_id relink, or business fact mutation.",
    }
    write_json(result_json, payload)
    print("USER_PROJECT_MASTER_RECONCILIATION_PACKAGE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
