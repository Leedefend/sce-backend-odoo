# -*- coding: utf-8 -*-
"""Project legacy person certificates into the runtime certificate entry.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_document_certificate_projection_write.py
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path


FACT_TYPE = "certificate_registration"
SOURCE_TABLE = "fresh_db_legacy_person_certificate"
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
    if not value or value == "长期":
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y.%m.%d"):
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
    return str(row.get("active") or "").strip() != "0" and str(raw.get("del") or raw.get("DEL") or "0").strip() != "1"


def load_rows(input_csv):
    rows = []
    with input_csv.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            row["_raw"] = parse_json(row.get("raw_payload"))
            rows.append(row)
    return rows


def person_index(rows):
    people = {}
    for row in rows:
        if row.get("source_table") != "DataSpider_ScjstPersonInfo":
            continue
        raw = row["_raw"]
        person_id = clean(raw.get("Id"))
        if not person_id:
            continue
        people[person_id.upper()] = {
            "name": clean(raw.get("PersonName")),
            "id_number": clean(raw.get("IdNumber")),
        }
    return people


def certificate_info(raw):
    info = parse_json(raw.get("CertificateInfoJson"))
    return {
        str(key or "").strip().rstrip(":："): clean(value)
        for key, value in info.items()
    }


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


def insert_certificate(record, currency_id):
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
            certificate_name,
            certificate_no,
            holder_name,
            issue_authority,
            issue_date,
            valid_until,
            document_title,
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
            %s
        )
        """,
        (
            record["name"],
            record["document_no"],
            FACT_TYPE,
            record["business_date"],
            record["certificate_name"],
            record["certificate_no"],
            record["holder_name"],
            record["issue_authority"],
            record["issue_date"],
            record["valid_until"],
            record["document_title"],
            record["description"],
            record["legacy_document_no"],
            record["legacy_document_state"],
            SOURCE_TABLE,
            record["legacy_source_id"],
            currency_id,
            record["active"],
        ),
    )


output_json = resolve_artifact_root() / "fresh_db_document_certificate_projection_write_result_v1.json"
input_csv = resolve_input_csv()
rows = load_rows(input_csv)
people = person_index(rows)
seen = existing_legacy_ids()
currency_id = env.ref("base.CNY", raise_if_not_found=False).id  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_document_admin_document WHERE fact_type = %s", (FACT_TYPE,))  # noqa: F821
before_count = env.cr.fetchone()[0]  # noqa: F821

inserted = 0
active_inserted = 0
samples = []

for row in rows:
    if row.get("source_table") != "DataSpider_ScjstPersonCertificate":
        continue
    raw = row["_raw"]
    legacy_id = id_from_legacy_record_id(row.get("legacy_record_id"))
    if not legacy_id or legacy_id in seen:
        continue
    info = certificate_info(raw)
    person = people.get(str(raw.get("ScjstPersonInfoId") or "").strip().upper(), {})
    certificate_name = first(raw.get("CertificateName"), raw.get("CertificateType"), info.get("证书级别"), info.get("等级"))
    certificate_no = first(info.get("证书号"), info.get("注册证书号"), info.get("岗位"), raw.get("CertificateType"), legacy_id)
    holder_name = first(person.get("name"), raw.get("PersonName"), raw.get("HolderName"), raw.get("ScjstPersonInfoId"), "历史证照持有人")
    issue_date = parse_date(first(info.get("发证时间"), info.get("初始注册")))
    valid_until = parse_date(first(info.get("有效期"), info.get("证书有效期")))
    business_date = parse_date(row.get("document_date")) or parse_date(raw.get("LRSJ")) or issue_date
    active = bool_active(row, raw)
    title = "%s - %s" % (certificate_name or "证照", holder_name)
    description = "\n".join(
        [
            "证照类别: %s" % (raw.get("CertificateType") or ""),
            "持有人证件: %s" % (person.get("id_number") or ""),
            "所在单位: %s" % (first(info.get("所在单位"), raw.get("CompanyName")) or ""),
            "原始证照信息: %s" % (raw.get("CertificateInfoJson") or ""),
            "来源表: DataSpider_ScjstPersonCertificate",
        ]
    )
    record = {
        "name": title,
        "document_no": "CERT-%s" % legacy_id[:12],
        "business_date": business_date,
        "certificate_name": certificate_name or "历史证照",
        "certificate_no": certificate_no or legacy_id,
        "holder_name": holder_name,
        "issue_authority": first(info.get("发证机构"), info.get("所在单位")),
        "issue_date": issue_date,
        "valid_until": valid_until,
        "document_title": title,
        "description": description,
        "legacy_document_no": legacy_id,
        "legacy_document_state": "历史证照信息",
        "legacy_source_id": legacy_id,
        "active": active,
    }
    insert_certificate(record, currency_id)
    inserted += 1
    active_inserted += 1 if active else 0
    seen.add(legacy_id)
    if len(samples) < 5:
        samples.append(
            {
                "document_no": record["document_no"],
                "certificate_name": record["certificate_name"],
                "certificate_no": record["certificate_no"],
                "holder_name": record["holder_name"],
                "valid_until": str(record["valid_until"] or ""),
                "active": active,
            }
        )

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_document_admin_document WHERE fact_type = %s", (FACT_TYPE,))  # noqa: F821
after_count = env.cr.fetchone()[0]  # noqa: F821

result = {
    "mode": "fresh_db_document_certificate_projection_write",
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
