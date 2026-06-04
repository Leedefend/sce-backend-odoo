# -*- coding: utf-8 -*-
"""Inventory legacy attachment coverage across all business surfaces.

Run through ``odoo shell``. The script scans models with legacy attachment
signals and reports whether attachment references can be resolved through the
local file index and mounted custody roots.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from odoo.addons.smart_core.handlers.file_download import (
    _legacy_file_index_relative_path,
    _resolve_legacy_file_path,
)


OUTPUT_JSON = Path(
    os.getenv("LEGACY_ATTACHMENT_SURFACE_OUTPUT", "/tmp/legacy_attachment_surface_inventory_v1.json")
)
MODEL_PATTERN = os.getenv("LEGACY_ATTACHMENT_SURFACE_MODEL_PATTERN", r"^(sc\.|project\.project$)")
MODEL_ALLOW = {
    item.strip()
    for item in re.split(r"[,，]", os.getenv("LEGACY_ATTACHMENT_SURFACE_MODELS", ""))
    if item.strip()
}
LIMIT_PER_MODEL = int(os.getenv("LEGACY_ATTACHMENT_SURFACE_LIMIT_PER_MODEL", "0") or "0")
EXAMPLE_LIMIT = int(os.getenv("LEGACY_ATTACHMENT_SURFACE_EXAMPLE_LIMIT", "20") or "20")
VISIBLE_ONLY = os.getenv("LEGACY_ATTACHMENT_SURFACE_VISIBLE_ONLY", "0").strip().lower() in {"1", "true", "yes", "on"}
ATTACHMENT_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")
ATTACHMENT_LABEL_RE = re.compile(r"^(附件\([1-9]\d*\)|历史附件)$")
SPLIT_RE = re.compile(r"[\s,，;；|]+")
LOCAL_STATUS_CACHE = {}
INDEX_FIELDS = ("bill_id", "legacy_file_id", "legacy_file_key", "business_id", "legacy_pid")


def clean(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def split_refs(value):
    result = []
    for token in SPLIT_RE.split(clean(value)):
        token = token.strip()
        if not token:
            continue
        if token.startswith("legacy-file://"):
            token = token.replace("legacy-file://", "", 1)
        if token.startswith("legacy-file-id://"):
            token = token.replace("legacy-file-id://", "", 1)
        result.append(token)
    return result


def model_has_attachment_surface(model):
    fields = getattr(model, "_fields", {}) or {}
    names = set(fields)
    if {"attachment_ref", "line_attachment_ref", "legacy_attachment_ref", "attachment_text", "raw_payload"} & names:
        return True
    return any(name.startswith("legacy_visible_") and "attachment" in name for name in names)


def fields_to_read(model):
    fields = getattr(model, "_fields", {}) or {}
    names = ["display_name"]
    for field in ("attachment_ref", "line_attachment_ref", "legacy_attachment_ref", "attachment_text", "raw_payload"):
        if field in fields:
            names.append(field)
    names.extend(
        sorted(name for name in fields if name.startswith("legacy_visible_") and "attachment" in name)
    )
    names.extend(
        sorted(
            name
            for name in fields
            if name.startswith("legacy_visible_")
            and name not in names
            and getattr(fields[name], "type", "") in {"char", "text", "html", "selection"}
        )
    )
    return list(dict.fromkeys(names))


def candidate_models():
    pattern = re.compile(MODEL_PATTERN)
    rows = []
    for model_name in sorted(env.registry.models):  # noqa: F821
        if model_name not in env:  # noqa: F821
            continue
        if MODEL_ALLOW and model_name not in MODEL_ALLOW:
            continue
        if not MODEL_ALLOW and not pattern.search(model_name):
            continue
        Model = env[model_name]  # noqa: F821
        if model_has_attachment_surface(Model):
            rows.append(model_name)
    return rows


def raw_payload(record):
    if isinstance(record, dict):
        value = record.get("raw_payload", "")
    else:
        value = getattr(record, "raw_payload", "")
    if not value:
        return {}
    try:
        payload = json.loads(value)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def visible_attachment_signals(record):
    fields = getattr(record, "_fields", {}) or {}
    if isinstance(record, dict):
        field_names = set(record)
        getter = record.get
    else:
        field_names = set(fields)
        getter = lambda field, default="": getattr(record, field, default)
    values = []
    for field in ("attachment_text",):
        if field in field_names:
            value = clean(getter(field, ""))
            if ATTACHMENT_LABEL_RE.match(value):
                values.append({"field": field, "value": value})
    payload = raw_payload(record)
    for field in ("f_FJ", "FJ_FJ", "f_FJ_FJ"):
        value = clean(payload.get(field))
        if ATTACHMENT_LABEL_RE.match(value):
            values.append({"field": f"raw_payload.{field}", "value": value})
    for field in sorted(name for name in field_names if name.startswith("legacy_visible_")):
        value = clean(getter(field, ""))
        if ATTACHMENT_LABEL_RE.match(value):
            values.append({"field": field, "value": value})
    return values


def attachment_refs(record):
    fields = getattr(record, "_fields", {}) or {}
    if isinstance(record, dict):
        field_names = set(record)
        getter = record.get
    else:
        field_names = set(fields)
        getter = lambda field, default="": getattr(record, field, default)
    refs = []
    for field in ("attachment_ref", "line_attachment_ref", "legacy_attachment_ref"):
        if field in field_names:
            refs.extend(split_refs(getter(field, "")))
    payload = raw_payload(record)
    for field in ("FJ", "f_FJ"):
        value = clean(payload.get(field))
        if ATTACHMENT_ID_RE.match(value):
            refs.append(value)
    return list(dict.fromkeys(ref for ref in refs if ref))


def chunks(values, size=1000):
    values = list(values)
    for index in range(0, len(values), size):
        yield values[index:index + size]


def local_file_index_map(refs):
    result = {}
    missing = {ref for ref in refs if ref}
    if not missing or "sc.legacy.file.index" not in env:  # noqa: F821
        return result
    FileIndex = env["sc.legacy.file.index"].sudo()  # noqa: F821
    for batch in chunks(sorted(missing), 500):
        domain = [("active", "=", True), "|", "|", "|", "|"]
        domain.extend((field, "in", batch) for field in INDEX_FIELDS)
        for item in FileIndex.search(domain, order="upload_time desc, id desc"):
            for field in INDEX_FIELDS:
                value = clean(getattr(item, field, ""))
                if value in missing and value not in result:
                    result[value] = item
    return result


def local_status(ref, index_by_ref=None):
    if ref in LOCAL_STATUS_CACHE:
        return LOCAL_STATUS_CACHE[ref]
    item = (index_by_ref or {}).get(ref)
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


def audit_model(model_name):
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    domain = [("active", "=", True)] if "active" in Model._fields else []
    records = Model.search_read(domain, fields=fields_to_read(Model), limit=LIMIT_PER_MODEL or None, order="id")
    counts = Counter()
    examples = []
    pending = []
    refs_seen = {}
    for record in records:
        counts["checked"] += 1
        visible = visible_attachment_signals(record)
        refs = attachment_refs(record)
        if visible:
            counts["records_with_visible_signal"] += 1
        elif VISIBLE_ONLY:
            counts["records_without_visible_signal_skipped"] += 1
            continue
        if refs:
            counts["records_with_ref"] += 1
        if visible and not refs:
            counts["visible_missing_ref"] += 1
            if len(examples) < EXAMPLE_LIMIT:
                examples.append(
                    {
                        "kind": "visible_missing_ref",
                        "id": record["id"],
                        "display_name": clean(record.get("display_name")),
                        "visible": visible[:5],
                    }
                )
        for ref in refs:
            counts["refs_seen"] += 1
            if ref in refs_seen:
                counts["refs_reused"] += 1
                continue
            refs_seen[ref] = {
                "id": record["id"],
                "display_name": clean(record.get("display_name")),
                "visible": visible[:5],
            }
            pending.append(ref)
    index_by_ref = local_file_index_map(pending)
    for ref, evidence in refs_seen.items():
        status = local_status(ref, index_by_ref)
        visible = evidence["visible"]
        counts[f"unique_ref_{status['status']}"] += 1
        if visible and status["status"] != "ok":
            counts[f"user_visible_{status['status']}"] += 1
        elif status["status"] != "ok":
            counts[f"storage_only_{status['status']}"] += 1
        if status["status"] != "ok" and len(examples) < EXAMPLE_LIMIT:
            examples.append(
                {
                    "kind": "attachment_ref_gap",
                    "id": evidence["id"],
                    "display_name": evidence["display_name"],
                    "ref": ref,
                    "status": status,
                    "visible": visible,
                }
            )
    return {
        "model": model_name,
        "counts": dict(counts),
        "unique_refs": len(refs_seen),
        "examples": examples,
        "status": "PASS"
        if not counts.get("visible_missing_ref")
        and not counts.get("user_visible_missing_index")
        and not counts.get("user_visible_missing_file")
        else "WARN",
    }


def main():
    rows = [audit_model(model_name) for model_name in candidate_models()]
    summary = Counter()
    for row in rows:
        summary["models_checked"] += 1
        if row["status"] != "PASS":
            summary["models_with_warning"] += 1
        for key, value in row["counts"].items():
            summary[key] += value
    result = {
        "status": "PASS" if not summary.get("models_with_warning") else "WARN",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_name": env.cr.dbname,  # noqa: F821
        "limit_per_model": LIMIT_PER_MODEL,
        "visible_only": VISIBLE_ONLY,
        "summary": dict(summary),
        "models": rows,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


main()
