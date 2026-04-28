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


def split_account_label(value: object) -> tuple[str, str]:
    text = clean(value)
    left, sep, right = text.partition("/")
    if sep:
        name = clean(left) or clean(right)
        account_no = clean(right).replace(" ", "")
        return name, account_no
    normalized = text.replace(" ", "")
    if normalized and normalized.replace("-", "").isdigit():
        return text, normalized
    return text, ""


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
    for rec in Model.search_read([("source_key", "!=", False)], ["source_key"], limit=False)
}
existing_by_key = {
    clean(rec["source_key"]): rec
    for rec in Model.search_read([("source_key", "!=", False)], ["source_key", "account_id"], limit=False)
}
project_legacy_ids = sorted({clean(row.get("project_legacy_id")) for row in rows if clean(row.get("project_legacy_id"))})
project_map = {
    rec["legacy_project_id"]: rec["id"]
    for rec in Project.search_read([("legacy_project_id", "in", project_legacy_ids)], ["legacy_project_id"], limit=False)
    if rec.get("legacy_project_id")
}
account_legacy_ids = sorted({clean(row.get("account_legacy_id")) for row in rows if clean(row.get("account_legacy_id"))})
account_map = {
    rec["legacy_account_id"]: rec["id"]
    for rec in Account.search_read([("legacy_account_id", "in", account_legacy_ids)], ["legacy_account_id"], limit=False)
    if rec.get("legacy_account_id")
}
supplemental_accounts: dict[str, dict[str, object]] = {}
for row in rows:
    legacy_id = clean(row.get("account_legacy_id"))
    if not legacy_id or legacy_id in account_map or legacy_id in supplemental_accounts:
        continue
    name, account_no = split_account_label(row.get("account_name"))
    project_legacy_id = clean(row.get("project_legacy_id"))
    supplemental_accounts[legacy_id] = {
        "legacy_account_id": legacy_id,
        "project_legacy_id": project_legacy_id,
        "project_name": clean(row.get("project_name")),
        "project_id": project_map.get(project_legacy_id) or False,
        "name": name or legacy_id,
        "account_no": account_no or False,
        "account_type": "历史来源账户",
        "opening_balance": 0.0,
        "source_table": "legacy_account_transaction_source",
        "note": "source=legacy account transaction replay; missing from C_Base_ZHSZ",
        "active": True,
    }
if supplemental_accounts:
    Account.create(list(supplemental_accounts.values()))
    account_map = {
        rec["legacy_account_id"]: rec["id"]
        for rec in Account.search_read([("legacy_account_id", "in", account_legacy_ids)], ["legacy_account_id"], limit=False)
        if rec.get("legacy_account_id")
    }
account_records = Account.search_read([], ["legacy_account_id", "name", "account_no", "active"], limit=False)
account_no_map: dict[str, int] = {}
account_name_map: dict[str, int] = {}
account_active_by_id: dict[int, bool] = {}
account_no_candidates: dict[str, list[dict[str, object]]] = {}
account_name_candidates: dict[str, list[dict[str, object]]] = {}
for rec in account_records:
    account_active_by_id[rec["id"]] = bool(rec.get("active"))
    account_no = clean(rec.get("account_no")).replace(" ", "")
    if account_no:
        account_no_candidates.setdefault(account_no, []).append(rec)
    name = clean(rec.get("name")).lower()
    if name:
        account_name_candidates.setdefault(name, []).append(rec)


def choose_unique_or_active(candidates: list[dict[str, object]]) -> int | None:
    if len(candidates) == 1:
        return int(candidates[0]["id"])
    active_candidates = [item for item in candidates if item.get("active")]
    if len(active_candidates) == 1:
        return int(active_candidates[0]["id"])
    return None


for key, candidates in account_no_candidates.items():
    account_id = choose_unique_or_active(candidates)
    if account_id:
        account_no_map[key] = account_id
for key, candidates in account_name_candidates.items():
    account_id = choose_unique_or_active(candidates)
    if account_id:
        account_name_map[key] = account_id


def resolve_account_id(row: dict[str, str]) -> int | None:
    account_text = clean(row.get("account_name"))
    name_part, _, no_part = account_text.partition("/")
    normalized_full = account_text.replace(" ", "")
    if normalized_full and normalized_full in account_no_map:
        return account_no_map[normalized_full]
    normalized_no = clean(no_part).replace(" ", "")
    if normalized_no and normalized_no in account_no_map:
        return account_no_map[normalized_no]
    normalized_name = clean(name_part or account_text).lower()
    if normalized_name and normalized_name in account_name_map:
        return account_name_map[normalized_name]
    legacy_id = clean(row.get("account_legacy_id"))
    return account_map.get(legacy_id)

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
        existing_account = existing.get("account_id")
        existing_account_id = existing_account[0] if existing_account else None
        should_update_account = bool(account_id and not existing_account_id)
        if account_id and existing_account_id and existing_account_id != account_id:
            should_update_account = not account_active_by_id.get(existing_account_id, False)
        if should_update_account:
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
    "supplemental_accounts_created": len(supplemental_accounts),
    "decision": "legacy_account_transaction_replay_complete" if created + skipped == len(rows) else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_ACCOUNT_TRANSACTION_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
