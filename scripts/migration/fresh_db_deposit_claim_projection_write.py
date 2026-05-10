# -*- coding: utf-8 -*-
"""Project legacy deposit-related facts into user-operable expense claims.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_deposit_claim_projection_write.py
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


def amount(value):
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


def project_for(record):
    if getattr(record, "project_id", False):
        return record.project_id
    project_name = clean(getattr(record, "project_name", None)) or clean(
        getattr(record, "legacy_project_name", None)
    )
    if not project_name:
        project_name = "历史保证金未归集项目"
    Project = env["project.project"].sudo()  # noqa: F821
    project = Project.search([("name", "=", project_name)], limit=1)
    if project:
        return project
    return Project.create({"name": project_name})


def partner_for(record):
    if getattr(record, "partner_id", False):
        return record.partner_id.id
    partner_name = clean(getattr(record, "partner_name", None)) or clean(
        getattr(record, "legacy_partner_name", None)
    )
    if not partner_name:
        return False
    Partner = env["res.partner"].sudo()  # noqa: F821
    partner = Partner.search([("name", "=", partner_name)], limit=1)
    if partner:
        return partner.id
    return Partner.create({"name": partner_name}).id


def exists(source_model, record_id):
    return bool(
        Claim.search(
            [("legacy_source_model", "=", source_model), ("legacy_record_id", "=", str(record_id))],
            limit=1,
        )
    )


def state_from_legacy(value):
    text = clean(value)
    if text in {"2", "已通过", "已完成", "已确认", "审核通过"}:
        return "legacy_confirmed"
    return "legacy_confirmed"


def create_claim(record, *, source_model, claim_type, expense_type, summary, claim_amount, date_value):
    if claim_amount <= 0 or exists(source_model, record.id):
        return None
    project = project_for(record)
    document_no = clean(getattr(record, "document_no", None))
    legacy_state = clean(getattr(record, "document_state", None)) or clean(getattr(record, "legacy_state", None))
    vals = {
        "name": document_no or "%s-%s" % (expense_type, record.id),
        "source_origin": "legacy",
        "claim_type": claim_type,
        "state": state_from_legacy(legacy_state),
        "project_id": project.id,
        "partner_id": partner_for(record),
        "applicant_name": clean(getattr(record, "handler_name", None))
        or clean(getattr(record, "creator_name", None))
        or clean(getattr(record, "partner_name", None))
        or clean(getattr(record, "legacy_partner_name", None)),
        "guarantee_project_name": clean(getattr(record, "project_name", None))
        or clean(getattr(record, "legacy_project_name", None))
        or project.name,
        "guarantee_type": "bid",
        "payment_method": clean(getattr(record, "payment_method", None)),
        "clearing_method": clean(getattr(record, "receipt_type", None)),
        "receipt_account_name": clean(getattr(record, "account_name", None)),
        "payment_account_name": clean(getattr(record, "bank_account", None)),
        "date_claim": date_value or False,
        "fill_date": date_value or False,
        "expense_type": expense_type,
        "summary": summary,
        "amount": claim_amount,
        "approved_amount": claim_amount,
        "legacy_source_model": source_model,
        "legacy_source_table": clean(getattr(record, "source_table", None))
        or clean(getattr(record, "legacy_source_table", None)),
        "legacy_record_id": str(record.id),
        "legacy_document_no": document_no,
        "legacy_document_state": legacy_state,
        "note": clean(getattr(record, "note", None)),
    }
    return Claim.create(vals)


Claim = env["sc.expense.claim"].sudo()  # noqa: F821
SelfFunding = env["sc.legacy.self.funding.fact"].sudo().with_context(active_test=False)  # noqa: F821
PaymentResidual = env["sc.legacy.payment.residual.fact"].sudo().with_context(active_test=False)  # noqa: F821

output_json = resolve_artifact_root() / "fresh_db_deposit_claim_projection_write_result_v1.json"
before = {
    "self_funding_deposit": Claim.search_count(
        [("claim_type", "=", "deposit_receive"), ("expense_type", "=", "自筹保证金")]
    ),
    "self_funding_refund": Claim.search_count(
        [("claim_type", "=", "deposit_refund"), ("expense_type", "=", "自筹保证金退回")]
    ),
    "payment_deposit_return": Claim.search_count(
        [("claim_type", "=", "deposit_pay"), ("expense_type", "=", "付款还保证金")]
    ),
}

created = {"self_funding_deposit": 0, "self_funding_refund": 0, "payment_deposit_return": 0}
samples = {"self_funding_deposit": [], "self_funding_refund": [], "payment_deposit_return": []}

for rec in SelfFunding.search([("active", "in", [True, False])], order="document_date desc, id desc"):
    if rec.line_type == "income":
        claim = create_claim(
            rec,
            source_model="sc.legacy.self.funding.fact",
            claim_type="deposit_receive",
            expense_type="自筹保证金",
            summary="自筹保证金",
            claim_amount=amount(rec.self_funding_amount),
            date_value=rec.document_date,
        )
        bucket = "self_funding_deposit"
    elif rec.line_type == "refund":
        claim = create_claim(
            rec,
            source_model="sc.legacy.self.funding.fact",
            claim_type="deposit_refund",
            expense_type="自筹保证金退回",
            summary="自筹保证金退回",
            claim_amount=amount(rec.refund_amount),
            date_value=rec.document_date,
        )
        bucket = "self_funding_refund"
    else:
        continue
    if claim:
        created[bucket] += 1
        if len(samples[bucket]) < 5:
            samples[bucket].append(
                {
                    "name": claim.name,
                    "project": claim.project_id.display_name,
                    "partner": claim.partner_id.display_name,
                    "amount": claim.amount,
                    "date": str(claim.date_claim or ""),
                }
            )

for rec in PaymentResidual.search(
    [("active", "in", [True, False]), ("payment_family", "in", ["deposit_payment_registration", "deposit_borrow_request"])],
    order="document_date desc, id desc",
):
    claim_amount = amount(rec.paid_amount) or amount(rec.planned_amount)
    claim = create_claim(
        rec,
        source_model="sc.legacy.payment.residual.fact",
        claim_type="deposit_pay",
        expense_type="付款还保证金",
        summary="付款还保证金",
        claim_amount=claim_amount,
        date_value=rec.document_date,
    )
    if claim:
        created["payment_deposit_return"] += 1
        if len(samples["payment_deposit_return"]) < 5:
            samples["payment_deposit_return"].append(
                {
                    "name": claim.name,
                    "project": claim.project_id.display_name,
                    "partner": claim.partner_id.display_name,
                    "amount": claim.amount,
                    "date": str(claim.date_claim or ""),
                }
            )

env.cr.commit()  # noqa: F821

after = {
    "self_funding_deposit": Claim.search_count(
        [("claim_type", "=", "deposit_receive"), ("expense_type", "=", "自筹保证金")]
    ),
    "self_funding_refund": Claim.search_count(
        [("claim_type", "=", "deposit_refund"), ("expense_type", "=", "自筹保证金退回")]
    ),
    "payment_deposit_return": Claim.search_count(
        [("claim_type", "=", "deposit_pay"), ("expense_type", "=", "付款还保证金")]
    ),
}
result = {
    "mode": "fresh_db_deposit_claim_projection_write",
    "target_model": "sc.expense.claim",
    "before": before,
    "created": created,
    "after": after,
    "samples": samples,
}
output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
