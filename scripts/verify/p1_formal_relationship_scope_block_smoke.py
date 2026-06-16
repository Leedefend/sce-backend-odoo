# -*- coding: utf-8 -*-
"""Smoke test formal relationship scope blockers.

Run inside ``odoo shell``.  The smoke creates deliberately invalid new formal
documents and expects project-scope blockers to fire, then rolls back every
probe.  It never rewrites locked historical facts.
"""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path

from odoo.exceptions import UserError, ValidationError


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("P1_RELATIONSHIP_SMOKE_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/p1_relationship/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def _sample_projects(exclude_id=False):
    domain = [("id", "!=", int(exclude_id))] if exclude_id else []
    return env["project.project"].sudo().search(domain, limit=1)  # noqa: F821


def _sample_partner(exclude_id=False):
    domain = [("id", "!=", int(exclude_id))] if exclude_id else []
    return env["res.partner"].sudo().search(domain, limit=1)  # noqa: F821


def _expect_block(label, func):
    try:
        func()
    except (UserError, ValidationError) as exc:
        env.cr.rollback()  # noqa: F821
        return OrderedDict(
            [
                ("label", label),
                ("status", "BLOCKED"),
                ("exception", type(exc).__name__),
                ("message", str(exc)[:240]),
            ]
        )
    except Exception as exc:
        env.cr.rollback()  # noqa: F821
        return OrderedDict(
            [
                ("label", label),
                ("status", "UNEXPECTED"),
                ("exception", type(exc).__name__),
                ("message", str(exc)[:240]),
            ]
        )
    env.cr.rollback()  # noqa: F821
    return OrderedDict([("label", label), ("status", "NOT_BLOCKED")])


PaymentRequest = env["payment.request"].sudo()  # noqa: F821
PaymentExecution = env["sc.payment.execution"].sudo()  # noqa: F821
ExpenseClaim = env["sc.expense.claim"].sudo()  # noqa: F821
ReceiptIncome = env["sc.receipt.income"].sudo()  # noqa: F821

pay_request = PaymentRequest.search(
    [("type", "=", "pay"), ("project_id", "!=", False), ("partner_id", "!=", False)],
    limit=1,
)
receive_request = PaymentRequest.search(
    [("type", "=", "receive"), ("project_id", "!=", False), ("partner_id", "!=", False)],
    limit=1,
)

errors = []
rows = []
if not pay_request:
    errors.append({"key": "missing_pay_request_sample"})
if not receive_request:
    errors.append({"key": "missing_receive_request_sample"})

if pay_request:
    mismatch_project = _sample_projects(exclude_id=pay_request.project_id.id)
    mismatch_partner = _sample_partner(exclude_id=pay_request.partner_id.id)
    if not mismatch_project:
        errors.append({"key": "missing_mismatch_project_for_pay_request", "request_id": pay_request.id})
    else:
        def payment_execution_mismatch():
            rec = PaymentExecution.create(
                {
                    "name": "REL-GUARD-PAY-EXEC",
                    "source_origin": "manual",
                    "source_kind": "actual_outflow",
                    "project_id": mismatch_project.id,
                    "partner_id": pay_request.partner_id.id,
                    "payment_request_id": pay_request.id,
                    "planned_amount": pay_request.amount or 1.0,
                    "paid_amount": pay_request.amount or 1.0,
                    "currency_id": pay_request.currency_id.id or env.company.currency_id.id,  # noqa: F821
                }
            )
            rec.action_confirm()

        rows.append(_expect_block("payment_execution_project_scope", payment_execution_mismatch))

        def expense_claim_mismatch():
            rec = ExpenseClaim.create(
                {
                    "name": "REL-GUARD-EXPENSE",
                    "source_origin": "manual",
                    "claim_type": "expense",
                    "project_id": mismatch_project.id,
                    "partner_id": pay_request.partner_id.id,
                    "payment_request_id": pay_request.id,
                    "amount": pay_request.amount or 1.0,
                    "approved_amount": pay_request.amount or 1.0,
                    "currency_id": pay_request.currency_id.id or env.company.currency_id.id,  # noqa: F821
                }
            )
            rec.action_submit()

        rows.append(_expect_block("expense_claim_project_scope", expense_claim_mismatch))
    if not mismatch_partner:
        errors.append({"key": "missing_mismatch_partner_for_pay_request", "request_id": pay_request.id})
    else:
        def payment_execution_partner_mismatch():
            rec = PaymentExecution.create(
                {
                    "name": "REL-GUARD-PAY-EXEC-PARTNER",
                    "source_origin": "manual",
                    "source_kind": "actual_outflow",
                    "project_id": pay_request.project_id.id,
                    "partner_id": mismatch_partner.id,
                    "payment_request_id": pay_request.id,
                    "planned_amount": pay_request.amount or 1.0,
                    "paid_amount": pay_request.amount or 1.0,
                    "currency_id": pay_request.currency_id.id or env.company.currency_id.id,  # noqa: F821
                }
            )
            rec.action_confirm()

        rows.append(_expect_block("payment_execution_partner_scope", payment_execution_partner_mismatch))

        def expense_claim_partner_mismatch():
            rec = ExpenseClaim.create(
                {
                    "name": "REL-GUARD-EXPENSE-PARTNER",
                    "source_origin": "manual",
                    "claim_type": "expense",
                    "project_id": pay_request.project_id.id,
                    "partner_id": mismatch_partner.id,
                    "payment_request_id": pay_request.id,
                    "amount": pay_request.amount or 1.0,
                    "approved_amount": pay_request.amount or 1.0,
                    "currency_id": pay_request.currency_id.id or env.company.currency_id.id,  # noqa: F821
                }
            )
            rec.action_submit()

        rows.append(_expect_block("expense_claim_partner_scope", expense_claim_partner_mismatch))

if receive_request:
    mismatch_project = _sample_projects(exclude_id=receive_request.project_id.id)
    mismatch_partner = _sample_partner(exclude_id=receive_request.partner_id.id)
    if not mismatch_project:
        errors.append({"key": "missing_mismatch_project_for_receive_request", "request_id": receive_request.id})
    else:
        def receipt_income_mismatch():
            rec = ReceiptIncome.create(
                {
                    "name": "REL-GUARD-RECEIPT",
                    "source_origin": "manual",
                    "source_kind": "receipt_income",
                    "project_id": mismatch_project.id,
                    "partner_id": receive_request.partner_id.id,
                    "payment_request_id": receive_request.id,
                    "amount": receive_request.amount or 1.0,
                    "currency_id": receive_request.currency_id.id or env.company.currency_id.id,  # noqa: F821
                }
            )
            rec.action_confirm()

        rows.append(_expect_block("receipt_income_project_scope", receipt_income_mismatch))
    if not mismatch_partner:
        errors.append({"key": "missing_mismatch_partner_for_receive_request", "request_id": receive_request.id})
    else:
        def receipt_income_partner_mismatch():
            rec = ReceiptIncome.create(
                {
                    "name": "REL-GUARD-RECEIPT-PARTNER",
                    "source_origin": "manual",
                    "source_kind": "receipt_income",
                    "project_id": receive_request.project_id.id,
                    "partner_id": mismatch_partner.id,
                    "payment_request_id": receive_request.id,
                    "amount": receive_request.amount or 1.0,
                    "currency_id": receive_request.currency_id.id or env.company.currency_id.id,  # noqa: F821
                }
            )
            rec.action_confirm()

        rows.append(_expect_block("receipt_income_partner_scope", receipt_income_partner_mismatch))

for row in rows:
    if row["status"] != "BLOCKED":
        errors.append(dict(row))

payload = OrderedDict(
    [
        ("status", "PASS" if not errors else "FAIL"),
        ("database", env.cr.dbname),  # noqa: F821
        ("scope", "P1 formal relationship scope blockers"),
        ("rows", rows),
        ("errors", errors),
    ]
)
artifact = artifact_root() / f"p1_formal_relationship_scope_block_smoke_{env.cr.dbname}.json"  # noqa: F821
artifact.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(json.dumps({"status": payload["status"], "error_count": len(errors), "artifact": str(artifact)}, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit(1)
