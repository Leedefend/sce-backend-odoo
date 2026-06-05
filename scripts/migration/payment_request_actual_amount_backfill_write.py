#!/usr/bin/env python3
"""Backfill accepted payment request actual-paid amounts from payment evidence."""

from __future__ import annotations

import gzip
import json
import os
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path


def clean(value):
    if value is None or value is False:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def amount(value) -> Decimal:
    text = clean(value).replace(",", "")
    if not text:
        return Decimal("0")
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def amount_text(value: Decimal) -> str:
    value = value.quantize(Decimal("0.01"))
    if value == value.to_integral():
        return str(value.to_integral())
    return format(value.normalize(), "f")


def ensure_allowed_db():
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def joint_payment_source_path() -> Path:
    candidates = [
        os.getenv("PAYMENT_REQUEST_JOINT_PAYMENT_ROWS_JSON"),
        "/mnt/artifacts/migration/scbs_55_old_live_full_rows_current/seq031.json.gz",
        "artifacts/migration/scbs_55_old_live_full_rows_current/seq031.json.gz",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    raise RuntimeError({"payment_request_joint_payment_rows_missing": [item for item in candidates if item]})


def payload_dict(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}
    return {}


def add_evidence(summary: dict[str, Decimal], row: dict, request_no_key="ZFSQDH", request_id_key="f_ZFSQGLId"):
    payment_amount = amount(row.get("f_FKJE") or row.get("FKJE"))
    request_no = clean(row.get(request_no_key))
    request_id = clean(row.get(request_id_key))
    if request_no:
        summary.setdefault("by_no", {})
        summary["by_no"][request_no] = summary["by_no"].get(request_no, Decimal("0")) + payment_amount
    if request_id:
        summary.setdefault("by_id", {})
        summary["by_id"][request_id] = summary["by_id"].get(request_id, Decimal("0")) + payment_amount
    return bool(request_no or request_id)


ensure_allowed_db()

Payment = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
DirectFact = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821

stats = {
    "direct_source_rows": 0,
    "direct_source_unlinked_rows": 0,
    "direct_checked": 0,
    "direct_matched": 0,
    "direct_updated": 0,
    "direct_unmatched": 0,
    "joint_source_rows": 0,
    "joint_checked": 0,
    "joint_matched": 0,
    "joint_updated": 0,
    "joint_unmatched": 0,
}

direct_summary: dict[str, dict[str, Decimal]] = {"by_no": {}, "by_id": {}}
direct_facts = DirectFact.search(
    [("source_system", "=", "online_old_scbsly"), ("acceptance_label", "=", "往来单位付款"), ("active", "=", True)]
)
stats["direct_source_rows"] = len(direct_facts)
for fact in direct_facts:
    if not add_evidence(direct_summary, payload_dict(fact.raw_payload)):
        stats["direct_source_unlinked_rows"] += 1

for record in Payment.search(
    [("legacy_source_table", "=", "SCBSLY_DIRECT_PAYMENT_APPLY_ACCEPTED"), ("operation_strategy", "=", "direct")]
):
    stats["direct_checked"] += 1
    key = clean(record.name) or clean(record.legacy_record_id)
    if key not in direct_summary["by_no"]:
        stats["direct_unmatched"] += 1
        continue
    value = amount_text(direct_summary["by_no"][key])
    stats["direct_matched"] += 1
    if clean(record.legacy_visible_actual_paid_amount) != value:
        record.write({"legacy_visible_actual_paid_amount": value})
        stats["direct_updated"] += 1

joint_summary: dict[str, dict[str, Decimal]] = {"by_no": {}, "by_id": {}}
path = joint_payment_source_path()
with gzip.open(path, "rt", encoding="utf-8") as handle:
    joint_rows = json.load(handle).get("rows") or []
stats["joint_source_rows"] = len(joint_rows)
for row in joint_rows:
    add_evidence(joint_summary, row)

for record in Payment.search([("legacy_source_table", "=", "C_ZFSQGL"), ("operation_strategy", "=", "joint")]):
    stats["joint_checked"] += 1
    key_id = clean(record.legacy_record_id)
    key_no = clean(record.name)
    if key_id in joint_summary["by_id"]:
        value = amount_text(joint_summary["by_id"][key_id])
    elif key_no in joint_summary["by_no"]:
        value = amount_text(joint_summary["by_no"][key_no])
    else:
        stats["joint_unmatched"] += 1
        continue
    stats["joint_matched"] += 1
    if clean(record.legacy_visible_actual_paid_amount) != value:
        record.write({"legacy_visible_actual_paid_amount": value})
        stats["joint_updated"] += 1

env.cr.commit()  # noqa: F821
print(
    "PAYMENT_REQUEST_ACTUAL_AMOUNT_BACKFILL="
    + json.dumps(
        {
            "database": env.cr.dbname,  # noqa: F821
            "mode": "payment_request_actual_amount_backfill_write",
            "status": "PASS",
            **stats,
            "decision": "actual_paid_amount_is_summed_from_linked_payment_execution_rows_not_default_zero",
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
