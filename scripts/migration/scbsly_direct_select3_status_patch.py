#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replay SCBSLY direct-project SelectType=3 status fields into Odoo.

Run with:

    odoo shell -c /var/lib/odoo/odoo.conf -d sc_demo --no-http < scripts/migration/scbsly_direct_select3_status_patch.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


ARTIFACT_NAME = "artifacts/migration/scbsly_direct_select3_status_online_dump_20260603.json"
for root in (
    Path("/opt/projects/repos/sce-backend-odoo"),
    Path("/mnt"),
    Path("/mnt/extra-addons"),
    Path.cwd(),
):
    ARTIFACT = root / ARTIFACT_NAME
    if ARTIFACT.exists():
        break
else:
    try:
        ARTIFACT = Path(__file__).resolve().parents[2] / ARTIFACT_NAME
    except NameError:
        ARTIFACT = Path(ARTIFACT_NAME)
STATUS_FIELDS = (
    "CCCC_DJJE",
    "CCCC_FKZT",
    "CCCC_FKJE",
    "CCCC_WFKJE",
    "CCCC_SQZT",
    "CCCC_SQJE",
    "CCCC_WSQJE",
    "CCCC_JSZT",
    "CCCC_JSJE",
    "CCCC_WJSJE",
)
SUMMARY_FIELDS = {"CCCC_FKZT", "CCCC_SQZT", "CCCC_JSZT"}
LINE_KEY_FIELDS = {
    "入库": (
        "CLMC$T_RK_RKDCB",
        "GGXH$T_RK_RKDCB",
        "SL$T_RK_RKDCB",
        "DJ$T_RK_RKDCB",
        "HJ$T_RK_RKDCB",
    ),
    "零星用工": (
        "SGNR$SGGL_LWGL_LXYG_CB",
        "GRHJ$SGGL_LWGL_LXYG_CB",
        "DJ$SGGL_LWGL_LXYG_CB",
        "JE$SGGL_LWGL_LXYG_CB",
        "BZ$SGGL_LWGL_LXYG_CB",
    ),
}
NUMBER_LINE_FIELDS = {
    "SL$T_RK_RKDCB",
    "DJ$T_RK_RKDCB",
    "HJ$T_RK_RKDCB",
    "GRHJ$SGGL_LWGL_LXYG_CB",
    "DJ$SGGL_LWGL_LXYG_CB",
    "JE$SGGL_LWGL_LXYG_CB",
}


def clean(value):
    if value is None or (isinstance(value, bool) and value is False):
        return ""
    return str(value).strip()


def number_key(value):
    text = clean(value).replace(",", "")
    if not text:
        return ""
    try:
        return ("%.6f" % float(text)).rstrip("0").rstrip(".")
    except Exception:
        return text


def line_key(label, payload):
    line_fields = LINE_KEY_FIELDS.get(label)
    if not line_fields:
        return ""
    master_id = clean(payload.get("ID") or payload.get("Id") or payload.get("ZBID$T_RK_RKDCB"))
    document_no = clean(payload.get("RKDH") or payload.get("DJBH"))
    if not master_id and not document_no:
        return ""
    parts = [label, master_id, document_no]
    for field_name in line_fields:
        value = payload.get(field_name)
        if field_name in NUMBER_LINE_FIELDS:
            parts.append(number_key(value))
        else:
            parts.append(clean(value))
    return "|".join(parts)


def has_value(row, field_name):
    return field_name in row and row[field_name] is not None and not (
        isinstance(row[field_name], bool) and row[field_name] is False
    )


def load_payload(record):
    try:
        payload = json.loads(record.raw_payload or "{}")
    except Exception:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def index_records(model, label):
    records = model.search([("active", "=", True), ("acceptance_label", "=", label)])
    buckets = defaultdict(list)
    for record in records:
        payload = load_payload(record)
        candidates = {
            record.legacy_record_id,
            record.document_no,
            payload.get("Id"),
            payload.get("ID"),
            payload.get("DJBH"),
            payload.get("RKDH"),
        }
        for value in candidates:
            key = clean(value)
            if key:
                buckets[key].append(record)
        key = line_key(label, payload)
        if key:
            buckets[f"line:{key}"].append(record)
    unique = {}
    ambiguous = {}
    for key, recs in buckets.items():
        ids = {rec.id for rec in recs}
        if len(ids) == 1:
            unique[key] = recs[0]
        else:
            ambiguous[key] = recs
    return unique, ambiguous, len(records)


def row_keys(label, row):
    keys = []
    key = line_key(label, row)
    if key:
        keys.append(f"line:{key}")
    keys.extend(clean(row.get(field)) for field in ("Id", "ID", "DJBH", "RKDH") if clean(row.get(field)))
    return keys


data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
Model = env["sc.legacy.direct.acceptance.fact"]
summary = []

for label_data in data.get("rows") or []:
    label = label_data.get("label")
    rows = label_data.get("rows") or []
    by_key, ambiguous, existing_count = index_records(Model, label)
    updated = 0
    unchanged = 0
    missing = []
    ambiguous_hits = []
    field_counters = {field: Counter() for field in STATUS_FIELDS}

    for row in rows:
        records = []
        hit_key = ""
        for key in row_keys(label, row):
            if key in ambiguous:
                records = ambiguous[key]
                ambiguous_hits.append(key)
                hit_key = key
                break
            if key in by_key:
                records = [by_key[key]]
                hit_key = key
                break
        if not records:
            missing.append(row_keys(label, row)[:3])
            continue

        for record in records:
            payload = load_payload(record)
            changed = False
            for field_name in STATUS_FIELDS:
                if not has_value(row, field_name):
                    continue
                value = row[field_name]
                if field_name in SUMMARY_FIELDS:
                    field_counters[field_name][clean(value)] += 1
                if payload.get(field_name) != value:
                    payload[field_name] = value
                    changed = True
            if changed:
                record.raw_payload = json.dumps(payload, ensure_ascii=False, sort_keys=True)
                updated += 1
            else:
                unchanged += 1

    summary.append(
        {
            "label": label,
            "artifact_rows": len(rows),
            "existing_records": existing_count,
            "updated": updated,
            "unchanged": unchanged,
            "missing": len(missing),
            "ambiguous": len(ambiguous_hits),
            "field_counters": {
                field: dict(counter)
                for field, counter in field_counters.items()
                if counter
            },
            "missing_sample": missing[:10],
            "ambiguous_sample": ambiguous_hits[:10],
        }
    )

env.cr.commit()
print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
