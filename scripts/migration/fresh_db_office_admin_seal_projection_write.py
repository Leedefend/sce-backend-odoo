# -*- coding: utf-8 -*-
"""Project legacy seal-use requests into the runtime office admin surface.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_office_admin_seal_projection_write.py
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path


FACT_TYPE = "seal_use"
SOURCE_TABLE = "BGGL_QSJRW_GZQS"
INPUT_CSV_NAME = "fresh_db_legacy_business_fact_residual_replay_payload_v1.csv"

SEAL_INCLUDE_TERMS = ("印章", "用章", "盖章", "公章", "合同章", "财务章", "法人章", "项目章", "印油", "签章")


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


def parse_date(value):
    parsed = parse_datetime(value)
    return parsed.date() if parsed else None


def state(value):
    text = str(value or "").strip()
    if text == "2":
        return "done"
    if text in {"-1", "9", "cancel"}:
        return "cancel"
    return "in_progress"


def seal_type(text):
    if "合同章" in text:
        return "contract"
    if "财务章" in text:
        return "finance"
    if "法人章" in text:
        return "legal_person"
    if "项目章" in text:
        return "project"
    if "公章" in text:
        return "company"
    return "other"


def is_seal_request(raw):
    text = " ".join(str(raw.get(field) or "") for field in ("BT", "QSJS", "QSXS"))
    return any(term in text for term in SEAL_INCLUDE_TERMS)


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
            if not is_seal_request(raw):
                continue
            legacy_source_id = row.get("legacy_record_id") or raw.get("ID")
            yield row, raw, legacy_source_id


output_json = resolve_artifact_root() / "fresh_db_office_admin_seal_projection_write_result_v1.json"
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
    document_no = str(row.get("document_no") or raw.get("DJBH") or "").strip()
    document_date = parse_date(raw.get("QSRQ") or row.get("document_date") or raw.get("LRSJ"))
    applicant = str(raw.get("QSR") or raw.get("LRR") or "").strip()
    department = str(raw.get("SSBM") or raw.get("SJBMC") or "").strip()
    title = str(raw.get("BT") or "").strip() or "印章使用审批"
    use_purpose = str(raw.get("QSJS") or raw.get("QSXS") or title).strip()
    text = "%s %s" % (title, use_purpose)
    description_parts = [
        "旧系统标题: %s" % title,
        "申请人: %s" % applicant,
        "部门: %s" % department,
        "紧急程度: %s" % (raw.get("JJCD") or ""),
        "附件引用: %s" % (raw.get("FJ") or ""),
        "旧系统说明: %s" % use_purpose,
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
            seal_type,
            use_purpose,
            use_date,
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
            TRUE
        )
        """,
        (
            title,
            document_no or None,
            FACT_TYPE,
            state(raw.get("DJZT")),
            document_date,
            seal_type(text),
            use_purpose[:255] if use_purpose else title,
            document_date,
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
                "title": title,
                "applicant": applicant,
                "department": department,
                "seal_type": seal_type(text),
                "use_date": document_date.isoformat() if document_date else None,
            }
        )

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_office_admin_document WHERE fact_type = %s", (FACT_TYPE,))  # noqa: F821
after_count = env.cr.fetchone()[0]  # noqa: F821

result = {
    "mode": "fresh_db_office_admin_seal_projection_write",
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
