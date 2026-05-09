# -*- coding: utf-8 -*-
"""Project legacy social-insurance rows into the runtime HR payroll surface.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_hr_payroll_social_projection_write.py
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path


PERSON_FACT_TYPE = "social_person_registration"
REGISTRATION_FACT_TYPE = "social_registration"
PERSON_SOURCE_TABLE = "D_SCBSJS_BGGL_XZ_SBRY"
SALARY_SOURCE_TABLE = "fresh_db_legacy_salary_line"
BUSINESS_FACT_CSV = "fresh_db_legacy_business_fact_residual_replay_payload_v1.csv"
SALARY_LINE_CSV = "fresh_db_legacy_salary_line_replay_payload_v1.csv"


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


def resolve_input_csv(env_name, file_name):
    env_path = os.getenv(env_name)
    candidates = [Path(env_path)] if env_path else []
    candidates.append(Path("/mnt/artifacts/migration") / file_name)
    candidates.append(Path("artifacts/migration") / file_name)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("missing input csv: %s" % [str(c) for c in candidates])


def parse_datetime(value):
    value = str(value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def parse_date(value):
    parsed = parse_datetime(value)
    return parsed.date() if parsed else None


def parse_float(value):
    try:
        if value in (None, ""):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def parse_int(value):
    try:
        return int(float(str(value or "").strip()))
    except Exception:
        return 0


def state(value):
    text = str(value or "").strip()
    if text == "2":
        return "done"
    if text in {"-1", "9", "cancel"}:
        return "cancel"
    return "in_progress"


def bool_active(value):
    return str(value or "").strip() not in {"0", "False", "false"}


def existing_pairs():
    env.cr.execute(  # noqa: F821
        """
        SELECT legacy_source_table, legacy_source_id
          FROM sc_hr_payroll_document
         WHERE legacy_source_table IN %s
           AND legacy_source_id IS NOT NULL
        """,
        ((PERSON_SOURCE_TABLE, SALARY_SOURCE_TABLE),),
    )
    return {(row[0], row[1]) for row in env.cr.fetchall()}  # noqa: F821


def currency_id():
    return env.company.currency_id.id  # noqa: F821


def department_id_by_name(name):
    text = str(name or "").strip()
    if not text:
        return None
    dept = env["hr.department"].sudo().search([("name", "=", text)], limit=1)  # noqa: F821
    if not dept:
        dept = env["hr.department"].sudo().search([("name", "ilike", text)], limit=1)  # noqa: F821
    return dept.id or None


def insert_document(vals):
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
            id_number,
            period_year,
            period_month,
            payer_unit,
            social_security_base,
            company_amount,
            individual_amount,
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
            vals.get("name"),
            vals.get("document_no"),
            vals.get("fact_type"),
            vals.get("state"),
            vals.get("business_date"),
            vals.get("department_id"),
            vals.get("employee_name"),
            vals.get("id_number"),
            vals.get("period_year"),
            vals.get("period_month"),
            vals.get("payer_unit"),
            vals.get("social_security_base"),
            vals.get("company_amount"),
            vals.get("individual_amount"),
            vals.get("amount"),
            vals.get("item_type"),
            vals.get("occurrence_date"),
            vals.get("description"),
            vals.get("legacy_document_no"),
            vals.get("legacy_document_state"),
            vals.get("legacy_source_table"),
            vals.get("legacy_source_id"),
            vals.get("currency_id"),
            vals.get("active", True),
        ),
    )


def project_social_person_rows(input_csv, seen, cur_currency_id):
    created = 0
    active_created = 0
    samples = []
    with input_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("source_table") != PERSON_SOURCE_TABLE:
                continue
            raw = json.loads(row.get("raw_payload") or "{}")
            legacy_source_id = row.get("legacy_record_id") or raw.get("ID")
            pair = (PERSON_SOURCE_TABLE, legacy_source_id)
            if pair in seen:
                continue
            document_date = parse_date(raw.get("DJRQ") or row.get("document_date") or raw.get("LRSJ"))
            employee_name = str(raw.get("XM") or "").strip()
            payer_unit = str(raw.get("ZS") or raw.get("XMMC") or "").strip()
            document_no = str(row.get("document_no") or raw.get("DJBH") or "").strip()
            is_active = bool_active(row.get("active"))
            description_parts = [
                "人员类型: %s" % (raw.get("RYLX") or ""),
                "人员状态: %s" % (raw.get("RYZT") or ""),
                "联系方式: %s" % (raw.get("LXFS") or ""),
                "证书/备注: %s" % (raw.get("ZS") or raw.get("BZ") or ""),
                "公司金额: %s" % (raw.get("GSJE") or ""),
                "养老金额: %s" % (raw.get("YLJE") or ""),
                "失业金额: %s" % (raw.get("SYJE") or ""),
                "附件引用: %s" % (raw.get("FJ") or ""),
            ]
            insert_document(
                {
                    "name": "社保人员登记 - %s" % (employee_name or document_no or "历史人员"),
                    "document_no": document_no or None,
                    "fact_type": PERSON_FACT_TYPE,
                    "state": state(raw.get("DJZT")),
                    "business_date": document_date,
                    "employee_name": employee_name or None,
                    "id_number": str(raw.get("SFZHM") or "").strip() or None,
                    "period_year": document_date.year if document_date else 0,
                    "period_month": document_date.month if document_date else 0,
                    "payer_unit": payer_unit or None,
                    "social_security_base": parse_float(raw.get("SBJS")),
                    "company_amount": parse_float(raw.get("GSJE")) + parse_float(raw.get("YLJE")),
                    "individual_amount": parse_float(raw.get("SYJE")),
                    "amount": parse_float(raw.get("GSJE")) + parse_float(raw.get("YLJE")) + parse_float(raw.get("SYJE")),
                    "item_type": str(raw.get("RYLX") or "社保人员登记").strip(),
                    "occurrence_date": document_date,
                    "description": "\n".join(description_parts),
                    "legacy_document_no": document_no or None,
                    "legacy_document_state": str(raw.get("DJZT") or ""),
                    "legacy_source_table": PERSON_SOURCE_TABLE,
                    "legacy_source_id": legacy_source_id,
                    "currency_id": cur_currency_id,
                    "active": is_active,
                }
            )
            created += 1
            active_created += 1 if is_active else 0
            seen.add(pair)
            if len(samples) < 5:
                samples.append(
                    {
                        "document_no": document_no,
                        "employee_name": employee_name,
                        "payer_unit": payer_unit,
                        "social_security_base": parse_float(raw.get("SBJS")),
                        "active": is_active,
                    }
                )
    return created, active_created, samples


def project_social_registration_rows(input_csv, seen, cur_currency_id):
    created = 0
    active_created = 0
    samples = []
    with input_csv.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            social_amount = parse_float(row.get("social_security"))
            company_amount = (
                parse_float(row.get("social_security_company_deduction"))
                + parse_float(row.get("medical_insurance_company"))
                + parse_float(row.get("unemployment_insurance"))
            )
            individual_amount = parse_float(row.get("social_security_individual_deduction")) or social_amount
            if not (social_amount or company_amount or individual_amount):
                continue
            legacy_source_id = row.get("legacy_line_id")
            pair = (SALARY_SOURCE_TABLE, legacy_source_id)
            if pair in seen:
                continue
            year = parse_int(row.get("salary_year"))
            month = parse_int(row.get("salary_month"))
            document_no = str(row.get("document_no") or "").strip()
            employee_name = str(row.get("person_name") or "").strip()
            dept_name = str(row.get("department_name") or "").strip()
            payer_unit = str(row.get("payer_unit") or row.get("company_name") or "").strip()
            occurrence_date = parse_date("%04d-%02d-01" % (year, month)) if year and month else parse_date(row.get("created_time"))
            is_active = bool_active(row.get("active"))
            description_parts = [
                "工资单号: %s" % document_no,
                "人员: %s" % employee_name,
                "部门: %s" % dept_name,
                "工资期间: %s-%s" % (year or "", month or ""),
                "工资社保扣款: %s" % (row.get("social_security") or ""),
                "附件引用: %s" % (row.get("attachment_ref") or ""),
                "行备注: %s" % (row.get("line_note") or ""),
            ]
            insert_document(
                {
                    "name": "社保登记 - %s %s-%02d" % (employee_name or "历史人员", year or 0, month or 0),
                    "document_no": document_no or None,
                    "fact_type": REGISTRATION_FACT_TYPE,
                    "state": "done",
                    "business_date": occurrence_date,
                    "department_id": department_id_by_name(dept_name),
                    "employee_name": employee_name or None,
                    "id_number": str(row.get("id_number") or "").strip() or None,
                    "period_year": year,
                    "period_month": month,
                    "payer_unit": payer_unit or None,
                    "social_security_base": parse_float(row.get("salary_base")),
                    "company_amount": company_amount,
                    "individual_amount": individual_amount,
                    "amount": company_amount + individual_amount,
                    "item_type": "社保登记",
                    "occurrence_date": occurrence_date,
                    "description": "\n".join(description_parts),
                    "legacy_document_no": document_no or None,
                    "legacy_document_state": str(row.get("document_state") or ""),
                    "legacy_source_table": SALARY_SOURCE_TABLE,
                    "legacy_source_id": legacy_source_id,
                    "currency_id": cur_currency_id,
                    "active": is_active,
                }
            )
            created += 1
            active_created += 1 if is_active else 0
            seen.add(pair)
            if len(samples) < 5:
                samples.append(
                    {
                        "document_no": document_no,
                        "period": "%s-%02d" % (year, month),
                        "employee_name": employee_name,
                        "individual_amount": individual_amount,
                        "company_amount": company_amount,
                    }
                )
    return created, active_created, samples


artifact_root = resolve_artifact_root()
business_csv = resolve_input_csv("MIGRATION_BUSINESS_FACT_RESIDUAL_CSV", BUSINESS_FACT_CSV)
salary_csv = resolve_input_csv("MIGRATION_SALARY_LINE_CSV", SALARY_LINE_CSV)
output_json = artifact_root / "fresh_db_hr_payroll_social_projection_write_result_v1.json"
seen = existing_pairs()
cur_currency_id = currency_id()

env.cr.execute(  # noqa: F821
    "SELECT fact_type, COUNT(*) FROM sc_hr_payroll_document WHERE fact_type IN %s GROUP BY fact_type",
    ((PERSON_FACT_TYPE, REGISTRATION_FACT_TYPE),),
)
before_counts = {row[0]: row[1] for row in env.cr.fetchall()}  # noqa: F821

person_inserted, person_active_inserted, person_samples = project_social_person_rows(business_csv, seen, cur_currency_id)
registration_inserted, registration_active_inserted, registration_samples = project_social_registration_rows(
    salary_csv,
    seen,
    cur_currency_id,
)

env.cr.commit()  # noqa: F821

env.cr.execute(  # noqa: F821
    "SELECT fact_type, COUNT(*) FROM sc_hr_payroll_document WHERE fact_type IN %s GROUP BY fact_type",
    ((PERSON_FACT_TYPE, REGISTRATION_FACT_TYPE),),
)
after_counts = {row[0]: row[1] for row in env.cr.fetchall()}  # noqa: F821

result = {
    "mode": "fresh_db_hr_payroll_social_projection_write",
    "business_source_csv": str(business_csv),
    "salary_source_csv": str(salary_csv),
    "target_model": "sc.hr.payroll.document",
    "before_counts": before_counts,
    "after_counts": after_counts,
    "inserted": {
        PERSON_FACT_TYPE: person_inserted,
        REGISTRATION_FACT_TYPE: registration_inserted,
    },
    "active_inserted": {
        PERSON_FACT_TYPE: person_active_inserted,
        REGISTRATION_FACT_TYPE: registration_active_inserted,
    },
    "samples": {
        PERSON_FACT_TYPE: person_samples,
        REGISTRATION_FACT_TYPE: registration_samples,
    },
}
output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
