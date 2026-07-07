# -*- coding: utf-8 -*-
"""Mirror online legacy attachments into local custody and file index.

Run through ``odoo shell``. This is the migration bridge from online old-system
fallback to durable local files. It scans business records with visible legacy
attachments, downloads every file returned by the old ``GetFileByBillId`` API,
writes it below a configured local root, and upserts ``sc.legacy.file.index``.
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from odoo.addons.smart_core.handlers.file_download import (
    _fetch_online_legacy_file_by_bill_id,
    _legacy_file_index_relative_path,
    _resolve_legacy_file_path,
)


MODEL = os.getenv("LEGACY_ONLINE_MIRROR_MODEL", "sc.legacy.direct.acceptance.fact")
LABELS = {
    item.strip()
    for item in re.split(r"[,，]", os.getenv("LEGACY_ONLINE_MIRROR_LABELS", ""))
    if item.strip()
}
LIMIT = int(os.getenv("LEGACY_ONLINE_MIRROR_LIMIT", "0") or "0")
MAX_UNIQUE_REFS = int(os.getenv("LEGACY_ONLINE_MIRROR_MAX_UNIQUE_REFS", "0") or "0")
MAX_FILES = int(os.getenv("LEGACY_ONLINE_MIRROR_MAX_FILES", "0") or "0")
EXAMPLE_LIMIT = int(os.getenv("LEGACY_ONLINE_MIRROR_EXAMPLE_LIMIT", "30") or "30")
COMMIT_EVERY_FILES = int(os.getenv("LEGACY_ONLINE_MIRROR_COMMIT_EVERY_FILES", "20") or "0")
SKIP_LOCAL_OK = os.getenv("LEGACY_ONLINE_MIRROR_SKIP_LOCAL_OK", "0").strip().lower() in {"1", "true", "yes", "on"}
REQUIRE_VISIBLE_LABEL = os.getenv("LEGACY_ONLINE_MIRROR_REQUIRE_VISIBLE_LABEL", "1").strip().lower() in {"1", "true", "yes", "on"}
DOWNLOAD_TIMEOUT = int(os.getenv("LEGACY_ONLINE_MIRROR_DOWNLOAD_TIMEOUT", "120") or "120")
APPLY = os.getenv("LEGACY_ONLINE_MIRROR_APPLY", "1").strip().lower() in {"1", "true", "yes", "on"}
MIRROR_ROOT = Path(os.getenv("LEGACY_ONLINE_MIRROR_ROOT", "/mnt/artifacts/legacy-online-mirror"))
OUTPUT_JSON = Path(os.getenv("LEGACY_ONLINE_MIRROR_OUTPUT", "/tmp/legacy_online_attachment_mirror_result_v1.json"))
ATTACHMENT_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")
ATTACHMENT_LABEL_RE = re.compile(r"^附件\([1-9]\d*\)$")
INDEX_FIELDS = ("bill_id", "legacy_file_id", "legacy_file_key", "business_id", "legacy_pid")
LOCAL_OK_CACHE = {}


def clean(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def raw_payload(record):
    try:
        payload = json.loads(getattr(record, "raw_payload", "") or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def visible_attachment_text(record):
    payload = raw_payload(record)
    for field in ("f_FJ", "FJ_FJ", "f_FJ_FJ"):
        value = clean(payload.get(field))
        if ATTACHMENT_LABEL_RE.match(value):
            return value
    for index in range(1, 61):
        field = f"legacy_visible_{index:02d}"
        if field not in getattr(record, "_fields", {}):
            continue
        value = clean(getattr(record, field, ""))
        if ATTACHMENT_LABEL_RE.match(value):
            return value
    return ""


def attachment_ref(record):
    ref = clean(getattr(record, "attachment_ref", ""))
    if ref:
        return ref
    payload = raw_payload(record)
    for field in ("FJ", "f_FJ"):
        value = clean(payload.get(field))
        if ATTACHMENT_ID_RE.match(value):
            return value
    return ""


def online_base_url(record):
    source_label = online_source_label(record)
    if source_label == "online_old_scbsly":
        return "https://www.builderp.cn/SCBSLY_V2"
    return "https://www.builderp.cn/SCBS"


def online_source_label(record):
    source_system = clean(getattr(record, "source_system", ""))
    source_table = clean(getattr(record, "source_table", ""))
    legacy_source_table = clean(getattr(record, "legacy_source_table", ""))
    for value in (source_system, source_table, legacy_source_table):
        if value.startswith("online_old_scbsly"):
            return "online_old_scbsly"
        if value.startswith("online_old_scbs"):
            return "online_old_scbs"
    return "online_old_scbs"


def fetch_all_online_files(bill_id, base_url):
    url = f"{base_url.rstrip('/')}/api/System/FileApi/GetFileByBillId?BillId={bill_id}"
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rows = payload.get("Data") if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return []
    result = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("DEL") or "0") not in ("0", "False", "false", ""):
            continue
        if clean(row.get("ATTR_PATH")):
            result.append(row)
    return result


def extension_for(row):
    name = clean(row.get("ATTR_NAME"))
    suffix = Path(name).suffix
    if suffix:
        return suffix
    path_suffix = Path(clean(row.get("ATTR_PATH")).split("?", 1)[0]).suffix
    if path_suffix:
        return path_suffix
    return mimetypes.guess_extension(clean(row.get("CONTENT_TYPE"))) or ".bin"


def relative_path_for(row, source_system):
    bill_id = clean(row.get("BILLID")) or "no_bill"
    file_id = clean(row.get("ID")) or clean(row.get("FileId")) or bill_id
    safe_source = re.sub(r"[^A-Za-z0-9_.-]+", "_", source_system or "online_old")
    return str(Path(safe_source) / bill_id[:2] / bill_id / f"{file_id}{extension_for(row)}")


def download_to_local(row, relative_path):
    target = MIRROR_ROOT / relative_path
    if target.exists() and target.stat().st_size > 0:
        return target
    if not APPLY:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_target = target.with_suffix(target.suffix + ".part")
    with urlopen(Request(clean(row.get("ATTR_PATH")), headers={"User-Agent": "Mozilla/5.0"}), timeout=DOWNLOAD_TIMEOUT) as response:
        tmp_target.write_bytes(response.read())
    tmp_target.replace(target)
    return target


def safe_download_to_local(row, relative_path):
    try:
        return download_to_local(row, relative_path), None
    except Exception as exc:
        return None, str(exc)


def existing_local_ok_for_ref(ref):
    if not ref:
        return False
    if ref in LOCAL_OK_CACHE:
        return LOCAL_OK_CACHE[ref]
    FileIndex = env["sc.legacy.file.index"].sudo().with_context(active_test=False)  # noqa: F821
    domain = [("active", "=", True), "|", "|", "|", "|"]
    domain.extend((field, "=", ref) for field in INDEX_FIELDS)
    for item in FileIndex.search(domain, order="upload_time desc, id desc"):
        relative = _legacy_file_index_relative_path(item)
        if relative and _resolve_legacy_file_path(relative):
            LOCAL_OK_CACHE[ref] = True
            return True
    LOCAL_OK_CACHE[ref] = False
    return False


def upsert_file_index(row, relative_path, source_system, record):
    FileIndex = env["sc.legacy.file.index"].sudo().with_context(active_test=False)  # noqa: F821
    file_id = clean(row.get("ID")) or clean(row.get("FileId")) or clean(row.get("BILLID"))
    key = f"ONLINE:{source_system}:{file_id}"
    values = {
        "legacy_file_key": key,
        "source_table": f"{source_system}:online_file_api",
        "legacy_file_id": file_id,
        "legacy_pid": clean(getattr(record, "legacy_record_id", "")) or False,
        "bill_id": clean(row.get("BILLID")) or False,
        "bill_type": clean(getattr(record, "acceptance_label", "")) or False,
        "business_id": clean(row.get("BUSINESSID")) or False,
        "file_system_data_id": clean(row.get("PID")) or False,
        "file_name": clean(row.get("ATTR_NAME")) or file_id,
        "file_path": relative_path,
        "preview_path": False,
        "file_md5": clean(row.get("FILEMD5")) or False,
        "file_size": int(float(clean(row.get("FILESIZE")) or 0)),
        "extension": extension_for(row).lstrip(".").lower(),
        "uploader_legacy_user_id": clean(row.get("LRRID")) or False,
        "uploader_name": clean(row.get("LRR")) or False,
        "encrypted_flag": clean(row.get("ISENCRYPT")) or False,
        "temporary_flag": clean(row.get("IsTemporary")) or False,
        "active": True,
    }
    env.cr.execute("SELECT id FROM sc_legacy_file_index WHERE legacy_file_key = %s LIMIT 1", [key])  # noqa: F821
    row_id = env.cr.fetchone()  # noqa: F821
    existing = FileIndex.browse(row_id[0]) if row_id else FileIndex.browse()
    if existing:
        if APPLY:
            existing.write(values)
        return "updated"
    if APPLY:
        try:
            FileIndex.create(values)
        except Exception:
            env.cr.rollback()  # noqa: F821
            existing = FileIndex.search([("legacy_file_key", "=", key)], limit=1)
            if not existing:
                raise
            existing.write(values)
            return "updated_after_conflict"
    return "created"


def main():
    if MODEL not in env:  # noqa: F821
        raise RuntimeError(f"model not found: {MODEL}")
    Model = env[MODEL].sudo().with_context(active_test=False)  # noqa: F821
    domain = [("active", "=", True)] if "active" in Model._fields else []
    if LABELS and "acceptance_label" in Model._fields:
        domain.append(("acceptance_label", "in", sorted(LABELS)))
    records = Model.search(domain, limit=LIMIT or None, order="id")
    counts = Counter()
    examples = []
    seen_refs = {}
    committed_files = 0
    stop_requested = False
    total_records = len(records)
    for record_index, record in enumerate(records):
        if stop_requested:
            counts["records_skipped_after_stop"] += total_records - record_index
            break
        counts["records_checked"] += 1
        if REQUIRE_VISIBLE_LABEL and not visible_attachment_text(record):
            counts["records_without_visible_attachment"] += 1
            continue
        ref = attachment_ref(record)
        if not ref:
            counts["visible_missing_ref"] += 1
            continue
        if ref in seen_refs:
            counts["records_reused_ref"] += 1
            continue
        if SKIP_LOCAL_OK and existing_local_ok_for_ref(ref):
            seen_refs[ref] = []
            counts["refs_skipped_local_ok"] += 1
            continue
        if MAX_UNIQUE_REFS and len(seen_refs) >= MAX_UNIQUE_REFS:
            counts["records_skipped_by_max_unique_refs"] += 1
            continue
        source_system = online_source_label(record)
        base_url = online_base_url(record)
        try:
            files = fetch_all_online_files(ref, base_url)
        except Exception as exc:
            seen_refs[ref] = []
            counts["online_fetch_failed"] += 1
            if len(examples) < EXAMPLE_LIMIT:
                examples.append(
                    {
                        "kind": "online_fetch_failed",
                        "record_id": record.id,
                        "ref": ref,
                        "document_no": clean(getattr(record, "document_no", "")),
                        "error": str(exc),
                    }
                )
            continue
        seen_refs[ref] = files
        if not files:
            counts["online_missing"] += 1
            if len(examples) < EXAMPLE_LIMIT:
                examples.append({"kind": "online_missing", "record_id": record.id, "ref": ref, "document_no": clean(getattr(record, "document_no", ""))})
            continue
        counts["online_refs_ok"] += 1
        for file_index, row in enumerate(files):
            if MAX_FILES and committed_files >= MAX_FILES:
                stop_requested = True
                counts["files_skipped_by_max_files"] += len(files) - file_index
                break
            relative = relative_path_for(row, source_system)
            target, error = safe_download_to_local(row, relative)
            if error:
                counts["files_download_failed"] += 1
                if len(examples) < EXAMPLE_LIMIT:
                    examples.append(
                        {
                            "kind": "download_failed",
                            "record_id": record.id,
                            "ref": ref,
                            "file_name": clean(row.get("ATTR_NAME")),
                            "relative_path": relative,
                            "error": error,
                        }
                    )
                continue
            if target and target.exists() and target.stat().st_size > 0:
                counts["files_local_ok"] += 1
            else:
                counts["files_local_missing"] += 1
            action = upsert_file_index(row, relative, source_system, record)
            counts[f"file_index_{action}"] += 1
            committed_files += 1
            if APPLY and COMMIT_EVERY_FILES and committed_files % COMMIT_EVERY_FILES == 0:
                env.cr.commit()  # noqa: F821
                counts["intermediate_commits"] += 1
            if len(examples) < EXAMPLE_LIMIT:
                examples.append(
                    {
                        "kind": "mirrored",
                        "record_id": record.id,
                        "ref": ref,
                        "file_name": clean(row.get("ATTR_NAME")),
                        "relative_path": relative,
                        "action": action,
                    }
                )
    if APPLY:
        env.cr.commit()  # noqa: F821
    result = {
        "status": "PASS",
        "apply": APPLY,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_name": env.cr.dbname,  # noqa: F821
        "model": MODEL,
        "labels": sorted(LABELS),
        "mirror_root": str(MIRROR_ROOT),
        "require_visible_label": REQUIRE_VISIBLE_LABEL,
        "counts": dict(counts),
        "unique_refs": len(seen_refs),
        "examples": examples,
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


main()
