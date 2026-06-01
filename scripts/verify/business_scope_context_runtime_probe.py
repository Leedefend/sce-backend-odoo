# -*- coding: utf-8 -*-
"""Runtime probe for company/project/operation-strategy business scope."""

import json

from odoo.addons.smart_construction_core.handlers.project_entry_context_options import (
    ProjectEntryContextOptionsHandler,
)
from odoo.addons.smart_construction_core.handlers.project_entry_context_resolve import (
    ProjectEntryContextResolveHandler,
)
from odoo.addons.smart_core.core.project_context import apply_business_scope_domain
from odoo.addons.smart_core.handlers.api_data import ApiDataHandler
from odoo.addons.smart_core.handlers.project_context import ProjectContextSearchHandler


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def first_company():
    company = env.company
    assert_true(company, "missing current company")
    return company


def ensure_project(company, strategy):
    Project = env["project.project"].sudo()
    name = "BUSINESS-SCOPE-PROBE-%s-%s" % (company.id, strategy.upper())
    project = Project.search([("name", "=", name), ("company_id", "=", company.id)], limit=1)
    vals = {
        "name": name,
        "company_id": company.id,
        "operation_strategy": strategy,
    }
    if project:
        if project.operation_strategy != strategy or project.company_id.id != company.id:
            project.write(vals)
        return project
    return Project.create(vals)


def ensure_contract(project, strategy):
    Contract = env["sc.general.contract"].sudo()
    contract_name = "Business Scope Probe %s" % strategy.upper()
    contract = Contract.search(
        [("project_id", "=", project.id), ("contract_name", "=", contract_name)],
        limit=1,
    )
    vals = {
        "project_id": project.id,
        "contract_name": contract_name,
        "amount_total": 100.0 if strategy == "direct" else 200.0,
        "contract_direction": "neutral",
    }
    if contract:
        contract.write(vals)
        return contract
    vals["name"] = "BUSINESS-SCOPE-%s-%s" % (project.id, strategy.upper())
    return Contract.create(vals)


def api_list_contract_ids(company_id, operation_strategy, project_id=0):
    params = {
        "model": "sc.general.contract",
        "op": "list",
        "fields": ["id", "contract_name", "project_id", "company_id", "operation_strategy"],
        "limit": 20,
        "need_total": True,
        "company_id": company_id,
        "operation_strategy": operation_strategy,
    }
    if project_id:
        params["current_project_id"] = project_id
    result = ApiDataHandler(env).handle(**params)
    assert_true(isinstance(result, tuple) and len(result) == 2, "api.data list did not return data/meta tuple")
    data, meta = result
    assert_true(isinstance(data, dict), "api.data list data invalid")
    assert_true(isinstance(meta, dict), "api.data list meta invalid")
    return {int(row["id"]) for row in data.get("records") or []}, data, meta


def selector_options(company_id, operation_strategy, active_project_id=0):
    payload = {
        "params": {
            "company_id": company_id,
            "operation_strategy": operation_strategy,
            "project_id": active_project_id,
        }
    }
    result = ProjectEntryContextOptionsHandler(env, payload=payload).handle()
    assert_true(result.get("ok") is True, "project.entry.context.options failed")
    return result.get("data") or {}


def selector_resolve(project_id, company_id, operation_strategy):
    payload = {
        "params": {
            "project_id": project_id,
            "company_id": company_id,
            "operation_strategy": operation_strategy,
        }
    }
    result = ProjectEntryContextResolveHandler(env, payload=payload).handle()
    assert_true(result.get("ok") is True, "project.entry.context.resolve failed")
    return result.get("data") or {}


def record_context_search(company_id, operation_strategy):
    result = ProjectContextSearchHandler(env).handle(
        payload={
            "params": {
                "search": "BUSINESS-SCOPE-PROBE",
                "limit": 20,
                "company_id": company_id,
                "operation_strategy": operation_strategy,
            }
        }
    )
    assert_true(getattr(result, "ok", False) is True, "project.context.search failed")
    return result.data or {}


company = first_company()
direct_project = ensure_project(company, "direct")
joint_project = ensure_project(company, "joint")
direct_contract = ensure_contract(direct_project, "direct")
joint_contract = ensure_contract(joint_project, "joint")

direct_ids, direct_data, direct_meta = api_list_contract_ids(company.id, "direct")
joint_ids, joint_data, joint_meta = api_list_contract_ids(company.id, "joint")
assert_true(direct_contract.id in direct_ids, "direct contract missing from direct scoped list")
assert_true(joint_contract.id not in direct_ids, "joint contract leaked into direct scoped list")
assert_true(joint_contract.id in joint_ids, "joint contract missing from joint scoped list")
assert_true(direct_contract.id not in joint_ids, "direct contract leaked into joint scoped list")

mismatch_domain, mismatch_meta = apply_business_scope_domain(
    env["sc.general.contract"].sudo(),
    [],
    {"company_id": company.id, "current_project_id": direct_project.id, "operation_strategy": "joint"},
    {"company_id": company.id, "current_project_id": direct_project.id, "operation_strategy": "joint"},
)
assert_true(mismatch_meta.get("project_operation_strategy_mismatch") is True, "project/op mismatch not flagged")
assert_true(
    env["sc.general.contract"].sudo().search_count(mismatch_domain) == 0,
    "project/op mismatch should deny all records",
)

mismatch_ids, mismatch_data, mismatch_api_meta = api_list_contract_ids(company.id, "joint", project_id=direct_project.id)
assert_true(direct_contract.id not in mismatch_ids, "mismatched project/op list exposed direct contract")
assert_true(joint_contract.id not in mismatch_ids, "mismatched project/op list exposed joint contract")
assert_true(mismatch_api_meta.get("project_scope", {}).get("project_operation_strategy_mismatch") is True, "api mismatch meta missing")

direct_options = selector_options(company.id, "direct", active_project_id=direct_project.id)
joint_options = selector_options(company.id, "joint", active_project_id=joint_project.id)
direct_option_ids = {int(item.get("project_id") or 0) for item in direct_options.get("options") or []}
joint_option_ids = {int(item.get("project_id") or 0) for item in joint_options.get("options") or []}
assert_true(direct_project.id in direct_option_ids, "direct project missing from direct selector options")
assert_true(joint_project.id not in direct_option_ids, "joint project leaked into direct selector options")
assert_true(joint_project.id in joint_option_ids, "joint project missing from joint selector options")
assert_true(direct_project.id not in joint_option_ids, "direct project leaked into joint selector options")

resolved_direct = selector_resolve(direct_project.id, company.id, "direct")
resolved_mismatch = selector_resolve(direct_project.id, company.id, "joint")
assert_true(resolved_direct.get("available") is True, "direct project should resolve in direct scope")
assert_true(resolved_mismatch.get("available") is False, "direct project should not resolve in joint scope")

direct_record_context = record_context_search(company.id, "direct")
joint_record_context = record_context_search(company.id, "joint")
direct_record_context_ids = {int(item.get("id") or 0) for item in direct_record_context.get("options") or []}
joint_record_context_ids = {int(item.get("id") or 0) for item in joint_record_context.get("options") or []}
assert_true(direct_project.id in direct_record_context_ids, "direct project missing from sidebar project context search")
assert_true(joint_project.id not in direct_record_context_ids, "joint project leaked into direct sidebar project context search")
assert_true(joint_project.id in joint_record_context_ids, "joint project missing from sidebar project context search")
assert_true(direct_project.id not in joint_record_context_ids, "direct project leaked into joint sidebar project context search")

print(
    "BUSINESS_SCOPE_CONTEXT_RUNTIME_PROBE="
    + json.dumps(
        {
            "status": "PASS",
            "company_id": company.id,
            "direct_project_id": direct_project.id,
            "joint_project_id": joint_project.id,
            "direct_contract_id": direct_contract.id,
            "joint_contract_id": joint_contract.id,
            "direct_total": direct_data.get("total"),
            "joint_total": joint_data.get("total"),
            "mismatch_total": mismatch_data.get("total"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
