# -*- coding: utf-8 -*-
"""Project legacy document borrowing facts into the runtime borrow entry.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_document_borrow_projection_write.py
"""

import csv
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path


FACT_TYPE = "document_borrow"
SOURCE_TABLE = "fresh_db_legacy_document_borrow"
INPUT_CSV_NAME = "fresh_db_legacy_business_fact_residual_replay_payload_v1.csv"
BORROW_SOURCE_TABLES = {"BGGL_TZXX_WJPYCJ", "BGGL_TZXX_WJHQ"}


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


def strip_html(value):
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


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


def existing_legacy_ids():
    env.cr.execute(  # noqa: F821
        """
        SELECT legacy_source_id
          FROM sc_document_admin_document
         WHERE fact_type = %s
           AND legacy_source_table = %s
           AND legacy_source_id IS NOT NULL
        """,
        (FACT_TYPE, SOURCE_TABLE),
    )
    return {row[0] for row in env.cr.fetchall()}  # noqa: F821


def user_id_by_name(*names):
    for name in names:
        user_id = _user_id_by_one_name(name)
        if user_id:
            return user_id
    return env.ref("base.user_admin").id  # noqa: F821


def _user_id_by_one_name(name):
    text = clean(name)
    if not text:
        return None
    user = env["res.users"].sudo().search([("name", "=", text)], limit=1)  # noqa: F821
    if not user:
        user = env["res.users"].sudo().search([("name", "ilike", text)], limit=1)  # noqa: F821
    return user.id or None


def is_document_borrow(row, raw):
    if row.get("source_table") not in BORROW_SOURCE_TABLES:
        return False
    text = " ".join(
        [
            str(raw.get("WJBT") or ""),
            str(raw.get("WJMC") or ""),
            strip_html(raw.get("WJNR") or ""),
        ]
    )
    if "借用" not in text and "借" not in text:
        return False
    # The vehicle borrowing table also contains 借用; it is intentionally not in BORROW_SOURCE_TABLES.
    return True


def build_record(row):
    raw = row["_raw"]
    legacy_id = id_from_legacy_record_id(row.get("legacy_record_id"))
    table = row.get("source_table")
    document_no = first(raw.get("DJBH"), row.get("document_no"), "JY-%s" % legacy_id[:8])
    title = first(raw.get("WJBT"), raw.get("WJMC"), raw.get("LXMC"), "历史资料借阅")
    content = strip_html(first(raw.get("WJNR"), raw.get("WJBT"), raw.get("WJMC"), ""))
    borrower_name = first(raw.get("WJNGR"), raw.get("QSR"), raw.get("SQR"), raw.get("LRR"), raw.get("FWBM"))
    operator_name = first(raw.get("LRR"), raw.get("QSR"), raw.get("SQR"), raw.get("XGR"))
    borrow_date = parse_date(first(raw.get("DJRQ"), raw.get("WJTJRQ"), row.get("document_date"), raw.get("LRSJ")))
    actual_return_date = parse_date(raw.get("HQWCSJ")) if table == "BGGL_TZXX_WJHQ" else None
    expected_return_date = actual_return_date or (borrow_date + timedelta(days=30) if borrow_date else None)
    description = "\n".join(
        [
            "来源表: %s" % table,
            "文件类型: %s" % (first(raw.get("LXMC"), raw.get("WJLX")) or ""),
            "快递/文件编号: %s" % (first(raw.get("SDBH"), raw.get("WJBH")) or ""),
            "签收/借阅人: %s" % (borrower_name or ""),
            "项目: %s" % (first(row.get("project_name"), raw.get("XMMC")) or ""),
            "原始说明: %s" % content,
        ]
    )
    return {
        "name": "借阅申请 - %s" % title,
        "document_no": document_no,
        "business_date": borrow_date,
        "document_title": title,
        "holder_name": borrower_name,
        "borrow_user_id": user_id_by_name(borrower_name, operator_name),
        "borrow_project_name": first(row.get("project_name"), raw.get("XMMC")),
        "borrow_department_name": first(raw.get("SSDW"), raw.get("SS单位"), raw.get("FWBM")),
        "borrower_name": borrower_name,
        "borrow_form": first(raw.get("JJCD"), raw.get("WJLX"), raw.get("LXMC")),
        "application_date": borrow_date,
        "returned_flag": "是" if actual_return_date else "否",
        "return_confirm_time": actual_return_date,
        "borrow_date": borrow_date,
        "expected_return_date": expected_return_date,
        "actual_return_date": actual_return_date,
        "description": description,
        "legacy_document_no": document_no,
        "legacy_document_state": first(raw.get("DJZT"), row.get("active")) or "",
        "legacy_source_id": legacy_id,
        "active": bool_active(row, raw),
    }


def insert_borrow(record, currency_id):
    env.cr.execute(  # noqa: F821
        """
        INSERT INTO sc_document_admin_document (
            create_uid,
            write_uid,
            create_date,
            write_date,
            name,
            document_no,
            fact_type,
            state,
            business_date,
            document_title,
            holder_name,
            borrow_user_id,
            borrow_project_name,
            borrow_department_name,
            borrower_name,
            borrow_form,
            application_date,
            returned_flag,
            return_confirm_time,
            borrow_date,
            expected_return_date,
            actual_return_date,
            description,
            legacy_document_no,
            legacy_document_state,
            legacy_source_table,
            legacy_source_id,
            currency_id,
            active
        )
        VALUES (
            1,
            1,
            now(),
            now(),
            %s,
            %s,
            %s,
            'done',
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            record["name"],
            record["document_no"],
            FACT_TYPE,
            record["business_date"],
            record["document_title"],
            record["holder_name"],
            record["borrow_user_id"],
            record["borrow_project_name"],
            record["borrow_department_name"],
            record["borrower_name"],
            record["borrow_form"],
            record["application_date"],
            record["returned_flag"],
            record["return_confirm_time"],
            record["borrow_date"],
            record["expected_return_date"],
            record["actual_return_date"],
            record["description"],
            record["legacy_document_no"],
            record["legacy_document_state"],
            SOURCE_TABLE,
            record["legacy_source_id"],
            currency_id,
            record["active"],
        ),
    )


output_json = resolve_artifact_root() / "fresh_db_document_borrow_projection_write_result_v1.json"
input_csv = resolve_input_csv()
seen = existing_legacy_ids()
currency_id = env.ref("base.CNY", raise_if_not_found=False).id  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_document_admin_document WHERE fact_type = %s", (FACT_TYPE,))  # noqa: F821
before_count = env.cr.fetchone()[0]  # noqa: F821

inserted = 0
active_inserted = 0
samples = []

with input_csv.open(newline="", encoding="utf-8-sig") as handle:
    for row in csv.DictReader(handle):
        row["_raw"] = parse_json(row.get("raw_payload"))
        raw = row["_raw"]
        legacy_id = id_from_legacy_record_id(row.get("legacy_record_id"))
        if not legacy_id or legacy_id in seen or not is_document_borrow(row, raw):
            continue
        record = build_record(row)
        insert_borrow(record, currency_id)
        inserted += 1
        active_inserted += 1 if record["active"] else 0
        seen.add(legacy_id)
        if len(samples) < 5:
            samples.append(
                {
                    "document_no": record["document_no"],
                    "document_title": record["document_title"],
                    "borrow_date": str(record["borrow_date"] or ""),
                    "expected_return_date": str(record["expected_return_date"] or ""),
                    "actual_return_date": str(record["actual_return_date"] or ""),
                    "active": record["active"],
                }
            )

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_document_admin_document WHERE fact_type = %s", (FACT_TYPE,))  # noqa: F821
after_count = env.cr.fetchone()[0]  # noqa: F821

result = {
    "mode": "fresh_db_document_borrow_projection_write",
    "source_csv": str(input_csv),
    "source_table": SOURCE_TABLE,
    "target_model": "sc.document.admin.document",
    "fact_type": FACT_TYPE,
    "before_count": before_count,
    "inserted": inserted,
    "active_inserted": active_inserted,
    "after_count": after_count,
    "samples": samples,
}
output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
