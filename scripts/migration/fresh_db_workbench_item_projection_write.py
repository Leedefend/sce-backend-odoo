#!/usr/bin/env python3
"""Project historical workflow todos into the formal workbench item model."""

from __future__ import annotations

import json
import os
from pathlib import Path


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scalar(sql: str, params: list[object] | None = None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


ensure_allowed_db()
artifact_root = resolve_artifact_root()
output_json = artifact_root / "fresh_db_workbench_item_projection_write_result_v1.json"
currency_id = env.company.currency_id.id  # noqa: F821

before = int(scalar("SELECT COUNT(*) FROM sc_workbench_item") or 0)
todo_before = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_workbench_item
         WHERE fact_type = 'my_todo'
           AND source_model = 'sc.history.todo'
        """
    )
    or 0
)
approval_before = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_workbench_item
         WHERE fact_type = 'my_approval'
           AND source_model = 'sc.history.todo'
        """
    )
    or 0
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_workbench_item (
      name, document_no, fact_type, requester_id, handler_id, business_date,
      due_date, currency_id, state, description, active, source_model,
      source_res_id, priority, todo_deadline, create_uid, write_uid,
      create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(h.name, ''), '历史流程待办'),
      fact.document_prefix || h.id::text,
      fact.fact_type,
      NULL,
      NULL,
      COALESCE(h.received_at::date, h.approved_at::date, CURRENT_DATE),
      h.received_at::date,
      %s,
      CASE
        WHEN h.state IN ('resolved', 'archived') THEN 'done'
        ELSE 'in_progress'
      END,
      concat_ws(E'\n',
        NULLIF('旧系统流程ID: ' || COALESCE(h.legacy_workflow_id, ''), '旧系统流程ID: '),
        NULLIF('业务泳道: ' || COALESCE(h.target_lane, ''), '业务泳道: '),
        NULLIF('目标模型: ' || COALESCE(h.target_model, h.target_res_model, ''), '目标模型: '),
        NULLIF('旧系统步骤: ' || COALESCE(h.legacy_step_name, ''), '旧系统步骤: '),
        NULLIF('旧系统模板: ' || COALESCE(h.legacy_template_name, ''), '旧系统模板: '),
        NULLIF('旧系统处理人: ' || COALESCE(h.actor_name, ''), '旧系统处理人: '),
        NULLIF('审批意见: ' || COALESCE(h.approval_note, ''), '审批意见: ')
      ),
      TRUE,
      'sc.history.todo',
      h.id,
      CASE
        WHEN COALESCE(h.priority, 0) >= 90 THEN 'urgent'
        WHEN COALESCE(h.priority, 0) >= 50 THEN 'high'
        WHEN COALESCE(h.priority, 0) <= 0 THEN 'low'
        ELSE 'normal'
      END,
      h.received_at::date,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_history_todo h
    CROSS JOIN (
      VALUES
        ('my_todo', 'TODO-'),
        ('my_approval', 'APPR-')
    ) AS fact(fact_type, document_prefix)
    ON CONFLICT (fact_type, source_model, source_res_id)
    DO UPDATE SET
      name = EXCLUDED.name,
      document_no = EXCLUDED.document_no,
      business_date = EXCLUDED.business_date,
      due_date = EXCLUDED.due_date,
      currency_id = EXCLUDED.currency_id,
      state = EXCLUDED.state,
      description = EXCLUDED.description,
      active = EXCLUDED.active,
      priority = EXCLUDED.priority,
      todo_deadline = EXCLUDED.todo_deadline,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM sc_workbench_item") or 0)
todo_after = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_workbench_item
         WHERE fact_type = 'my_todo'
           AND source_model = 'sc.history.todo'
        """
    )
    or 0
)
approval_after = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_workbench_item
         WHERE fact_type = 'my_approval'
           AND source_model = 'sc.history.todo'
        """
    )
    or 0
)
legacy_source = int(scalar("SELECT COUNT(*) FROM sc_history_todo") or 0)
payload = {
    "status": "PASS",
    "mode": "fresh_db_workbench_item_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "delta": after - before,
    "todo_before": todo_before,
    "todo_after": todo_after,
    "todo_delta": todo_after - todo_before,
    "approval_before": approval_before,
    "approval_after": approval_after,
    "approval_delta": approval_after - approval_before,
    "legacy_source_rows": legacy_source,
    "decision": (
        "workbench_item_projection_complete"
        if todo_after >= legacy_source and approval_after >= legacy_source
        else "workbench_item_projection_gap"
    ),
}
write_json(output_json, payload)
print("WORKBENCH_ITEM_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
