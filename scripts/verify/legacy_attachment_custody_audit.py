# -*- coding: utf-8 -*-
"""Audit legacy attachment custody against local backup files and online fallback.

Run through ``odoo shell``. The audit is intentionally evidence-oriented:
it reports whether user-visible attachment references can be served from the
local file index/backup, whether they still need online legacy fallback, and
whether existing ``ir.attachment`` records still point to legacy online URLs.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from scripts.verify.online_capture_security import require_online_capture  # noqa: E402

from odoo.addons.smart_core.handlers.file_download import (
    _fetch_online_legacy_file_by_bill_id,
    _legacy_file_index_relative_path,
    _resolve_legacy_file_path,
)


MODEL = os.getenv("LEGACY_ATTACHMENT_AUDIT_MODEL", "sc.legacy.direct.acceptance.fact")
LABELS = {
    item.strip()
    for item in re.split(r"[,，]", os.getenv("LEGACY_ATTACHMENT_AUDIT_LABELS", ""))
    if item.strip()
}
LIMIT = int(os.getenv("LEGACY_ATTACHMENT_AUDIT_LIMIT", "0") or "0")
CHECK_ONLINE = os.getenv("LEGACY_ATTACHMENT_AUDIT_CHECK_ONLINE", "0").strip().lower() in {"1", "true", "yes", "on"}
FILE_INDEX_LIMIT = int(os.getenv("LEGACY_ATTACHMENT_AUDIT_FILE_INDEX_LIMIT", "5000") or "0")
OUTPUT_JSON = Path(
    os.getenv("LEGACY_ATTACHMENT_AUDIT_OUTPUT", "/tmp/legacy_attachment_custody_audit_result_v1.json")
)
ATTACHMENT_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")
ATTACHMENT_LABEL_RE = re.compile(r"^附件\([1-9]\d*\)$")
LOCAL_STATUS_CACHE = {}
ONLINE_STATUS_CACHE = {}


def clean(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def raw_payload(record):
    try:
        payload = json.loads(record.raw_payload or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def attachment_ref_from_record(record):
    ref = clean(getattr(record, "attachment_ref", ""))
    if ref:
        return ref
    payload = raw_payload(record)
    for field in ("FJ", "f_FJ"):
        value = clean(payload.get(field))
        if ATTACHMENT_ID_RE.match(value):
            return value
    return ""


def visible_attachment_text(record):
    payload = raw_payload(record)
    values = []
    for field in ("f_FJ", "FJ_FJ", "f_FJ_FJ"):
        value = clean(payload.get(field))
        if ATTACHMENT_LABEL_RE.match(value):
            values.append(value)
    for index in range(1, 61):
        field = f"legacy_visible_{index:02d}"
        if field not in getattr(record, "_fields", {}):
            continue
        value = clean(getattr(record, field, ""))
        if ATTACHMENT_LABEL_RE.match(value):
            values.append(value)
    return values[0] if values else ""


def local_file_index_for_ref(ref):
    if not ref or "sc.legacy.file.index" not in env:  # noqa: F821
        return None
    return env["sc.legacy.file.index"].sudo().search(  # noqa: F821
        [
            ("active", "=", True),
            "|",
            "|",
            ("bill_id", "=", ref),
            ("legacy_file_id", "=", ref),
            ("legacy_file_key", "=", ref),
        ],
        order="upload_time desc, id desc",
        limit=1,
    )


def local_status(ref):
    if ref in LOCAL_STATUS_CACHE:
        return LOCAL_STATUS_CACHE[ref]
    item = local_file_index_for_ref(ref)
    if not item:
        LOCAL_STATUS_CACHE[ref] = {"status": "missing_index"}
        return LOCAL_STATUS_CACHE[ref]
    relative = _legacy_file_index_relative_path(item)
    if not relative:
        LOCAL_STATUS_CACHE[ref] = {
            "status": "missing_file",
            "file_index_id": item.id,
            "file_name": item.file_name,
            "file_path": item.file_path,
            "preview_path": item.preview_path,
        }
        return LOCAL_STATUS_CACHE[ref]
    path = _resolve_legacy_file_path(relative)
    LOCAL_STATUS_CACHE[ref] = {
        "status": "ok" if path else "missing_file",
        "file_index_id": item.id,
        "file_name": item.file_name,
        "relative_path": relative,
        "resolved_path": str(path or ""),
    }
    return LOCAL_STATUS_CACHE[ref]


def online_status(ref, record):
    if not CHECK_ONLINE or not ref:
        return {"status": "skipped"}
    if ref in ONLINE_STATUS_CACHE:
        return ONLINE_STATUS_CACHE[ref]
    source_system = clean(getattr(record, "source_system", ""))
    system = "scbs"
    base_url = os.getenv("OLD_SCBS_BASE_URL", "").rstrip("/")
    if source_system.startswith("online_old_scbsly"):
        system = "scbsly"
        base_url = os.getenv("SCBSLY_BASE_URL", "").rstrip("/")
    require_online_capture((system,))
    info = _fetch_online_legacy_file_by_bill_id(ref, base_url)
    if not info:
        ONLINE_STATUS_CACHE[ref] = {"status": "missing"}
        return ONLINE_STATUS_CACHE[ref]
    ONLINE_STATUS_CACHE[ref] = {
        "status": "ok",
        "name": clean(info.get("ATTR_NAME")),
        "bill_id": clean(info.get("BILLID")),
        "path": clean(info.get("ATTR_PATH")),
    }
    return ONLINE_STATUS_CACHE[ref]


def audit_business_records():
    if MODEL not in env:  # noqa: F821
        return {"status": "SKIP", "reason": f"model not found: {MODEL}"}
    Model = env[MODEL].sudo().with_context(active_test=False)  # noqa: F821
    domain = [("active", "=", True)] if "active" in Model._fields else []
    label_field = "acceptance_label" if "acceptance_label" in Model._fields else ""
    if LABELS and label_field:
        domain.append((label_field, "in", sorted(LABELS)))
    records = Model.search(domain, limit=LIMIT or None, order="id")
    counts = Counter()
    examples = []
    for record in records:
        counts["checked"] += 1
        visible = visible_attachment_text(record)
        ref = attachment_ref_from_record(record)
        if not visible:
            counts["no_visible_attachment"] += 1
            continue
        if visible and not ref:
            counts["visible_missing_ref"] += 1
            if len(examples) < 30:
                examples.append({"kind": "visible_missing_ref", "id": record.id, "display_name": record.display_name})
            continue
        local = local_status(ref)
        online = online_status(ref, record)
        counts[f"local_{local['status']}"] += 1
        counts[f"online_{online['status']}"] += 1
        if local["status"] != "ok" or (CHECK_ONLINE and online["status"] != "ok"):
            if len(examples) < 30:
                examples.append(
                    {
                        "kind": "attachment_gap",
                        "id": record.id,
                        "label": clean(getattr(record, "acceptance_label", "")),
                        "document_no": clean(getattr(record, "document_no", "")),
                        "ref": ref,
                        "visible": visible,
                        "local": local,
                        "online": online,
                    }
                )
    return {"status": "PASS", "model": MODEL, "labels": sorted(LABELS), "counts": dict(counts), "examples": examples}


def audit_file_index_sample():
    if "sc.legacy.file.index" not in env:  # noqa: F821
        return {"status": "SKIP", "reason": "sc.legacy.file.index missing"}
    FileIndex = env["sc.legacy.file.index"].sudo().with_context(active_test=False)  # noqa: F821
    domain = [("active", "=", True)]
    rows = FileIndex.search(domain, limit=FILE_INDEX_LIMIT or None, order="id")
    counts = Counter()
    examples = []
    for item in rows:
        counts["checked"] += 1
        relative = _legacy_file_index_relative_path(item)
        if relative and _resolve_legacy_file_path(relative):
            counts["local_file_ok"] += 1
            continue
        counts["local_file_missing"] += 1
        if len(examples) < 30:
            examples.append(
                {
                    "file_index_id": item.id,
                    "file_name": item.file_name,
                    "bill_id": item.bill_id,
                    "legacy_file_id": item.legacy_file_id,
                    "file_path": item.file_path,
                    "preview_path": item.preview_path,
                }
            )
    return {"status": "PASS", "limit": FILE_INDEX_LIMIT, "counts": dict(counts), "examples": examples}


def audit_ir_attachment_urls():
    Attachment = env["ir.attachment"].sudo()  # noqa: F821
    legacy_urls = Attachment.search_count([("type", "=", "url"), ("url", "=like", "legacy-file%")])
    online_urls = Attachment.search_count([("type", "=", "url"), ("url", "=like", "https://www.builderp.cn/%")])
    missing_local = 0
    examples = []
    for item in Attachment.search([("type", "=", "url"), ("url", "=like", "legacy-file://%")], limit=5000, order="id"):
        relative = clean(item.url).replace("legacy-file://", "", 1)
        if _resolve_legacy_file_path(relative):
            continue
        missing_local += 1
        if len(examples) < 30:
            examples.append({"id": item.id, "name": item.name, "res_model": item.res_model, "res_id": item.res_id, "url": item.url})
    return {
        "status": "PASS",
        "legacy_url_count": legacy_urls,
        "online_url_count": online_urls,
        "sampled_legacy_url_missing_local": missing_local,
        "examples": examples,
    }


result = {
    "status": "PASS",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "db_name": env.cr.dbname,  # noqa: F821
    "check_online": CHECK_ONLINE,
    "business_records": audit_business_records(),
    "file_index_sample": audit_file_index_sample(),
    "ir_attachment_urls": audit_ir_attachment_urls(),
}
OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
