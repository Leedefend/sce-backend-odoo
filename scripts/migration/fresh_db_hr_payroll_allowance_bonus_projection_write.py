# -*- coding: utf-8 -*-
"""Project legacy subsidy and bonus facts into the runtime HR payroll surface.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_hr_payroll_allowance_bonus_projection_write.py
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path


INPUT_CSV_NAME = "fresh_db_legacy_business_fact_residual_replay_payload_v1.csv"
SUBSIDY_SOURCE_TABLE = "fresh_db_legacy_hr_subsidy"
BONUS_SOURCE_TABLE = "fresh_db_legacy_hr_bonus"


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


def parse_float(value):
    try:
        if value in (None, ""):
            return 0.0
        return float(str(value).strip())
    except Exception:
        return 0.0


def parse_int(value):
    try:
        return int(float(str(value or "").strip()))
    except Exception:
        return 0


def valid_year(value):
    year = parse_int(value)
    return year if 1900 <= year <= 2100 else 0


def valid_month(value):
    month = parse_int(value)
    return month if 1 <= month <= 12 else 0


def bool_active(value):
    return str(value or "").strip() not in {"0", "False", "false"}


def clean(value):
    text = str(value or "").strip()
    return text or None


def first(*values):
    for value in values:
        text = clean(value)
        if text:
            return text
    return None


def existing_legacy_ids(source_table, fact_type):
    env.cr.execute(  # noqa: F821
        """
        SELECT legacy_source_id
          FROM sc_hr_payroll_document
         WHERE fact_type = %s
           AND legacy_source_table = %s
           AND legacy_source_id IS NOT NULL
        """,
        (fact_type, source_table),
    )
    return {row[0] for row in env.cr.fetchall()}  # noqa: F821


def currency_id():
    return env.ref("base.CNY", raise_if_not_found=False).id  # noqa: F821


def department_id_by_name(name):
    text = clean(name)
    if not text:
        return None
    dept = env["hr.department"].sudo().search([("name", "=", text)], limit=1)  # noqa: F821
    if not dept:
        dept = env["hr.department"].sudo().search([("name", "ilike", text)], limit=1)  # noqa: F821
    return dept.id or None


def period_date(year, month):
    if year and month:
        return parse_date("%04d-%02d-01" % (year, month))
    return None


def load_rows(input_csv):
    rows = []
    with input_csv.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            raw = parse_json(row.get("raw_payload"))
            row["_raw"] = raw
            rows.append(row)
    return rows


def id_from_legacy_record_id(value):
    return str(value or "").split("#", 1)[0].strip()


def header_indexes(rows):
    headers = {"BGGL_XZ_BZ": {}, "BGGL_XZ_JXDJ_ZB": {}}
    for row in rows:
        table = row.get("source_table")
        if table not in headers:
            continue
        raw = row["_raw"]
        header_id = clean(raw.get("Id")) or id_from_legacy_record_id(row.get("legacy_record_id"))
        if header_id:
            headers[table][header_id] = row
        pid = clean(raw.get("PID")) or clean(raw.get("pid")) or clean(row.get("legacy_parent_id"))
        if pid:
            headers[table][pid] = row
    return headers


def insert_document(record, cur_currency_id):
    env.cr.execute(  # noqa: F821
        """
        INSERT INTO sc_hr_payroll_document (
            create_uid,
            write_uid,
            create_date,
            write_date,
            name,
            document_no,
            fact_type,
            state,
            business_date,
            department_id,
            employee_name,
            period_year,
            period_month,
            payer_unit,
            amount,
            item_type,
            occurrence_date,
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
            %s
        )
        """,
        (
            record["name"],
            record["document_no"],
            record["fact_type"],
            record["business_date"],
            department_id_by_name(record["department_name"]),
            record["employee_name"],
            record["period_year"],
            record["period_month"],
            record["payer_unit"],
            record["amount"],
            record["item_type"],
            record["occurrence_date"],
            record["description"],
            record["document_no"],
            record["legacy_document_state"],
            record["legacy_source_table"],
            record["legacy_source_id"],
            cur_currency_id,
            record["active"],
        ),
    )


def build_subsidy_records(rows, headers, seen):
    records = []
    for row in rows:
        table = row.get("source_table")
        if table not in {"BGGL_XZ_BZ", "BGGL_XZ_BZ_CB"}:
            continue
        raw = row["_raw"]
        amount = parse_float(first(raw.get("BZJE"), raw.get("JE"), row.get("amount_total")))
        if amount <= 0:
            continue
        legacy_id = id_from_legacy_record_id(row.get("legacy_record_id"))
        if not legacy_id or legacy_id in seen:
            continue
        header = headers["BGGL_XZ_BZ"].get(clean(raw.get("ZBID")) or clean(raw.get("Pid")) or clean(raw.get("pid")) or clean(row.get("legacy_parent_id"))) or row
        header_raw = header["_raw"]
        year = valid_year(first(raw.get("ND"), header_raw.get("ND")))
        month = valid_month(first(raw.get("YF"), header_raw.get("YF")))
        document_no = first(raw.get("DJBH"), header_raw.get("DJBH"), row.get("document_no"))
        item_type = first(raw.get("D_SCBSJS_BZSX"), raw.get("SY"), raw.get("SJBMC"), "补助")
        employee_name = first(raw.get("BZR"), raw.get("RY"), header_raw.get("BZR"), header_raw.get("RY"), header_raw.get("LRR"))
        if "测试" in str(employee_name or "") or "表单信息" in str(item_type or ""):
            continue
        department_name = first(raw.get("BMGW"), raw.get("BMGWMC"), header_raw.get("BMGW"))
        business_date = period_date(year, month) or parse_date(row.get("document_date")) or parse_date(header.get("document_date")) or parse_date(first(raw.get("LRSJ"), header_raw.get("LRSJ"), raw.get("XGSJ"), header_raw.get("XGSJ")))
        description = "\n".join(
            [
                "来源表: %s" % table,
                "补助事项: %s" % (item_type or ""),
                "人员: %s" % (employee_name or ""),
                "部门岗位: %s" % (department_name or ""),
                "项目: %s" % (first(row.get("project_name"), header.get("project_name"), raw.get("XMMC"), header_raw.get("XMMC")) or ""),
                "录入人: %s" % (first(raw.get("LRR"), header_raw.get("LRR"), raw.get("XGR"), header_raw.get("XGR")) or ""),
            ]
        )
        records.append(
            {
                "fact_type": "subsidy",
                "name": "补助 - %s %s" % (employee_name or "历史人员", item_type or ""),
                "document_no": document_no,
                "business_date": business_date,
                "department_name": department_name,
                "employee_name": employee_name,
                "period_year": year,
                "period_month": month,
                "payer_unit": first(raw.get("SSGS"), raw.get("XMMC"), header_raw.get("XMMC"), row.get("project_name")),
                "amount": amount,
                "item_type": item_type or "补助",
                "occurrence_date": business_date,
                "description": description,
                "legacy_document_state": first(raw.get("DJZT"), header_raw.get("DJZT"), row.get("active")) or "",
                "legacy_source_table": SUBSIDY_SOURCE_TABLE,
                "legacy_source_id": legacy_id,
                "active": bool_active(row.get("active")) and bool_active(raw.get("DEL") != 1),
            }
        )
    return records


def build_bonus_records(rows, headers, seen):
    records = []
    for row in rows:
        if row.get("source_table") != "BGGL_XZ_JXDJ":
            continue
        raw = row["_raw"]
        amount = parse_float(raw.get("JXGZ"))
        if amount <= 0:
            continue
        legacy_id = id_from_legacy_record_id(row.get("legacy_record_id"))
        if not legacy_id or legacy_id in seen:
            continue
        header = headers["BGGL_XZ_JXDJ_ZB"].get(clean(raw.get("ZBID")) or clean(row.get("legacy_parent_id"))) or row
        header_raw = header["_raw"]
        year = valid_year(header_raw.get("ND"))
        month = valid_month(header_raw.get("YF"))
        document_no = first(header_raw.get("DJBH"), row.get("document_no"), "JXDJ-%s" % legacy_id[:8])
        employee_name = first(raw.get("RY"), header_raw.get("RY"), header_raw.get("LRR"))
        item_type = first(raw.get("D_SCBSJS_RYLX"), raw.get("JL"), "奖金")
        if "测试" in str(employee_name or "") or "表单信息" in str(item_type or ""):
            continue
        business_date = period_date(year, month) or parse_date(header.get("document_date")) or parse_date(first(header_raw.get("LRSJ"), header_raw.get("XGSJ")))
        description = "\n".join(
            [
                "来源表: BGGL_XZ_JXDJ",
                "奖金类型: %s" % (item_type or ""),
                "人员: %s" % (employee_name or ""),
                "所属公司: %s" % (first(raw.get("SSGS"), raw.get("KHCJ"), header_raw.get("XMMC")) or ""),
                "奖励/备注: %s" % (raw.get("JL") or ""),
                "录入人: %s" % (first(header_raw.get("LRR"), header_raw.get("XGR")) or ""),
            ]
        )
        records.append(
            {
                "fact_type": "bonus",
                "name": "奖金 - %s %s-%02d" % (employee_name or "历史人员", year or 0, month or 0),
                "document_no": document_no,
                "business_date": business_date,
                "department_name": None,
                "employee_name": employee_name,
                "period_year": year,
                "period_month": month,
                "payer_unit": first(raw.get("SSGS"), raw.get("KHCJ"), header_raw.get("XMMC")),
                "amount": amount,
                "item_type": item_type or "奖金",
                "occurrence_date": business_date,
                "description": description,
                "legacy_document_state": first(header_raw.get("DJZT"), row.get("active")) or "",
                "legacy_source_table": BONUS_SOURCE_TABLE,
                "legacy_source_id": legacy_id,
                "active": bool_active(row.get("active")) and bool_active(header.get("active")) and bool_active(raw.get("DEL") != 1) and bool_active(header_raw.get("DEL") != 1),
            }
        )
    return records


output_json = resolve_artifact_root() / "fresh_db_hr_payroll_allowance_bonus_projection_write_result_v1.json"
input_csv = resolve_input_csv()
rows = load_rows(input_csv)
headers = header_indexes(rows)
cur_currency_id = currency_id()

result = {
    "mode": "fresh_db_hr_payroll_allowance_bonus_projection_write",
    "source_csv": str(input_csv),
    "target_model": "sc.hr.payroll.document",
    "facts": {},
}

for fact_type, source_table, builder in [
    ("subsidy", SUBSIDY_SOURCE_TABLE, build_subsidy_records),
    ("bonus", BONUS_SOURCE_TABLE, build_bonus_records),
]:
    env.cr.execute("SELECT COUNT(*) FROM sc_hr_payroll_document WHERE fact_type = %s", (fact_type,))  # noqa: F821
    before_count = env.cr.fetchone()[0]  # noqa: F821
    seen = existing_legacy_ids(source_table, fact_type)
    records = builder(rows, headers, seen)
    inserted = 0
    active_inserted = 0
    samples = []
    for record in records:
        insert_document(record, cur_currency_id)
        inserted += 1
        active_inserted += 1 if record["active"] else 0
        if len(samples) < 5:
            samples.append(
                {
                    "document_no": record["document_no"],
                    "employee_name": record["employee_name"],
                    "item_type": record["item_type"],
                    "amount": record["amount"],
                    "date": str(record["occurrence_date"] or ""),
                    "active": record["active"],
                }
            )
    env.cr.execute("SELECT COUNT(*) FROM sc_hr_payroll_document WHERE fact_type = %s", (fact_type,))  # noqa: F821
    after_count = env.cr.fetchone()[0]  # noqa: F821
    result["facts"][fact_type] = {
        "source_table": source_table,
        "before_count": before_count,
        "inserted": inserted,
        "active_inserted": active_inserted,
        "after_count": after_count,
        "samples": samples,
    }

env.cr.commit()  # noqa: F821

output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
