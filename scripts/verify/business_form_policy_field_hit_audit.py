# -*- coding: utf-8 -*-
"""Audit business-category form policies against their target model fields.

Run inside Odoo shell:
    docker compose exec -T odoo odoo shell -c /var/lib/odoo/odoo.conf -d sc_demo < scripts/verify/business_form_policy_field_hit_audit.py
"""

import json


Category = env["sc.business.category"].sudo()
categories = Category.search([], order="domain, code")
errors = []

for category in categories:
    if category.target_model not in env:
        errors.append("%s: missing target model %s" % (category.code, category.target_model))
        continue

    fields = set(env[category.target_model]._fields)
    policy = json.loads(category.form_policy_json or "{}")
    requested = []
    for section in policy.get("sections") or []:
        for field_name in section.get("fields") or []:
            if field_name and field_name not in requested:
                requested.append(field_name)

    missing = [field_name for field_name in requested if field_name not in fields]
    if missing:
        errors.append(
            "%s: target_model=%s missing_fields=%s"
            % (category.code, category.target_model, ",".join(missing))
        )

print(
    "business_form_policy_field_hit checked=%s errors=%s"
    % (len(categories), len(errors))
)
for error in errors:
    print("ERROR", error)
if errors:
    raise SystemExit(1)
print("business form policy field hit audit passed")
