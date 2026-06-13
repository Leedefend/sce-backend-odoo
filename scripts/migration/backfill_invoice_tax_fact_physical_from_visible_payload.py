#!/usr/bin/env python3
"""Backfill invoice tax fact physical fields from the preserved visible payload."""

from __future__ import annotations

import json
import re
from datetime import datetime


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def parse_datetime(value: object):
    text = clean(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19] if "%H" in fmt else text[:10], fmt)
        except ValueError:
            continue
    return None


def main() -> None:
    env.cr.execute("SELECT to_regclass('public.sc_p1_legacy_visible_alias_payload')")  # noqa: F821
    if not env.cr.fetchone()[0]:  # noqa: F821
        print(json.dumps({"status": "SKIP", "reason": "payload_table_missing"}, ensure_ascii=False))
        return

    Model = env["sc.legacy.invoice.tax.fact"].sudo().with_context(active_test=False)  # noqa: F821
    env.cr.execute(  # noqa: F821
        """
        SELECT f.id, p.payload
          FROM sc_legacy_invoice_tax_fact f
          JOIN sc_p1_legacy_visible_alias_payload p
            ON p.model = 'sc.legacy.invoice.tax.fact'
           AND p.res_id = f.id
         WHERE COALESCE(p.payload->>'发票公司类型', '') <> ''
            OR COALESCE(p.payload->>'发票号码', '') <> ''
            OR COALESCE(p.payload->>'推送结果', '') <> ''
            OR COALESCE(p.payload->>'录入人', '') <> ''
            OR COALESCE(p.payload->>'录入时间', '') <> ''
        """
    )
    rows = env.cr.fetchall()  # noqa: F821
    updated = 0
    touched = {
        "invoice_company_type": 0,
        "invoice_no": 0,
        "push_result": 0,
        "creator_name": 0,
        "created_time": 0,
    }
    for record_id, payload in rows:
        if not isinstance(payload, dict):
            continue
        rec = Model.browse(record_id)
        vals = {}
        mappings = {
            "invoice_company_type": "发票公司类型",
            "invoice_no": "发票号码",
            "push_result": "推送结果",
            "creator_name": "录入人",
        }
        for field_name, label in mappings.items():
            value = clean(payload.get(label))
            if value and clean(rec[field_name]) != value:
                vals[field_name] = value
                touched[field_name] += 1
        created_time = parse_datetime(payload.get("录入时间"))
        if created_time and rec.created_time != created_time:
            vals["created_time"] = created_time
            touched["created_time"] += 1
        if vals:
            rec.write(vals)
            updated += 1
    if updated:
        env.cr.commit()  # noqa: F821
    print(json.dumps({"status": "PASS", "candidate_rows": len(rows), "updated_rows": updated, "touched_fields": touched}, ensure_ascii=False, sort_keys=True))


main()
