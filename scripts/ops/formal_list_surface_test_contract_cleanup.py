# -*- coding: utf-8 -*-
"""Clean leaked test view orchestration from formal product list surfaces.

This script is intentionally narrow: it disables published ui.business.config
contracts that contain test placeholders on formal product actions, and removes
project ledger list-column user preferences so the page falls back to the
product baseline after cleanup.
"""

import json
import os


FORMAL_LIST_ACTION_IDS = {
    506, 525, 529, 530, 531, 545, 549, 565, 566, 615,
    642, 644, 645, 646, 647, 669, 701, 751, 752, 753,
    754, 756, 757, 758, 759, 761, 762, 764, 768, 769,
    770, 771, 772, 773, 776, 777, 778, 779, 780, 781,
    782, 783, 784, 786, 787, 805, 814, 841, 859, 862,
    868, 869, 871, 901, 902, 906, 907, 935, 936, 949,
    963, 964,
}

PROJECT_LEDGER_ACTION_ID = 506
TEST_TOKENS = ("CODEX_", "codex_view_orch_surface")


def _truthy(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _text(value):
    if value in (None, False):
        return ""
    return str(value)


def _action_xmlid(action):
    if not action:
        return ""
    return action.get_external_id().get(action.id, "")


apply = _truthy(os.environ.get("APPLY"))

Contract = env["ui.business.config.contract"].sudo()  # noqa: F821
Preference = env["sc.user.view.preference"].sudo()  # noqa: F821

contracts = Contract.search([
    ("active", "=", True),
    ("status", "=", "published"),
    ("action_id", "!=", False),
])

polluted_contracts = Contract.browse()
contract_rows = []
for rec in contracts:
    action_id = int(rec.action_id.id or 0)
    if action_id not in FORMAL_LIST_ACTION_IDS:
        continue
    payload_text = _text(rec.contract_json)
    name_text = _text(rec.name)
    matched = [token for token in TEST_TOKENS if token in name_text or token in payload_text]
    if not matched:
        continue
    polluted_contracts |= rec
    contract_rows.append({
        "contract_id": rec.id,
        "name": rec.name,
        "model": rec.model,
        "view_type": rec.view_type,
        "action_id": action_id,
        "action_name": rec.action_id.display_name,
        "action_xmlid": _action_xmlid(rec.action_id),
        "matched_tokens": matched,
    })

project_prefs = Preference.search([
    ("action_id", "=", PROJECT_LEDGER_ACTION_ID),
    ("preference_key", "=", "list_columns"),
])
preference_rows = [{
    "preference_id": rec.id,
    "user_id": rec.user_id.id,
    "user_login": rec.user_id.login,
    "scope_key": rec.scope_key,
    "value_json": rec.value_json if isinstance(rec.value_json, dict) else {},
} for rec in project_prefs]

if apply:
    if polluted_contracts:
        polluted_contracts.write({"active": False})
    if project_prefs:
        project_prefs.unlink()
    env.cr.commit()  # noqa: F821

report = {
    "script": "formal_list_surface_test_contract_cleanup",
    "apply": apply,
    "disabled_contract_count": len(polluted_contracts) if apply else 0,
    "candidate_contract_count": len(polluted_contracts),
    "removed_project_preference_count": len(project_prefs) if apply else 0,
    "candidate_project_preference_count": len(project_prefs),
    "contracts": contract_rows,
    "project_preferences": preference_rows,
    "status": "PASS",
}
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
print(
    "FORMAL_LIST_SURFACE_TEST_CONTRACT_CLEANUP="
    + json.dumps(report, ensure_ascii=False, sort_keys=True)
)
