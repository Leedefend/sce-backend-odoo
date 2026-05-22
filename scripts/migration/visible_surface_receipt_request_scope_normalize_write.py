#!/usr/bin/env python3
"""Normalize visible receive-request scope from legacy receipt categories."""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path


EXCLUDED_CATEGORIES = {"材料款", "开票税金", "保险费", "代理服务费", "代理费"}
MIGRATION_MARKER = "[migration:receipt_core]"


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "tmp/raw/receipt/receipt.csv").exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or str(repo_root() / "artifacts/migration"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u3000", " ").strip())


def legacy_receipt_id(note: object) -> str:
    match = re.search(r"legacy_receipt_id=([^;\s]+)", clean(note))
    return match.group(1) if match else ""


def load_receipt_categories(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            receipt_id = clean(row.get("Id"))
            if receipt_id:
                rows[receipt_id] = clean(row.get("f_SRLBName"))
    return rows


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


ensure_allowed_db()

Request = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
categories = load_receipt_categories(repo_root() / "tmp/raw/receipt/receipt.csv")
requests = Request.search([("type", "=", "receive"), ("note", "ilike", MIGRATION_MARKER)])

include_ids: list[int] = []
exclude_ids: list[int] = []
missing_raw_ids: list[int] = []
excluded_by_category: dict[str, int] = {category: 0 for category in sorted(EXCLUDED_CATEGORIES)}

for request in requests:
    receipt_id = legacy_receipt_id(request.note)
    category = categories.get(receipt_id)
    if category is None:
        missing_raw_ids.append(request.id)
        include_ids.append(request.id)
        continue
    if category in EXCLUDED_CATEGORIES:
        exclude_ids.append(request.id)
        excluded_by_category[category] += 1
    else:
        include_ids.append(request.id)

to_deactivate = Request.browse(exclude_ids).filtered(lambda rec: rec.active)
to_activate = Request.browse(include_ids).filtered(lambda rec: not rec.active)

if to_deactivate:
    to_deactivate.write({"active": False})
if to_activate:
    to_activate.write({"active": True})
env.cr.commit()  # noqa: F821

visible_count = Request.search_count([("type", "=", "receive"), ("active", "=", True)])
visible_migration_count = Request.search_count(
    [("type", "=", "receive"), ("active", "=", True), ("note", "ilike", MIGRATION_MARKER)]
)
hidden_excluded_count = Request.search_count(
    [("type", "=", "receive"), ("active", "=", False), ("note", "ilike", MIGRATION_MARKER)]
)

payload = {
    "status": "PASS",
    "mode": "visible_surface_receipt_request_scope_normalize_write",
    "database": env.cr.dbname,  # noqa: F821
    "excluded_categories": sorted(EXCLUDED_CATEGORIES),
    "migration_receipt_requests": len(requests),
    "include_rows": len(include_ids),
    "exclude_rows": len(exclude_ids),
    "excluded_by_category": excluded_by_category,
    "activated_rows": len(to_activate),
    "deactivated_rows": len(to_deactivate),
    "missing_raw_rows_kept_visible": len(missing_raw_ids),
    "visible_receive_request_count": visible_count,
    "visible_migration_receive_request_count": visible_migration_count,
    "hidden_excluded_migration_receive_request_count": hidden_excluded_count,
}

write_json(artifact_root() / "visible_surface_receipt_request_scope_normalize_write_result_v1.json", payload)
print("VISIBLE_SURFACE_RECEIPT_REQUEST_SCOPE_NORMALIZE_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
