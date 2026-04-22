#!/usr/bin/env python3
"""Materialize core default taxes in sc_migration_fresh."""

from __future__ import annotations

import json
from pathlib import Path

from odoo.addons.smart_construction_core.hooks import ensure_core_taxes


OUTPUT_JSON = Path("/mnt/artifacts/migration/fresh_db_core_tax_prereq_materialize_result_v1.json")
REQUIRED = [
    ("销项VAT 9%", 9.0, "sale"),
    ("进项VAT 13%", 13.0, "purchase"),
]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if env.cr.dbname != "sc_migration_fresh":  # noqa: F821
    raise RuntimeError({"db_name_not_sc_migration_fresh": env.cr.dbname})  # noqa: F821

Tax = env["account.tax"].sudo().with_context(active_test=False)  # noqa: F821
before = Tax.search_count([])
ensure_core_taxes(env)  # noqa: F821
after = Tax.search_count([])
rows = []
missing = []
for name, amount, tax_use in REQUIRED:
    tax = Tax.search(
        [
            ("name", "=", name),
            ("amount", "=", amount),
            ("type_tax_use", "=", tax_use),
            ("amount_type", "=", "percent"),
            ("price_include", "=", False),
        ],
        limit=1,
    )
    if not tax:
        missing.append({"name": name, "amount": amount, "type_tax_use": tax_use})
        continue
    rows.append(
        {
            "id": tax.id,
            "name": tax.name,
            "amount": tax.amount,
            "type_tax_use": tax.type_tax_use,
            "active": bool(tax.active),
        }
    )
status = "PASS" if not missing else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_core_tax_prereq_materialize",
    "database": env.cr.dbname,  # noqa: F821
    "tax_count_before": before,
    "tax_count_after": after,
    "required_taxes": rows,
    "missing_required_taxes": missing,
    "demo_targets_executed": 0,
    "transaction_rows_created": 0,
    "decision": "core_tax_prereq_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "retry fresh_db_contract_57_retry_write",
}
write_json(OUTPUT_JSON, result)
env.cr.commit()  # noqa: F821
print(
    "FRESH_DB_CORE_TAX_PREREQ_MATERIALIZE="
    + json.dumps(
        {
            "status": status,
            "tax_count_before": before,
            "tax_count_after": after,
            "required_taxes": len(rows),
            "demo_targets_executed": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
