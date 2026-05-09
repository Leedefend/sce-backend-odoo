# -*- coding: utf-8 -*-
"""Project legacy leave/holiday approval rows into the runtime office admin surface.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_office_admin_leave_projection_write.py
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path


FACT_TYPE = "leave_request"
SOURCE_TABLE = "BGGL_HBZJ_XZD_QJXJSPB"
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


def parse_datetime(value):
    value = str(value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(value, fmt)
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


def leave_type(value):
    text = str(value or "").strip()
    if "年假" in text:
        return "annual"
    if "事假" in text:
        return "personal"
    if "病假" in text:
        return "sick"
    if "婚" in text:
        return "marriage"
    if "产" in text:
        return "maternity"
    if "丧" in text:
        return "bereavement"
    if "调休" in text:
        return "compensatory"
    return "other"


def state(value):
    text = str(value or "").strip()
    if text == "2":
        return "done"
    if text in {"-1", "9", "cancel"}:
        return "cancel"
    return "in_progress"


def existing_legacy_ids():
    env.cr.execute(  # noqa: F821
        """
        SELECT legacy_source_id
          FROM sc_office_admin_document
         WHERE fact_type = %s
           AND legacy_source_table = %s
           AND legacy_source_id IS NOT NULL
        """,
        (FACT_TYPE, SOURCE_TABLE),
    )
    return {row[0] for row in env.cr.fetchall()}  # noqa: F821


def currency_id():
    return env.company.currency_id.id  # noqa: F821


def resolve_input_csv():
    env_path = os.getenv("MIGRATION_BUSINESS_FACT_RESIDUAL_CSV")
    candidates = [Path(env_path)] if env_path else []
    candidates.append(Path("/mnt/artifacts/migration") / INPUT_CSV_NAME)
    candidates.append(Path("artifacts/migration") / INPUT_CSV_NAME)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("missing residual payload csv: %s" % [str(c) for c in candidates])


def iter_rows():
    with input_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("source_table") != SOURCE_TABLE:
                continue
            raw = json.loads(row.get("raw_payload") or "{}")
            legacy_source_id = row.get("legacy_record_id") or raw.get("ID")
            yield row, raw, legacy_source_id


output_json = resolve_artifact_root() / "fresh_db_office_admin_leave_projection_write_result_v1.json"
input_csv = resolve_input_csv()
seen = existing_legacy_ids()
created = 0
samples = []
cur_currency_id = currency_id()

env.cr.execute("SELECT COUNT(*) FROM sc_office_admin_document WHERE fact_type = %s", (FACT_TYPE,))  # noqa: F821
before_count = env.cr.fetchone()[0]  # noqa: F821

for row, raw, legacy_source_id in iter_rows():
    if legacy_source_id in seen:
        continue
    document_date = parse_datetime(row.get("document_date") or raw.get("LRSJ"))
    start_dt = parse_datetime(raw.get("QJSJ"))
    end_dt = parse_datetime(raw.get("XJSJ") or raw.get("SJXJSJ"))
    applicant = str(raw.get("SQRXM") or raw.get("LRR") or "").strip()
    department = str(raw.get("SZBM") or "").strip()
    leave_label = str(raw.get("QJLX") or "").strip()
    document_no = str(row.get("document_no") or raw.get("DJBH") or "").strip()
    title = "请假/休假审批"
    if applicant:
        title = "%s - %s" % (title, applicant)
    description_parts = [
        "旧系统备注: %s" % (raw.get("BZ") or ""),
        "申请人: %s" % applicant,
        "部门: %s" % department,
        "请假类型: %s" % leave_label,
        "请假时长: %s小时 / %s天" % (raw.get("QJSC") or "", raw.get("QJTS") or ""),
        "附件引用: %s" % (raw.get("FJ") or ""),
    ]
    env.cr.execute(  # noqa: F821
        """
        INSERT INTO sc_office_admin_document (
            create_uid,
            write_uid,
            create_date,
            write_date,
            name,
            document_no,
            fact_type,
            state,
            business_date,
            leave_type,
            start_datetime,
            end_datetime,
            duration_days,
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
            TRUE
        )
        """,
        (
            title,
            document_no or None,
            FACT_TYPE,
            state(raw.get("DJZT")),
            document_date.date() if document_date else None,
            leave_type(leave_label),
            start_dt,
            end_dt,
            parse_float(raw.get("QJTS")),
            "\n".join(description_parts),
            document_no or None,
            str(raw.get("DJZT") or ""),
            SOURCE_TABLE,
            legacy_source_id,
            cur_currency_id,
        ),
    )
    created += 1
    seen.add(legacy_source_id)
    if len(samples) < 5:
        samples.append(
            {
                "document_no": document_no,
                "applicant": applicant,
                "department": department,
                "leave_type": leave_label,
                "start_datetime": start_dt.isoformat(sep=" ") if start_dt else None,
                "end_datetime": end_dt.isoformat(sep=" ") if end_dt else None,
            }
        )

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_office_admin_document WHERE fact_type = %s", (FACT_TYPE,))  # noqa: F821
after_count = env.cr.fetchone()[0]  # noqa: F821

result = {
    "mode": "fresh_db_office_admin_leave_projection_write",
    "source_csv": str(input_csv),
    "source_table": SOURCE_TABLE,
    "target_model": "sc.office.admin.document",
    "fact_type": FACT_TYPE,
    "before_count": before_count,
    "inserted": created,
    "after_count": after_count,
    "samples": samples,
}
output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
