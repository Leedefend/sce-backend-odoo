#!/usr/bin/env python3
"""Backfill receipt request creator facts from the raw receipt source."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "tmp/raw/receipt/receipt.csv").exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("ARTIFACT_ROOT")
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


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def first_nonempty(row: dict[str, str], fields: list[str]) -> str:
    for field in fields:
        value = clean(row.get(field))
        if value:
            return value
    return ""


def parse_datetime(value: str) -> str:
    raw = clean(value)
    if not raw:
        return ""
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return ""


def read_receipt_facts(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    facts: dict[str, dict[str, str]] = {}
    for row in rows:
        legacy_id = clean(row.get("Id"))
        if not legacy_id:
            continue
        facts[legacy_id] = {
            "creator_legacy_user_id": first_nonempty(row, ["LRRID", "f_LRRID"]),
            "creator_name": first_nonempty(row, ["LRR", "f_LRR"]),
            "created_time": parse_datetime(first_nonempty(row, ["LRSJ", "f_LRSJ"])),
        }
    return facts


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "").split(",") if item.strip()}
if allowlist and env.cr.dbname not in allowlist:  # noqa: F821
    raise RuntimeError({"db_name_not_allowed_for_visible_surface_write": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821

source_csv = repo_root() / "tmp/raw/receipt/receipt.csv"
facts = read_receipt_facts(source_csv)
Request = env["payment.request"].sudo()  # noqa: F821
requests = Request.search([("type", "=", "receive"), ("note", "ilike", "[migration:receipt_core]")])

updated = 0
with_creator_source = 0
with_created_source = 0
for request in requests:
    note = request.note or ""
    marker = "legacy_receipt_id="
    if marker not in note:
        continue
    legacy_id = note.split(marker, 1)[1].split(";", 1)[0].split()[0].strip()
    fact = facts.get(legacy_id)
    if not fact:
        continue
    vals = {}
    if fact["creator_legacy_user_id"] and not request.creator_legacy_user_id:
        vals["creator_legacy_user_id"] = fact["creator_legacy_user_id"]
    if fact["creator_name"]:
        with_creator_source += 1
        if not request.creator_name:
            vals["creator_name"] = fact["creator_name"]
    if fact["created_time"]:
        with_created_source += 1
        if not request.created_time:
            vals["created_time"] = fact["created_time"]
    if vals:
        request.write(vals)
        updated += 1

env.cr.commit()  # noqa: F821
payload = {
    "status": "PASS",
    "mode": "visible_surface_receipt_core_creator_normalize_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_csv": str(source_csv),
    "source_fact_rows": len(facts),
    "receipt_request_rows": len(requests),
    "source_with_creator_name": with_creator_source,
    "source_with_created_time": with_created_source,
    "updated_rows": updated,
    "receipt_requests_with_creator_name": Request.search_count([("type", "=", "receive"), ("note", "ilike", "[migration:receipt_core]"), ("creator_name", "!=", False)]),
    "receipt_requests_with_created_time": Request.search_count([("type", "=", "receive"), ("note", "ilike", "[migration:receipt_core]"), ("created_time", "!=", False)]),
    "decision": "receipt_core_creator_facts_backfilled_from_raw_source",
}
write_json(artifact_root() / "visible_surface_receipt_core_creator_normalize_write_result_v1.json", payload)
print("VISIBLE_SURFACE_RECEIPT_CORE_CREATOR_NORMALIZE_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
