#!/usr/bin/env python3
"""Replay privacy-restricted legacy salary line facts."""

from __future__ import annotations

import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_legacy_salary_line_replay_adapter_result_v1.json").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bulk_load(csv_path: Path, temp_table: str, columns: list[str]) -> None:
    env.cr.execute(f"DROP TABLE IF EXISTS {temp_table}")  # noqa: F821
    env.cr.execute(f"CREATE TEMP TABLE {temp_table} ({', '.join(f'{col} text' for col in columns)}) ON COMMIT DROP")  # noqa: F821
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        env.cr.copy_expert(f"COPY {temp_table} ({', '.join(columns)}) FROM STDIN WITH CSV HEADER", handle)  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_salary_line_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_salary_line_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_salary_line_replay_write_result_v1.json"

COLUMNS = [
    "legacy_line_id", "legacy_header_id", "legacy_pid", "legacy_header_pid",
    "source_dataset", "document_no", "document_state", "salary_year",
    "salary_month", "period_key", "title", "project_legacy_id",
    "project_name", "scope_legacy_ids", "scope_names", "person_legacy_id",
    "person_name", "department_legacy_id", "department_name",
    "position_legacy_id", "position_name", "id_number", "salary_base",
    "cash_amount", "social_security", "housing_fund", "individual_tax",
    "welfare_standard", "bonus", "deduction", "gross_amount",
    "performance_salary", "net_salary", "calculation_base",
    "overtime_amount", "post_allowance", "seniority_salary",
    "service_salary", "meal_allowance", "subsidy", "overtime_pay",
    "late_absence_deduction", "attendance_deduction",
    "medical_insurance_base", "medical_insurance_company",
    "unemployment_insurance", "social_security_individual_deduction",
    "social_security_company_deduction", "tax_deduction", "union_fee",
    "housing_fund_deduction", "payer_unit", "payment_people_count",
    "header_total_amount", "header_payable_amount", "header_people_count",
    "company_legacy_id", "company_name", "department_summary_legacy_id",
    "department_summary", "creator_legacy_user_id", "creator_name",
    "created_time", "modifier_legacy_user_id", "modifier_name",
    "modified_time", "attachment_ref", "source_note", "line_note", "active",
]

NUMERIC_COLUMNS = [
    "salary_base", "cash_amount", "social_security", "housing_fund",
    "individual_tax", "welfare_standard", "bonus", "deduction",
    "gross_amount", "performance_salary", "net_salary", "calculation_base",
    "overtime_amount", "post_allowance", "seniority_salary", "service_salary",
    "meal_allowance", "subsidy", "overtime_pay", "late_absence_deduction",
    "attendance_deduction", "medical_insurance_base",
    "medical_insurance_company", "unemployment_insurance",
    "social_security_individual_deduction",
    "social_security_company_deduction", "tax_deduction", "union_fee",
    "housing_fund_deduction", "header_total_amount", "header_payable_amount",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821
bulk_load(INPUT_CSV, "tmp_legacy_salary_line", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_salary_line")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

numeric_selects = [f"COALESCE(NULLIF(t.{col}, '')::numeric, 0)" for col in NUMERIC_COLUMNS]

env.cr.execute(  # noqa: F821
    f"""
    INSERT INTO sc_legacy_salary_line (
      legacy_line_id, legacy_header_id, legacy_pid, legacy_header_pid,
      source_dataset, document_no, document_state, salary_year, salary_month,
      period_key, title, project_legacy_id, project_name, project_id,
      scope_legacy_ids, scope_names, person_legacy_id, person_name,
      department_legacy_id, department_name, position_legacy_id, position_name,
      id_number, {', '.join(NUMERIC_COLUMNS[:29])}, payer_unit,
      payment_people_count, header_total_amount, header_payable_amount,
      header_people_count, company_legacy_id, company_name,
      department_summary_legacy_id, department_summary, creator_legacy_user_id,
      creator_name, created_time, modifier_legacy_user_id, modifier_name,
      modified_time, attachment_ref, source_note, line_note, source_table,
      active, create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_line_id,
      NULLIF(t.legacy_header_id, ''),
      NULLIF(t.legacy_pid, ''),
      NULLIF(t.legacy_header_pid, ''),
      NULLIF(t.source_dataset, ''),
      NULLIF(t.document_no, ''),
      NULLIF(t.document_state, ''),
      COALESCE(NULLIF(t.salary_year, '')::integer, 0),
      COALESCE(NULLIF(t.salary_month, '')::integer, 0),
      NULLIF(t.period_key, ''),
      NULLIF(t.title, ''),
      NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''),
      project.id,
      NULLIF(t.scope_legacy_ids, ''),
      NULLIF(t.scope_names, ''),
      NULLIF(t.person_legacy_id, ''),
      NULLIF(t.person_name, ''),
      NULLIF(t.department_legacy_id, ''),
      NULLIF(t.department_name, ''),
      NULLIF(t.position_legacy_id, ''),
      NULLIF(t.position_name, ''),
      NULLIF(t.id_number, ''),
      {', '.join(numeric_selects[:29])},
      NULLIF(t.payer_unit, ''),
      COALESCE(NULLIF(t.payment_people_count, '')::integer, 0),
      {numeric_selects[29]},
      {numeric_selects[30]},
      COALESCE(NULLIF(t.header_people_count, '')::integer, 0),
      NULLIF(t.company_legacy_id, ''),
      NULLIF(t.company_name, ''),
      NULLIF(t.department_summary_legacy_id, ''),
      NULLIF(t.department_summary, ''),
      NULLIF(t.creator_legacy_user_id, ''),
      NULLIF(t.creator_name, ''),
      NULLIF(t.created_time, '')::timestamp,
      NULLIF(t.modifier_legacy_user_id, ''),
      NULLIF(t.modifier_name, ''),
      NULLIF(t.modified_time, '')::timestamp,
      NULLIF(t.attachment_ref, ''),
      NULLIF(t.source_note, ''),
      NULLIF(t.line_note, ''),
      'BGGL_XZ_GZ_CB',
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_salary_line t
    LEFT JOIN (
      SELECT DISTINCT ON (legacy_project_id) legacy_project_id, id
      FROM project_project
      WHERE legacy_project_id IS NOT NULL
      ORDER BY legacy_project_id, id
    ) project ON project.legacy_project_id = NULLIF(t.project_legacy_id, '')
    ON CONFLICT (legacy_line_id) DO UPDATE SET
      legacy_header_id = EXCLUDED.legacy_header_id,
      legacy_pid = EXCLUDED.legacy_pid,
      legacy_header_pid = EXCLUDED.legacy_header_pid,
      source_dataset = EXCLUDED.source_dataset,
      document_no = EXCLUDED.document_no,
      document_state = EXCLUDED.document_state,
      salary_year = EXCLUDED.salary_year,
      salary_month = EXCLUDED.salary_month,
      period_key = EXCLUDED.period_key,
      title = EXCLUDED.title,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      project_id = EXCLUDED.project_id,
      scope_legacy_ids = EXCLUDED.scope_legacy_ids,
      scope_names = EXCLUDED.scope_names,
      person_legacy_id = EXCLUDED.person_legacy_id,
      person_name = EXCLUDED.person_name,
      department_legacy_id = EXCLUDED.department_legacy_id,
      department_name = EXCLUDED.department_name,
      position_legacy_id = EXCLUDED.position_legacy_id,
      position_name = EXCLUDED.position_name,
      id_number = EXCLUDED.id_number,
      salary_base = EXCLUDED.salary_base,
      cash_amount = EXCLUDED.cash_amount,
      social_security = EXCLUDED.social_security,
      housing_fund = EXCLUDED.housing_fund,
      individual_tax = EXCLUDED.individual_tax,
      welfare_standard = EXCLUDED.welfare_standard,
      bonus = EXCLUDED.bonus,
      deduction = EXCLUDED.deduction,
      gross_amount = EXCLUDED.gross_amount,
      performance_salary = EXCLUDED.performance_salary,
      net_salary = EXCLUDED.net_salary,
      calculation_base = EXCLUDED.calculation_base,
      overtime_amount = EXCLUDED.overtime_amount,
      post_allowance = EXCLUDED.post_allowance,
      seniority_salary = EXCLUDED.seniority_salary,
      service_salary = EXCLUDED.service_salary,
      meal_allowance = EXCLUDED.meal_allowance,
      subsidy = EXCLUDED.subsidy,
      overtime_pay = EXCLUDED.overtime_pay,
      late_absence_deduction = EXCLUDED.late_absence_deduction,
      attendance_deduction = EXCLUDED.attendance_deduction,
      medical_insurance_base = EXCLUDED.medical_insurance_base,
      medical_insurance_company = EXCLUDED.medical_insurance_company,
      unemployment_insurance = EXCLUDED.unemployment_insurance,
      social_security_individual_deduction = EXCLUDED.social_security_individual_deduction,
      social_security_company_deduction = EXCLUDED.social_security_company_deduction,
      tax_deduction = EXCLUDED.tax_deduction,
      union_fee = EXCLUDED.union_fee,
      housing_fund_deduction = EXCLUDED.housing_fund_deduction,
      payer_unit = EXCLUDED.payer_unit,
      payment_people_count = EXCLUDED.payment_people_count,
      header_total_amount = EXCLUDED.header_total_amount,
      header_payable_amount = EXCLUDED.header_payable_amount,
      header_people_count = EXCLUDED.header_people_count,
      company_legacy_id = EXCLUDED.company_legacy_id,
      company_name = EXCLUDED.company_name,
      department_summary_legacy_id = EXCLUDED.department_summary_legacy_id,
      department_summary = EXCLUDED.department_summary,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      modifier_legacy_user_id = EXCLUDED.modifier_legacy_user_id,
      modifier_name = EXCLUDED.modifier_name,
      modified_time = EXCLUDED.modified_time,
      attachment_ref = EXCLUDED.attachment_ref,
      source_note = EXCLUDED.source_note,
      line_note = EXCLUDED.line_note,
      source_table = EXCLUDED.source_table,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_salary_line")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_salary_line WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_salary_line WHERE project_id IS NOT NULL")  # noqa: F821
project_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(DISTINCT person_legacy_id) FROM sc_legacy_salary_line")  # noqa: F821
people_count = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COALESCE(SUM(gross_amount), 0), COALESCE(SUM(net_salary), 0) FROM sc_legacy_salary_line")  # noqa: F821
gross_amount, net_salary = env.cr.fetchone()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_salary_line_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "project_linked": project_linked,
    "people_count": people_count,
    "gross_amount": str(gross_amount),
    "net_salary": str(net_salary),
    "privacy_boundary": "restricted_config_admin_only",
    "db_writes": max(after - before, 0),
    "decision": "legacy_salary_line_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_SALARY_LINE_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
