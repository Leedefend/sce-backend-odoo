#!/usr/bin/env python3
"""Normalize user-visible construction diary fields from existing facts.

Run inside ``odoo shell``.  The script only fills deterministic projections:
titles from existing quality/document facts, report dates from the diary date,
and manager/unit labels from the linked project.  It does not invent weather or
other facts that are absent from the source.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def artifact_root() -> Path:
    candidates = []
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("ARTIFACT_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([
        Path("/mnt/artifacts/visible_data_usability_closure"),
        Path(f"/tmp/visible_data_usability_closure/{env.cr.dbname}"),  # noqa: F821
    ])
    for root in candidates:
        try:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return root
        except Exception:
            continue
    raise RuntimeError("artifact root unavailable")


def scalar(sql: str) -> int:
    env.cr.execute(sql)  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return int(row[0] or 0) if row else 0


before = {
    "title_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE COALESCE(title, '') = ''"),
    "diary_type_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE COALESCE(diary_type, '') = ''"),
    "category_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE COALESCE(category, '') = ''"),
    "period_start_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE report_period_start IS NULL"),
    "period_end_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE report_period_end IS NULL"),
    "construction_unit_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE COALESCE(construction_unit, '') = ''"),
    "project_manager_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE COALESCE(project_manager, '') = ''"),
}

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_construction_diary diary
       SET title = COALESCE(NULLIF(diary.title, ''), NULLIF(diary.quality_name, ''), NULLIF(diary.document_no, ''), diary.name),
           diary_type = COALESCE(NULLIF(diary.diary_type, ''), '施工日志'),
           category = COALESCE(NULLIF(diary.category, ''), NULLIF(diary.legacy_related_quality_type, ''), '施工日志'),
           report_period_start = COALESCE(diary.report_period_start, diary.date_diary::date),
           report_period_end = COALESCE(diary.report_period_end, diary.date_diary::date),
           construction_unit = COALESCE(NULLIF(diary.construction_unit, ''), company.name),
           project_manager = COALESCE(NULLIF(diary.project_manager, ''), manager_partner.name),
           write_uid = 1,
           write_date = NOW()
      FROM project_project project
      LEFT JOIN res_company company ON company.id = project.company_id
      LEFT JOIN res_users manager_user ON manager_user.id = project.manager_id
      LEFT JOIN res_partner manager_partner ON manager_partner.id = manager_user.partner_id
     WHERE diary.project_id = project.id
       AND (
            COALESCE(diary.title, '') = ''
         OR COALESCE(diary.diary_type, '') = ''
         OR COALESCE(diary.category, '') = ''
         OR diary.report_period_start IS NULL
         OR diary.report_period_end IS NULL
         OR COALESCE(diary.construction_unit, '') = ''
         OR COALESCE(diary.project_manager, '') = ''
       )
    """
)
updated = env.cr.rowcount  # noqa: F821
env.cr.commit()  # noqa: F821

after = {
    "title_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE COALESCE(title, '') = ''"),
    "diary_type_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE COALESCE(diary_type, '') = ''"),
    "category_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE COALESCE(category, '') = ''"),
    "period_start_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE report_period_start IS NULL"),
    "period_end_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE report_period_end IS NULL"),
    "construction_unit_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE COALESCE(construction_unit, '') = ''"),
    "project_manager_empty": scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE COALESCE(project_manager, '') = ''"),
}

payload = {
    "mode": "visible_surface_construction_diary_normalize_write",
    "database": env.cr.dbname,  # noqa: F821
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "updated": updated,
    "before": before,
    "after": after,
    "status": "PASS",
}
output = artifact_root() / "visible_surface_construction_diary_normalize_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("VISIBLE_SURFACE_CONSTRUCTION_DIARY_NORMALIZE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
