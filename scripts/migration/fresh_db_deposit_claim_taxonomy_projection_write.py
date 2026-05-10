# -*- coding: utf-8 -*-
"""Normalize legacy deposit claim source-family codes into user-facing entry types.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_deposit_claim_taxonomy_projection_write.py
"""

import json
import os
from pathlib import Path


def resolve_artifact_root():
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path("/tmp/history_continuity/%s/adhoc" % env.cr.dbname))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path("/tmp/history_continuity/%s/adhoc" % env.cr.dbname)  # noqa: F821


Claim = env["sc.expense.claim"].sudo()  # noqa: F821
output_json = resolve_artifact_root() / "fresh_db_deposit_claim_taxonomy_projection_write_result_v1.json"

targets = [
    {
        "bucket": "payment_deposit_return",
        "before_domain": [("claim_type", "=", "deposit_pay"), ("expense_type", "=", "付款还保证金")],
        "source_domain": [
            ("legacy_source_model", "=", "sc.legacy.expense.deposit.fact"),
            ("claim_type", "=", "deposit_pay"),
            ("expense_type", "=", "pay_guarantee_deposit"),
        ],
        "expense_type": "付款还保证金",
        "summary": "付款还保证金",
    },
    {
        "bucket": "payment_deposit_refund",
        "before_domain": [("claim_type", "=", "deposit_refund"), ("expense_type", "=", "付款保证金退回")],
        "source_domain": [
            ("legacy_source_model", "=", "sc.legacy.expense.deposit.fact"),
            ("claim_type", "=", "deposit_refund"),
            ("expense_type", "=", "pay_guarantee_deposit_refund"),
        ],
        "expense_type": "付款保证金退回",
        "summary": "付款保证金退回",
    },
]

before = {target["bucket"]: Claim.search_count(target["before_domain"]) for target in targets}
updated = {}
samples = {}
for target in targets:
    records = Claim.search(target["source_domain"])
    updated[target["bucket"]] = len(records)
    if records:
        env.cr.execute(  # noqa: F821
            """
            UPDATE sc_expense_claim
               SET expense_type = %s,
                   summary = %s,
                   write_uid = %s,
                   write_date = NOW()
             WHERE id = ANY(%s)
            """,
            [target["expense_type"], target["summary"], env.uid, records.ids],  # noqa: F821
        )
    sample_records = Claim.search(target["before_domain"], order="date_claim desc, id desc", limit=5)
    samples[target["bucket"]] = [
        {
            "name": rec.name,
            "project": rec.project_id.display_name,
            "partner": rec.partner_id.display_name,
            "amount": rec.amount,
            "date": str(rec.date_claim or ""),
        }
        for rec in sample_records
    ]

env.cr.commit()  # noqa: F821

after = {target["bucket"]: Claim.search_count(target["before_domain"]) for target in targets}
result = {
    "mode": "fresh_db_deposit_claim_taxonomy_projection_write",
    "target_model": "sc.expense.claim",
    "before": before,
    "updated": updated,
    "after": after,
    "samples": samples,
}
output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
