# -*- coding: utf-8 -*-
"""Runtime guard for formal list surfaces against test placeholder contracts.

Run through Odoo shell:
    DB_NAME=sc_demo make verify.formal_list_surface.no_test_placeholder_guard
"""

import json


FORMAL_LIST_ACTION_IDS = {
    506, 525, 529, 530, 531, 545, 549, 565, 566, 615,
    642, 644, 645, 646, 647, 669, 701, 751, 752, 753,
    754, 756, 757, 758, 759, 761, 762, 764, 768, 769,
    770, 771, 772, 773, 776, 777, 778, 779, 780, 781,
    782, 783, 784, 786, 787, 805, 814, 841, 859, 862,
    868, 869, 871, 901, 902, 906, 907, 935, 936, 949,
    963, 964,
}

TEST_TOKENS = ("CODEX_", "codex_view_orch_surface")


def _text(value):
    if value in (None, False):
        return ""
    return str(value)


def _action_xmlid(action):
    if not action:
        return ""
    return action.get_external_id().get(action.id, "")


Contract = env["ui.business.config.contract"].sudo()  # noqa: F821
contracts = Contract.search([
    ("active", "=", True),
    ("status", "=", "published"),
    ("action_id", "!=", False),
])

errors = []
rows = []
for rec in contracts:
    action_id = int(rec.action_id.id or 0)
    if action_id not in FORMAL_LIST_ACTION_IDS:
        continue
    payload_text = _text(rec.contract_json)
    name_text = _text(rec.name)
    matched = [token for token in TEST_TOKENS if token in name_text or token in payload_text]
    if not matched:
        continue
    row = {
        "contract_id": rec.id,
        "name": rec.name,
        "model": rec.model,
        "view_type": rec.view_type,
        "action_id": action_id,
        "action_name": rec.action_id.display_name,
        "action_xmlid": _action_xmlid(rec.action_id),
        "matched_tokens": matched,
        "write_date": _text(rec.write_date),
    }
    rows.append(row)
    errors.append({**row, "error": "formal_surface_test_placeholder_contract"})

report = {
    "guard": "formal_list_surface_no_test_placeholder_guard",
    "checked_formal_action_count": len(FORMAL_LIST_ACTION_IDS),
    "polluted_contract_count": len(rows),
    "rows": rows,
    "errors": errors,
    "status": "FAIL" if errors else "PASS",
}
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
print(
    "FORMAL_LIST_SURFACE_NO_TEST_PLACEHOLDER_GUARD="
    + json.dumps(report, ensure_ascii=False, sort_keys=True)
)
if errors:
    raise SystemExit(1)
