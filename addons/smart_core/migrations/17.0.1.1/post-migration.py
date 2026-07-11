# -*- coding: utf-8 -*-
from __future__ import annotations

import json


AUDIT_FIELD_NAMES = {"create_uid", "create_date", "write_uid", "write_date"}


def _field_name(value):
    if isinstance(value, dict):
        return str(value.get("name") or value.get("field") or value.get("id") or "").strip()
    return str(value or "").strip()


def _without_audit_fields(values):
    if not isinstance(values, list):
        return values, False
    next_values = []
    changed = False
    for value in values:
        if _field_name(value) in AUDIT_FIELD_NAMES:
            changed = True
            continue
        next_values.append(value)
    return next_values, changed


def _sanitize_payload(payload):
    if isinstance(payload, list):
        changed = False
        next_items = []
        for item in payload:
            next_item, item_changed = _sanitize_payload(item)
            next_items.append(next_item)
            changed = changed or item_changed
        return next_items, changed
    if not isinstance(payload, dict):
        return payload, False

    next_payload = dict(payload)
    changed = False
    for key in ("columns", "columns_schema", "read_fields"):
        if key not in next_payload:
            continue
        next_values, key_changed = _without_audit_fields(next_payload.get(key))
        if key_changed:
            next_payload[key] = next_values
            changed = True

    for key, value in list(next_payload.items()):
        if key in ("columns", "columns_schema", "read_fields"):
            continue
        next_value, value_changed = _sanitize_payload(value)
        if value_changed:
            next_payload[key] = next_value
            changed = True
    return next_payload, changed


def _payload(value):
    if isinstance(value, dict):
        return dict(value)
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def migrate(cr, version):
    updates = {"app_view_config": 0, "ui_business_config_contract": 0}

    cr.execute("""
        SELECT id, arch_parsed
          FROM app_view_config
         WHERE view_type = 'tree'
           AND arch_parsed IS NOT NULL
    """)
    for rec_id, raw_payload in cr.fetchall():
        payload, changed = _sanitize_payload(_payload(raw_payload))
        if not changed:
            continue
        cr.execute(
            """
            UPDATE app_view_config
               SET arch_parsed = %s::jsonb,
                   write_date = NOW()
             WHERE id = %s
            """,
            (json.dumps(payload, ensure_ascii=False), rec_id),
        )
        updates["app_view_config"] += 1

    cr.execute("""
        SELECT id, contract_json
          FROM ui_business_config_contract
         WHERE contract_json IS NOT NULL
           AND (
             view_type = 'tree'
             OR contract_json ? 'view_orchestration'
             OR contract_json ? 'columns'
             OR contract_json ? 'columns_schema'
           )
    """)
    for rec_id, raw_payload in cr.fetchall():
        payload, changed = _sanitize_payload(_payload(raw_payload))
        if not changed:
            continue
        cr.execute(
            """
            UPDATE ui_business_config_contract
               SET contract_json = %s::jsonb,
                   write_date = NOW()
             WHERE id = %s
            """,
            (json.dumps(payload, ensure_ascii=False), rec_id),
        )
        updates["ui_business_config_contract"] += 1

    print(
        "[17.0.1.1] product list audit fields removed: app_view_config=%s ui_business_config_contract=%s"
        % (updates["app_view_config"], updates["ui_business_config_contract"])
    )
