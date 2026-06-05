#!/usr/bin/env python3
"""Allow users to read direct-acceptance formal projections in formal menus.

Run with:
    DB_NAME=sc_demo MIGRATION_REPLAY_DB_ALLOWLIST=sc_demo \
      bash scripts/ops/odoo_shell_exec.sh < scripts/ops/direct_acceptance_formal_visibility_rules_apply.py
"""

from __future__ import annotations

import json
import os


MODULE = "smart_construction_core"
SOURCE_FACT_MODEL = "online_old_scbsly:direct_acceptance_fact"

RULES = [
    {
        "xml_name": "rule_sc_labor_usage_direct_acceptance_formal_read",
        "name": "SC Internal - direct acceptance labor formal read",
        "model": "sc.labor.usage",
        "domain": [("legacy_fact_model", "=", SOURCE_FACT_MODEL)],
    },
    {
        "xml_name": "rule_sc_subcontract_request_direct_acceptance_formal_read",
        "name": "SC Internal - direct acceptance subcontract formal read",
        "model": "sc.subcontract.request",
        "domain": [("legacy_fact_model", "=", SOURCE_FACT_MODEL)],
    },
]


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_direct_acceptance_visibility_rules": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def ensure_xmlid(record, name: str) -> None:
    Imd = env["ir.model.data"].sudo()  # noqa: F821
    existing = Imd.search([("module", "=", MODULE), ("name", "=", name), ("model", "=", record._name)], limit=1)
    if existing:
        if int(existing.res_id or 0) != int(record.id):
            existing.write({"res_id": int(record.id)})
        return
    Imd.create({"module": MODULE, "name": name, "model": record._name, "res_id": int(record.id), "noupdate": True})


ensure_allowed_db()
Rule = env["ir.rule"].sudo()  # noqa: F821
Model = env["ir.model"].sudo()  # noqa: F821
group = env.ref("smart_construction_core.group_sc_internal_user", raise_if_not_found=False)  # noqa: F821
if not group:
    raise RuntimeError({"missing_group": "smart_construction_core.group_sc_internal_user"})

results = []
for spec in RULES:
    model = Model.search([("model", "=", spec["model"])], limit=1)
    if not model:
        results.append({"status": "FAIL", "reason": "missing_model", **spec})
        continue
    values = {
        "name": spec["name"],
        "model_id": model.id,
        "domain_force": repr(spec["domain"]),
        "groups": [(6, 0, [group.id])],
        "perm_read": True,
        "perm_write": False,
        "perm_create": False,
        "perm_unlink": False,
        "active": True,
    }
    rule = env.ref(f"{MODULE}.{spec['xml_name']}", raise_if_not_found=False)  # noqa: F821
    if rule:
        rule.write(values)
        status = "UPDATED"
    else:
        rule = Rule.create(values)
        ensure_xmlid(rule, spec["xml_name"])
        status = "CREATED"
    results.append({"status": status, "xmlid": f"{MODULE}.{spec['xml_name']}", "rule_id": int(rule.id), "model": spec["model"]})

env.cr.commit()  # noqa: F821
payload = {
    "status": "PASS" if all(row["status"] in {"CREATED", "UPDATED"} for row in results) else "FAIL",
    "database": env.cr.dbname,  # noqa: F821
    "results": results,
}
print("DIRECT_ACCEPTANCE_FORMAL_VISIBILITY_RULES=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
