# -*- coding: utf-8 -*-
"""Project legacy tender document purchase requests into tender.doc.purchase."""

import csv
import json
import os
from datetime import datetime
from pathlib import Path


INPUT_CSV_NAME = "fresh_db_legacy_tender_doc_purchase_payload_v1.csv"
OUTPUT_JSON_NAME = "fresh_db_legacy_tender_doc_purchase_projection_write_result_v1.json"
SOURCE_TABLE = "BGGL_ZTBJHT_TBBM_TBBMFSQ"


def resolve_artifact_root():
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path("/tmp/history_continuity/%s/adhoc" % env.cr.dbname))  # noqa: F821
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    return candidates[0] if candidates and candidates[0] else Path("/mnt/artifacts/migration")


def parse_date(value):
    value = str(value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value[:19], fmt).date()
        except ValueError:
            continue
    return None


def parse_datetime(value):
    value = str(value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:19], fmt)
        except ValueError:
            continue
    return None


def parse_float(value):
    try:
        if value in (None, ""):
            return 0.0
        return float(str(value).strip())
    except Exception:
        return 0.0


def clean(value):
    text = str(value or "").strip()
    return text or None


def first(*values):
    for value in values:
        text = clean(value)
        if text:
            return text
    return None


def user_id_by_name(name):
    text = clean(name)
    if not text:
        return env.ref("base.user_admin").id  # noqa: F821
    User = env["res.users"].sudo()  # noqa: F821
    user = User.search([("name", "=", text)], limit=1) or User.search([("name", "ilike", text)], limit=1)
    return user.id or env.ref("base.user_admin").id  # noqa: F821


def project_by_name(name):
    project_name = clean(name) or "历史投标项目"
    Project = env["project.project"].sudo()  # noqa: F821
    project = Project.search([("name", "=", project_name)], limit=1)
    if project:
        return project
    return Project.create({"name": project_name})


def bid_by_row(row):
    tender_name = first(row.get("tender_project_name"), row.get("project_name"), row.get("note")) or "历史投标报名"
    project = project_by_name(first(row.get("project_name"), row.get("tender_project_name"), tender_name))
    document_no = first(row.get("document_no"), row.get("legacy_record_id"))
    Bid = env["tender.bid"].sudo()  # noqa: F821
    bid = Bid.search([("name", "=", document_no), ("project_id", "=", project.id)], limit=1)
    if bid:
        return bid, False
    bid = Bid.search([("tender_name", "=", tender_name), ("project_id", "=", project.id)], limit=1)
    if bid:
        return bid, False
    return Bid.create(
        {
            "name": document_no or "TBBM-%s" % clean(row.get("legacy_record_id")),
            "tender_name": tender_name,
            "project_id": project.id,
            "state": "submitted" if str(row.get("document_state") or "") == "2" else "prepare",
        }
    ), True


artifact_root = resolve_artifact_root()
input_csv = Path(os.getenv("MIGRATION_TENDER_DOC_PURCHASE_CSV") or artifact_root / INPUT_CSV_NAME)
output_json = artifact_root / OUTPUT_JSON_NAME
if not input_csv.exists():
    raise FileNotFoundError("missing tender doc purchase payload: %s" % input_csv)

rows = list(csv.DictReader(input_csv.open(encoding="utf-8-sig", newline="")))
Purchase = env["tender.doc.purchase"].sudo()  # noqa: F821
Plan = env["sc.legacy.user.priority.menu.plan"].sudo()  # noqa: F821

created = 0
updated = 0
created_bids = 0
active_rows = 0
samples = []

for row in rows:
    if str(row.get("active") or "").strip() == "0":
        continue
    active_rows += 1
    bid, bid_created = bid_by_row(row)
    created_bids += int(bid_created)
    document_no = first(row.get("document_no"), row.get("legacy_record_id"))
    legacy_record_id = clean(row.get("legacy_record_id"))
    existing = Purchase.search([
        ("legacy_source_table", "=", SOURCE_TABLE),
        ("legacy_record_id", "=", legacy_record_id),
    ], limit=1)
    vals = {
        "bid_id": bid.id,
        "applicant_id": user_id_by_name(first(row.get("applicant_name"), row.get("creator_name"))),
        "apply_date": parse_date(first(row.get("apply_date"), row.get("created_time"))),
        "amount": parse_float(row.get("amount")),
        "invoice_no": document_no,
        "payment_method": clean(row.get("payment_method")),
        "receipt_partner_name": clean(row.get("receipt_partner_name")),
        "receipt_payee_name": clean(row.get("receipt_payee_name")),
        "receipt_bank_name": clean(row.get("receipt_bank_name")),
        "receipt_bank_account": clean(row.get("receipt_bank_account")),
        "remark": clean(row.get("note")),
        "legacy_source_created_by": first(row.get("creator_name"), row.get("applicant_name")),
        "legacy_source_created_at": parse_datetime(row.get("created_time")),
        "legacy_record_id": legacy_record_id,
        "legacy_source_table": SOURCE_TABLE,
        "legacy_attachment_ref": clean(row.get("attachment_ref")),
        "state": "approved" if str(row.get("document_state") or "") == "2" else "submitted",
    }
    if existing:
        existing.write(vals)
        updated += 1
        record = existing
    else:
        record = Purchase.create(vals)
        created += 1
    if len(samples) < 5:
        samples.append(
            {
                "id": record.id,
                "invoice_no": record.invoice_no,
                "project": record.project_id.display_name,
                "amount": record.amount,
                "apply_date": str(record.apply_date or ""),
            }
        )

plan = Plan.search([("priority_sequence", "=", 170), ("legacy_menu_name", "=", "投标报名费申请")], limit=1)
if plan:
    model = env["ir.model"].sudo().search([("model", "=", "tender.doc.purchase")], limit=1)  # noqa: F821
    plan.write(
        {
            "target_model": "tender.doc.purchase",
            "target_model_id": model.id or False,
            "legacy_source_tables": SOURCE_TABLE,
            "replay_status": "verified",
            "current_round_action": "specialized_carrier_exists",
            "target_iteration": "user_page_aligned_v2",
            "next_scope": "投标报名费申请已按旧表 BGGL_ZTBJHT_TBBM_TBBMFSQ 投影到 tender.doc.purchase。",
        }
    )

env.cr.commit()  # noqa: F821

result = {
    "status": "PASS",
    "mode": "fresh_db_legacy_tender_doc_purchase_projection_write",
    "source_table": SOURCE_TABLE,
    "input_rows": len(rows),
    "active_rows": active_rows,
    "created": created,
    "updated": updated,
    "created_bids": created_bids,
    "target_total": Purchase.search_count([("legacy_source_table", "=", SOURCE_TABLE)]),
    "samples": samples,
}
output_json.parent.mkdir(parents=True, exist_ok=True)
output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
