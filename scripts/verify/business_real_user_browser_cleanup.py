# -*- coding: utf-8 -*-
"""Cleanup temporary real-user browser closure records."""

import json
from pathlib import Path


ARTIFACT_DIR = Path("/mnt/artifacts/browser-real-user-business-closure/current")
SETUP_JSON = ARTIFACT_DIR / "setup.json"
PREFIX = "BROWSER-CLOSURE"


def _env():
    return globals()["env"]


def _unlink_if_exists(model_name, ids):
    if not ids:
        return
    records = _env()[model_name].sudo().browse(ids).exists()
    if records:
        if model_name == "product.product":
            records.write({"active": False})
            return
        if model_name == "purchase.order":
            active_orders = records.filtered(lambda rec: rec.state != "cancel")
            if active_orders:
                active_orders.button_cancel()
        records.unlink()


def main():
    env = _env()
    case_rows = []
    if SETUP_JSON.exists():
        case_rows = json.loads(SETUP_JSON.read_text(encoding="utf-8")).get("cases") or []

    for row in case_rows:
        model_name = row.get("model")
        record_id = int(row.get("record_id") or 0)
        if model_name and record_id:
            env["tier.review"].sudo().search([("model", "=", model_name), ("res_id", "=", record_id)]).unlink()
            _unlink_if_exists(model_name, [record_id])
        cleanup_rows = row.get("cleanup") if isinstance(row.get("cleanup"), list) else []
        for item in cleanup_rows:
            if not isinstance(item, dict):
                continue
            cleanup_model = str(item.get("model") or "").strip()
            cleanup_id = int(item.get("id") or 0)
            if cleanup_model and cleanup_id:
                _unlink_if_exists(cleanup_model, [cleanup_id])

    project_ids = [int(row.get("project_id") or 0) for row in case_rows if int(row.get("project_id") or 0)]
    _unlink_if_exists("project.project", project_ids)

    env["sc.approval.policy"].sudo().search(
        [
            (
                "target_model",
                "in",
                [
                    "sc.receipt.income",
                    "payment.request",
                    "sc.expense.claim",
                    "project.material.plan",
                    "sc.settlement.order",
                    "purchase.order",
                    "sc.payment.execution",
                    "sc.invoice.registration",
                    "sc.financing.loan",
                    "sc.treasury.reconciliation",
                    "sc.settlement.adjustment",
                ],
            )
        ]
    ).write({"approval_required": False, "mode": "none"})

    env.cr.commit()
    print("BUSINESS_REAL_USER_BROWSER_CLEANUP=PASS")
    print("%s rows cleaned" % len(case_rows))


main()
