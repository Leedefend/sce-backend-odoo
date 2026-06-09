# -*- coding: utf-8 -*-
"""Backfill direct-acceptance settlement visible fields into formal settlements.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/ops/user_confirmed_settlement_usability_backfill.py
"""

import json
import sys
import traceback


SOURCE_PREFIX = "sc.legacy.direct.acceptance.fact"
VISIBLE_FIELD_COUNT = 60
VISIBLE_FALLBACKS = {
    "材料结算单": {
        "legacy_visible_04": ("title", "name"),
        "legacy_visible_07": ("settlement_amount", "amount_total"),
    },
    "机械结算单": {
        "legacy_visible_07": ("settlement_amount", "amount_total"),
    },
    "劳务结算": {
        "legacy_visible_07": ("settlement_amount", "amount_total"),
    },
    "分包结算单": {
        "legacy_visible_04": ("title", "name"),
        "legacy_visible_06": ("settlement_amount", "amount_total"),
    },
    "工程结算单": {
        "legacy_visible_07": ("settlement_amount", "amount_total"),
    },
}
REQUESTED_AMOUNT_VISIBLE_FIELD_BY_LABEL = {
    "材料结算单": "legacy_visible_12",
    "机械结算单": "legacy_visible_12",
    "劳务结算": "legacy_visible_12",
    "分包结算单": "legacy_visible_11",
}


def _text(value):
    value = "" if value is None or value is False else str(value)
    return value.strip()


def _fallback_value(settlement, field_names):
    for field_name in field_names:
        value = getattr(settlement, field_name, False)
        if value not in (None, False, ""):
            return value
    return False


def _money(value):
    text = _text(value).replace(",", "").replace("￥", "").replace("¥", "")
    if not text:
        return None
    match = __import__("re").search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _copy_visible_fields(settlement, fact):
    vals = {}
    label = settlement.legacy_acceptance_label or fact.acceptance_label
    if not settlement.legacy_acceptance_label and label:
        vals["legacy_acceptance_label"] = label
    for index in range(1, VISIBLE_FIELD_COUNT + 1):
        field_name = "legacy_visible_%02d" % index
        if field_name not in settlement._fields or field_name not in fact._fields:
            continue
        if _text(getattr(settlement, field_name, False)):
            continue
        value = _text(getattr(fact, field_name, False))
        if value:
            vals[field_name] = value
    for field_name, fallback_fields in VISIBLE_FALLBACKS.get(label or "", {}).items():
        if field_name not in settlement._fields:
            continue
        if _text(vals.get(field_name)) or _text(getattr(settlement, field_name, False)):
            continue
        value = _fallback_value(settlement, fallback_fields)
        if value not in (None, False, ""):
            vals[field_name] = value
    if not settlement.source_created_by and fact.creator_name:
        vals["source_created_by"] = fact.creator_name
    if not settlement.source_created_at and fact.created_time:
        vals["source_created_at"] = fact.created_time
    requested_field = REQUESTED_AMOUNT_VISIBLE_FIELD_BY_LABEL.get(label or "")
    if requested_field:
        requested_amount = _money(vals.get(requested_field) or getattr(settlement, requested_field, False))
        if requested_amount is not None and settlement.requested_fund_amount != requested_amount:
            vals["requested_fund_amount"] = requested_amount
    return vals


def main():
    Settlement = env["sc.settlement.order"].sudo().with_context(active_test=False)  # noqa: F821
    Fact = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
    settlements = Settlement.search([("legacy_fact_model", "=ilike", SOURCE_PREFIX + "%")])
    updated = 0
    copied_fields = 0
    missing_fact = []
    by_label = {}

    for settlement in settlements:
        fact = Fact.browse(settlement.legacy_fact_id)
        if not fact.exists():
            missing_fact.append(settlement.id)
            continue
        vals = _copy_visible_fields(settlement, fact)
        if not vals:
            continue
        settlement.write(vals)
        updated += 1
        copied_fields += len(vals)
        label = vals.get("legacy_acceptance_label") or settlement.legacy_acceptance_label or fact.acceptance_label or ""
        by_label[label] = by_label.get(label, 0) + 1

    env.cr.commit()  # noqa: F821
    result = {
        "operation": "user_confirmed_settlement_usability_backfill",
        "status": "PASS" if not missing_fact else "WARN",
        "settlement_count": len(settlements),
        "updated": updated,
        "copied_fields": copied_fields,
        "updated_by_label": by_label,
        "missing_fact_count": len(missing_fact),
        "missing_fact_sample": missing_fact[:20],
    }
    print("USER_CONFIRMED_SETTLEMENT_USABILITY_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


try:
    sys.exit(main())
except Exception as err:
    print(
        "USER_CONFIRMED_SETTLEMENT_USABILITY_BACKFILL: %s"
        % json.dumps(
            {
                "operation": "user_confirmed_settlement_usability_backfill",
                "status": "FAIL",
                "error": str(err),
                "traceback": traceback.format_exc(),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    sys.exit(1)
