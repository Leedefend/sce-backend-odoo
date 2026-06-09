# -*- coding: utf-8 -*-
"""Audit direct-acceptance settlement usability fields on formal settlements.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/verify/user_confirmed_settlement_usability_audit.py
"""

import json
import sys
import traceback


SOURCE_PREFIX = "sc.legacy.direct.acceptance.fact"
REQUIRED_VISIBLE_FIELDS_BY_LABEL = {
    "材料结算单": ("legacy_visible_01", "legacy_visible_02", "legacy_visible_03", "legacy_visible_04", "legacy_visible_07"),
    "机械结算单": ("legacy_visible_01", "legacy_visible_02", "legacy_visible_03", "legacy_visible_04", "legacy_visible_07"),
    "劳务结算": ("legacy_visible_01", "legacy_visible_02", "legacy_visible_03", "legacy_visible_04", "legacy_visible_07"),
    "分包结算单": ("legacy_visible_01", "legacy_visible_02", "legacy_visible_03", "legacy_visible_04", "legacy_visible_06"),
    "工程结算单": ("legacy_visible_01", "legacy_visible_02", "legacy_visible_03", "legacy_visible_04", "legacy_visible_07"),
}
AMOUNT_VISIBLE_FIELDS = {
    "legacy_visible_06",
    "legacy_visible_07",
}


def _text(value):
    value = "" if value is None or value is False else str(value)
    return value.strip()


def _count_missing(records, field_name):
    count = 0
    for record in records:
        if _text(getattr(record, field_name, False)):
            continue
        if field_name in AMOUNT_VISIBLE_FIELDS and not (record.settlement_amount or record.amount_total):
            continue
        count += 1
    return count


def main():
    Settlement = env["sc.settlement.order"].sudo().with_context(active_test=False)  # noqa: F821
    settlements = Settlement.search([("legacy_fact_model", "=ilike", SOURCE_PREFIX + "%")])
    failures = []
    by_label = {}
    missing_label = settlements.filtered(lambda record: not _text(record.legacy_acceptance_label))
    if missing_label:
        failures.append(
            {
                "check": "legacy_acceptance_label",
                "missing": len(missing_label),
                "sample": missing_label.ids[:20],
            }
        )

    for label, required_fields in REQUIRED_VISIBLE_FIELDS_BY_LABEL.items():
        records = settlements.filtered(lambda record, label=label: record.legacy_acceptance_label == label)
        by_label[label] = len(records)
        if not records:
            failures.append({"check": "label_present", "label": label, "missing": True})
            continue
        for field_name in required_fields:
            missing_count = _count_missing(records, field_name)
            if missing_count:
                failures.append(
                    {
                        "check": "visible_field",
                        "label": label,
                        "field": field_name,
                        "missing": missing_count,
                    }
                )

    result = {
        "audit": "user_confirmed_settlement_usability_audit",
        "status": "PASS" if not failures else "FAIL",
        "settlement_count": len(settlements),
        "by_label": by_label,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("USER_CONFIRMED_SETTLEMENT_USABILITY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    result = {
        "audit": "user_confirmed_settlement_usability_audit",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print(
        "USER_CONFIRMED_SETTLEMENT_USABILITY_AUDIT: %s"
        % json.dumps(result, ensure_ascii=False, sort_keys=True)
    )
    sys.exit(1)
