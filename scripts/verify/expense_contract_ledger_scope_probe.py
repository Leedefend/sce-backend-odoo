#!/usr/bin/env python3
"""Verify unified expense contract ledger scope and source coverage."""

from __future__ import annotations

import json
import os
from pathlib import Path


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend(
        [
            Path("/mnt/artifacts/verify"),
            Path(f"/tmp/history_continuity/{env.cr.dbname}/verify"),  # noqa: F821
        ]
    )
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/verify")  # noqa: F821


def scalar(sql: str) -> object:
    env.cr.execute(sql)  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def rows(sql: str) -> list[dict[str, object]]:
    env.cr.execute(sql)  # noqa: F821
    return env.cr.dictfetchall()  # noqa: F821


errors: list[str] = []

project_expense = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM construction_contract_expense e
          JOIN construction_contract c ON c.id = e.contract_id
         WHERE c.type = 'in'
           AND c.active
           AND COALESCE(c.subject, '') NOT ILIKE '发票关联支出合同%'
        """
    )
    or 0
)
invoice_anchor_project_expense_wrappers = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM construction_contract_expense e
          JOIN construction_contract c ON c.id = e.contract_id
         WHERE c.type = 'in'
           AND c.active
           AND COALESCE(c.subject, '') ILIKE '发票关联支出合同%'
        """
    )
    or 0
)
base_invoice_anchor_contracts = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM construction_contract
         WHERE type = 'in'
           AND active
           AND COALESCE(subject, '') ILIKE '发票关联支出合同%'
        """
    )
    or 0
)
general_expense = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_general_contract
         WHERE active IS TRUE
           AND contract_direction = 'expense'
        """
    )
    or 0
)
general_scbs_supplier_excluded_from_general_action = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_general_contract
         WHERE active IS TRUE
           AND contract_type = 'SCBS供应商合同'
        """
    )
    or 0
)
general_action_domain = scalar(
    """
    SELECT domain
      FROM ir_act_window
     WHERE id = (
           SELECT res_id
             FROM ir_model_data
            WHERE module = 'smart_construction_core'
              AND name = 'action_sc_general_contract'
              AND model = 'ir.actions.act_window'
     )
    """
)
general_action_visible_count = env["sc.general.contract"].search_count([("contract_type", "!=", "SCBS供应商合同")])  # noqa: F821
ledger_total = int(scalar("SELECT COUNT(*) FROM sc_expense_contract_ledger") or 0)
expected_total = project_expense + general_expense

scbs_supplier = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_expense_contract_ledger
         WHERE contract_family = 'expense'
           AND source_model = 'sc.general.contract'
           AND contract_type = 'SCBS供应商合同'
        """
    )
    or 0
)
general_scbs_supplier = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_general_contract
         WHERE active IS TRUE
           AND contract_direction = 'expense'
           AND contract_type = 'SCBS供应商合同'
        """
    )
    or 0
)

if ledger_total != expected_total:
    errors.append(f"ledger_total={ledger_total} expected={expected_total}")
if scbs_supplier != general_scbs_supplier:
    errors.append(f"scbs_supplier={scbs_supplier} expected={general_scbs_supplier}")
expected_general_domain = "[('contract_type', '!=', 'SCBS供应商合同')]"
if general_action_domain != expected_general_domain:
    errors.append(f"general_action_domain={general_action_domain!r} expected={expected_general_domain!r}")
non_expense_family = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_expense_contract_ledger
         WHERE contract_family != 'expense'
            OR contract_family IS NULL
        """
    )
    or 0
)
if non_expense_family:
    errors.append(f"non_expense_family={non_expense_family} expected=0")
if invoice_anchor_project_expense_wrappers:
    errors.append(f"invoice_anchor_project_expense_wrappers={invoice_anchor_project_expense_wrappers} expected=0")

family_rows = rows(
    """
    SELECT contract_family, COUNT(*)::integer AS rows, ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount
      FROM sc_expense_contract_ledger
     GROUP BY contract_family
     ORDER BY contract_family
    """
)

payload = {
    "status": "FAIL" if errors else "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "project_expense_contracts": project_expense,
    "invoice_anchor_project_expense_wrappers": invoice_anchor_project_expense_wrappers,
    "base_invoice_anchor_contracts_retained": base_invoice_anchor_contracts,
    "general_expense_contracts": general_expense,
    "general_action_domain": general_action_domain,
    "general_action_visible_count": general_action_visible_count,
    "general_scbs_supplier_excluded_from_general_action": general_scbs_supplier_excluded_from_general_action,
    "expected_ledger_total": expected_total,
    "ledger_total": ledger_total,
    "scbs_supplier_contracts": scbs_supplier,
    "non_expense_family_rows": non_expense_family,
    "family_rows": family_rows,
    "errors": errors,
}

output = artifact_root() / "expense_contract_ledger_scope_probe_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("EXPENSE_CONTRACT_LEDGER_SCOPE_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))

if errors:
    raise SystemExit(1)
