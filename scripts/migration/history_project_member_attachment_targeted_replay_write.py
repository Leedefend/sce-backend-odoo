#!/usr/bin/env python3
"""Replay targeted project-member neutral rows required by legacy attachments."""

from __future__ import annotations

import csv
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
        if (candidate / "artifacts/migration/history_project_member_attachment_targeted_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def resolve_user_id(row: dict[str, str], user_model) -> int | None:
    legacy_user_ref = clean(row.get("legacy_user_ref"))
    if legacy_user_ref:
        for login in [legacy_user_ref, f"legacy_{legacy_user_ref}"]:
            matches = user_model.search([("login", "=", login)], limit=2)
            if len(matches) == 1:
                return matches.id
            if len(matches) > 1:
                raise RuntimeError({"duplicate_login_matches": login, "user_ids": matches.ids})
    return None


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/history_project_member_attachment_targeted_replay_payload_v1.csv"
INPUT_JSON = REPO_ROOT / "artifacts/migration/history_project_member_attachment_targeted_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "history_project_member_attachment_targeted_replay_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["payload_rows"])

Model = env["sc.project.member.staging"].sudo().with_context(active_test=False)  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821

existing_legacy_ids = {
    rec["legacy_member_id"]
    for rec in Model.search_read([("legacy_member_id", "!=", False)], ["legacy_member_id"])
    if rec.get("legacy_member_id")
}
project_ids = sorted({clean(row.get("legacy_project_id")) for row in rows if clean(row.get("legacy_project_id"))})
project_map = {
    rec["legacy_project_id"]: rec["id"]
    for rec in Project.search_read([("legacy_project_id", "in", project_ids)], ["legacy_project_id"])
    if rec.get("legacy_project_id")
}

created = 0
skipped = 0
buffer: list[dict[str, object]] = []
batch_size = 500
for row in rows:
    legacy_member_id = clean(row.get("legacy_member_id"))
    if legacy_member_id in existing_legacy_ids:
        skipped += 1
        continue
    legacy_project_id = clean(row.get("legacy_project_id"))
    project_id = project_map.get(legacy_project_id)
    if not project_id:
        raise RuntimeError({"missing_project_anchor": legacy_project_id, "legacy_member_id": legacy_member_id})
    user_id = resolve_user_id(row, Users)
    if not user_id:
        raise RuntimeError({"missing_user_anchor": clean(row.get("legacy_user_ref")), "legacy_member_id": legacy_member_id})
    buffer.append(
        {
            "legacy_member_id": legacy_member_id,
            "legacy_project_id": legacy_project_id,
            "legacy_user_ref": clean(row.get("legacy_user_ref")),
            "project_id": project_id,
            "user_id": user_id,
            "legacy_role_text": "",
            "role_fact_status": clean(row.get("role_fact_status")) or "missing",
            "import_batch": clean(row.get("import_batch")) or "project_member_neutral_xml_v1",
            "evidence": clean(row.get("evidence")) or "history_project_member_attachment_targeted_replay",
            "notes": clean(row.get("notes")) or "neutral staging only; role fact missing",
            "active": clean(row.get("active")).lower() not in {"0", "false", "no", "n"},
        }
    )
    existing_legacy_ids.add(legacy_member_id)
    if len(buffer) >= batch_size:
        Model.create(buffer)
        created += len(buffer)
        buffer = []

if buffer:
    Model.create(buffer)
    created += len(buffer)

env.cr.commit()  # noqa: F821
status = "PASS" if created + skipped == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "history_project_member_attachment_targeted_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "db_writes": created,
    "decision": "project_member_attachment_targeted_replay_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("HISTORY_PROJECT_MEMBER_ATTACHMENT_TARGETED_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
