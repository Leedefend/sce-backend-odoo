#!/usr/bin/env python3
"""Backfill legacy entry metadata onto existing project records."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def _repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def _clean(value: object) -> str:
    if value is None or value is False:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"false", "none", "null"} else text


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _first_useful_source(Model, project, creator_field: str, time_field: str):
    order = f"{time_field} asc, id asc" if time_field in Model._fields else "id asc"
    records = Model.search([("project_id", "=", project.id)], order=order, limit=50)
    for record in records:
        source_created_by = _clean(record[creator_field])
        source_created_at = record[time_field] if time_field in record._fields else False
        if (not project.legacy_source_created_by and source_created_by) or (
            not project.legacy_source_created_at and source_created_at
        ):
            return record
    return Model.browse()


db_name = env.cr.dbname  # noqa: F821
allowlist = {
    item.strip()
    for item in os.getenv("PROJECT_LEGACY_ENTRY_BACKFILL_DB_ALLOWLIST", db_name).split(",")
    if item.strip()
}
if db_name not in allowlist:
    raise RuntimeError({"db_name_not_allowed_for_project_legacy_entry_backfill": db_name, "allowlist": sorted(allowlist)})

root = _repo_root()
input_csv = Path(os.getenv("PROJECT_LEGACY_ENTRY_BACKFILL_CSV", str(root / "artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv")))
artifact_root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(root / "artifacts/backend")))
output_json = artifact_root / "project_legacy_entry_backfill_result.json"

Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
rows = _read_rows(input_csv)
updated: list[dict[str, object]] = []
skipped = {
    "missing_entry_fields": 0,
    "no_match": 0,
    "ambiguous": 0,
    "unchanged": 0,
    "no_source_fact": 0,
    "technical_false_cleared": 0,
}

technical_false_domain = [
    "|",
    ("legacy_source_created_by", "in", ["False", "false", "None", "none", "NULL", "null"]),
    ("legacy_source_created_at", "in", ["False", "false", "None", "none", "NULL", "null"]),
]
for project in Project.search(technical_false_domain):
    vals = {}
    if not _clean(project.legacy_source_created_by):
        vals["legacy_source_created_by"] = False
    if not _clean(project.legacy_source_created_at):
        vals["legacy_source_created_at"] = False
    if vals:
        project.write(vals)
        skipped["technical_false_cleared"] += 1

for row in rows:
    created_by = _clean(row.get("legacy_source_created_by"))
    created_by_id = _clean(row.get("legacy_source_created_by_id"))
    created_at = _clean(row.get("legacy_source_created_at"))
    if not any((created_by, created_by_id, created_at)):
        skipped["missing_entry_fields"] += 1
        continue

    identity_domains = []
    legacy_project_id = _clean(row.get("legacy_project_id"))
    legacy_project_code = _clean(row.get("legacy_project_code"))
    other_system_code = _clean(row.get("other_system_code"))
    name = _clean(row.get("name"))
    if legacy_project_id:
        identity_domains.append([("legacy_project_id", "=", legacy_project_id)])
    if legacy_project_code:
        identity_domains.append(["|", ("legacy_project_code", "=", legacy_project_code), ("project_code", "=", legacy_project_code)])
    if other_system_code:
        identity_domains.append([("other_system_code", "=", other_system_code)])
    if name:
        identity_domains.append([("name", "=", name)])

    matches = Project.browse()
    for domain in identity_domains:
        matches |= Project.search(domain)
    matches = matches.exists()
    if not matches:
        skipped["no_match"] += 1
        continue
    if len(matches) > 1:
        skipped["ambiguous"] += 1
        continue

    project = matches[0]
    vals = {}
    if created_by and not project.legacy_source_created_by:
        vals["legacy_source_created_by"] = created_by
    if created_by_id and not project.legacy_source_created_by_id:
        vals["legacy_source_created_by_id"] = created_by_id
    if created_at and not project.legacy_source_created_at:
        vals["legacy_source_created_at"] = created_at
    if not vals:
        skipped["unchanged"] += 1
        continue
    project.write(vals)
    updated.append(
        {
            "id": project.id,
            "name": project.name or "",
            "project_code": project.project_code or "",
            "legacy_project_id": project.legacy_project_id or "",
            "source": "project_anchor_payload",
            "updated_fields": sorted(vals),
        }
    )

source_models = [
    ("sc.legacy.enterprise.business.fact", "creator_name", "created_time"),
    ("sc.legacy.scbs.fact.staging", "creator_name", "created_time"),
    ("sc.legacy.purchase.contract.fact", "creator_name", "created_time"),
    ("sc.legacy.account.transaction.line", "creator_name", "created_time"),
    ("sc.legacy.construction.diary.line", "creator_name", "created_time"),
    ("sc.legacy.expense.reimbursement.line", "creator_name", "created_time"),
    ("sc.legacy.fund.confirmation.line", "creator_name", "created_time"),
    ("sc.legacy.invoice.registration.line", "creator_name", "created_time"),
    ("sc.legacy.payment.residual.fact", "creator_name", "created_time"),
    ("sc.legacy.receipt.residual.fact", "creator_name", "created_time"),
    ("sc.legacy.salary.line", "creator_name", "created_time"),
    ("sc.legacy.supplier.contract.pricing.fact", "creator_name", "created_time"),
    ("sc.legacy.task.evidence", "creator_name", "created_time"),
    ("sc.legacy.user.project.scope", "created_by_name", "created_time"),
]
missing_projects = Project.search(
    [
        "|",
        ("legacy_source_created_by", "=", False),
        ("legacy_source_created_at", "=", False),
    ]
)
for project in missing_projects:
    candidate = None
    candidate_model = ""
    for model_name, creator_field, time_field in source_models:
        if model_name not in env:  # noqa: F821
            continue
        Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
        if "project_id" not in Model._fields or creator_field not in Model._fields:
            continue
        record = _first_useful_source(Model, project, creator_field, time_field)
        if not record:
            continue
        candidate = record
        candidate_model = model_name
        break
    if not candidate:
        skipped["no_source_fact"] += 1
        continue
    vals = {}
    source_created_by = _clean(candidate[creator_field])
    source_created_at = candidate[time_field] if time_field in candidate._fields else False
    if source_created_by and not project.legacy_source_created_by:
        vals["legacy_source_created_by"] = source_created_by
    if source_created_at and not project.legacy_source_created_at:
        vals["legacy_source_created_at"] = source_created_at
    if not vals:
        skipped["unchanged"] += 1
        continue
    project.write(vals)
    updated.append(
        {
            "id": project.id,
            "name": project.name or "",
            "project_code": project.project_code or "",
            "legacy_project_id": project.legacy_project_id or "",
            "source": candidate_model,
            "updated_fields": sorted(vals),
        }
    )

env.cr.commit()  # noqa: F821
result = {
    "status": "PASS",
    "mode": "project_legacy_entry_backfill",
    "database": db_name,
    "input_csv": str(input_csv),
    "input_rows": len(rows),
    "updated_rows": len(updated),
    "skipped": skipped,
    "updated_samples": updated[:20],
    "artifact": str(output_json),
}
try:
    _write_json(output_json, result)
except OSError as exc:
    result["artifact_write_error"] = str(exc)
print("PROJECT_LEGACY_ENTRY_BACKFILL=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
