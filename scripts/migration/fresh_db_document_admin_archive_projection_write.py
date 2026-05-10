# -*- coding: utf-8 -*-
"""Project legacy company document archive files into the runtime document surface.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_document_admin_archive_projection_write.py
"""

import json
import os
from pathlib import Path


FACT_TYPE = "company_document_archive"
SOURCE_FILTER = "company_file_name"


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


OUTPUT_JSON = resolve_artifact_root() / "fresh_db_document_admin_archive_projection_write_result_v1.json"

env.cr.execute(
    """
    SELECT COUNT(*)
      FROM sc_document_admin_document
     WHERE fact_type = %s
    """,
    (FACT_TYPE,),
)
before_count = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(
    """
    WITH source_rows AS (
        SELECT
            f.id,
            f.legacy_file_key,
            f.source_table,
            f.legacy_file_id,
            f.file_name,
            f.file_path,
            f.extension,
            f.uploader_name,
            f.upload_time,
            f.file_size,
            f.note
          FROM sc_legacy_file_index f
         WHERE f.active IS TRUE
           AND f.file_name ILIKE '%%公司%%'
    )
    INSERT INTO sc_document_admin_document (
        create_uid,
        write_uid,
        create_date,
        write_date,
        name,
        document_no,
        fact_type,
        state,
        document_title,
        holder_name,
        business_date,
        description,
        legacy_document_no,
        legacy_document_state,
        legacy_source_table,
        legacy_source_id,
        currency_id,
        active
    )
    SELECT
        1,
        1,
        now(),
        now(),
        '公司资料存档',
        'COMPANY_ARCHIVE-' || s.id::text,
        %s,
        'done',
        left(s.file_name, 255),
        NULLIF(s.uploader_name, ''),
        COALESCE(s.upload_time::date, CURRENT_DATE),
        concat_ws(
            E'\n',
            '旧文件路径: ' || COALESCE(s.file_path, ''),
            '扩展名: ' || COALESCE(s.extension, ''),
            '上传人: ' || COALESCE(s.uploader_name, ''),
            '上传时间: ' || COALESCE(s.upload_time::text, ''),
            '文件大小: ' || COALESCE(s.file_size::text, ''),
            '分类规则: ' || %s,
            COALESCE(s.note, '')
        ),
        s.legacy_file_id,
        '历史文件索引',
        s.source_table,
        s.legacy_file_key,
        COALESCE((SELECT currency_id FROM res_company WHERE id = 1), 1),
        TRUE
      FROM source_rows s
     WHERE NOT EXISTS (
        SELECT 1
          FROM sc_document_admin_document d
         WHERE d.legacy_source_table = s.source_table
           AND d.legacy_source_id = s.legacy_file_key
     )
    """,
    (FACT_TYPE, SOURCE_FILTER),
)
inserted = env.cr.rowcount  # noqa: F821
env.cr.commit()  # noqa: F821

env.cr.execute(
    """
    SELECT COUNT(*)
      FROM sc_document_admin_document
     WHERE fact_type = %s
    """,
    (FACT_TYPE,),
)
after_count = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(
    """
    SELECT id, document_no, document_title, holder_name, business_date
      FROM sc_document_admin_document
     WHERE fact_type = %s
     ORDER BY business_date DESC NULLS LAST, id DESC
     LIMIT 5
    """,
    (FACT_TYPE,),
)
samples = [
    {
        "id": row[0],
        "document_no": row[1],
        "document_title": row[2],
        "holder_name": row[3],
        "business_date": row[4].isoformat() if row[4] else None,
    }
    for row in env.cr.fetchall()  # noqa: F821
]

result = {
    "mode": "fresh_db_document_admin_archive_projection_write",
    "fact_type": FACT_TYPE,
    "source_model": "sc.legacy.file.index",
    "target_model": "sc.document.admin.document",
    "source_filter": SOURCE_FILTER,
    "before_count": before_count,
    "inserted": inserted,
    "after_count": after_count,
    "samples": samples,
}

OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
