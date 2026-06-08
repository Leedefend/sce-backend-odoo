# -*- coding: utf-8 -*-
"""Bind real legacy file-index rows to user-confirmed formal business records.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/ops/user_confirmed_attachment_bind.py

The accepted list surface can show legacy values such as ``附件(1)``.  Formal
business handling must expose those files through real ``ir.attachment`` rows,
not through display text.  This script is idempotent and only creates URL-type
attachments when ``sc.legacy.file.index`` has a concrete file row.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict


MARKER = "[migration:user_confirmed_attachment_bind]"
HEX_REF_RE = re.compile(r"^[0-9a-fA-F]{32}$")
ATTACHMENT_LABEL_RE = re.compile(r"附件\((?P<count>\d+)\)")
FACT_CACHE_BY_LABELS = {}

TARGETS = [
    {
        "model": "tender.doc.purchase",
        "domain": [("legacy_attachment_ref", "!=", False)],
        "record_ref_fields": ["legacy_attachment_ref", "invoice_no", "legacy_record_id"],
        "fact_labels": [],
    },
    {
        "model": "sc.construction.diary",
        "domain": ["|", ("legacy_attachment_ref", "!=", False), ("legacy_visible_09", "!=", False)],
        "record_ref_fields": ["legacy_attachment_ref", "document_no", "name"],
        "fact_labels": ["施工日志（新）"],
    },
    {
        "model": "project.material.plan",
        "domain": [("legacy_visible_11", "!=", False)],
        "record_ref_fields": ["name"],
        "fact_labels": ["材料计划"],
    },
    {
        "model": "sc.subcontract.request",
        "domain": [("legacy_visible_13", "!=", False)],
        "record_ref_fields": ["name"],
        "fact_labels": ["分包方单"],
    },
    {
        "model": "sc.settlement.order",
        "domain": [("legacy_visible_attachment", "!=", False)],
        "record_ref_fields": ["name"],
        "fact_labels": ["工程结算单", "材料结算单", "劳务结算", "分包结算单", "机械结算单", "租赁结算单"],
    },
    {
        "model": "sc.hr.payroll.document",
        "domain": [("legacy_visible_12", "!=", False)],
        "record_ref_fields": ["legacy_document_no", "legacy_source_id", "name"],
        "fact_labels": ["管理人员工资表"],
    },
    {
        "model": "sc.legacy.direct.acceptance.fact",
        "domain": [
            ("acceptance_label", "in", ["租入", "还租"]),
            "|",
            ("attachment_ref", "!=", False),
            ("raw_payload", "ilike", '"FJ": "'),
        ],
        "record_ref_fields": ["attachment_ref", "legacy_record_id", "document_no"],
        "fact_labels": [],
    },
    {
        "model": "sc.labor.usage",
        "domain": [],
        "record_ref_fields": ["name", "legacy_visible_11"],
        "fact_labels": ["方单", "零星用工"],
    },
    {
        "model": "sc.equipment.usage",
        "domain": [],
        "record_ref_fields": ["name", "legacy_visible_13"],
        "fact_labels": ["机械台班记录"],
    },
    {
        "model": "sc.material.rfq",
        "domain": [],
        "record_ref_fields": ["name", "legacy_visible_15"],
        "fact_labels": ["报价单"],
    },
    {
        "model": "sc.material.inbound",
        "domain": [],
        "record_ref_fields": ["name", "legacy_visible_19"],
        "fact_labels": ["入库"],
    },
]


def _text(value) -> str:
    return str(value or "").strip()


def _is_attachment_label(value) -> bool:
    return bool(ATTACHMENT_LABEL_RE.search(_text(value)))


def _payload_dict(raw_payload):
    try:
        payload = json.loads(raw_payload or "{}")
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _payload_attachment_refs(raw_payload):
    refs = []
    payload = _payload_dict(raw_payload)
    for key, value in payload.items():
        if value is None or value is False:
            continue
        key_text = _text(key)
        value_text = _text(value)
        if not value_text:
            continue
        if key_text.endswith("FJ") or key_text.endswith("_FJ") or key_text in {"FJ", "f_FJ"}:
            if HEX_REF_RE.match(value_text) or not _is_attachment_label(value_text):
                refs.append(value_text)
            if _is_attachment_label(value_text):
                base_key = key_text[:-3] if key_text.endswith("_FJ") else ""
                base_value = _text(payload.get(base_key)) if base_key else ""
                if HEX_REF_RE.match(base_value):
                    refs.append(base_value)
    return refs


def _payload_lookup_keys(raw_payload):
    payload = _payload_dict(raw_payload)
    keys = []
    for key in ("DJBH", "RKDH", "ID", "Pid", "PID"):
        text = _text(payload.get(key))
        if text:
            keys.append(text)
    return keys


def _record_refs(record, field_names):
    refs = []
    for field_name in field_names:
        if field_name not in record._fields:
            continue
        value = record[field_name]
        if hasattr(value, "display_name"):
            value = value.display_name
        text = _text(value)
        if text and not _is_attachment_label(text):
            refs.append(text)
    return refs


def _find_facts(record, labels):
    if not labels:
        return env["sc.legacy.direct.acceptance.fact"].sudo().browse()  # noqa: F821
    Fact = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
    label_key = tuple(sorted(labels))
    if label_key not in FACT_CACHE_BY_LABELS:
        facts = Fact.search(
            [
                ("acceptance_label", "in", list(label_key)),
                "|",
                ("attachment_ref", "!=", False),
                ("raw_payload", "ilike", '"FJ": "'),
            ]
        )
        by_key = defaultdict(lambda: Fact.browse())
        for fact in facts:
            keys = [
                _text(fact.document_no),
                _text(fact.legacy_record_id),
                *_payload_lookup_keys(fact.raw_payload),
            ]
            for key in keys:
                if key:
                    by_key[key] |= fact
        FACT_CACHE_BY_LABELS[label_key] = by_key
    names = [
        value
        for value in {
            _text(getattr(record, "name", "")),
            _text(getattr(record, "legacy_document_no", "")),
            _text(getattr(record, "document_no", "")),
            _text(getattr(record, "legacy_record_id", "")),
            _text(getattr(record, "legacy_fact_id", "")),
        }
        if value
    ]
    if not names:
        return Fact.browse()
    facts = Fact.browse()
    by_key = FACT_CACHE_BY_LABELS[label_key]
    for name in names:
        facts |= by_key.get(name, Fact.browse())
    if facts:
        return facts
    raw_matches = Fact.browse()
    for name in names:
        raw_matches |= Fact.search([("acceptance_label", "in", labels), ("raw_payload", "ilike", name)], limit=10)
    return raw_matches


def _refs_for_record(record, target):
    refs = _record_refs(record, target.get("record_ref_fields") or [])
    if "raw_payload" in record._fields:
        refs.extend(_payload_attachment_refs(record.raw_payload))
    for fact in _find_facts(record, target.get("fact_labels") or []):
        for value in (fact.attachment_ref, fact.legacy_record_id, fact.document_no):
            text = _text(value)
            if text and not _is_attachment_label(text):
                refs.append(text)
        refs.extend(_payload_attachment_refs(fact.raw_payload))
    result = []
    seen = set()
    for ref in refs:
        if ref not in seen:
            result.append(ref)
            seen.add(ref)
    return result


def _file_rows_for_refs(refs):
    clean_refs = [ref for ref in refs if ref]
    if not clean_refs:
        return env["sc.legacy.file.index"].sudo().browse()  # noqa: F821
    File = env["sc.legacy.file.index"].sudo().with_context(active_test=False)  # noqa: F821
    domain = [
        "|",
        "|",
        "|",
        ("legacy_file_id", "in", clean_refs),
        ("legacy_pid", "in", clean_refs),
        ("bill_id", "in", clean_refs),
        ("business_id", "in", clean_refs),
    ]
    return File.search(domain)


def _legacy_url(file_row):
    path = _text(file_row.file_path or file_row.preview_path)
    if path:
        return "legacy-file://" + path.lstrip("/")
    return "legacy-file-id://" + _text(file_row.legacy_file_id or file_row.id)


def _ensure_attachment(record, file_row):
    Attachment = env["ir.attachment"].sudo()  # noqa: F821
    url = _legacy_url(file_row)
    existing = Attachment.search(
        [
            ("res_model", "=", record._name),
            ("res_id", "=", record.id),
            ("url", "=", url),
        ],
        limit=1,
    )
    if existing:
        return existing, False
    description = (
        f"{MARKER} model={record._name}; record_id={record.id}; "
        f"legacy_file_key={file_row.legacy_file_key}; legacy_file_id={file_row.legacy_file_id}; "
        f"legacy_pid={file_row.legacy_pid}; bill_id={file_row.bill_id}"
    )
    attachment = Attachment.create(
        {
            "name": file_row.file_name or file_row.legacy_file_id or "legacy attachment",
            "type": "url",
            "url": url,
            "res_model": record._name,
            "res_id": record.id,
            "description": description,
        }
    )
    return attachment, True


def _ensure_legacy_file_id_attachment(record, legacy_file_id):
    Attachment = env["ir.attachment"].sudo()  # noqa: F821
    clean_id = _text(legacy_file_id)
    if not clean_id:
        return Attachment.browse(), False
    url = "legacy-file-id://" + clean_id
    existing = Attachment.search(
        [
            ("res_model", "=", record._name),
            ("res_id", "=", record.id),
            ("url", "=", url),
        ],
        limit=1,
    )
    if existing:
        return existing, False
    description = f"{MARKER} model={record._name}; record_id={record.id}; legacy_file_id={clean_id}; source=raw_legacy_ref"
    attachment = Attachment.create(
        {
            "name": "legacy attachment %s" % clean_id[:12],
            "type": "url",
            "url": url,
            "res_model": record._name,
            "res_id": record.id,
            "description": description,
        }
    )
    return attachment, True


def _bind_record(record, target):
    refs = _refs_for_record(record, target)
    files = _file_rows_for_refs(refs)
    attachment_ids = []
    created = 0
    for file_row in files:
        attachment, is_created = _ensure_attachment(record, file_row)
        attachment_ids.append(attachment.id)
        created += int(is_created)
    if not files:
        for ref in refs:
            if not HEX_REF_RE.match(ref):
                continue
            attachment, is_created = _ensure_legacy_file_id_attachment(record, ref)
            if attachment:
                attachment_ids.append(attachment.id)
                created += int(is_created)
            break
    if not attachment_ids:
        return {"blocked": True, "reason": "missing_legacy_attachment_ref", "refs": refs[:10], "created": 0, "linked": 0}
    linked = 0
    if "attachment_ids" in record._fields:
        current_ids = set(record.attachment_ids.ids)
        to_link = [attachment_id for attachment_id in attachment_ids if attachment_id not in current_ids]
        if to_link:
            record.write({"attachment_ids": [(4, attachment_id) for attachment_id in to_link]})
            linked = len(to_link)
    return {"blocked": False, "created": created, "linked": linked, "file_count": len(files), "refs": refs[:10]}


def main():
    model_filter = {
        model.strip()
        for model in os.environ.get("USER_CONFIRMED_ATTACHMENT_BIND_MODELS", "").split(",")
        if model.strip()
    }
    summary = {
        "script": "user_confirmed_attachment_bind",
        "marker": MARKER,
        "models": {},
        "created_attachments": 0,
        "linked_attachments": 0,
        "blocked_count": 0,
        "blocked_samples": [],
        "blocked_reasons": {},
    }
    blocked_reasons = Counter()
    for target in TARGETS:
        model_name = target["model"]
        if model_filter and model_name not in model_filter:
            continue
        Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
        records = Model.search(target.get("domain") or [])
        model_stats = defaultdict(int)
        for record in records:
            result = _bind_record(record, target)
            model_stats["records"] += 1
            if result.get("blocked"):
                model_stats["blocked"] += 1
                summary["blocked_count"] += 1
                blocked_reasons[result.get("reason") or "blocked"] += 1
                if len(summary["blocked_samples"]) < 50:
                    summary["blocked_samples"].append(
                        {
                            "model": model_name,
                            "id": record.id,
                            "name": getattr(record, "name", ""),
                            "reason": result.get("reason"),
                            "refs": result.get("refs") or [],
                        }
                    )
                continue
            model_stats["created_attachments"] += result["created"]
            model_stats["linked_attachments"] += result["linked"]
            summary["created_attachments"] += result["created"]
            summary["linked_attachments"] += result["linked"]
        summary["models"][model_name] = dict(model_stats)
        env.cr.commit()  # noqa: F821
        print(json.dumps({"model": model_name, **dict(model_stats)}, ensure_ascii=False))
    summary["blocked_reasons"] = dict(blocked_reasons)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


main()
