#!/usr/bin/env python3
"""Project legacy-backed receive requests into receipt income facts."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path


def resolve_repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def parse_date(value: str) -> str:
    text = clean(value)
    if not text:
        return ""
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return text[:10]


def parse_datetime(value: str) -> str:
    text = clean(value)
    if not text:
        return ""
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(text, fmt).isoformat(sep=" ")
        except ValueError:
            continue
    return text


def read_raw_receipts(repo_root: Path) -> list[dict[str, str]]:
    path = Path(os.getenv("MIGRATION_RECEIPT_RAW_CSV", str(repo_root / "tmp/raw/receipt/receipt.csv")))
    if not path.exists():
        raise RuntimeError({"missing_receipt_raw_csv": str(path)})
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            legacy_id = clean(row.get("Id"))
            if not legacy_id:
                continue
            rows.append(
                {
                    "legacy_record_id": legacy_id,
                    "document_no": clean(row.get("DJBH")),
                    "document_date": parse_date(row.get("f_RQ", "")),
                    "legacy_document_state": clean(row.get("DJZT")),
                    "deleted_flag": clean(row.get("DEL")),
                    "legacy_receipt_type": clean(row.get("type")),
                    "legacy_receipt_subtype": clean(row.get("BT")),
                    "income_category": clean(row.get("f_SRLBName") or row.get("D_HLCSXT_SRLB")),
                    "payment_method": clean(row.get("FKFSMC")),
                    "receiving_account": clean(row.get("SKZH")),
                    "bill_no": clean(row.get("PJH")),
                    "invoice_ref": clean(row.get("FP")),
                    "legacy_attachment_ref": clean(row.get("FJ")),
                    "creator_legacy_user_id": clean(row.get("LRRID")),
                    "creator_name": clean(row.get("LRR") or row.get("f_LRR")),
                    "created_time": parse_datetime(row.get("LRSJ") or row.get("f_LRSJ") or ""),
                    "note": clean(row.get("f_BZ")),
                }
            )
    return rows


def bulk_load(rows: list[dict[str, str]], columns: list[str]) -> None:
    env.cr.execute("DROP TABLE IF EXISTS tmp_receipt_income_raw_receipt")  # noqa: F821
    env.cr.execute(  # noqa: F821
        "CREATE TEMP TABLE tmp_receipt_income_raw_receipt (%s) ON COMMIT DROP"
        % ", ".join(f"{column} text" for column in columns)
    )
    if not rows:
        return
    env.cr.executemany(  # noqa: F821
        "INSERT INTO tmp_receipt_income_raw_receipt (%s) VALUES (%s)"
        % (", ".join(columns), ", ".join(["%s"] * len(columns))),
        [tuple(row.get(column, "") for column in columns) for row in rows],
    )


ensure_allowed_db()
repo_root = resolve_repo_root()
artifact_root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(repo_root / "artifacts/migration")))
output_json = artifact_root / "fresh_db_receipt_income_from_payment_request_projection_write_result_v1.json"
currency_id = env.company.currency_id.id  # noqa: F821

columns = [
    "legacy_record_id",
    "document_no",
    "document_date",
    "legacy_document_state",
    "deleted_flag",
    "legacy_receipt_type",
    "legacy_receipt_subtype",
    "income_category",
    "payment_method",
    "receiving_account",
    "bill_no",
    "invoice_ref",
    "legacy_attachment_ref",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "note",
]
raw_rows = read_raw_receipts(repo_root)
bulk_load(raw_rows, columns)

env.cr.execute("SELECT COUNT(*) FROM sc_receipt_income WHERE legacy_source_model = 'payment.request'")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH request_source AS (
      SELECT
        pr.id AS payment_request_id,
        COALESCE(NULLIF(pr.legacy_record_id, ''), substring(pr.note from 'legacy_receipt_id=([^;\\s]+)')) AS legacy_record_id,
        pr.name AS request_name,
        pr.state AS request_state,
        pr.project_id,
        pr.partner_id,
        pr.contract_id,
        pr.date_request,
        pr.amount,
        pr.currency_id,
        pr.note AS request_note,
        pr.legacy_source_table,
        pr.creator_legacy_user_id AS request_creator_legacy_user_id,
        pr.creator_name AS request_creator_name,
        pr.created_time AS request_created_time
      FROM payment_request pr
      WHERE pr.type = 'receive'
        AND COALESCE(pr.amount, 0) > 0
        AND COALESCE(NULLIF(pr.legacy_record_id, ''), substring(pr.note from 'legacy_receipt_id=([^;\\s]+)')) IS NOT NULL
    ),
    source AS (
      SELECT DISTINCT ON (rs.legacy_record_id)
        rs.*,
        raw.document_no,
        raw.document_date,
        raw.legacy_document_state,
        raw.deleted_flag,
        raw.legacy_receipt_type,
        raw.legacy_receipt_subtype,
        raw.income_category,
        raw.payment_method,
        raw.receiving_account,
        raw.bill_no,
        raw.invoice_ref,
        raw.legacy_attachment_ref,
        raw.creator_legacy_user_id,
        raw.creator_name,
        raw.created_time,
        raw.note
      FROM request_source rs
      LEFT JOIN tmp_receipt_income_raw_receipt raw ON raw.legacy_record_id = rs.legacy_record_id
      ORDER BY rs.legacy_record_id, rs.payment_request_id
    )
    INSERT INTO sc_receipt_income (
      name, source_origin, source_kind, state, project_id, partner_id, contract_id,
      payment_request_id, date_receipt, document_no, receipt_type,
      legacy_receipt_type, legacy_receipt_subtype, income_category,
      payment_method, receiving_account, bill_no, invoice_ref, amount,
      currency_id, legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, legacy_attachment_ref, creator_legacy_user_id,
      creator_name, created_time, note, active,
      create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(source.document_no, ''), source.request_name),
      'legacy',
      'receipt_income',
      CASE WHEN COALESCE(source.legacy_document_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      source.project_id,
      source.partner_id,
      source.contract_id,
      source.payment_request_id,
      COALESCE(NULLIF(source.document_date, '')::date, source.date_request, CURRENT_DATE),
      NULLIF(source.document_no, ''),
      COALESCE(NULLIF(source.legacy_receipt_type, ''), '收款申请'),
      NULLIF(source.legacy_receipt_type, ''),
      NULLIF(source.legacy_receipt_subtype, ''),
      NULLIF(source.income_category, ''),
      NULLIF(source.payment_method, ''),
      NULLIF(source.receiving_account, ''),
      NULLIF(source.bill_no, ''),
      NULLIF(source.invoice_ref, ''),
      source.amount,
      COALESCE(source.currency_id, %s),
      'payment.request',
      COALESCE(NULLIF(source.legacy_source_table, ''), 'C_JFHKLR'),
      source.legacy_record_id,
      NULLIF(source.legacy_document_state, ''),
      NULLIF(source.legacy_attachment_ref, ''),
      COALESCE(NULLIF(source.creator_legacy_user_id, ''), NULLIF(source.request_creator_legacy_user_id, '')),
      COALESCE(NULLIF(source.creator_name, ''), NULLIF(source.request_creator_name, '')),
      COALESCE(NULLIF(source.created_time, '')::timestamp, source.request_created_time),
      CONCAT_WS(E'\\n',
        '[migration:receipt_income_from_payment_request] legacy_record_id=' || source.legacy_record_id,
        'payment_request_id=' || source.payment_request_id,
        NULLIF(source.note, ''),
        NULLIF(source.request_note, '')
      ),
      COALESCE(NULLIF(source.deleted_flag, ''), '0') = '0',
      1,
      1,
      NOW(),
      NOW()
    FROM source
    WHERE source.project_id IS NOT NULL
      AND NOT EXISTS (
        SELECT 1
        FROM sc_receipt_income existing
        WHERE existing.legacy_record_id = source.legacy_record_id
          AND existing.legacy_source_table = 'C_JFHKLR'
          AND existing.legacy_source_model <> 'payment.request'
      )
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      contract_id = EXCLUDED.contract_id,
      payment_request_id = EXCLUDED.payment_request_id,
      date_receipt = EXCLUDED.date_receipt,
      document_no = EXCLUDED.document_no,
      receipt_type = EXCLUDED.receipt_type,
      legacy_receipt_type = EXCLUDED.legacy_receipt_type,
      legacy_receipt_subtype = EXCLUDED.legacy_receipt_subtype,
      income_category = EXCLUDED.income_category,
      payment_method = EXCLUDED.payment_method,
      receiving_account = EXCLUDED.receiving_account,
      bill_no = EXCLUDED.bill_no,
      invoice_ref = EXCLUDED.invoice_ref,
      amount = EXCLUDED.amount,
      currency_id = EXCLUDED.currency_id,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_attachment_ref = EXCLUDED.legacy_attachment_ref,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.execute("SELECT COUNT(*) FROM sc_receipt_income WHERE legacy_source_model = 'payment.request'")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_receipt_income_attachment_rel (receipt_id, attachment_id)
    SELECT income.id, rel.attachment_id
    FROM sc_receipt_income income
    JOIN payment_request_attachment_rel rel ON rel.request_id = income.payment_request_id
    WHERE income.legacy_source_model = 'payment.request'
      AND NOT EXISTS (
        SELECT 1
        FROM sc_receipt_income_attachment_rel existing
        WHERE existing.receipt_id = income.id AND existing.attachment_id = rel.attachment_id
      )
    """
)
attachment_links = env.cr.rowcount  # noqa: F821
env.cr.commit()  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    SELECT legacy_receipt_type, COUNT(*), COALESCE(SUM(amount), 0)
    FROM sc_receipt_income
    WHERE legacy_source_model = 'payment.request' AND COALESCE(legacy_receipt_type, '') <> ''
    GROUP BY legacy_receipt_type
    ORDER BY COUNT(*) DESC
    """
)
type_counts = [{"receipt_type": row[0], "count": row[1], "amount": str(row[2])} for row in env.cr.fetchall()]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    SELECT legacy_receipt_subtype, COUNT(*), COALESCE(SUM(amount), 0)
    FROM sc_receipt_income
    WHERE legacy_source_model = 'payment.request' AND COALESCE(legacy_receipt_subtype, '') <> ''
    GROUP BY legacy_receipt_subtype
    ORDER BY COUNT(*) DESC
    LIMIT 40
    """
)
subtype_counts = [{"receipt_subtype": row[0], "count": row[1], "amount": str(row[2])} for row in env.cr.fetchall()]  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_receipt_income_from_payment_request_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "raw_receipt_rows": len(raw_rows),
    "before": before,
    "after": after,
    "delta": after - before,
    "attachment_links": attachment_links,
    "type_counts": type_counts,
    "subtype_counts": subtype_counts,
    "decision": "legacy_receive_request_facts_projected_to_receipt_income",
}
write_json(output_json, payload)
print("RECEIPT_INCOME_FROM_PAYMENT_REQUEST_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
