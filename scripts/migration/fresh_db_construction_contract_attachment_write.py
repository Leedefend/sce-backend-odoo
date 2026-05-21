#!/usr/bin/env python3
"""Replay full construction contract attachment URL assets from legacy file index."""

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
        if (candidate / "tmp/raw/contract/contract.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
RAW_CSV = Path(os.getenv("CONSTRUCTION_CONTRACT_RAW_CSV", str(REPO_ROOT / "tmp/raw/contract/contract.csv")))
FILE_INDEX_CSV = Path(os.getenv("MIGRATION_FILE_INDEX_CSV", str(ARTIFACT_ROOT / "fresh_db_legacy_file_index_replay_payload_v1.csv")))
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_construction_contract_attachment_write_result_v1.json"
DETAIL_CSV = ARTIFACT_ROOT / "fresh_db_construction_contract_attachment_write_detail_v1.csv"
ATTACHMENT_MARKER = "[migration:construction_contract_attachment_full]"
EXPECTED_VISIBLE_ROWS = int(os.getenv("CONSTRUCTION_CONTRACT_INCOME_VISIBLE_EXPECTED_ROWS", "1532"))


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "legacy_contract_id",
        "legacy_document_no",
        "legacy_contract_no",
        "contract_id",
        "legacy_attachment_bill_id",
        "attachment_count",
        "attachment_names",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def legacy_file_url(row: dict[str, str]) -> str:
    path = clean(row.get("file_path")) or clean(row.get("preview_path"))
    if path:
        return "legacy-file://" + path.lstrip("/")
    return "legacy-file-id://" + clean(row.get("legacy_file_id"))


def is_legacy_income_visible(row: dict[str, str]) -> bool:
    return (
        clean(row.get("DEL")) != "1"
        and clean(row.get("DJZT")) in {"2", "1", ""}
        and bool(clean(row.get("HTBT")))
        and bool(clean(row.get("FBF")))
    )


ensure_allowed_db()

Contract = env["construction.contract"].sudo()  # noqa: F821
Attachment = env["ir.attachment"].sudo()  # noqa: F821

raw_rows = read_csv(RAW_CSV)
visible_rows = [row for row in raw_rows if clean(row.get("Id")) and is_legacy_income_visible(row)]
file_rows = read_csv(FILE_INDEX_CSV)

if len({clean(row.get("Id")) for row in visible_rows}) != EXPECTED_VISIBLE_ROWS:
    raise RuntimeError({"unexpected_visible_rows": len(visible_rows), "expected": EXPECTED_VISIBLE_ROWS})

active_files_by_bill: dict[str, list[dict[str, str]]] = {}
for row in file_rows:
    bill_id = clean(row.get("bill_id"))
    if not bill_id or clean(row.get("active")) != "1" or not clean(row.get("file_name")):
        continue
    active_files_by_bill.setdefault(bill_id, []).append(row)

old_attachments = Attachment.search(
    [
        ("res_model", "=", "construction.contract"),
        ("description", "ilike", ATTACHMENT_MARKER),
    ]
)
removed = len(old_attachments)
old_attachments.unlink()

created = 0
matched_contracts = 0
missing_contracts: list[dict[str, object]] = []
unmatched_bills: list[dict[str, object]] = []
detail_rows: list[dict[str, object]] = []

for row in visible_rows:
    legacy_id = clean(row.get("Id"))
    document_no = clean(row.get("DJBH"))
    contract_no = clean(row.get("HTBH"))
    bill_id = clean(row.get("f_FJ"))
    contract = Contract.search([("legacy_contract_id", "=", legacy_id)], limit=1)
    if not contract:
        missing_contracts.append({"legacy_contract_id": legacy_id, "legacy_document_no": document_no, "legacy_contract_no": contract_no})
        continue
    files = active_files_by_bill.get(bill_id, [])
    if not files:
        unmatched_bills.append(
            {
                "legacy_contract_id": legacy_id,
                "legacy_document_no": document_no,
                "legacy_contract_no": contract_no,
                "legacy_attachment_bill_id": bill_id,
            }
        )
        continue
    matched_contracts += 1
    names: list[str] = []
    attachment_lines: list[str] = []
    seen_keys: set[str] = set()
    for file_row in files:
        legacy_file_key = clean(file_row.get("legacy_file_key")) or clean(file_row.get("legacy_file_id"))
        if legacy_file_key in seen_keys:
            continue
        seen_keys.add(legacy_file_key)
        name = clean(file_row.get("file_name"))
        url = legacy_file_url(file_row)
        names.append(name)
        attachment_lines.append(f"{name} | {url}")
        Attachment.create(
            {
                "name": name,
                "type": "url",
                "url": url,
                "res_model": "construction.contract",
                "res_id": contract.id,
                "description": (
                    f"{ATTACHMENT_MARKER} legacy_contract_id={legacy_id}; "
                    f"document_no={document_no}; bill_id={bill_id}; "
                    f"legacy_file_key={legacy_file_key}; source_table={clean(file_row.get('source_table'))}"
                ),
                "mimetype": clean(file_row.get("extension")),
            }
        )
        created += 1
    if attachment_lines:
        contract.write({"attachment_text": "\n".join(attachment_lines)})
    detail_rows.append(
        {
            "legacy_contract_id": legacy_id,
            "legacy_document_no": document_no,
            "legacy_contract_no": contract_no,
            "contract_id": contract.id,
            "legacy_attachment_bill_id": bill_id,
            "attachment_count": len(names),
            "attachment_names": "\n".join(names),
        }
    )

env.cr.commit()  # noqa: F821

post_count = Attachment.search_count(
    [
        ("res_model", "=", "construction.contract"),
        ("description", "ilike", ATTACHMENT_MARKER),
    ]
)
post_errors = []
if missing_contracts:
    post_errors.append({"error": "missing_target_contracts", "actual": len(missing_contracts), "expected": 0})
if post_count != created:
    post_errors.append({"error": "attachment_count_not_expected", "actual": post_count, "expected": created})

status = "PASS" if not post_errors else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_construction_contract_attachment_write",
    "database": env.cr.dbname,  # noqa: F821
    "legacy_source_table": "T_ProjectContract_Out",
    "legacy_file_join": "T_ProjectContract_Out.f_FJ = legacy_file_index.bill_id",
    "raw_visible_rows": len(visible_rows),
    "matched_contract_rows": matched_contracts,
    "unmatched_contract_rows": len(unmatched_bills),
    "attachment_removed_rows": removed,
    "attachment_created_rows": created,
    "attachment_count": post_count,
    "missing_contract_rows": len(missing_contracts),
    "unmatched_bills_sample": unmatched_bills[:20],
    "missing_contracts_sample": missing_contracts[:20],
    "post_errors": post_errors,
    "artifacts": {"detail_csv": str(DETAIL_CSV)},
}
write_csv(DETAIL_CSV, detail_rows)
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_CONSTRUCTION_CONTRACT_ATTACHMENT_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if status != "PASS":
    raise RuntimeError({"construction_contract_attachment_write_failed": post_errors})
