#!/usr/bin/env python3
"""Replay legacy account transaction lines into the neutral carrier."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_account_transaction_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def as_float(value: object) -> float:
    text = clean(value)
    return float(text) if text else 0.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")
    except PermissionError:
        fallback = Path("/tmp") / path.name
        payload["artifact_fallback"] = str(fallback)
        fallback.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_legacy_account_transaction_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_account_transaction_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_account_transaction_replay_write_result_v1.json"

ensure_allowed_db()
manifest = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)

Model = env["sc.legacy.account.transaction.line"].sudo().with_context(active_test=False)  # noqa: F821
Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
Account = env["sc.legacy.account.master"].sudo().with_context(active_test=False)  # noqa: F821

existing_keys = {
    clean(rec["source_key"])
    for rec in Model.search_read([("source_key", "!=", False)], ["source_key"])
}
existing_by_key = {
    clean(rec["source_key"]): rec
    for rec in Model.search_read([("source_key", "!=", False)], ["source_key", "account_id"])
}
project_legacy_ids = sorted({clean(row.get("project_legacy_id")) for row in rows if clean(row.get("project_legacy_id"))})
project_map = {
    rec["legacy_project_id"]: rec["id"]
    for rec in Project.search_read([("legacy_project_id", "in", project_legacy_ids)], ["legacy_project_id"])
    if rec.get("legacy_project_id")
}
account_legacy_ids = sorted({clean(row.get("account_legacy_id")) for row in rows if clean(row.get("account_legacy_id"))})
account_map = {
    rec["legacy_account_id"]: rec["id"]
    for rec in Account.search_read([("legacy_account_id", "in", account_legacy_ids)], ["legacy_account_id"])
    if rec.get("legacy_account_id")
}
account_records = Account.search_read([], ["legacy_account_id", "name", "account_no"])
account_no_map: dict[str, int] = {}
account_name_map: dict[str, int] = {}
ambiguous_account_nos: set[str] = set()
ambiguous_account_names: set[str] = set()
for rec in account_records:
    account_no = clean(rec.get("account_no")).replace(" ", "")
    if account_no:
        if account_no in account_no_map:
            ambiguous_account_nos.add(account_no)
        else:
            account_no_map[account_no] = rec["id"]
    name = clean(rec.get("name")).lower()
    if name:
        if name in account_name_map:
            ambiguous_account_names.add(name)
        else:
            account_name_map[name] = rec["id"]
for key in ambiguous_account_nos:
    account_no_map.pop(key, None)
for key in ambiguous_account_names:
    account_name_map.pop(key, None)


def resolve_account_id(row: dict[str, str]) -> int | None:
    legacy_id = clean(row.get("account_legacy_id"))
    if legacy_id in account_map:
        return account_map[legacy_id]
    account_text = clean(row.get("account_name"))
    name_part, _, no_part = account_text.partition("/")
    normalized_no = clean(no_part).replace(" ", "")
    if normalized_no and normalized_no in account_no_map:
        return account_no_map[normalized_no]
    normalized_name = clean(name_part or account_text).lower()
    return account_name_map.get(normalized_name)

created = 0
skipped = 0
missing_account = 0
updated_existing = 0
buffer: list[dict[str, object]] = []
batch_size = 500
for row in rows:
    source_key = clean(row.get("source_key"))
    if not source_key:
        skipped += 1
        continue
    account_legacy_id = clean(row.get("account_legacy_id"))
    account_id = resolve_account_id(row)
    if source_key in existing_keys:
        existing = existing_by_key.get(source_key) or {}
        if account_id and not existing.get("account_id"):
            Model.browse(existing["id"]).write({"account_id": account_id})
            updated_existing += 1
        skipped += 1
        continue
    if not account_id:
        missing_account += 1
    vals = {
        "source_key": source_key,
        "source_table": clean(row.get("source_table")) or "C_FKGL_ZHJZJWL",
        "legacy_record_id": clean(row.get("legacy_record_id")),
        "document_no": clean(row.get("document_no")),
        "transaction_date": clean(row.get("transaction_date")) or False,
        "document_state": clean(row.get("document_state")),
        "deleted_flag": clean(row.get("deleted_flag")) or "0",
        "project_legacy_id": clean(row.get("project_legacy_id")),
        "project_name": clean(row.get("project_name")),
        "project_id": project_map.get(clean(row.get("project_legacy_id"))) or False,
        "account_legacy_id": account_legacy_id,
        "account_id": account_id or False,
        "account_name": clean(row.get("account_name")),
        "counterparty_account_legacy_id": clean(row.get("counterparty_account_legacy_id")),
        "counterparty_account_name": clean(row.get("counterparty_account_name")),
        "direction": clean(row.get("direction")),
        "metric_bucket": clean(row.get("metric_bucket")) or "account_transfer",
        "amount": as_float(row.get("amount")),
        "category": clean(row.get("category")),
        "source_summary": clean(row.get("source_summary")),
        "note": clean(row.get("note")),
        "import_batch": "legacy_account_transaction_v1",
        "active": clean(row.get("active")) != "0",
    }
    buffer.append(vals)
    existing_keys.add(source_key)
    if len(buffer) >= batch_size:
        Model.create(buffer)
        created += len(buffer)
        buffer = []

if buffer:
    Model.create(buffer)
    created += len(buffer)

env.cr.commit()  # noqa: F821

payload = {
    "mode": "fresh_db_legacy_account_transaction_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "manifest_rows": int(manifest.get("rows") or 0),
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "updated_existing": updated_existing,
    "missing_account": missing_account,
    "decision": "legacy_account_transaction_replay_complete" if created + skipped == len(rows) else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_ACCOUNT_TRANSACTION_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
