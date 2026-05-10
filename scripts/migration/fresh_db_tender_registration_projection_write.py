# -*- coding: utf-8 -*-
"""Project legacy tender registration and registration-fee facts.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_tender_registration_projection_write.py
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path


INPUT_CSV_NAME = "fresh_db_legacy_business_fact_residual_replay_payload_v1.csv"


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


def resolve_input_csv():
    env_path = os.getenv("MIGRATION_BUSINESS_RESIDUAL_CSV")
    candidates = [Path(env_path)] if env_path else []
    candidates.append(Path("/mnt/artifacts/migration") / INPUT_CSV_NAME)
    candidates.append(Path("artifacts/migration") / INPUT_CSV_NAME)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("missing business residual payload csv: %s" % [str(c) for c in candidates])


def parse_json(value):
    try:
        return json.loads(value or "{}")
    except Exception:
        return {}


def parse_date(value):
    value = str(value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value[:19], fmt).date()
        except ValueError:
            continue
    return None


def parse_datetime(value):
    value = str(value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
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


def id_from_legacy_record_id(value):
    return str(value or "").split("#", 1)[0].strip()


def bool_active(row, raw):
    return str(row.get("active") or "").strip() != "0" and str(raw.get("DEL") or raw.get("del") or "0").strip() != "1"


def user_id_by_name(name):
    text = clean(name)
    if not text:
        return env.ref("base.user_admin").id  # noqa: F821
    user = env["res.users"].sudo().search([("name", "=", text)], limit=1)  # noqa: F821
    if not user:
        user = env["res.users"].sudo().search([("name", "ilike", text)], limit=1)  # noqa: F821
    return user.id or env.ref("base.user_admin").id  # noqa: F821


def project_by_name(name):
    project_name = clean(name) or "历史投标项目"
    Project = env["project.project"].sudo()  # noqa: F821
    project = Project.search([("name", "=", project_name)], limit=1)
    if project:
        return project
    return Project.create({"name": project_name})


def tender_state(raw):
    status = first(raw.get("TBZT"), raw.get("f_ZT"), raw.get("DJZT"))
    if status in {"中标", "已中标", "won"}:
        return "won"
    if status in {"未中标", "lost"}:
        return "lost"
    if status in {"2", "已提交", "submitted"}:
        return "submitted"
    return "prepare"


def bid_by_key(name, project_name, document_no, raw):
    tender_name = clean(name) or "历史投标报名"
    project = project_by_name(project_name or tender_name)
    Bid = env["tender.bid"].sudo()  # noqa: F821
    bid = Bid.search([("name", "=", document_no or ""), ("project_id", "=", project.id)], limit=1)
    if bid:
        return bid, False
    bid = Bid.search([("tender_name", "=", tender_name), ("project_id", "=", project.id)], limit=1)
    if bid:
        return bid, False
    bid = Bid.create(
        {
            "name": document_no or "TENDER-%s" % id_from_legacy_record_id(raw.get("Id"))[:8],
            "tender_name": tender_name,
            "project_id": project.id,
            "bid_amount": parse_float(first(raw.get("ZGXJ"), raw.get("XMGM"))),
            "deadline": parse_datetime(raw.get("EndBMSD")),
            "open_date": parse_datetime(raw.get("KBSJ")),
            "state": tender_state(raw),
        }
    )
    return bid, True


def load_rows(input_csv):
    rows = []
    with input_csv.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            row["_raw"] = parse_json(row.get("raw_payload"))
            rows.append(row)
    return rows


output_json = resolve_artifact_root() / "fresh_db_tender_registration_projection_write_result_v1.json"
input_csv = resolve_input_csv()
rows = load_rows(input_csv)

env.cr.execute("SELECT COUNT(*) FROM tender_bid")  # noqa: F821
before_bid_count = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM tender_doc_purchase")  # noqa: F821
before_fee_count = env.cr.fetchone()[0]  # noqa: F821

created_bids = 0
created_fees = 0
active_fee_rows = 0
bid_samples = []
fee_samples = []

for row in rows:
    if row.get("source_table") != "P_ZTB_GCXXGL":
        continue
    raw = row["_raw"]
    if not bool_active(row, raw):
        continue
    document_no = first(raw.get("DJBH"), row.get("document_no"))
    tender_name = first(raw.get("f_GCMC"), row.get("project_name"), raw.get("GCMC"))
    bid, created = bid_by_key(tender_name, tender_name, document_no, raw)
    if created:
        created_bids += 1
        if len(bid_samples) < 5:
            bid_samples.append({"name": bid.name, "tender_name": bid.tender_name, "state": bid.state})

for row in rows:
    if row.get("source_table") != "BGGL_ZTBJHT_TBBM_TBBMFSQ":
        continue
    raw = row["_raw"]
    if not bool_active(row, raw):
        continue
    document_no = first(raw.get("DJBH"), row.get("document_no"))
    amount = parse_float(first(raw.get("JE"), row.get("amount_total")))
    tender_name = first(raw.get("TBXMMC"), row.get("project_name"), raw.get("BZ"))
    bid, bid_created = bid_by_key(tender_name, tender_name, "TBBM-%s" % (clean(raw.get("TBXMID")) or id_from_legacy_record_id(row.get("legacy_record_id"))[:8]), raw)
    if bid_created:
        created_bids += 1
    Purchase = env["tender.doc.purchase"].sudo()  # noqa: F821
    exists = Purchase.search([("invoice_no", "=", document_no or ""), ("bid_id", "=", bid.id)], limit=1)
    if exists:
        continue
    purchase = Purchase.create(
        {
            "bid_id": bid.id,
            "applicant_id": user_id_by_name(first(raw.get("SQR"), raw.get("LRR"))),
            "apply_date": parse_date(first(raw.get("SQRQ"), raw.get("LRSJ"), row.get("document_date"))),
            "amount": amount,
            "invoice_no": document_no,
            "state": "approved" if str(raw.get("DJZT") or "") == "2" else "submitted",
        }
    )
    created_fees += 1
    active_fee_rows += 1
    if len(fee_samples) < 5:
        fee_samples.append(
            {
                "invoice_no": purchase.invoice_no,
                "tender_name": bid.tender_name,
                "amount": purchase.amount,
                "apply_date": str(purchase.apply_date or ""),
            }
        )

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM tender_bid")  # noqa: F821
after_bid_count = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM tender_doc_purchase")  # noqa: F821
after_fee_count = env.cr.fetchone()[0]  # noqa: F821

result = {
    "mode": "fresh_db_tender_registration_projection_write",
    "source_csv": str(input_csv),
    "target_models": ["tender.bid", "tender.doc.purchase"],
    "before_bid_count": before_bid_count,
    "created_bids": created_bids,
    "after_bid_count": after_bid_count,
    "before_fee_count": before_fee_count,
    "created_fees": created_fees,
    "active_fee_rows": active_fee_rows,
    "after_fee_count": after_fee_count,
    "bid_samples": bid_samples,
    "fee_samples": fee_samples,
}
output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
