#!/usr/bin/env python3
"""Create minimal project anchors for valid legacy receipt income facts."""

from __future__ import annotations

import json
import os
from pathlib import Path


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


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fetch_missing_project_refs() -> list[dict[str, object]]:
    env.cr.execute(  # noqa: F821
        """
        SELECT
          r.project_legacy_id,
          COALESCE(NULLIF(MAX(r.project_name), ''), '历史收入事实项目 ' || r.project_legacy_id) AS project_name,
          COUNT(*) AS fact_count,
          COALESCE(SUM(r.amount), 0) AS amount_sum,
          (ARRAY_AGG(r.legacy_record_id ORDER BY r.document_date, r.legacy_record_id))[1:10] AS legacy_record_ids
        FROM sc_legacy_receipt_residual_fact r
        LEFT JOIN project_project p ON p.legacy_project_id = r.project_legacy_id
        WHERE r.active
          AND COALESCE(r.amount, 0) > 0
          AND COALESCE(r.project_legacy_id, '') <> ''
          AND r.project_id IS NULL
          AND p.id IS NULL
        GROUP BY r.project_legacy_id
        ORDER BY amount_sum DESC, project_name
        """
    )
    rows = []
    for legacy_project_id, project_name, fact_count, amount_sum, legacy_record_ids in env.cr.fetchall():  # noqa: F821
        rows.append(
            {
                "legacy_project_id": legacy_project_id,
                "project_name": project_name,
                "fact_count": int(fact_count or 0),
                "amount_sum": float(amount_sum or 0),
                "legacy_record_ids_sample": list(legacy_record_ids or []),
            }
        )
    return rows


ensure_allowed_db()
artifact_root = resolve_artifact_root()
output_json = artifact_root / "fresh_db_receipt_income_missing_project_anchor_write_result_v1.json"
uid = env.uid  # noqa: F821
Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821

missing_refs = fetch_missing_project_refs()
created_projects = []
updated_fact_count = 0
for item in missing_refs:
    legacy_project_id = item["legacy_project_id"]
    project = Project.search(
        ["|", ("legacy_project_id", "=", legacy_project_id), ("legacy_parent_id", "=", legacy_project_id)],
        limit=1,
    )
    if not project:
        vals = {"name": item["project_name"]}
        if "legacy_project_id" in Project._fields:
            vals["legacy_project_id"] = legacy_project_id
        if "legacy_parent_id" in Project._fields:
            vals["legacy_parent_id"] = legacy_project_id
        if "legacy_note" in Project._fields:
            vals["legacy_note"] = (
                "历史收款事实补锚；source=C_JFHKLR; "
                f"fact_count={item['fact_count']}; amount_sum={item['amount_sum']}"
            )
        project = Project.create(vals)
        created_projects.append(
            {
                "legacy_project_id": legacy_project_id,
                "project_id": project.id,
                "project_name": project.display_name,
                "fact_count": item["fact_count"],
                "amount_sum": item["amount_sum"],
                "legacy_record_ids_sample": item["legacy_record_ids_sample"],
            }
        )

    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_legacy_receipt_residual_fact
           SET project_id = %s,
               write_uid = %s,
               write_date = NOW()
         WHERE active
           AND COALESCE(amount, 0) > 0
           AND project_id IS NULL
           AND project_legacy_id = %s
        """,
        [project.id, uid, legacy_project_id],
    )
    updated_fact_count += env.cr.rowcount  # noqa: F821

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_receipt_income_missing_project_anchor_write",
    "database": env.cr.dbname,  # noqa: F821
    "missing_project_ref_count": len(missing_refs),
    "created_project_count": len(created_projects),
    "updated_residual_fact_count": updated_fact_count,
    "created_projects": created_projects,
    "decision": "valid_legacy_receipt_income_requires_project_anchor_before_runtime_projection",
}
write_json(output_json, payload)
print("FRESH_DB_RECEIPT_INCOME_MISSING_PROJECT_ANCHOR_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
