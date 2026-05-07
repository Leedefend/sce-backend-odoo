# -*- coding: utf-8 -*-
"""Guard user-assignable role groups and user-visible approval templates.

Run with:
  make verify.user_role_approval_matrix.guard DB_NAME=<db>

This script expects to be executed by ``odoo shell`` and uses the global
``env`` object. It is read-only and fails fast when role/approval contracts
drift away from the user-visible business matrix.
"""

EXPECTED_ASSIGNABLE_ROLE_XMLIDS = [
    "smart_construction_core.group_sc_role_business_admin",
    "smart_construction_core.group_sc_role_temporary_finance",
    "smart_construction_core.group_sc_role_contract_admin",
    "smart_construction_core.group_sc_role_partner_manager",
    "smart_construction_core.group_sc_role_cost_user",
    "smart_construction_core.group_sc_role_material_manager",
    "smart_construction_core.group_sc_role_material_user",
    "smart_construction_core.group_sc_role_executive",
    "smart_construction_core.group_sc_role_operation_user",
    "smart_construction_core.group_sc_role_settlement_manager",
    "smart_construction_core.group_sc_role_settlement_user",
    "smart_construction_core.group_sc_role_finance_user",
    "smart_construction_core.group_sc_role_finance_manager",
    "smart_construction_core.group_sc_role_general_user",
    "smart_construction_core.group_sc_role_purchase_user",
    "smart_construction_core.group_sc_role_project_manager",
    "smart_construction_core.group_sc_role_project_user",
]

EXPECTED_SCOPES = {
    "executive": "smart_construction_core.group_sc_role_executive",
    "business_admin": "smart_construction_core.group_sc_role_business_admin",
    "operation_user": "smart_construction_core.group_sc_role_operation_user",
    "partner_manager": "smart_construction_core.group_sc_role_partner_manager",
    "project_user": "smart_construction_core.group_sc_role_project_user",
    "project_manager": "smart_construction_core.group_sc_cap_project_manager",
    "material_manager": "smart_construction_core.group_sc_cap_material_manager",
    "purchase_manager": "smart_construction_core.group_sc_cap_purchase_manager",
    "finance_manager": "smart_construction_core.group_sc_cap_finance_manager",
    "finance_user": "smart_construction_core.group_sc_role_finance_user",
    "temporary_finance": "smart_construction_core.group_sc_role_temporary_finance",
    "contract_manager": "smart_construction_core.group_sc_cap_contract_manager",
    "contract_user": "smart_construction_core.group_sc_role_contract_admin",
    "cost_manager": "smart_construction_core.group_sc_cap_cost_manager",
    "cost_user": "smart_construction_core.group_sc_role_cost_user",
    "settlement_manager": "smart_construction_core.group_sc_cap_settlement_manager",
    "settlement_user": "smart_construction_core.group_sc_role_settlement_user",
}

EXPECTED_POLICY_STEPS = {
    "project_contract_approval": {
        "mode": "linear",
        "required": True,
        "active_tier_count": 5,
        "steps": ["contract_user", "operation_user", "project_manager", "cost_manager", "executive"],
    },
    "general_contract_approval": {
        "mode": "linear",
        "required": True,
        "active_tier_count": 4,
        "steps": ["contract_user", "operation_user", "finance_manager", "executive"],
    },
    "purchase_order_approval": {
        "mode": "linear",
        "required": True,
        "active_tier_count": 4,
        "steps": ["project_user", "project_manager", "purchase_manager", "finance_manager"],
    },
    "settlement_order_approval": {
        "mode": "linear",
        "required": True,
        "active_tier_count": 4,
        "steps": ["settlement_user", "project_manager", "cost_manager", "settlement_manager"],
    },
    "payment_request_approval": {
        "mode": "linear",
        "required": True,
        "active_tier_count": 4,
        "steps": ["finance_user", "project_manager", "finance_manager", "executive"],
    },
    "receipt_income_optional_approval": {
        "mode": "none",
        "required": False,
        "active_tier_count": 0,
        "steps": ["finance_user", "operation_user", "finance_manager"],
    },
    "settlement_adjustment_optional_approval": {
        "mode": "none",
        "required": False,
        "active_tier_count": 0,
        "steps": ["settlement_user", "cost_manager", "settlement_manager"],
    },
}


def _env():
    return globals()["env"]


def _xmlid(record):
    if not record:
        return ""
    return record.get_external_id().get(record.id, "")


def _fail(errors):
    if errors:
        for error in errors:
            print("USER_ROLE_APPROVAL_MATRIX_ERROR=%s" % error)
        raise AssertionError("; ".join(errors))


def _check_assignable_roles():
    errors = []
    env = _env()
    Groups = env["res.groups"].sudo()
    assignable = Groups.search([("sc_assignable_user_permission", "=", True)])
    actual = sorted(_xmlid(group) for group in assignable)
    expected = sorted(EXPECTED_ASSIGNABLE_ROLE_XMLIDS)
    if actual != expected:
        errors.append("assignable role xmlids mismatch expected=%s actual=%s" % (expected, actual))
    leaked = assignable.filtered(lambda group: group.name.startswith("SC 能力 -") or group.name.startswith("SC 基础 -"))
    if leaked:
        errors.append("capability/base groups leaked into assignable roles: %s" % ", ".join(leaked.mapped("name")))
    print("USER_ROLE_ASSIGNABLE_COUNT=%s" % len(assignable))
    _fail(errors)


def _check_scopes():
    errors = []
    env = _env()
    Policy = env["sc.approval.policy"]
    Scope = env["sc.approval.scope"].sudo()
    for scope_key, expected_xmlid in EXPECTED_SCOPES.items():
        group = Policy._group_for_approval_scope(scope_key)
        actual_xmlid = _xmlid(group)
        if actual_xmlid != expected_xmlid:
            errors.append("scope %s group mismatch expected=%s actual=%s" % (scope_key, expected_xmlid, actual_xmlid))
        scope_record = Scope.search([("scope_key", "=", scope_key)], limit=1)
        if not scope_record:
            errors.append("missing approval scope record: %s" % scope_key)
        elif _xmlid(scope_record.group_id) != expected_xmlid:
            errors.append(
                "scope record %s group mismatch expected=%s actual=%s"
                % (scope_key, expected_xmlid, _xmlid(scope_record.group_id))
            )
    print("USER_APPROVAL_SCOPE_COUNT=%s" % Scope.search_count([]))
    _fail(errors)


def _check_policies():
    errors = []
    env = _env()
    Policy = env["sc.approval.policy"].sudo()
    Tier = env["tier.definition"].sudo()
    marker = Policy.USER_VISIBLE_TEMPLATE_MARKER
    for code, expected in EXPECTED_POLICY_STEPS.items():
        policy = Policy.search([("code", "=", code)], limit=1)
        if not policy:
            errors.append("missing approval policy: %s" % code)
            continue
        if policy.mode != expected["mode"]:
            errors.append("policy %s mode expected=%s actual=%s" % (code, expected["mode"], policy.mode))
        if bool(policy.approval_required) != expected["required"]:
            errors.append(
                "policy %s approval_required expected=%s actual=%s"
                % (code, expected["required"], bool(policy.approval_required))
            )
        if marker not in (policy.note or ""):
            errors.append("policy %s missing user-visible template marker" % code)
        actual_steps = policy.step_ids.sorted("sequence").mapped("approval_scope_key")
        if actual_steps != expected["steps"]:
            errors.append("policy %s steps expected=%s actual=%s" % (code, expected["steps"], actual_steps))
        for step in policy.step_ids:
            expected_group = Policy._group_for_approval_scope(step.approval_scope_key)
            if step.approve_group_id != expected_group:
                errors.append(
                    "policy %s step %s group mismatch expected=%s actual=%s"
                    % (code, step.name, _xmlid(expected_group), _xmlid(step.approve_group_id))
                )
        active_tiers = Tier.search([("model", "=", policy.target_model), ("active", "=", True)])
        if len(active_tiers) != expected["active_tier_count"]:
            errors.append(
                "policy %s active tier count expected=%s actual=%s"
                % (code, expected["active_tier_count"], len(active_tiers))
            )
        if expected["mode"] == "linear" and active_tiers and not all(active_tiers.mapped("approve_sequence")):
            errors.append("policy %s has active tiers without approve_sequence" % code)
        print(
            "USER_APPROVAL_POLICY=%s mode=%s required=%s steps=%s active_tiers=%s"
            % (code, policy.mode, bool(policy.approval_required), ">".join(actual_steps), len(active_tiers))
        )
    _fail(errors)


def main():
    _check_assignable_roles()
    _check_scopes()
    _check_policies()
    print("[user_role_approval_matrix_guard] PASS")


main()
