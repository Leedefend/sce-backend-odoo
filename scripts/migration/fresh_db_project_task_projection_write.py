# -*- coding: utf-8 -*-
"""Project legacy task evidence into project.task.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_project_task_projection_write.py
"""

import json
import os
from pathlib import Path


def artifact_root():
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or "/mnt/artifacts/migration")
    try:
        root.mkdir(parents=True, exist_ok=True)
        return root
    except Exception:
        fallback = Path("/tmp/history_continuity/%s/adhoc" % env.cr.dbname)  # noqa: F821
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


ARTIFACT_DIR = artifact_root()
RESULT_JSON = ARTIFACT_DIR / "fresh_db_project_task_projection_write_result_v1.json"

Evidence = env["sc.legacy.task.evidence"].sudo().with_context(active_test=False)  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM project_task")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

uid = env.uid  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH source AS (
      SELECT
        e.id AS evidence_id,
        e.legacy_task_id,
        e.source_table,
        e.business_id,
        e.business_name,
        e.subject,
        e.project_id,
        p.company_id,
        e.primary_executor_user_id,
        CASE WHEN COALESCE(NULLIF(e.priority, ''), '0') IN ('1', 'high', 'urgent') THEN '1' ELSE '0' END AS priority,
        CASE WHEN COALESCE(e.done_flag, '') = '1' THEN '1_done' ELSE '01_in_progress' END AS state,
        CASE WHEN COALESCE(e.done_flag, '') = '1' THEN 'done' ELSE 'in_progress' END AS sc_state,
        COALESCE(e.start_time, e.create_date) AS date_assign,
        e.finish_time AS date_end,
        e.due_time AS date_deadline,
        e.active,
        TRUE AS display_in_project,
        CONCAT_WS(
          E'\n',
          '历史任务证据',
          '来源表：' || COALESCE(NULLIF(e.source_table, ''), ''),
          '旧任务ID：' || COALESCE(NULLIF(e.legacy_task_id, ''), ''),
          '单据号：' || COALESCE(NULLIF(e.bill_no, ''), ''),
          '业务名称：' || COALESCE(NULLIF(e.business_name, ''), ''),
          '创建人：' || COALESCE(NULLIF(e.creator_name, ''), ''),
          '完成人：' || COALESCE(NULLIF(e.finish_name, ''), ''),
          '完成说明：' || COALESCE(NULLIF(e.finish_remark, ''), ''),
          NULLIF(e.description, '')
        ) AS description,
        jsonb_build_object(
          'legacy_task_evidence_id', e.id::text,
          'legacy_task_id', COALESCE(e.legacy_task_id, ''),
          'legacy_source_table', COALESCE(e.source_table, ''),
          'legacy_business_id', COALESCE(e.business_id, ''),
          'legacy_business_name', COALESCE(e.business_name, '')
        ) AS task_properties
      FROM sc_legacy_task_evidence e
      JOIN project_project p ON p.id = e.project_id
      WHERE e.active IS TRUE
    ),
    updated AS (
      UPDATE project_task t
      SET
        name = s.subject,
        project_id = s.project_id,
        company_id = s.company_id,
        description = s.description,
        priority = s.priority,
        state = s.state,
        sc_state = s.sc_state,
        date_assign = s.date_assign,
        date_end = s.date_end,
        date_deadline = s.date_deadline,
        task_properties = s.task_properties,
        active = s.active,
        display_in_project = s.display_in_project,
        write_uid = %s,
        write_date = NOW()
      FROM source s
      WHERE t.task_properties->>'legacy_task_evidence_id' = s.evidence_id::text
      RETURNING t.id, s.evidence_id, s.primary_executor_user_id
    ),
    inserted AS (
      INSERT INTO project_task (
        sequence, name, project_id, company_id, description, priority, state, sc_state,
        date_assign, date_end, date_deadline, task_properties, active,
        display_in_project, create_uid, create_date, write_uid, write_date
      )
      SELECT
        10, s.subject, s.project_id, s.company_id, s.description, s.priority, s.state, s.sc_state,
        s.date_assign, s.date_end, s.date_deadline, s.task_properties, s.active,
        s.display_in_project, %s, NOW(), %s, NOW()
      FROM source s
      WHERE NOT EXISTS (
        SELECT 1 FROM project_task t
        WHERE t.task_properties->>'legacy_task_evidence_id' = s.evidence_id::text
      )
      RETURNING id, (task_properties->>'legacy_task_evidence_id')::integer AS evidence_id
    ),
    rel_source AS (
      SELECT id AS task_id, evidence_id FROM inserted
      UNION ALL
      SELECT id AS task_id, evidence_id FROM updated
    ),
    rel_inserted AS (
      INSERT INTO project_task_user_rel (task_id, user_id, create_uid, create_date, write_uid, write_date)
      SELECT rs.task_id, e.primary_executor_user_id, %s, NOW(), %s, NOW()
      FROM rel_source rs
      JOIN sc_legacy_task_evidence e ON e.id = rs.evidence_id
      WHERE e.primary_executor_user_id IS NOT NULL
      ON CONFLICT (task_id, user_id) DO NOTHING
      RETURNING id
    )
    SELECT
      (SELECT COUNT(*) FROM source) AS active_project_linked_rows,
      (SELECT COUNT(*) FROM inserted) AS created,
      (SELECT COUNT(*) FROM updated) AS updated,
      (SELECT COUNT(*) FROM source WHERE primary_executor_user_id IS NOT NULL) AS assigned,
      (SELECT COUNT(*) FROM rel_inserted) AS assigned_rel_created
    """,
    [uid, uid, uid, uid, uid],
)
active_rows, created, updated, assigned, assigned_rel_created = env.cr.fetchone()  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    SELECT COUNT(*)
    FROM sc_legacy_task_evidence
    WHERE active IS TRUE AND project_id IS NULL
    """
)
skipped_without_project = env.cr.fetchone()[0]  # noqa: F821

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM project_task")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute(  # noqa: F821
    """
    SELECT t.name, p.name, partner.name, t.state
    FROM project_task t
    JOIN project_project p ON p.id = t.project_id
    LEFT JOIN project_task_user_rel rel ON rel.task_id = t.id
    LEFT JOIN res_users u ON u.id = rel.user_id
    LEFT JOIN res_partner partner ON partner.id = u.partner_id
    WHERE t.task_properties ? 'legacy_task_evidence_id'
    ORDER BY t.id
    LIMIT 5
    """
)
sample = [
    {"task": task, "project": project, "executor": executor, "state": state}
    for task, project, executor, state in env.cr.fetchall()  # noqa: F821
]

result = {
    "status": "PASS",
    "mode": "fresh_db_project_task_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_rows": Evidence.search_count([("active", "=", True)]),
    "active_project_linked_rows": active_rows,
    "before": before,
    "after": after,
    "created": created,
    "updated": updated,
    "assigned": assigned,
    "assigned_rel_created": assigned_rel_created,
    "skipped_without_project": skipped_without_project,
    "sample": sample,
}
RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("FRESH_DB_PROJECT_TASK_PROJECTION_WRITE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
