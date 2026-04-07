#!/usr/bin/env python3
from pathlib import Path


RULES_FILE = Path('addons/smart_construction_core/security/sc_record_rules.xml')


TARGET_RULES = {
    'rule_sc_project_read_project_project': [
        'project_member_ids.user_id',
        'project_manager_user_id',
        'finance_contact_user_id',
    ],
    'rule_sc_project_user_project_project': [
        'project_member_ids.user_id',
        'business_lead_user_id',
        'cost_lead_user_id',
    ],
    'rule_sc_project_read_project_task': [
        'project_id.project_member_ids.user_id',
        'project_id.project_manager_user_id',
        "('user_ids','in',[user.id])",
    ],
    'rule_sc_project_user_project_task': [
        'project_id.project_member_ids.user_id',
        'project_id.finance_contact_user_id',
        "('user_ids','in',[user.id])",
    ],
    'rule_sc_cost_read_project_budget': ['project_id.project_member_ids.user_id'],
    'rule_sc_cost_read_project_cost_ledger': ['project_id.project_member_ids.user_id'],
    'rule_sc_cost_user_project_cost_ledger': ['project_id.project_member_ids.user_id'],
    'rule_sc_finance_read_payment_request': ['project_id.project_member_ids.user_id'],
    'rule_sc_finance_user_payment_request': ['project_id.project_member_ids.user_id'],
    'rule_sc_finance_read_payment_ledger': ['project_id.project_member_ids.user_id'],
    'rule_sc_finance_user_payment_ledger': ['project_id.project_member_ids.user_id'],
    'rule_sc_settlement_read_order': ['project_id.project_member_ids.user_id'],
    'rule_sc_settlement_user_order': ['project_id.project_member_ids.user_id'],
}


def _rule_block(text: str, rule_id: str) -> str:
    start_tag = f'<record id="{rule_id}" model="ir.rule">'
    start = text.find(start_tag)
    if start < 0:
        return ''
    end = text.find('</record>', start)
    if end < 0:
        return ''
    return text[start:end]


def main():
    text = RULES_FILE.read_text(encoding='utf-8')
    failures = []
    for rule_id, needles in TARGET_RULES.items():
        block = _rule_block(text, rule_id)
        if not block:
            failures.append(f'missing rule block: {rule_id}')
            continue
        if 'message_is_follower' in block:
            failures.append(f'legacy follower dependency remains: {rule_id}')
        for needle in needles:
            if needle not in block:
                failures.append(f'missing token {needle} in {rule_id}')

    if failures:
        raise SystemExit(
            '[native_business_fact_project_member_rule_binding_verify] FAIL ' + '; '.join(failures)
        )

    print(
        '[native_business_fact_project_member_rule_binding_verify] PASS '
        f'rules={len(TARGET_RULES)}'
    )


if __name__ == '__main__':
    main()
