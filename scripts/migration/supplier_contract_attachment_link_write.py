#!/usr/bin/env python3
"""Create visible supplier-contract attachment links without downloading files."""

from __future__ import annotations

import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path.cwd()))
from scripts.verify.online_capture_security import require_online_capture  # noqa: E402


SOURCE_MODEL = "sc.legacy.supplier.contract.pricing.fact"
WRAPPER_MODEL = "construction.contract.expense"
ONLINE_BASE_URL = os.getenv("SUPPLIER_CONTRACT_ONLINE_ATTACHMENT_BASE_URL") or os.getenv("OLD_SCBS_BASE_URL", "")
SOURCE_MARKER = "[migration:supplier_contract_attachment_link]"
WRAPPER_MARKER = "[migration:direct_supplier_contract_pricing_to_expense_execution]"
OUTPUT_JSON_NAME = "supplier_contract_attachment_link_write_result_v1.json"


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_supplier_attachment_link": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/scbs55_supplier_contract_attachment_display_lock_v1.json").exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(repo_root() / "artifacts/migration")
    candidates.append(Path(f"/tmp/supplier_contract_attachment_link/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/supplier_contract_attachment_link/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scalar(sql: str, params: tuple | list | None = None) -> int:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return int(row[0] or 0) if row else 0


def lock_rows_by_legacy_id() -> dict[str, dict[str, object]]:
    lock_path = Path(
        os.getenv(
            "SCBS55_SUPPLIER_ATTACHMENT_DISPLAY_LOCK",
            str(repo_root() / "artifacts/migration/scbs55_supplier_contract_attachment_display_lock_v1.json"),
        )
    )
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    return {clean(row.get("Id")): row for row in rows if clean(row.get("Id"))}


def fetch_online_files(bill_id: str) -> list[dict[str, object]]:
    require_online_capture(("scbs",))
    url = f"{ONLINE_BASE_URL}/api/System/FileApi/GetFileByBillId?BillId={bill_id}"
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rows = payload.get("Data") if isinstance(payload, dict) else []
    result = []
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("DEL") or "0") not in ("0", "False", "false", ""):
            continue
        if clean(row.get("ATTR_PATH")):
            result.append(row)
    return result


ensure_allowed_db()
Attachment = env["ir.attachment"].sudo()  # noqa: F821
lock_by_legacy = lock_rows_by_legacy_id()

env.cr.execute(  # noqa: F821
    """
    SELECT f.id, f.legacy_contract_id, e.id AS wrapper_id
      FROM sc_legacy_supplier_contract_pricing_fact f
      JOIN construction_contract c
        ON c.type = 'in'
       AND c.legacy_contract_id = f.legacy_contract_id
      JOIN construction_contract_expense e
        ON e.contract_id = c.id
     WHERE f.legacy_source_table = 'T_GYSHT_INFO'
       AND COALESCE(f.attachment_text, '') ~ '^附件\\([1-9][0-9]*\\)$'
       AND NOT EXISTS (
            SELECT 1
              FROM ir_attachment a
             WHERE a.res_model = %s
               AND a.res_id = f.id
       )
     ORDER BY f.id
    """,
    [SOURCE_MODEL],
)
missing_rows = []
for fact_id, legacy_contract_id, wrapper_id in env.cr.fetchall():  # noqa: F821
    legacy_contract_id = clean(legacy_contract_id)
    lock_row = lock_by_legacy.get(legacy_contract_id)
    bill_id = clean(lock_row.get("f_FJ")) if lock_row else ""
    if bill_id:
        missing_rows.append(
            {
                "fact_id": int(fact_id),
                "legacy_contract_id": legacy_contract_id,
                "wrapper_id": int(wrapper_id),
                "bill_id": bill_id,
            }
        )

created_source_links = 0
created_wrapper_links = 0
online_missing = []
online_failed = []

for item in missing_rows:
    try:
        online_files = fetch_online_files(item["bill_id"])
    except Exception as exc:
        if len(online_failed) < 50:
            online_failed.append({"legacy_contract_id": item["legacy_contract_id"], "bill_id": item["bill_id"], "error": str(exc)})
        continue
    if not online_files:
        if len(online_missing) < 50:
            online_missing.append({"legacy_contract_id": item["legacy_contract_id"], "bill_id": item["bill_id"]})
        continue
    for row in online_files:
        file_id = clean(row.get("ID")) or clean(row.get("FileId")) or item["bill_id"]
        url = clean(row.get("ATTR_PATH"))
        name = clean(row.get("ATTR_NAME")) or file_id
        mimetype = mimetypes.guess_type(name or url)[0] or "application/octet-stream"
        source_attachment = Attachment.search(
            [("res_model", "=", SOURCE_MODEL), ("res_id", "=", item["fact_id"]), ("type", "=", "url"), ("url", "=", url)],
            limit=1,
        )
        if not source_attachment:
            source_attachment = Attachment.create(
                {
                    "name": name,
                    "type": "url",
                    "url": url,
                    "res_model": SOURCE_MODEL,
                    "res_id": item["fact_id"],
                    "description": f"{SOURCE_MARKER} legacy_contract_id={item['legacy_contract_id']}; bill_id={item['bill_id']}; online_file_id={file_id}",
                    "mimetype": mimetype,
                }
            )
            created_source_links += 1
        wrapper_attachment = Attachment.search(
            [
                ("res_model", "=", WRAPPER_MODEL),
                ("res_id", "=", item["wrapper_id"]),
                ("type", "=", "url"),
                ("url", "=", url),
            ],
            limit=1,
        )
        if not wrapper_attachment:
            Attachment.create(
                {
                    "name": name,
                    "type": "url",
                    "url": url,
                    "res_model": WRAPPER_MODEL,
                    "res_id": item["wrapper_id"],
                    "description": f"{WRAPPER_MARKER} source_model={SOURCE_MODEL}; source_id={item['fact_id']}; source_attachment_id={source_attachment.id}; online_link_only=1",
                    "mimetype": mimetype,
                }
            )
            created_wrapper_links += 1

env.cr.commit()  # noqa: F821

remaining_visible_text_without_wrapper = scalar(
    """
    SELECT COUNT(*)
      FROM construction_contract_expense e
      JOIN construction_contract c ON c.id = e.contract_id
     WHERE c.state IN ('confirmed', 'running')
       AND COALESCE(c.legacy_visible_attachment, c.attachment_text, '') <> ''
       AND NOT EXISTS (
            SELECT 1
              FROM ir_attachment a
             WHERE a.res_model = %s
               AND a.res_id = e.id
       )
    """,
    [WRAPPER_MODEL],
)
wrapper_attachment_count = Attachment.search_count([("res_model", "=", WRAPPER_MODEL)])

payload = {
    "status": "PASS" if remaining_visible_text_without_wrapper == 0 and not online_failed and not online_missing else "FAIL",
    "mode": "supplier_contract_attachment_link_write",
    "database": env.cr.dbname,  # noqa: F821
    "online_base_url": ONLINE_BASE_URL,
    "missing_link_rows_before": len(missing_rows),
    "created_source_links": created_source_links,
    "created_wrapper_links": created_wrapper_links,
    "remaining_visible_text_without_wrapper_attachment_count": remaining_visible_text_without_wrapper,
    "wrapper_attachment_count": wrapper_attachment_count,
    "online_failed_sample": online_failed,
    "online_missing_sample": online_missing,
}
write_json(artifact_root() / OUTPUT_JSON_NAME, payload)
print("SUPPLIER_CONTRACT_ATTACHMENT_LINK_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise RuntimeError(payload)
