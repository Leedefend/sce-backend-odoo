# -*- coding: utf-8 -*-
"""Bind real legacy file-index rows to user-confirmed formal business records.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/ops/user_confirmed_attachment_bind.py

Optional environment:
    USER_CONFIRMED_ATTACHMENT_BIND_MODELS=sc.labor.usage,sc.material.inbound
    USER_CONFIRMED_ATTACHMENT_BIND_FAST=0
    USER_CONFIRMED_ATTACHMENT_BIND_BATCH_SIZE=2000
    USER_CONFIRMED_ATTACHMENT_BIND_DEEP_RAW_SEARCH=1

The accepted list surface can show legacy values such as ``附件(1)``.  Formal
business handling must expose those files through real ``ir.attachment`` rows,
not through display text.  This script is idempotent and creates URL-type
attachments from concrete ``sc.legacy.file.index`` rows when possible, otherwise
it preserves the raw legacy file id through a ``legacy-file-id://`` URL.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict

from psycopg2.extras import execute_values


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
        facts = Fact.search([("acceptance_label", "in", list(label_key))])
        by_key = defaultdict(list)
        for fact in facts:
            if not fact.attachment_ref and not _payload_attachment_refs(fact.raw_payload):
                continue
            keys = [
                _text(fact.document_no),
                _text(fact.legacy_record_id),
                *_payload_lookup_keys(fact.raw_payload),
            ]
            for key in keys:
                if key:
                    by_key[key].append(fact)
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
    by_key = FACT_CACHE_BY_LABELS[label_key]
    facts = []
    seen_fact_ids = set()
    for name in names:
        for fact in by_key.get(name, []):
            if fact.id in seen_fact_ids:
                continue
            facts.append(fact)
            seen_fact_ids.add(fact.id)
    if facts:
        return facts
    if os.environ.get("USER_CONFIRMED_ATTACHMENT_BIND_DEEP_RAW_SEARCH", "0") != "1":
        return Fact.browse()
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


def _file_rows_by_ref(refs):
    result = defaultdict(list)
    for file_row in _file_rows_for_refs(refs):
        for ref in (file_row.legacy_file_id, file_row.legacy_pid, file_row.bill_id, file_row.business_id):
            text = _text(ref)
            if text:
                result[text].append(file_row)
    return result


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


def _attachment_spec_for_file(record, file_row):
    url = _legacy_url(file_row)
    description = (
        f"{MARKER} model={record._name}; record_id={record.id}; "
        f"legacy_file_key={file_row.legacy_file_key}; legacy_file_id={file_row.legacy_file_id}; "
        f"legacy_pid={file_row.legacy_pid}; bill_id={file_row.bill_id}"
    )
    return {
        "name": file_row.file_name or file_row.legacy_file_id or "legacy attachment",
        "type": "url",
        "url": url,
        "res_model": record._name,
        "res_id": record.id,
        "description": description,
    }


def _attachment_spec_for_legacy_ref(record, ref):
    clean_ref = _text(ref)
    return {
        "name": "legacy attachment %s" % clean_ref[:12],
        "type": "url",
        "url": "legacy-file-id://" + clean_ref,
        "res_model": record._name,
        "res_id": record.id,
        "description": f"{MARKER} model={record._name}; record_id={record.id}; legacy_file_id={clean_ref}; source=raw_legacy_ref",
    }


def _existing_attachment_ids(model_name, record_ids):
    if not record_ids:
        return {}
    Attachment = env["ir.attachment"].sudo()  # noqa: F821
    result = {}
    for attachment in Attachment.search(
        [
            ("res_model", "=", model_name),
            ("res_id", "in", record_ids),
            ("type", "=", "url"),
        ]
    ):
        result[(attachment.res_id, attachment.url)] = attachment.id
    return result


def _existing_rel_pairs(field, record_ids):
    if not record_ids:
        return set()
    env.cr.execute(  # noqa: F821
        f"SELECT {field.column1}, {field.column2} FROM {field.relation} WHERE {field.column1} = ANY(%s)",
        [record_ids],
    )
    return set(env.cr.fetchall())  # noqa: F821


def _bulk_link_attachment_ids(field, pairs):
    if not pairs:
        return 0
    unique_pairs = list(dict.fromkeys(pairs))
    execute_values(
        env.cr,  # noqa: F821
        f"""
        INSERT INTO {field.relation} ({field.column1}, {field.column2})
        SELECT incoming.{field.column1}, incoming.{field.column2}
          FROM (VALUES %s) AS incoming({field.column1}, {field.column2})
         WHERE NOT EXISTS (
               SELECT 1
                 FROM {field.relation} existing
                WHERE existing.{field.column1} = incoming.{field.column1}
                  AND existing.{field.column2} = incoming.{field.column2}
         )
        """,
        unique_pairs,
        page_size=5000,
    )
    return len(unique_pairs)


def _bind_records_fast(records, target):
    records = records.exists()
    if not records or "attachment_ids" not in records._fields:
        return None

    refs_by_record = {}
    all_refs = set()
    blocked_samples = []
    for record in records:
        refs = _refs_for_record(record, target)
        refs_by_record[record.id] = refs
        all_refs.update(refs)

    files_by_ref = _file_rows_by_ref(all_refs)
    existing_attachments = _existing_attachment_ids(records._name, records.ids)
    create_values = []
    pending_links = []
    blocked = 0
    for record in records:
        refs = refs_by_record.get(record.id) or []
        specs = []
        for ref in refs:
            file_rows = files_by_ref.get(ref) or []
            if file_rows:
                specs.extend(_attachment_spec_for_file(record, file_row) for file_row in file_rows)
            elif HEX_REF_RE.match(ref):
                specs.append(_attachment_spec_for_legacy_ref(record, ref))
        if not specs:
            blocked += 1
            if len(blocked_samples) < 50:
                blocked_samples.append(
                    {
                        "model": records._name,
                        "id": record.id,
                        "name": getattr(record, "name", ""),
                        "reason": "missing_legacy_attachment_ref",
                        "refs": refs[:10],
                    }
                )
            continue
        seen_urls = set()
        for spec in specs:
            url = spec["url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            existing_id = existing_attachments.get((record.id, url))
            if existing_id:
                pending_links.append((record.id, existing_id))
                continue
            create_values.append(spec)
            pending_links.append((record.id, None))

    Attachment = env["ir.attachment"].sudo()  # noqa: F821
    created_attachments = Attachment.create(create_values) if create_values else Attachment.browse()
    created_iter = iter(created_attachments)
    link_pairs = []
    for record_id, attachment_id in pending_links:
        if not attachment_id:
            attachment_id = next(created_iter).id
        link_pairs.append((record_id, attachment_id))

    field = records._fields["attachment_ids"]
    existing_pairs = _existing_rel_pairs(field, records.ids)
    to_insert = [pair for pair in link_pairs if pair not in existing_pairs]
    linked = _bulk_link_attachment_ids(field, to_insert)
    return {
        "records": len(records),
        "blocked": blocked,
        "created_attachments": len(created_attachments),
        "linked_attachments": linked,
        "blocked_samples": blocked_samples,
    }


def _merge_fast_stats(target_stats, batch_result):
    target_stats["records"] += batch_result["records"]
    target_stats["blocked"] += batch_result["blocked"]
    target_stats["created_attachments"] += batch_result["created_attachments"]
    target_stats["linked_attachments"] += batch_result["linked_attachments"]
    target_stats.setdefault("blocked_samples", [])
    remaining = max(0, 50 - len(target_stats["blocked_samples"]))
    target_stats["blocked_samples"].extend(batch_result["blocked_samples"][:remaining])


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
    fast_mode = os.environ.get("USER_CONFIRMED_ATTACHMENT_BIND_FAST", "1") != "0"
    batch_size = int(os.environ.get("USER_CONFIRMED_ATTACHMENT_BIND_BATCH_SIZE", "2000") or "2000")
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
        fast_result = None
        if fast_mode and "attachment_ids" in Model._fields:
            aggregate = defaultdict(int)
            aggregate["blocked_samples"] = []
            record_ids = records.ids
            for offset in range(0, len(record_ids), batch_size):
                batch = Model.browse(record_ids[offset : offset + batch_size])
                batch_result = _bind_records_fast(batch, target)
                if batch_result is None:
                    aggregate = None
                    break
                _merge_fast_stats(aggregate, batch_result)
            fast_result = aggregate
        if fast_result is not None:
            model_stats.update({key: value for key, value in fast_result.items() if key != "blocked_samples"})
            summary["blocked_count"] += fast_result["blocked"]
            summary["created_attachments"] += fast_result["created_attachments"]
            summary["linked_attachments"] += fast_result["linked_attachments"]
            if fast_result["blocked"]:
                blocked_reasons["missing_legacy_attachment_ref"] += fast_result["blocked"]
            remaining_sample_slots = max(0, 50 - len(summary["blocked_samples"]))
            summary["blocked_samples"].extend(fast_result["blocked_samples"][:remaining_sample_slots])
        else:
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
