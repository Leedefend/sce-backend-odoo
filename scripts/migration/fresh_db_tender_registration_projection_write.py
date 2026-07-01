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
    active_value = row.get("active")
    if active_value is False:
        return False
    return str(active_value or "").strip() != "0" and str(raw.get("DEL") or raw.get("del") or "0").strip() != "1"


def user_id_by_name(name):
    text = clean(name)
    if not text:
        return env.ref("base.user_admin").id  # noqa: F821
    user = env["res.users"].sudo().search([("name", "=", text)], limit=1)  # noqa: F821
    if not user:
        user = env["res.users"].sudo().search([("name", "ilike", text)], limit=1)  # noqa: F821
    return user.id or env.ref("base.user_admin").id  # noqa: F821


def partner_by_name(name):
    text = clean(name)
    if not text:
        return False
    Partner = env["res.partner"].sudo()  # noqa: F821
    partner = Partner.search([("name", "=", text)], limit=1)
    if partner:
        return partner.id
    return Partner.create({"name": text, "customer_rank": 1, "is_company": True}).id


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


def tender_state_from_fact(fact):
    status = first(fact.tender_status, fact.document_state)
    if status in {"中标", "已中标", "won"}:
        return "won"
    if status in {"未中标", "lost"}:
        return "lost"
    if status in {"2", "已提交", "submitted", "legacy_confirmed"}:
        return "submitted"
    if fact.opening_time:
        return "waiting"
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


def bid_by_fact(fact):
    if not fact.project_id:
        return None, False
    Bid = env["tender.bid"].sudo()  # noqa: F821
    bid = Bid.search(
        [
            ("legacy_fact_model", "=", fact._name),
            ("legacy_fact_id", "=", fact.id),
        ],
        limit=1,
    )
    vals = {
        "name": fact.document_no or "TENDER-%s" % fact.legacy_record_id,
        "tender_name": first(fact.project_name, fact.document_no) or "历史投标报名",
        "project_id": fact.project_id.id,
        "owner_id": partner_by_name(fact.owner_name),
        "legacy_owner_name": fact.owner_name,
        "bid_amount": fact.max_price or 0.0,
        "applicant_name": first(fact.creator_name, fact.contact_name),
        "apply_date": (fact.registration_time or fact.created_time).date()
        if fact.registration_time or fact.created_time
        else False,
        "note": fact.note,
        "created_time": fact.created_time,
        "deadline": fact.bid_time or fact.guarantee_deadline,
        "open_date": fact.opening_time,
        "state": tender_state_from_fact(fact),
        "legacy_fact_model": fact._name,
        "legacy_fact_id": fact.id,
        "legacy_fact_type": "legacy_tender_registration",
        "legacy_note": fact.note,
        "legacy_attachment_ref": fact.attachment_ref,
    }
    if bid:
        bid.write(vals)
        return bid, False
    return Bid.create(vals), True


def guarantee_by_fact(fact, bid):
    if not bid or not fact.guarantee_amount:
        return None, False
    Guarantee = env["tender.guarantee"].sudo()  # noqa: F821
    amount = fact.guarantee_amount or 0.0
    date_value = fact.guarantee_deadline or fact.opening_time or fact.registration_time or fact.created_time
    date_value = date_value.date() if hasattr(date_value, "date") else date_value
    remark = "历史投标保证金：%s" % (fact.document_no or fact.legacy_record_id)
    exists = Guarantee.search(
        [
            ("bid_id", "=", bid.id),
            ("type", "=", "out"),
            ("amount", "=", amount),
            ("date", "=", date_value),
            ("remark", "=", remark),
        ],
        limit=1,
    )
    vals = {
        "bid_id": bid.id,
        "type": "out",
        "date": date_value,
        "amount": amount,
        "remark": remark,
    }
    if exists:
        exists.write(vals)
        return exists, False
    return Guarantee.create(vals), True


def opening_result_from_fact(fact):
    state = tender_state_from_fact(fact)
    if state == "won":
        return "won"
    if state == "lost":
        return "lost"
    return "pending"


def opening_by_fact(fact, bid):
    if not bid or not fact.opening_time:
        return None, False
    Opening = env["tender.opening"].sudo()  # noqa: F821
    exists = Opening.search(
        [
            ("bid_id", "=", bid.id),
            ("open_time", "=", fact.opening_time),
        ],
        limit=1,
    )
    vals = {
        "bid_id": bid.id,
        "open_time": fact.opening_time,
        "result": opening_result_from_fact(fact),
        "win_price": fact.max_price or 0.0,
        "remark": "\n".join(
            item
            for item in [
                "历史投标开标记录：%s" % (fact.document_no or fact.legacy_record_id),
                "来源表：%s" % (fact.source_table or ""),
                fact.note or "",
            ]
            if item
        ),
    }
    if exists:
        exists.write(vals)
        return exists, False
    return Opening.create(vals), True


def load_rows(input_csv):
    rows = []
    with input_csv.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            row["_raw"] = parse_json(row.get("raw_payload"))
            rows.append(row)
    return rows


def load_rows_from_residual_model(source_tables):
    Fact = env["sc.legacy.business.fact.residual"].sudo()  # noqa: F821
    rows = []
    for fact in Fact.search([("source_table", "in", list(source_tables))], order="id"):
        def value(field_name):
            return fact[field_name] if field_name in Fact._fields else None

        row = {
            "source_table": value("source_table"),
            "document_no": value("document_no"),
            "project_name": value("project_name"),
            "document_date": value("document_date"),
            "amount_total": value("amount_total"),
            "legacy_record_id": value("legacy_record_id") or value("source_record_id") or fact.id,
            "active": value("active"),
            "raw_payload": value("raw_payload"),
        }
        row["_raw"] = parse_json(row.get("raw_payload"))
        rows.append(row)
    return rows


output_json = resolve_artifact_root() / "fresh_db_tender_registration_projection_write_result_v1.json"
input_csv = resolve_input_csv()
rows = load_rows(input_csv)
source_tables = {row.get("source_table") for row in rows}
residual_model_rows = []
if "BGGL_ZTBJHT_TBBM_TBBMFSQ" not in source_tables:
    residual_model_rows = load_rows_from_residual_model({"BGGL_ZTBJHT_TBBM_TBBMFSQ", "P_ZTB_GCXXGL"})
    rows.extend(residual_model_rows)

env.cr.execute("SELECT COUNT(*) FROM tender_bid")  # noqa: F821
before_bid_count = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM tender_doc_purchase")  # noqa: F821
before_fee_count = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM tender_guarantee")  # noqa: F821
before_guarantee_count = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM tender_opening")  # noqa: F821
before_opening_count = env.cr.fetchone()[0]  # noqa: F821

created_bids = 0
updated_fact_bids = 0
created_fees = 0
updated_fees = 0
created_guarantees = 0
updated_guarantees = 0
created_openings = 0
updated_openings = 0
active_fee_rows = 0
bid_samples = []
fee_samples = []
guarantee_samples = []
opening_samples = []

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
    active_fee_rows += 1
    document_no = first(raw.get("DJBH"), row.get("document_no"))
    amount = parse_float(first(raw.get("JE"), row.get("amount_total")))
    tender_name = first(raw.get("TBXMMC"), row.get("project_name"), raw.get("BZ"))
    bid, bid_created = bid_by_key(tender_name, tender_name, "TBBM-%s" % (clean(raw.get("TBXMID")) or id_from_legacy_record_id(row.get("legacy_record_id"))[:8]), raw)
    if bid_created:
        created_bids += 1
    Purchase = env["tender.doc.purchase"].sudo()  # noqa: F821
    exists = Purchase.search([("invoice_no", "=", document_no or ""), ("bid_id", "=", bid.id)], limit=1)
    vals = {
        "bid_id": bid.id,
        "applicant_id": user_id_by_name(first(raw.get("SQR"), raw.get("LRR"))),
        "apply_date": parse_date(first(raw.get("SQRQ"), raw.get("LRSJ"), row.get("document_date"))),
        "amount": amount,
        "invoice_no": document_no,
        "payment_method": first(raw.get("FKFS")),
        "receipt_partner_name": first(raw.get("SKDW")),
        "receipt_payee_name": first(raw.get("SKR")),
        "receipt_bank_name": first(raw.get("KHH")),
        "receipt_bank_account": first(raw.get("SKZH")),
        "remark": first(raw.get("BZ")),
        "legacy_source_created_by": first(raw.get("LRR"), raw.get("SQR")),
        "legacy_source_created_at": parse_datetime(first(raw.get("LRSJ"), raw.get("SQRQ"))),
        "legacy_record_id": id_from_legacy_record_id(first(row.get("legacy_record_id"), raw.get("Id"))),
        "legacy_source_table": row.get("source_table"),
        "state": "approved" if str(raw.get("DJZT") or "") == "2" else "submitted",
    }
    if exists:
        exists.write(vals)
        updated_fees += 1
        if len(fee_samples) < 5:
            fee_samples.append(
                {
                    "invoice_no": exists.invoice_no,
                    "tender_name": bid.tender_name,
                    "amount": exists.amount,
                    "apply_date": str(exists.apply_date or ""),
                    "receipt_partner_name": exists.receipt_partner_name,
                    "receipt_bank_account": exists.receipt_bank_account,
                    "updated": True,
                }
            )
        continue
    purchase = Purchase.create(vals)
    created_fees += 1
    if len(fee_samples) < 5:
        fee_samples.append(
            {
                "invoice_no": purchase.invoice_no,
                "tender_name": bid.tender_name,
                "amount": purchase.amount,
                "apply_date": str(purchase.apply_date or ""),
                "receipt_partner_name": purchase.receipt_partner_name,
                "receipt_bank_account": purchase.receipt_bank_account,
                "updated": False,
            }
        )

Fact = env["sc.legacy.tender.registration.fact"].sudo().with_context(active_test=False)  # noqa: F821
for fact in Fact.search([("active", "=", True)], order="id"):
    bid, created = bid_by_fact(fact)
    if not bid:
        continue
    if created:
        created_bids += 1
        if len(bid_samples) < 5:
            bid_samples.append({"name": bid.name, "tender_name": bid.tender_name, "state": bid.state})
    else:
        updated_fact_bids += 1
    guarantee, guarantee_created = guarantee_by_fact(fact, bid)
    if guarantee_created:
        created_guarantees += 1
        if len(guarantee_samples) < 5:
            guarantee_samples.append(
                {
                    "bid": bid.name,
                    "amount": float(guarantee.amount or 0.0),
                    "date": str(guarantee.date or ""),
                    "remark": guarantee.remark,
                }
            )
    elif guarantee:
        updated_guarantees += 1
    opening, opening_created = opening_by_fact(fact, bid)
    if opening_created:
        created_openings += 1
        if len(opening_samples) < 5:
            opening_samples.append(
                {
                    "bid": bid.name,
                    "open_time": str(opening.open_time or ""),
                    "result": opening.result,
                    "win_price": float(opening.win_price or 0.0),
                }
            )
    elif opening:
        updated_openings += 1

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM tender_bid")  # noqa: F821
after_bid_count = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM tender_doc_purchase")  # noqa: F821
after_fee_count = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM tender_guarantee")  # noqa: F821
after_guarantee_count = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM tender_opening")  # noqa: F821
after_opening_count = env.cr.fetchone()[0]  # noqa: F821

result = {
    "mode": "fresh_db_tender_registration_projection_write",
    "source_csv": str(input_csv),
    "residual_model_rows": len(residual_model_rows),
    "target_models": ["tender.bid", "tender.doc.purchase", "tender.guarantee", "tender.opening"],
    "before_bid_count": before_bid_count,
    "created_bids": created_bids,
    "updated_fact_bids": updated_fact_bids,
    "after_bid_count": after_bid_count,
    "before_fee_count": before_fee_count,
    "created_fees": created_fees,
    "updated_fees": updated_fees,
    "active_fee_rows": active_fee_rows,
    "after_fee_count": after_fee_count,
    "before_guarantee_count": before_guarantee_count,
    "created_guarantees": created_guarantees,
    "updated_guarantees": updated_guarantees,
    "after_guarantee_count": after_guarantee_count,
    "before_opening_count": before_opening_count,
    "created_openings": created_openings,
    "updated_openings": updated_openings,
    "after_opening_count": after_opening_count,
    "bid_samples": bid_samples,
    "fee_samples": fee_samples,
    "guarantee_samples": guarantee_samples,
    "opening_samples": opening_samples,
}
output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
