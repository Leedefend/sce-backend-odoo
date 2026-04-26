#!/usr/bin/env python3
"""Project legacy workflow audit facts into an actionable history todo surface."""

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
        if (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_history_todo_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scalar(sql: str, params: list[object] | None = None) -> int:
    env.cr.execute(sql, params or [])  # noqa: F821
    return int(env.cr.fetchone()[0] or 0)  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_history_todo_projection_write_result_v1.json"

ensure_allowed_db()
uid = env.uid  # noqa: F821

before = scalar("SELECT COUNT(*) FROM sc_history_todo")
audit_rows = scalar("SELECT COUNT(*) FROM sc_legacy_workflow_audit")

env.cr.execute(  # noqa: F821
    """
    WITH payment_target_map AS (
      SELECT DISTINCT ON (target_external_id)
        target_external_id,
        'payment.request'::text AS target_res_model,
        id AS target_res_id
      FROM (
        SELECT
          'legacy_outflow_sc_' || substring(note from 'legacy_outflow_id=([^;[:space:]]+)') AS target_external_id,
          id
        FROM payment_request
        WHERE note LIKE '%%legacy_outflow_id=%%'
        UNION ALL
        SELECT
          'legacy_receipt_sc_' || substring(note from 'legacy_receipt_id=([^;[:space:]]+)') AS target_external_id,
          id
        FROM payment_request
        WHERE note LIKE '%%legacy_receipt_id=%%'
        UNION ALL
        SELECT
          'legacy_actual_outflow_sc_' || substring(note from 'legacy_actual_outflow_id=([^;[:space:]]+)') AS target_external_id,
          id
        FROM payment_request
        WHERE note LIKE '%%legacy_actual_outflow_id=%%'
      ) raw
      WHERE target_external_id IS NOT NULL
      ORDER BY target_external_id, id
    ),
    contract_target_map AS (
      SELECT DISTINCT ON (target_external_id)
        target_external_id,
        'construction.contract'::text AS target_res_model,
        id AS target_res_id
      FROM (
        SELECT 'legacy_contract_sc_' || legacy_contract_id AS target_external_id, id
        FROM construction_contract
        WHERE legacy_contract_id IS NOT NULL
        UNION ALL
        SELECT 'legacy_supplier_contract_sc_' || legacy_contract_id AS target_external_id, id
        FROM construction_contract
        WHERE legacy_contract_id IS NOT NULL
          AND note LIKE '%%legacy_supplier_contract_id=%%'
      ) raw
      WHERE target_external_id IS NOT NULL
      ORDER BY target_external_id, id
    ),
    target_map AS (
      SELECT * FROM payment_target_map
      UNION ALL
      SELECT * FROM contract_target_map
    )
    INSERT INTO sc_history_todo (
      name, state, priority, workflow_audit_id,
      legacy_workflow_id, legacy_source_table, target_lane, target_model,
      target_external_id, target_res_model, target_res_id,
      actor_legacy_user_id, actor_name, legacy_step_name, legacy_template_name,
      action_classification, legacy_status, legacy_approval_type,
      received_at, approved_at, approval_note, source_table,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      LEFT(
        CONCAT_WS(
          ' / ',
          COALESCE(NULLIF(a.legacy_template_name, ''), NULLIF(a.target_lane, ''), NULLIF(a.target_model, ''), '历史流程'),
          COALESCE(NULLIF(a.legacy_step_name, ''), NULLIF(a.action_classification, ''), NULLIF(a.legacy_status, ''), NULLIF(a.legacy_workflow_id, ''))
        ),
        255
      ) AS name,
      'todo' AS state,
      CASE
        WHEN COALESCE(NULLIF(a.action_classification, ''), '') = 'approve' THEN 90
        WHEN COALESCE(NULLIF(a.legacy_status, ''), '') IN ('2', 'approved', 'done') THEN 80
        WHEN a.received_at IS NOT NULL AND a.approved_at IS NULL THEN 70
        ELSE 10
      END AS priority,
      a.id AS workflow_audit_id,
      NULLIF(a.legacy_workflow_id, ''),
      NULLIF(a.legacy_source_table, ''),
      NULLIF(a.target_lane, ''),
      NULLIF(a.target_model, ''),
      NULLIF(a.target_external_id, ''),
      CASE
        WHEN tm.target_res_id IS NOT NULL THEN tm.target_res_model
        WHEN imd.res_id IS NOT NULL THEN imd.model
        ELSE NULLIF(a.target_model, '')
      END AS target_res_model,
      COALESCE(tm.target_res_id, imd.res_id) AS target_res_id,
      NULLIF(a.actor_legacy_user_id, ''),
      NULLIF(a.actor_name, ''),
      NULLIF(a.legacy_step_name, ''),
      NULLIF(a.legacy_template_name, ''),
      NULLIF(a.action_classification, ''),
      NULLIF(a.legacy_status, ''),
      NULLIF(a.legacy_approval_type, ''),
      a.received_at,
      a.approved_at,
      NULLIF(a.approval_note, ''),
      'sc.legacy.workflow.audit',
      %s, NOW(), %s, NOW()
    FROM sc_legacy_workflow_audit a
    LEFT JOIN target_map tm
      ON tm.target_external_id = NULLIF(a.target_external_id, '')
     AND (NULLIF(a.target_model, '') IS NULL OR tm.target_res_model = NULLIF(a.target_model, ''))
    LEFT JOIN ir_model_data imd
      ON imd.module = 'smart_construction_core'
     AND imd.name = NULLIF(a.target_external_id, '')
     AND (NULLIF(a.target_model, '') IS NULL OR imd.model = NULLIF(a.target_model, ''))
    ON CONFLICT (workflow_audit_id) DO UPDATE SET
      name = EXCLUDED.name,
      priority = EXCLUDED.priority,
      legacy_workflow_id = EXCLUDED.legacy_workflow_id,
      legacy_source_table = EXCLUDED.legacy_source_table,
      target_lane = EXCLUDED.target_lane,
      target_model = EXCLUDED.target_model,
      target_external_id = EXCLUDED.target_external_id,
      target_res_model = EXCLUDED.target_res_model,
      target_res_id = EXCLUDED.target_res_id,
      actor_legacy_user_id = EXCLUDED.actor_legacy_user_id,
      actor_name = EXCLUDED.actor_name,
      legacy_step_name = EXCLUDED.legacy_step_name,
      legacy_template_name = EXCLUDED.legacy_template_name,
      action_classification = EXCLUDED.action_classification,
      legacy_status = EXCLUDED.legacy_status,
      legacy_approval_type = EXCLUDED.legacy_approval_type,
      received_at = EXCLUDED.received_at,
      approved_at = EXCLUDED.approved_at,
      approval_note = EXCLUDED.approval_note,
      source_table = EXCLUDED.source_table,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)

env.cr.commit()  # noqa: F821

after = scalar("SELECT COUNT(*) FROM sc_history_todo")
created = max(after - before, 0)
state_counts = {}
env.cr.execute("SELECT state, COUNT(*) FROM sc_history_todo GROUP BY state ORDER BY state")  # noqa: F821
for state, count in env.cr.fetchall():  # noqa: F821
    state_counts[str(state or "__empty__")] = int(count)

payload = {
    "status": "PASS" if after >= audit_rows else "FAIL",
    "mode": "fresh_db_history_todo_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "workflow_audit_rows": audit_rows,
    "before_rows": before,
    "after_rows": after,
    "created_rows": created,
    "updated_or_existing_rows": max(audit_rows - created, 0),
    "target_linked_rows": scalar("SELECT COUNT(*) FROM sc_history_todo WHERE target_res_id IS NOT NULL"),
    "state_counts": state_counts,
    "db_writes": audit_rows,
    "decision": "history_todo_projection_complete" if after >= audit_rows else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_HISTORY_TODO_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
