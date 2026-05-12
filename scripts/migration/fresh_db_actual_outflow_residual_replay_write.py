#!/usr/bin/env python3
"""Replay residual actual-outflow parent carriers into allowed databases."""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_actual_outflow_residual_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def as_float(value: str) -> float:
    try:
        return float(value or 0.0)
    except ValueError:
        return 0.0


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in {"False", "false", "None", "none", "NULL", "null"} else text


def legacy_user_names() -> dict[str, str]:
    names: dict[str, str] = {}
    if "sc.legacy.user.profile" not in env.registry:  # noqa: F821
        return names
    Profile = env["sc.legacy.user.profile"].sudo().with_context(active_test=False)  # noqa: F821
    for profile in Profile.search([]):
        legacy_id = clean(profile.legacy_user_id)
        name = clean(profile.display_name) or clean(profile.user_id.name)
        if legacy_id and name:
            names[legacy_id] = name
    return names


LEGACY_ACTUAL_OUTFLOW_ID_RE = re.compile(r"legacy_actual_outflow_id=([0-9a-fA-F]+)")

REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_actual_outflow_residual_replay_payload_v1.csv"
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_actual_outflow_residual_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_actual_outflow_residual_replay_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["expected_rows"])

Request = env["payment.request"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821
legacy_user_name_by_id = legacy_user_names()

project_ids = sorted({row["legacy_project_id"] for row in rows if row.get("legacy_project_id")})
project_map = {
    rec["legacy_project_id"]: rec["id"]
    for rec in Project.search_read([("legacy_project_id", "in", project_ids)], ["legacy_project_id"])
}

partner_ids = sorted({row["legacy_partner_id"] for row in rows if row.get("legacy_partner_id")})
partner_map: dict[str, int] = {}
if partner_ids:
    for rec in Partner.search_read([("legacy_partner_id", "in", partner_ids)], ["legacy_partner_id"]):
        partner_map.setdefault(rec["legacy_partner_id"], rec["id"])

existing_actual_ids: set[str] = set()
existing_actual_id_to_request = {}
for rec in Request.search_read([("note", "ilike", "[migration:actual_outflow_core]")], ["note"]):
    note = rec.get("note") or ""
    match = LEGACY_ACTUAL_OUTFLOW_ID_RE.search(note)
    if match:
        legacy_actual_id = match.group(1)
        existing_actual_ids.add(legacy_actual_id)
        existing_actual_id_to_request[legacy_actual_id] = rec["id"]

created = 0
updated_existing = 0
created_partner_anchors = 0
created_project_anchors = 0
skipped = 0
blocked: list[dict[str, str]] = []
buffer: list[dict[str, object]] = []
batch_size = 500

for index, row in enumerate(rows, start=1):
    legacy_actual_id = row["legacy_actual_outflow_id"]
    if legacy_actual_id in existing_actual_ids:
        request = Request.browse(existing_actual_id_to_request.get(legacy_actual_id)).exists()
        if request:
            creator_legacy_user_id = clean(row.get("creator_legacy_user_id"))
            creator_name = clean(row.get("creator_name")) or legacy_user_name_by_id.get(creator_legacy_user_id, "")
            vals = {}
            if not request.legacy_source_table:
                vals["legacy_source_table"] = "T_FK_Supplier"
            if not request.legacy_record_id:
                vals["legacy_record_id"] = legacy_actual_id
            if creator_legacy_user_id and not request.creator_legacy_user_id:
                vals["creator_legacy_user_id"] = creator_legacy_user_id
            if creator_name and not request.creator_name:
                vals["creator_name"] = creator_name
            if clean(row.get("created_time")) and not request.created_time:
                vals["created_time"] = clean(row.get("created_time"))[:19]
            if vals:
                request.write(vals)
                updated_existing += 1
        skipped += 1
        continue

    project_id = project_map.get(row.get("legacy_project_id") or "")
    if not project_id and row.get("legacy_project_id"):
        project = Project.create(
            {
                "name": row.get("legacy_project_name") or row.get("legacy_project_id"),
                "legacy_project_id": row.get("legacy_project_id"),
                "short_name": row.get("legacy_project_name") or False,
                "project_environment": "legacy_residual_actual_outflow",
                "other_system_code": row.get("legacy_project_code") or False,
                "legacy_state": "residual_anchor_for_actual_outflow_line",
            }
        )
        project_id = project.id
        project_map[row["legacy_project_id"]] = project_id
        created_project_anchors += 1
    if not project_id:
        blocked.append(
            {
                "line": str(index),
                "reason": "missing_project_anchor",
                "legacy_actual_outflow_id": legacy_actual_id,
                "legacy_project_id": row.get("legacy_project_id", ""),
            }
        )
        continue

    legacy_partner_id = row.get("legacy_partner_id") or ""
    synthetic_partner = False
    if not legacy_partner_id:
        synthetic_partner = True
        legacy_partner_id = f"actual_outflow_missing_partner:{legacy_actual_id}"
    partner_id = partner_map.get(legacy_partner_id)
    if not partner_id and legacy_partner_id:
        partner = Partner.create(
            {
                "name": row.get("legacy_partner_name") or f"Unknown legacy supplier-{row.get('document_no') or legacy_actual_id[:8]}",
                "company_type": "company",
                "is_company": True,
                "legacy_partner_id": legacy_partner_id,
                "legacy_partner_source": "actual_outflow_residual_counterparty",
                "legacy_partner_name": row.get("legacy_partner_name") or False,
                "legacy_source_evidence": (
                    "T_FK_Supplier residual parent required by T_FK_Supplier_CB"
                    + ("; source row had empty f_SupplierID" if synthetic_partner else "")
                ),
            }
        )
        partner_id = partner.id
        partner_map[legacy_partner_id] = partner_id
        created_partner_anchors += 1

    if not partner_id:
        blocked.append(
            {
                "line": str(index),
                "reason": "missing_partner_anchor",
                "legacy_actual_outflow_id": legacy_actual_id,
                "legacy_partner_id": legacy_partner_id,
            }
        )
        continue

    vals = {
        "type": row.get("type") or "pay",
        "project_id": project_id,
        "partner_id": partner_id,
        "amount": as_float(row.get("amount", "")),
        "note": row["note"],
        "legacy_source_table": "T_FK_Supplier",
        "legacy_record_id": legacy_actual_id,
    }
    if row.get("date_request"):
        vals["date_request"] = row["date_request"]
    creator_legacy_user_id = clean(row.get("creator_legacy_user_id"))
    creator_name = clean(row.get("creator_name")) or legacy_user_name_by_id.get(creator_legacy_user_id, "")
    if creator_legacy_user_id:
        vals["creator_legacy_user_id"] = creator_legacy_user_id
    if creator_name:
        vals["creator_name"] = creator_name
    if clean(row.get("created_time")):
        vals["created_time"] = clean(row.get("created_time"))[:19]
    buffer.append(vals)
    existing_actual_ids.add(legacy_actual_id)
    if len(buffer) >= batch_size:
        Request.create(buffer)
        created += len(buffer)
        buffer = []

if buffer:
    Request.create(buffer)
    created += len(buffer)

env.cr.commit()  # noqa: F821
status = "PASS" if created + skipped + len(blocked) == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_actual_outflow_residual_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "updated_existing": updated_existing,
    "created_partner_anchors": created_partner_anchors,
    "created_project_anchors": created_project_anchors,
    "skipped_existing": skipped,
    "blocked_rows": len(blocked),
    "blocked_samples": blocked[:50],
    "db_writes": created + created_partner_anchors + created_project_anchors,
    "decision": "actual_outflow_residual_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_ACTUAL_OUTFLOW_RESIDUAL_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
