# -*- coding: utf-8 -*-
"""Runtime probe for platform-owned company access models."""

REQUIRED_MODELS = {
    "sc.subscription.plan": ["code", "active", "feature_flags_json", "limits_json"],
    "sc.subscription": ["company_id", "plan_id", "state", "start_date", "end_date"],
    "sc.entitlement": ["company_id", "plan_id", "effective_flags_json", "effective_limits_json"],
    "sc.usage.counter": ["company_id", "key", "value"],
    "sc.ops.job": ["name", "job_type", "status"],
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

company = env.company
assert_true(company, "missing current company")

plan = env["sc.subscription.plan"].sudo().search([("active", "=", True)], limit=1)
if not plan:
    plan = env["sc.subscription.plan"].sudo().create(
        {
            "name": "Probe Default",
            "code": "probe_default",
            "active": True,
            "feature_flags_json": {},
            "limits_json": {},
        }
    )

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
    f"models={len(REQUIRED_MODELS)} company_id={company.id} plan={entitlement.plan_id.code}"
)
