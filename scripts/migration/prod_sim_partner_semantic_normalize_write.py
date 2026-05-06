#!/usr/bin/env python3
"""Normalize prod-sim partner semantics from contract and cash-flow facts.

Policy:
- counterparties with income contract or receipt facts are customers;
- counterparties with outflow contract, general contract, or actual outflow facts are suppliers;
- the same partner may be both customer and supplier when both facts exist;
- partners without business facts are discarded from business semantics;
- system partners referenced by users/companies are kept active but not ranked.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons").exists() and (candidate / "scripts").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def rows_from_sql(sql: str) -> list[dict[str, object]]:
    env.cr.execute(sql)  # noqa: F821
    columns = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def ids_from_sql(sql: str) -> set[int]:
    return {int(row["id"]) for row in rows_from_sql(sql)}


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rec_value(rec, field_name: str) -> object:
    if field_name in rec._fields:
        return rec[field_name]
    env.cr.execute("SELECT %s FROM res_partner WHERE id = %%s" % field_name, (rec.id,))  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else ""


ensure_allowed_db()

Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821

REPO_ROOT = repo_root()
run_id = datetime.utcnow().strftime("prod_sim_partner_semantic_normalize_%Y%m%dT%H%M%SZ")
artifact_root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration"))) / run_id
result_json = artifact_root / "partner_semantic_normalize_result_v2.json"
rollback_csv = artifact_root / "partner_semantic_normalize_rollback_targets_v2.csv"
discard_csv = artifact_root / "partner_semantic_normalize_discard_targets_v2.csv"

customer_ids = ids_from_sql(
    """
    SELECT DISTINCT partner_id AS id
    FROM construction_contract
    WHERE type = 'out'
      AND partner_id IS NOT NULL
    UNION
    SELECT DISTINCT partner_id AS id
    FROM sc_receipt_income
    WHERE partner_id IS NOT NULL
      AND state IN ('received', 'legacy_confirmed')
      AND COALESCE(amount, 0) > 0
    UNION
    SELECT DISTINCT partner_id AS id
    FROM sc_legacy_receipt_income_fact
    WHERE partner_id IS NOT NULL
      AND COALESCE(source_amount, 0) > 0
    """
)

supplier_ids = ids_from_sql(
    """
    SELECT DISTINCT partner_id AS id
    FROM construction_contract
    WHERE type = 'in'
      AND partner_id IS NOT NULL
    UNION
    SELECT DISTINCT partner_id AS id
    FROM sc_general_contract
    WHERE partner_id IS NOT NULL
    UNION
    SELECT DISTINCT partner_id AS id
    FROM sc_payment_execution
    WHERE partner_id IS NOT NULL
      AND source_kind = 'actual_outflow'
      AND state IN ('paid', 'legacy_confirmed')
      AND COALESCE(paid_amount, 0) > 0
    """
)

keep_ids = customer_ids | supplier_ids
all_partner_ids = set(Partner.search([]).ids)
discard_ids = all_partner_ids - keep_ids
system_keep_ids = ids_from_sql(
    """
    SELECT DISTINCT partner_id AS id FROM res_users WHERE partner_id IS NOT NULL
    UNION
    SELECT DISTINCT partner_id AS id FROM res_company WHERE partner_id IS NOT NULL
    """
)
system_discard_keep_ids = discard_ids & system_keep_ids
archive_discard_ids = discard_ids - system_discard_keep_ids

errors: list[dict[str, object]] = []
missing_ids = keep_ids - all_partner_ids
if missing_ids:
    errors.append({"error": "fact_partner_missing_in_res_partner", "samples": sorted(missing_ids)[:30]})
if not customer_ids:
    errors.append({"error": "empty_customer_set"})
if not supplier_ids:
    errors.append({"error": "empty_supplier_set"})
if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors})

target_ids = keep_ids | discard_ids
snapshot_rows = []
for rec in Partner.browse(sorted(target_ids)):
    if not rec.exists():
        continue
    is_customer = rec.id in customer_ids
    is_supplier = rec.id in supplier_ids
    if is_customer or is_supplier:
        if is_customer and is_supplier:
            target_role = "customer_and_supplier"
        elif is_customer:
            target_role = "customer"
        else:
            target_role = "supplier"
        target_customer_rank = 1 if is_customer else 0
        target_supplier_rank = 1 if is_supplier else 0
        target_active = True
        discard_action = ""
    elif rec.id in system_discard_keep_ids:
        target_role = "discard_system_keep"
        target_customer_rank = 0
        target_supplier_rank = 0
        target_active = True
        discard_action = "keep_active_system_reference"
    else:
        target_role = "discard_archive"
        target_customer_rank = 0
        target_supplier_rank = 0
        target_active = False
        discard_action = "archive_no_business_fact"
    snapshot_rows.append(
        {
            "run_id": run_id,
            "partner_id": rec.id,
            "name": rec.name or "",
            "legacy_partner_source": rec_value(rec, "legacy_partner_source") or "",
            "legacy_partner_id": rec_value(rec, "legacy_partner_id") or "",
            "old_customer_rank": rec.customer_rank,
            "old_supplier_rank": rec.supplier_rank,
            "old_active": rec.active,
            "target_role": target_role,
            "target_customer_rank": target_customer_rank,
            "target_supplier_rank": target_supplier_rank,
            "target_active": target_active,
            "discard_action": discard_action,
        }
    )

write_csv(
    rollback_csv,
    [
        "run_id",
        "partner_id",
        "name",
        "legacy_partner_source",
        "legacy_partner_id",
        "old_customer_rank",
        "old_supplier_rank",
        "old_active",
        "target_role",
        "target_customer_rank",
        "target_supplier_rank",
        "target_active",
        "discard_action",
    ],
    snapshot_rows,
)
write_csv(
    discard_csv,
    [
        "run_id",
        "partner_id",
        "name",
        "legacy_partner_source",
        "legacy_partner_id",
        "old_customer_rank",
        "old_supplier_rank",
        "old_active",
        "target_role",
        "target_customer_rank",
        "target_supplier_rank",
        "target_active",
        "discard_action",
    ],
    [row for row in snapshot_rows if str(row["target_role"]).startswith("discard")],
)

try:
    non_customer_ids = all_partner_ids - customer_ids
    non_supplier_ids = all_partner_ids - supplier_ids
    if customer_ids:
        Partner.browse(sorted(customer_ids)).write({"customer_rank": 1, "active": True})
    if non_customer_ids:
        Partner.browse(sorted(non_customer_ids)).write({"customer_rank": 0})
    if supplier_ids:
        Partner.browse(sorted(supplier_ids)).write({"supplier_rank": 1, "active": True})
    if non_supplier_ids:
        Partner.browse(sorted(non_supplier_ids)).write({"supplier_rank": 0})
    if system_discard_keep_ids:
        Partner.browse(sorted(system_discard_keep_ids)).write(
            {"customer_rank": 0, "supplier_rank": 0, "active": True}
        )
    if archive_discard_ids:
        Partner.browse(sorted(archive_discard_ids)).write({"customer_rank": 0, "supplier_rank": 0, "active": False})
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

post = {
    "total_partners": Partner.search_count([]),
    "active_partners": Partner.search_count([("active", "=", True)]),
    "customer_rank_partners": Partner.search_count([("customer_rank", ">", 0)]),
    "supplier_rank_partners": Partner.search_count([("supplier_rank", ">", 0)]),
    "both_rank_partners": Partner.search_count([("customer_rank", ">", 0), ("supplier_rank", ">", 0)]),
    "neither_active_partners": Partner.search_count(
        [("active", "=", True), ("customer_rank", "=", 0), ("supplier_rank", "=", 0)]
    ),
}
result = {
    "status": "PASS"
    if post["customer_rank_partners"] == len(customer_ids)
    and post["supplier_rank_partners"] == len(supplier_ids)
    and post["both_rank_partners"] == len(customer_ids & supplier_ids)
    else "FAIL",
    "mode": "prod_sim_partner_semantic_normalize_write",
    "database": env.cr.dbname,  # noqa: F821
    "run_id": run_id,
    "policy": "contract_or_cash_fact_income_or_receipt_is_customer_outflow_or_general_contract_or_payment_is_supplier_allow_dual_role_discard_no_fact",
    "customer_ids": len(customer_ids),
    "supplier_ids": len(supplier_ids),
    "both_customer_supplier_ids": len(customer_ids & supplier_ids),
    "keep_ids": len(keep_ids),
    "discard_ids": len(discard_ids),
    "system_discard_keep_ids": len(system_discard_keep_ids),
    "archive_discard_ids": len(archive_discard_ids),
    "rollback_csv": str(rollback_csv),
    "discard_csv": str(discard_csv),
    "post": post,
}
write_json(result_json, result)
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
