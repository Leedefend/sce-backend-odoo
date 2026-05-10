"""Project legacy A_SCBS daily progress facts into sc.construction.diary.

Dry-run by default. Set MIGRATION_APPLY=1 or APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


SOURCE_MODEL = "legacy.main.A_SCBS_JDRB"
SOURCE_TABLE = "A_SCBS_JDRB"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path.cwd() / "artifacts/migration", Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("/tmp")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def clean(value) -> str:
    return str(value or "").strip()


def to_date(value: str):
    return value[:10] if value else False


def to_datetime(value: str):
    if not value:
        return False
    return value.replace("T", " ")[:19]


def raw_json(record) -> dict[str, object]:
    try:
        return json.loads(record.raw_payload or "{}")
    except json.JSONDecodeError:
        return {}


def project_by_legacy_id(cache: dict[str, int | bool], legacy_id: str, name: str):
    key = clean(legacy_id) or "__name__:" + clean(name)
    if key in cache:
        return cache[key]
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    project = False
    if clean(legacy_id):
        project = Project.search([("legacy_project_id", "=", clean(legacy_id))], limit=1)
    if not project and clean(name):
        project = Project.search([("name", "=", clean(name))], limit=1)
    cache[key] = project.id if project else False
    return cache[key]


def main() -> None:
    apply = os.getenv("APPLY") == "1" or os.getenv("MIGRATION_APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "legacy_a_scbs_construction_diary_projection_plan_v1.csv"
    residual_csv = artifacts / "legacy_a_scbs_construction_diary_projection_residual_v1.csv"
    result_json = artifacts / "legacy_a_scbs_construction_diary_projection_result_v1.json"

    Residual = env["sc.legacy.business.fact.residual"].sudo().with_context(active_test=False)  # noqa: F821
    Diary = env["sc.construction.diary"].sudo().with_context(active_test=False)  # noqa: F821
    rows = Residual.search([("source_table", "=", SOURCE_TABLE)], order="document_date, id")
    existing = Diary.search_read([("legacy_source_model", "=", SOURCE_MODEL)], ["legacy_record_id"])
    existing_ids = {row["legacy_record_id"] for row in existing}
    project_cache: dict[str, int | bool] = {}
    plan_rows: list[dict[str, object]] = []
    residual_rows: list[dict[str, object]] = []
    planned = 0
    created = 0
    skipped_existing = 0
    blocked = 0

    for row in rows:
        payload = raw_json(row)
        source_id = clean(payload.get("Id")) or row.legacy_record_id.split("#", 1)[0]
        project_id = project_by_legacy_id(project_cache, row.project_legacy_id, row.project_name)
        description = clean(payload.get("JDMS"))
        reason = ""
        if not row.active:
            reason = "inactive_legacy_record"
        elif not project_id:
            reason = "missing_project_anchor"
        elif not description:
            reason = "missing_progress_description"

        if source_id in existing_ids:
            action = "skip_existing"
            skipped_existing += 1
        elif reason:
            action = "blocked"
            blocked += 1
            residual_rows.append(
                {
                    "legacy_record_id": source_id,
                    "document_no": row.document_no,
                    "project_legacy_id": row.project_legacy_id,
                    "project_name": row.project_name,
                    "description": description,
                    "reason": reason,
                }
            )
        else:
            action = "create_construction_diary"
            planned += 1
            if apply:
                diary = Diary.create(
                    {
                        "name": row.document_no or "A_SCBS进度日报-%s" % source_id,
                        "source_origin": "legacy",
                        "state": "legacy_confirmed",
                        "project_id": project_id,
                        "date_diary": to_datetime(str(payload.get("DJRQ") or row.document_date or "")),
                        "report_period_start": to_date(str(payload.get("DJRQ") or row.document_date or "")),
                        "report_period_end": to_date(str(payload.get("DJRQ") or row.document_date or "")),
                        "document_no": row.document_no,
                        "title": row.document_no or "保盛进度日报",
                        "diary_type": "日报表",
                        "category": "进度日报",
                        "construction_unit": clean(payload.get("SGBW")),
                        "handler_name": clean(payload.get("TXR")) or clean(payload.get("LRR")),
                        "description": description,
                        "note": "\n".join(
                            [
                                "旧系统保盛进度日报迁入。",
                                "source_table=%s" % SOURCE_TABLE,
                                "legacy_record_id=%s" % source_id,
                                "legacy_pid=%s" % (row.legacy_pid or ""),
                                "legacy_creator=%s(%s)" % (clean(payload.get("LRR")), clean(payload.get("LRRID"))),
                            ]
                        ),
                        "legacy_source_model": SOURCE_MODEL,
                        "legacy_source_table": SOURCE_TABLE,
                        "legacy_record_id": source_id,
                        "legacy_header_id": source_id,
                        "legacy_document_state": clean(payload.get("DJZT")),
                        "legacy_attachment_ref": clean(payload.get("FJ")),
                    }
                )
                created += 1 if diary else 0

        plan_rows.append(
            {
                "legacy_record_id": source_id,
                "document_no": row.document_no,
                "project_legacy_id": row.project_legacy_id,
                "project_name": row.project_name,
                "description": description,
                "target_model": "sc.construction.diary",
                "action": action,
                "reason": reason,
            }
        )

    if apply:
        env.cr.commit()  # noqa: F821

    fieldnames = [
        "legacy_record_id",
        "document_no",
        "project_legacy_id",
        "project_name",
        "description",
        "target_model",
        "action",
        "reason",
    ]
    write_csv(plan_csv, plan_rows, fieldnames)
    write_csv(residual_csv, residual_rows, [key for key in fieldnames if key not in {"target_model", "action"}])
    result = {
        "status": "PASS",
        "mode": "legacy_a_scbs_construction_diary_projection",
        "apply": apply,
        "source_rows": len(rows),
        "planned_rows": planned,
        "created": created,
        "skipped_existing": skipped_existing,
        "blocked_rows": blocked,
        "plan_csv": str(plan_csv),
        "residual_csv": str(residual_csv),
    }
    write_json(result_json, result)
    print("LEGACY_A_SCBS_CONSTRUCTION_DIARY_PROJECTION=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
