#!/usr/bin/env python3
"""Verify unified income contract ledger scope and source boundaries."""

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
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


project_income = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM construction_contract_income i
          JOIN construction_contract c ON c.id = i.contract_id
         WHERE c.type = 'out'
           AND c.active
           AND (COALESCE(c.legacy_contract_id, '') = '' OR c.legacy_income_surface_visible)
        """
    )
    or 0
)
general_income = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_general_contract
         WHERE active
           AND contract_direction = 'income'
        """
    )
    or 0
)
ledger_total = int(scalar("SELECT COUNT(*) FROM sc_income_contract_ledger") or 0)
receipt_included = int(
    scalar("SELECT COUNT(*) FROM sc_income_contract_ledger WHERE source_model = 'sc.receipt.income'") or 0
)
family_rows = rows(
    """
    SELECT contract_family, COUNT(*)::integer AS rows, ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount
      FROM sc_income_contract_ledger
     GROUP BY contract_family
     ORDER BY contract_family
    """
)
general_direction_rows = rows(
    """
    SELECT contract_direction, COUNT(*)::integer AS rows, ROUND(COALESCE(SUM(amount_total), 0)::numeric, 2) AS amount
      FROM sc_general_contract
     GROUP BY contract_direction
     ORDER BY contract_direction
    """
)
bad_general_income = rows(
    """
    SELECT id, contract_no, contract_name, contract_type, contract_attribute, amount_total
      FROM sc_general_contract
     WHERE active
       AND contract_direction = 'income'
       AND COALESCE(contract_direction_source, '') NOT IN ('contract_evidence', 'manual')
     ORDER BY id
     LIMIT 20
    """
)

expected_total = project_income + general_income
status = "PASS"
errors: list[str] = []
if ledger_total != expected_total:
    status = "FAIL"
    errors.append(f"ledger_total={ledger_total} expected={expected_total}")
if receipt_included:
    status = "FAIL"
    errors.append(f"receipt_income_rows_included={receipt_included}")
if bad_general_income:
    status = "FAIL"
    errors.append("general_income_without_direction_source")

payload = {
    "status": status,
    "database": env.cr.dbname,  # noqa: F821
    "project_income_contracts": project_income,
    "general_income_contracts": general_income,
    "expected_ledger_total": expected_total,
    "ledger_total": ledger_total,
    "receipt_income_rows_included": receipt_included,
    "family_rows": family_rows,
    "general_direction_rows": general_direction_rows,
    "bad_general_income_sample": bad_general_income,
    "errors": errors,
}

output = artifact_root() / "income_contract_ledger_scope_probe_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("INCOME_CONTRACT_LEDGER_SCOPE_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if status != "PASS":
    raise SystemExit(1)
