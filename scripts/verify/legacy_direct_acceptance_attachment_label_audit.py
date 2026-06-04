# -*- coding: utf-8 -*-
"""Summarize direct-acceptance legacy attachment gaps by menu label."""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from odoo.addons.smart_core.handlers.file_download import _legacy_file_index_relative_path, _resolve_legacy_file_path


OUTPUT_JSON = Path(
    os.getenv("LEGACY_DIRECT_ATTACHMENT_LABEL_OUTPUT", "/tmp/legacy_direct_acceptance_attachment_label_audit_v1.json")
)
EXAMPLE_LIMIT = int(os.getenv("LEGACY_DIRECT_ATTACHMENT_LABEL_EXAMPLE_LIMIT", "5") or "5")
ATTACHMENT_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")
ATTACHMENT_LABEL_RE = re.compile(r"^(附件\([1-9]\d*\)|历史附件)$")
SPLIT_RE = re.compile(r"[\s,，;；|]+")
INDEX_FIELDS = ("bill_id", "legacy_file_id", "legacy_file_key", "business_id", "legacy_pid")


def clean(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def split_refs(value):
    refs = []
    for token in SPLIT_RE.split(clean(value)):
        if token:
            refs.append(token.replace("legacy-file://", "", 1).replace("legacy-file-id://", "", 1))
    return refs


def raw_payload(value):
    try:
        payload = json.loads(value or "{}")
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def visible_signals(row):
    payload = raw_payload(row.get("raw_payload"))
    values = []
    for field in ("f_FJ", "FJ_FJ", "f_FJ_FJ"):
        value = clean(payload.get(field))
        if ATTACHMENT_LABEL_RE.match(value):
            values.append({"field": f"raw_payload.{field}", "value": value})
    for field, value in row.items():
        if field.startswith("legacy_visible_") and ATTACHMENT_LABEL_RE.match(clean(value)):
            values.append({"field": field, "value": clean(value)})
    return values


def attachment_refs(row):
    refs = []
    refs.extend(split_refs(row.get("attachment_ref")))
    payload = raw_payload(row.get("raw_payload"))
    for field in ("FJ", "f_FJ"):
        value = clean(payload.get(field))
        if ATTACHMENT_ID_RE.match(value):
            refs.append(value)
    return list(dict.fromkeys(refs))


def file_index_map(refs):
    refs = sorted({ref for ref in refs if ref})
    result = {}
    FileIndex = env["sc.legacy.file.index"].sudo()  # noqa: F821
    for index in range(0, len(refs), 500):
        batch = refs[index:index + 500]
        domain = [("active", "=", True), "|", "|", "|", "|"]
        domain.extend((field, "in", batch) for field in INDEX_FIELDS)
        for item in FileIndex.search(domain, order="upload_time desc, id desc"):
            for field in INDEX_FIELDS:
                value = clean(getattr(item, field, ""))
                if value in batch and value not in result:
                    result[value] = item
    return result


def local_status(item):
    if not item:
        return "missing_index"
    relative = _legacy_file_index_relative_path(item)
    if not relative:
        return "missing_file"
    return "ok" if _resolve_legacy_file_path(relative) else "missing_file"


def main():
    Model = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
    fields = ["display_name", "acceptance_label", "document_no", "attachment_ref", "raw_payload"]
    fields.extend(sorted(name for name in Model._fields if name.startswith("legacy_visible_")))
    rows = Model.search_read([("active", "=", True)], fields=fields, order="id")
    by_label = defaultdict(Counter)
    examples = defaultdict(list)
    unique_refs_by_label = defaultdict(dict)
    all_refs = []
    for row in rows:
        label = clean(row.get("acceptance_label")) or "(empty)"
        by_label[label]["checked"] += 1
        visible = visible_signals(row)
        if not visible:
            by_label[label]["without_visible_attachment"] += 1
            continue
        by_label[label]["with_visible_attachment"] += 1
        refs = attachment_refs(row)
        if not refs:
            by_label[label]["visible_missing_ref"] += 1
            if len(examples[label]) < EXAMPLE_LIMIT:
                examples[label].append(
                    {
                        "kind": "visible_missing_ref",
                        "id": row["id"],
                        "display_name": clean(row.get("display_name")),
                        "document_no": clean(row.get("document_no")),
                        "visible": visible[:5],
                    }
                )
            continue
        for ref in refs:
            by_label[label]["refs_seen"] += 1
            unique_refs_by_label[label].setdefault(ref, row)
            all_refs.append(ref)
    index_by_ref = file_index_map(all_refs)
    for label, refs in unique_refs_by_label.items():
        for ref, row in refs.items():
            status = local_status(index_by_ref.get(ref))
            by_label[label][f"unique_ref_{status}"] += 1
            if status != "ok" and len(examples[label]) < EXAMPLE_LIMIT:
                examples[label].append(
                    {
                        "kind": "attachment_ref_gap",
                        "id": row["id"],
                        "display_name": clean(row.get("display_name")),
                        "document_no": clean(row.get("document_no")),
                        "ref": ref,
                        "status": status,
                    }
                )
    labels = []
    for label in sorted(by_label):
        row = dict(by_label[label])
        row["label"] = label
        row["unique_refs"] = len(unique_refs_by_label[label])
        row["examples"] = examples[label]
        row["status"] = "PASS" if not row.get("visible_missing_ref") and not row.get("unique_ref_missing_index") and not row.get("unique_ref_missing_file") else "WARN"
        labels.append(row)
    summary = Counter()
    for row in labels:
        summary["labels_checked"] += 1
        if row["status"] != "PASS":
            summary["labels_with_warning"] += 1
        for key, value in row.items():
            if isinstance(value, int):
                summary[key] += value
    result = {
        "status": "PASS" if not summary.get("labels_with_warning") else "WARN",
        "db_name": env.cr.dbname,  # noqa: F821
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": dict(summary),
        "labels": labels,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


main()
