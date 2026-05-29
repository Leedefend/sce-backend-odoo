#!/usr/bin/env python3
"""Backfill hash-named payment request projects from C_ZFSQGL.f_XMMC export."""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path


DEFAULT_SOURCE = Path("/tmp/c_zfsqgl_project_names.csv")
HEX_ID_RE = re.compile(r"^[0-9a-fA-F]{24,64}$")


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def source_csv() -> Path:
    candidates = [
        os.getenv("C_ZFSQGL_PROJECT_NAMES_CSV"),
        str(DEFAULT_SOURCE),
        "/mnt/extra-addons/tmp/raw/payment/c_zfsqgl_project_names.csv",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    raise RuntimeError({"c_zfsqgl_project_names_csv_missing": [item for item in candidates if item]})


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


ensure_allowed_db()

path = source_csv()
names_by_legacy_project_id: dict[str, set[str]] = {}
with path.open("r", encoding="utf-8-sig", newline="") as handle:
    sample = handle.read(4096)
    handle.seek(0)
    dialect = csv.Sniffer().sniff(sample, delimiters=",|\t") if sample else csv.excel
    for row in csv.DictReader(handle, dialect=dialect):
        legacy_project_id = clean(row.get("f_XMID"))
        project_name = clean(row.get("f_XMMC"))
        if legacy_project_id and project_name:
            names_by_legacy_project_id.setdefault(legacy_project_id, set()).add(project_name)

Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
Request = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821

project_ids = Request.search([("legacy_source_table", "=", "C_ZFSQGL"), ("project_id", "!=", False)]).mapped("project_id").ids
projects = Project.browse(project_ids).exists()

updated = 0
skipped_non_hash_name = 0
skipped_no_source_name = 0
skipped_conflict = 0
conflicts = []
samples = []

for project in projects:
    legacy_project_id = clean(getattr(project, "legacy_project_id", ""))
    current_name = clean(project.name)
    if not legacy_project_id or not HEX_ID_RE.fullmatch(current_name) or current_name.lower() != legacy_project_id.lower():
        skipped_non_hash_name += 1
        continue
    candidate_names = sorted(names_by_legacy_project_id.get(legacy_project_id, set()))
    if not candidate_names:
        skipped_no_source_name += 1
        continue
    if len(candidate_names) > 1:
        skipped_conflict += 1
        conflicts.append({"project_id": project.id, "legacy_project_id": legacy_project_id, "names": candidate_names[:10]})
        continue
    new_name = candidate_names[0]
    project.write({"name": new_name})
    updated += 1
    if len(samples) < 20:
        samples.append({"project_id": project.id, "legacy_project_id": legacy_project_id, "old_name": current_name, "new_name": new_name})

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS" if not conflicts else "REVIEW",
    "mode": "payment_request_project_name_from_c_zfsqgl_backfill_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_csv": str(path),
    "source_project_ids": len(names_by_legacy_project_id),
    "candidate_projects": len(projects),
    "updated_projects": updated,
    "skipped_non_hash_name": skipped_non_hash_name,
    "skipped_no_source_name": skipped_no_source_name,
    "skipped_conflict": skipped_conflict,
    "conflicts": conflicts[:50],
    "samples": samples,
}
print("PAYMENT_REQUEST_PROJECT_NAME_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
