# -*- coding: utf-8 -*-
"""Runtime probe for platform-owned company access models."""

REQUIRED_MODELS = {
    "sc.subscription.plan": ["code", "active", "feature_flags_json", "limits_json"],
    "sc.subscription": ["company_id", "plan_id", "state", "start_date", "end_date"],
    "sc.entitlement": ["company_id", "plan_id", "effective_flags_json", "effective_limits_json"],
    "sc.usage.counter": ["company_id", "key", "value"],
    "sc.ops.job": ["name", "job_type", "status"],
}

REQUIRED_PLATFORM_XMLIDS = {
    "ir.actions.act_window": [
        "action_sc_subscription_plan",
        "action_sc_subscription",
        "action_sc_entitlement",
        "action_sc_usage_counter",
        "action_sc_ops_job",
    ],
    "ir.ui.menu": [
        "menu_smart_core_platform_root",
        "menu_smart_core_company_access_root",
        "menu_sc_subscription_plan",
        "menu_sc_subscription",
        "menu_sc_entitlement",
        "menu_sc_usage_counter",
        "menu_sc_ops_job",
    ],
}
LEGACY_CONSTRUCTION_ACCESS_XMLIDS = [
    "access_sc_subscription_plan_read",
    "access_sc_subscription_plan_admin",
    "access_sc_subscription_read",
    "access_sc_subscription_admin",
    "access_sc_entitlement_read",
    "access_sc_entitlement_admin",
    "access_sc_usage_counter_read",
    "access_sc_usage_counter_admin",
    "access_sc_ops_job_read",
    "access_sc_ops_job_admin",
]
LEGACY_CONSTRUCTION_UI_XMLIDS = {
    "ir.ui.menu": [
        "menu_sc_ops_job",
        "menu_sc_usage_counter",
        "menu_sc_entitlement",
        "menu_sc_subscription",
        "menu_sc_subscription_plan",
        "menu_smart_core_company_access_root",
        "menu_smart_core_platform_root",
    ],
    "ir.actions.act_window": [
        "action_sc_subscription_plan",
        "action_sc_subscription",
        "action_sc_entitlement",
        "action_sc_usage_counter",
        "action_sc_ops_job",
    ],
    "ir.ui.view": [
        "view_sc_subscription_plan_tree",
        "view_sc_subscription_plan_form",
        "view_sc_subscription_tree",
        "view_sc_subscription_form",
        "view_sc_entitlement_tree",
        "view_sc_entitlement_form",
        "view_sc_usage_counter_tree",
        "view_sc_usage_counter_form",
        "view_sc_ops_job_tree",
        "view_sc_ops_job_form",
    ],
}


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


for model_name, field_names in REQUIRED_MODELS.items():
    assert_true(model_name in env, f"missing model: {model_name}")
    model = env[model_name]
    for field_name in field_names:
        assert_true(field_name in model._fields, f"missing field: {model_name}.{field_name}")
    model_data_name = "model_" + model_name.replace(".", "_")
    platform_model_ref = env["ir.model.data"].sudo().search(
        [("module", "=", "smart_core"), ("name", "=", model_data_name)],
        limit=1,
    )
    assert_true(platform_model_ref, f"model external id not owned by smart_core: {model_name}")

for model_name, xmlids in REQUIRED_PLATFORM_XMLIDS.items():
    for xmlid in xmlids:
        rec = env.ref(f"smart_core.{xmlid}", raise_if_not_found=False)
        assert_true(rec, f"missing platform XML id: smart_core.{xmlid}")
        assert_true(rec._name == model_name, f"wrong model for smart_core.{xmlid}: {rec._name}")
        assert_true(
            env["ir.model.data"].sudo().search(
                [("module", "=", "smart_core"), ("name", "=", xmlid), ("model", "=", model_name)],
                limit=1,
            ),
            f"platform XML id not owned by smart_core: {xmlid}",
        )

company = env.company
assert_true(company, "missing current company")

env["sc.subscription.plan"].sudo().ensure_platform_default_plans()
env["sc.subscription.plan"].sudo().ensure_platform_access_ownership()

legacy_access = env["ir.model.data"].sudo().search(
    [
        ("module", "=", "smart_construction_core"),
        ("name", "in", LEGACY_CONSTRUCTION_ACCESS_XMLIDS),
        ("model", "=", "ir.model.access"),
    ]
)
assert_true(not legacy_access, f"legacy construction ACL ownership remains: {legacy_access.mapped('name')}")

for model_name, xmlids in LEGACY_CONSTRUCTION_UI_XMLIDS.items():
    legacy_ui = env["ir.model.data"].sudo().search(
        [
            ("module", "=", "smart_construction_core"),
            ("name", "in", xmlids),
            ("model", "=", model_name),
        ]
    )
    assert_true(not legacy_ui, f"legacy construction UI ownership remains: {model_name} {legacy_ui.mapped('name')}")

plan = env["sc.subscription.plan"].sudo().search([("code", "=", "default"), ("active", "=", True)], limit=1)
if not plan:
    raise AssertionError("missing active default platform subscription plan")

pro_plan = env["sc.subscription.plan"].sudo().search([("code", "=", "pro"), ("active", "=", True)], limit=1)
assert_true(pro_plan, "missing active pro platform subscription plan")

sub = env["sc.subscription"].sudo().search([("company_id", "=", company.id)], limit=1)
if not sub:
    sub = env["sc.subscription"].sudo().create(
        {
            "company_id": company.id,
            "plan_id": plan.id,
            "state": "active",
            "is_trial": False,
        }
    )

entitlement = env["sc.entitlement"].sudo().get_effective(company)
assert_true(entitlement.company_id == company, "entitlement company mismatch")
assert_true(entitlement.plan_id, "entitlement plan missing")

env["sc.usage.counter"].sudo().bump(company, "platform_company_access_probe", 1)
usage = env["sc.usage.counter"].sudo().get_usage_map(company)
assert_true(usage.get("platform_company_access_probe", 0) >= 1, "usage counter did not update")

print(
    "PLATFORM_COMPANY_ACCESS_KERNEL_PROBE=PASS "
    f"models={len(REQUIRED_MODELS)} actions={len(REQUIRED_PLATFORM_XMLIDS['ir.actions.act_window'])} "
    f"menus={len(REQUIRED_PLATFORM_XMLIDS['ir.ui.menu'])} company_id={company.id} "
    f"plan={entitlement.plan_id.code} legacy_acl=0 legacy_ui=0"
)
