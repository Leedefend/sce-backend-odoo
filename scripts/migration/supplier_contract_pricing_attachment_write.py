#!/usr/bin/env python3
"""Backfill supplier contract pricing attachments from the locked SCBS55 surface."""

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
        if (candidate / "artifacts/migration/scbs55_supplier_contract_attachment_display_lock_v1.json").exists():
            return candidate
    return Path.cwd()


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except PermissionError:
        fallback = Path("/tmp") / path.name
        fallback.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        payload["output_json"] = str(fallback)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "legacy_contract_id",
        "contract_id",
        "attachment_bill_id",
        "attachment_display",
        "attachment_count",
        "attachment_names",
    ]
    target = path
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        handle = target.open("w", encoding="utf-8", newline="")
    except PermissionError:
        target = Path("/tmp") / path.name
        handle = target.open("w", encoding="utf-8", newline="")
    with handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def legacy_file_url(row: dict[str, object]) -> str:
    file_path = clean(row.get("file_path")) or clean(row.get("preview_path"))
    if file_path:
        return "legacy-file://" + file_path.lstrip("/")
    return "legacy-file-id://" + clean(row.get("legacy_file_id"))


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
LOCK_JSON = Path(
    os.getenv(
        "SCBS55_SUPPLIER_ATTACHMENT_DISPLAY_LOCK",
        str(ARTIFACT_ROOT / "scbs55_supplier_contract_attachment_display_lock_v1.json"),
    )
)
OUTPUT_JSON = ARTIFACT_ROOT / "supplier_contract_pricing_attachment_write_result_v1.json"
DETAIL_CSV = ARTIFACT_ROOT / "supplier_contract_pricing_attachment_write_detail_v1.csv"
ATTACHMENT_MARKER = "[migration:supplier_contract_pricing_attachment]"
TARGET_MODEL = "sc.legacy.supplier.contract.pricing.fact"

ensure_allowed_db()
if not LOCK_JSON.exists():
    raise RuntimeError({"supplier_attachment_display_lock_missing": str(LOCK_JSON)})

lock_payload = json.loads(LOCK_JSON.read_text(encoding="utf-8"))
lock_rows = lock_payload.get("rows") if isinstance(lock_payload.get("rows"), list) else []
expected_rows = int(lock_payload.get("row_count") or lock_payload.get("count") or len(lock_rows))
if len(lock_rows) != expected_rows:
    raise RuntimeError({"supplier_attachment_lock_row_count_mismatch": len(lock_rows), "expected": expected_rows})

Fact = env[TARGET_MODEL].sudo().with_context(active_test=False)  # noqa: F821
Attachment = env["ir.attachment"].sudo()  # noqa: F821
FileIndex = env["sc.legacy.file.index"].sudo().with_context(active_test=False)  # noqa: F821

legacy_ids = [clean(row.get("Id")) for row in lock_rows if clean(row.get("Id"))]
facts = Fact.search([("legacy_contract_id", "in", legacy_ids)])
fact_by_legacy = {clean(rec.legacy_contract_id): rec for rec in facts}

bill_ids = sorted({clean(row.get("f_FJ")) for row in lock_rows if clean(row.get("f_FJ"))})
files_by_bill: dict[str, list[dict[str, object]]] = {}
for rec in FileIndex.search_read(
    [("bill_id", "in", bill_ids), ("active", "=", True)],
    ["bill_id", "legacy_file_key", "legacy_file_id", "file_name", "file_path", "preview_path", "extension", "source_table"],
    order="id",
):
    bill_id = clean(rec.get("bill_id"))
    if bill_id:
        files_by_bill.setdefault(bill_id, []).append(rec)

old_attachments = Attachment.search([("res_model", "=", TARGET_MODEL), ("description", "ilike", ATTACHMENT_MARKER)])
removed = len(old_attachments)
old_attachments.unlink()

created = 0
records_with_files = 0
records_with_display = 0
missing_fact_rows: list[dict[str, object]] = []
unmatched_file_rows: list[dict[str, object]] = []
detail_rows: list[dict[str, object]] = []
buffer: list[dict[str, object]] = []
batch_size = 500

for row in lock_rows:
    legacy_id = clean(row.get("Id"))
    attachment_bill_id = clean(row.get("f_FJ"))
    display = clean(row.get("f_FJ_FJ"))
    fact = fact_by_legacy.get(legacy_id)
    if not fact:
        if len(missing_fact_rows) < 50:
            missing_fact_rows.append({"legacy_contract_id": legacy_id, "attachment_bill_id": attachment_bill_id})
        continue
    if display:
        records_with_display += 1
        fact.write({"attachment_text": display})
    files = files_by_bill.get(attachment_bill_id, [])
    if not files:
        if display and len(unmatched_file_rows) < 50:
            unmatched_file_rows.append(
                {"legacy_contract_id": legacy_id, "attachment_bill_id": attachment_bill_id, "attachment_display": display}
            )
        continue
    records_with_files += 1
    names: list[str] = []
    seen_keys: set[str] = set()
    for file_row in files:
        legacy_file_key = clean(file_row.get("legacy_file_key")) or clean(file_row.get("legacy_file_id"))
        if legacy_file_key in seen_keys:
            continue
        seen_keys.add(legacy_file_key)
        name = clean(file_row.get("file_name")) or legacy_file_key
        names.append(name)
        buffer.append(
            {
                "name": name,
                "type": "url",
                "url": legacy_file_url(file_row),
                "res_model": TARGET_MODEL,
                "res_id": fact.id,
                "description": (
                    f"{ATTACHMENT_MARKER} legacy_contract_id={legacy_id}; "
                    f"bill_id={attachment_bill_id}; legacy_file_key={legacy_file_key}; "
                    f"source_table={clean(file_row.get('source_table'))}"
                ),
                "mimetype": clean(file_row.get("extension")),
            }
        )
        if len(buffer) >= batch_size:
            Attachment.create(buffer)
            created += len(buffer)
            buffer = []
    detail_rows.append(
        {
            "legacy_contract_id": legacy_id,
            "contract_id": int(fact.id),
            "attachment_bill_id": attachment_bill_id,
            "attachment_display": display,
            "attachment_count": len(names),
            "attachment_names": "\n".join(names),
        }
    )

if buffer:
    Attachment.create(buffer)
    created += len(buffer)

env.cr.commit()  # noqa: F821

post_count = Attachment.search_count([("res_model", "=", TARGET_MODEL), ("description", "ilike", ATTACHMENT_MARKER)])
post_errors = []
if missing_fact_rows:
    post_errors.append({"error": "missing_supplier_contract_pricing_facts", "count": len(missing_fact_rows)})
if post_count != created:
    post_errors.append({"error": "attachment_count_not_expected", "actual": post_count, "expected": created})

status = "PASS" if not post_errors else "FAIL"
payload = {
    "status": status,
    "mode": "supplier_contract_pricing_attachment_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_model": TARGET_MODEL,
    "legacy_source_table": "T_GYSHT_INFO",
    "legacy_file_join": "T_GYSHT_INFO.f_FJ = legacy_file_index.bill_id",
    "lock_rows": len(lock_rows),
    "fact_rows": len(facts),
    "records_with_display": records_with_display,
    "records_with_files": records_with_files,
    "attachment_removed_rows": removed,
    "attachment_created_rows": created,
    "attachment_count": post_count,
    "unmatched_file_rows": max(records_with_display - records_with_files, 0),
    "missing_fact_rows": len(missing_fact_rows),
    "unmatched_file_sample": unmatched_file_rows,
    "missing_fact_sample": missing_fact_rows,
    "post_errors": post_errors,
    "artifacts": {"detail_csv": str(DETAIL_CSV)},
}
write_csv(DETAIL_CSV, detail_rows)
write_json(OUTPUT_JSON, payload)
print("SUPPLIER_CONTRACT_PRICING_ATTACHMENT_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if status != "PASS":
    raise RuntimeError({"supplier_contract_pricing_attachment_write_failed": post_errors})
