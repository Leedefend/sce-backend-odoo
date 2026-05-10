# -*- coding: utf-8 -*-
"""Project legacy loan repayment account transactions into user repayment claims.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_repayment_registration_projection_write.py
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


def clean(value):
    text = str(value or "").strip()
    return text or None


def project_for(line):
    if line.project_id:
        return line.project_id
    project_name = clean(line.project_name) or "历史还款未归集项目"
    Project = env["project.project"].sudo()  # noqa: F821
    project = Project.search([("name", "=", project_name)], limit=1)
    if project:
        return project
    return Project.create({"name": project_name})


def state_from_legacy(value):
    return "legacy_confirmed" if clean(value) in {"2", "已通过", "已确认", "已完成"} else "legacy_confirmed"


Claim = env["sc.expense.claim"].sudo()  # noqa: F821
Line = env["sc.legacy.account.transaction.line"].sudo().with_context(active_test=False)  # noqa: F821
output_json = resolve_artifact_root() / "fresh_db_repayment_registration_projection_write_result_v1.json"

domain = [
    ("source_table", "=", "ZJGL_ZCDFSZ_FXJK_HK"),
    ("direction", "=", "income"),
    ("amount", ">", 0),
]
target_domain = [("claim_type", "=", "expense"), ("expense_type", "=", "还款登记")]
before = Claim.search_count(target_domain)
created = 0
samples = []

for line in Line.search(domain, order="transaction_date desc, id desc"):
    source_key = clean(line.source_key) or "%s:%s" % (line.source_table, line.legacy_record_id)
    exists = Claim.search(
        [("legacy_source_model", "=", "sc.legacy.account.transaction.line"), ("legacy_record_id", "=", source_key)],
        limit=1,
    )
    if exists:
        continue
    project = project_for(line)
    claim = Claim.create(
        {
            "name": clean(line.document_no) or "HK-%s" % line.id,
            "source_origin": "legacy",
            "claim_type": "expense",
            "state": state_from_legacy(line.document_state),
            "project_id": project.id,
            "applicant_name": clean(line.counterparty_account_name),
            "payee": clean(line.counterparty_account_name),
            "receipt_account_name": clean(line.account_name),
            "date_claim": line.transaction_date or False,
            "fill_date": line.transaction_date or False,
            "expense_type": "还款登记",
            "summary": clean(line.source_summary) or "还款登记",
            "amount": float(line.amount or 0.0),
            "approved_amount": float(line.amount or 0.0),
            "legacy_source_model": "sc.legacy.account.transaction.line",
            "legacy_source_table": line.source_table,
            "legacy_record_id": source_key,
            "legacy_document_no": clean(line.document_no),
            "legacy_document_state": clean(line.document_state),
            "note": clean(line.note),
        }
    )
    created += 1
    if len(samples) < 5:
        samples.append(
            {
                "name": claim.name,
                "project": claim.project_id.display_name,
                "amount": claim.amount,
                "date": str(claim.date_claim or ""),
            }
        )

env.cr.commit()  # noqa: F821

after = Claim.search_count(target_domain)
result = {
    "mode": "fresh_db_repayment_registration_projection_write",
    "target_model": "sc.expense.claim",
    "source_model": "sc.legacy.account.transaction.line",
    "source_domain": domain,
    "before": before,
    "created": created,
    "after": after,
    "samples": samples,
}
output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
