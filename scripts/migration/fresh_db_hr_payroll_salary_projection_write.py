# -*- coding: utf-8 -*-
"""Project legacy salary lines into the runtime HR payroll surface.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_hr_payroll_salary_projection_write.py
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path


FACT_TYPE = "salary_registration"
SOURCE_TABLE = "fresh_db_legacy_salary_line_salary_registration"
INPUT_CSV_NAME = "fresh_db_legacy_salary_line_replay_payload_v1.csv"


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
    env_path = os.getenv("MIGRATION_SALARY_LINE_CSV")
    candidates = [Path(env_path)] if env_path else []
    candidates.append(Path("/mnt/artifacts/migration") / INPUT_CSV_NAME)
    candidates.append(Path("artifacts/migration") / INPUT_CSV_NAME)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("missing salary payload csv: %s" % [str(c) for c in candidates])


def parse_date(value):
    value = str(value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


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


def bool_active(value):
    return str(value or "").strip() not in {"0", "False", "false"}


def existing_legacy_ids():
    env.cr.execute(  # noqa: F821
        """
        SELECT legacy_source_id
          FROM sc_hr_payroll_document
         WHERE fact_type = %s
           AND legacy_source_table = %s
           AND legacy_source_id IS NOT NULL
        """,
        (FACT_TYPE, SOURCE_TABLE),
    )
    return {row[0] for row in env.cr.fetchall()}  # noqa: F821


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


def period_date(year, month):
    if year and month:
        return parse_date("%04d-%02d-01" % (year, month))
    return None


output_json = resolve_artifact_root() / "fresh_db_hr_payroll_salary_projection_write_result_v1.json"
input_csv = resolve_input_csv()
seen = existing_legacy_ids()
created = 0
active_created = 0
samples = []
cur_currency_id = currency_id()

env.cr.execute("SELECT COUNT(*) FROM sc_hr_payroll_document WHERE fact_type = %s", (FACT_TYPE,))  # noqa: F821
before_count = env.cr.fetchone()[0]  # noqa: F821

with input_csv.open(newline="", encoding="utf-8-sig") as handle:
    reader = csv.DictReader(handle)
    for row in reader:
        legacy_source_id = row.get("legacy_line_id")
        if not legacy_source_id or legacy_source_id in seen:
            continue
        year = parse_int(row.get("salary_year"))
        month = parse_int(row.get("salary_month"))
        document_no = str(row.get("document_no") or "").strip()
        employee_name = str(row.get("person_name") or "").strip()
        dept_name = str(row.get("department_name") or "").strip()
        business_date = period_date(year, month) or parse_date(row.get("created_time"))
        salary_base = parse_float(row.get("salary_base"))
        gross_amount = parse_float(row.get("gross_amount"))
        deduction_amount = (
            parse_float(row.get("deduction"))
            + parse_float(row.get("social_security"))
            + parse_float(row.get("housing_fund"))
            + parse_float(row.get("individual_tax"))
            + parse_float(row.get("attendance_deduction"))
            + parse_float(row.get("tax_deduction"))
            + parse_float(row.get("union_fee"))
            + parse_float(row.get("housing_fund_deduction"))
        )
        net_salary = parse_float(row.get("net_salary"))
        is_active = bool_active(row.get("active"))
        description_parts = [
            "工资单号: %s" % document_no,
            "工资标题: %s" % (row.get("title") or ""),
            "人员: %s" % employee_name,
            "部门: %s" % dept_name,
            "岗位: %s" % (row.get("position_name") or ""),
            "社保扣款: %s" % (row.get("social_security") or ""),
            "公积金: %s" % (row.get("housing_fund") or ""),
            "个税: %s" % (row.get("individual_tax") or ""),
            "附件引用: %s" % (row.get("attachment_ref") or ""),
            "行备注: %s" % (row.get("line_note") or ""),
        ]
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
                salary_base,
                gross_amount,
                deduction_amount,
                net_salary,
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
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                "工资登记 - %s %s-%02d" % (employee_name or "历史人员", year or 0, month or 0),
                document_no or None,
                FACT_TYPE,
                business_date,
                department_id_by_name(dept_name),
                employee_name or None,
                str(row.get("id_number") or "").strip() or None,
                year,
                month,
                str(row.get("payer_unit") or row.get("company_name") or "").strip() or None,
                salary_base,
                gross_amount,
                deduction_amount,
                net_salary,
                net_salary,
                "工资登记",
                business_date,
                "\n".join(description_parts),
                document_no or None,
                str(row.get("document_state") or ""),
                SOURCE_TABLE,
                legacy_source_id,
                cur_currency_id,
                is_active,
            ),
        )
        created += 1
        active_created += 1 if is_active else 0
        seen.add(legacy_source_id)
        if len(samples) < 5:
            samples.append(
                {
                    "document_no": document_no,
                    "period": "%s-%02d" % (year, month),
                    "employee_name": employee_name,
                    "gross_amount": gross_amount,
                    "net_salary": net_salary,
                    "active": is_active,
                }
            )

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_hr_payroll_document WHERE fact_type = %s", (FACT_TYPE,))  # noqa: F821
after_count = env.cr.fetchone()[0]  # noqa: F821

result = {
    "mode": "fresh_db_hr_payroll_salary_projection_write",
    "source_csv": str(input_csv),
    "source_table": SOURCE_TABLE,
    "target_model": "sc.hr.payroll.document",
    "fact_type": FACT_TYPE,
    "before_count": before_count,
    "inserted": created,
    "active_inserted": active_created,
    "after_count": after_count,
    "samples": samples,
}
output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
