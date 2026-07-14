# -*- coding: utf-8 -*-
"""Deterministic browser fixture for frontend productization acceptance.

This module is deliberately hosted by ``smart_construction_demo``.  It is an
administrative data builder for non-production demo databases; authorization
is verified separately with the real fixture users and without sudo.
"""

from __future__ import annotations

from typing import Any, Dict


MODULE = "smart_construction_demo"
PASSWORD = "demo"


def _ref(env, xmlid):
    record = env.ref(xmlid, raise_if_not_found=False)
    if not record:
        raise RuntimeError("missing required xmlid: %s" % xmlid)
    return record


def _bind_xmlid(env, name, record):
    imd = env["ir.model.data"].sudo()
    row = imd.search([("module", "=", MODULE), ("name", "=", name)], limit=1)
    values = {"model": record._name, "res_id": record.id, "noupdate": True}
    if row:
        row.write(values)
    else:
        imd.create({"module": MODULE, "name": name, **values})


def _upsert(env, model_name, xmlid_name, domain, values):
    model = env[model_name].sudo().with_context(active_test=False, tracking_disable=True)
    record = env.ref("%s.%s" % (MODULE, xmlid_name), raise_if_not_found=False)
    if record and record._name != model_name:
        raise RuntimeError("xmlid %s points to %s" % (xmlid_name, record._name))
    if not record:
        matches = model.search(domain)
        if len(matches) > 1:
            raise RuntimeError("fixture domain is not unique: %s %s" % (model_name, domain))
        record = matches[:1]
    if record:
        changed = {}
        for field_name, value in values.items():
            field = record._fields[field_name]
            current = record[field_name]
            if field.type == "many2one":
                is_equal = current.id == (value or False)
            elif field.type in ("one2many", "many2many"):
                is_equal = False
            else:
                is_equal = current == value
            if not is_equal:
                changed[field_name] = value
        if changed:
            record.write(changed)
    else:
        record = model.create(values)
    _bind_xmlid(env, xmlid_name, record)
    return record


def _company(env, suffix):
    name = "FE Company %s" % suffix
    return _upsert(
        env,
        "res.company",
        "fe_company_%s" % suffix.lower(),
        [("name", "=", name)],
        {
            "name": name,
            "currency_id": _ref(env, "base.CNY").id,
            "country_id": _ref(env, "base.cn").id,
        },
    )


def _user(env, login, name, company, companies, group_xmlids):
    groups = [_ref(env, "base.group_user")]
    groups.extend(_ref(env, xmlid) for xmlid in group_xmlids)
    return _upsert(
        env,
        "res.users",
        "fe_user_%s" % login.replace("demo_role_", ""),
        [("login", "=", login)],
        {
            "name": name,
            "login": login,
            "email": "%s@example.invalid" % login,
            "active": True,
            "share": False,
            "lang": "zh_CN",
            "tz": "Asia/Shanghai",
            "company_id": company.id,
            "company_ids": [(6, 0, [item.id for item in companies])],
            "groups_id": [(6, 0, [group.id for group in groups])],
            "password": PASSWORD,
        },
    )


def _partner(env, suffix, company):
    name = "FE-%s Counterparty" % suffix
    return _upsert(
        env,
        "res.partner",
        "fe_partner_%s" % suffix.lower(),
        [("name", "=", name), ("company_id", "=", company.id)],
        {
            "name": name,
            "company_id": company.id,
            "is_company": True,
            "company_type": "company",
            "supplier_rank": 1,
        },
    )


def _tax(env, suffix, company):
    helper = env["construction.contract"].sudo().with_company(company)
    group = helper._sc_contract_tax_group(company)
    name = helper._sc_format_contract_tax_name(13.0)
    return _upsert(
        env,
        "account.tax",
        "fe_tax_%s" % suffix.lower(),
        [
            ("company_id", "=", company.id),
            ("type_tax_use", "=", "none"),
            ("amount_type", "=", "percent"),
            ("amount", "=", 13.0),
        ],
        {
            "name": name,
            "company_id": company.id,
            "country_id": company.account_fiscal_country_id.id or _ref(env, "base.cn").id,
            "tax_group_id": group.id,
            "amount": 13.0,
            "amount_type": "percent",
            "type_tax_use": "none",
            "price_include": False,
            "active": True,
        },
    )


def _project(env, suffix, company, manager, partner):
    name = "FE Project %s" % suffix
    values = {
        "name": name,
        "code": "FE-%s" % suffix,
        "company_id": company.id,
        "partner_id": partner.id,
        "user_id": manager.id,
        "manager_id": manager.id,
        "privacy_visibility": "followers",
        "funding_enabled": True,
        "active": True,
    }
    if "project_code" in env["project.project"]._fields:
        values["project_code"] = "FE-%s" % suffix
    return _upsert(
        env,
        "project.project",
        "fe_project_%s" % suffix.lower(),
        [("name", "=", name), ("company_id", "=", company.id)],
        values,
    )


def _funding_baseline(env, suffix, project):
    return _upsert(
        env,
        "project.funding.baseline",
        "fe_funding_baseline_%s" % suffix.lower(),
        [("project_id", "=", project.id), ("state", "=", "active")],
        {
            "project_id": project.id,
            "total_amount": 5000.0,
            "state": "active",
        },
    )


def _contract(env, suffix, project, partner, tax, state, amount):
    subject = "FE-%s Contract" % suffix
    record = _upsert(
        env,
        "construction.contract",
        "fe_contract_%s" % suffix.lower(),
        [("subject", "=", subject), ("project_id", "=", project.id)],
        {
            "subject": subject,
            "type": "in",
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": project.company_id.id,
            "currency_id": project.company_id.currency_id.id,
            "tax_id": tax.id,
            "state": state,
            "active": True,
        },
    )
    line = _upsert(
        env,
        "construction.contract.line",
        "fe_contract_line_%s" % suffix.lower(),
        [("contract_id", "=", record.id), ("note", "=", "FE-%s fixed line" % suffix)],
        {
            "contract_id": record.id,
            "qty_contract": 1.0,
            "price_contract": amount,
            "note": "FE-%s fixed line" % suffix,
        },
    )
    record.invalidate_recordset()
    return record, line


def _settlement(env, suffix, project, contract, partner, state, amount):
    name = "FE-%s-SET-001" % suffix
    record = _upsert(
        env,
        "sc.settlement.order",
        "fe_settlement_%s" % suffix.lower(),
        [("name", "=", name), ("project_id", "=", project.id)],
        {
            "name": name,
            "title": "FE-%s Settlement" % suffix,
            "project_id": project.id,
            "contract_id": contract.id,
            "partner_id": partner.id,
            "settlement_unit_id": partner.id,
            "settlement_type": "out",
            "company_id": project.company_id.id,
            "currency_id": project.company_id.currency_id.id,
            "state": state,
        },
    )
    _upsert(
        env,
        "sc.settlement.order.line",
        "fe_settlement_line_%s" % suffix.lower(),
        [("settlement_id", "=", record.id), ("name", "=", "FE-%s fixed line" % suffix)],
        {
            "settlement_id": record.id,
            "contract_id": contract.id,
            "name": "FE-%s fixed line" % suffix,
            "qty": 1.0,
            "price_unit": amount,
        },
    )
    record.invalidate_recordset()
    return record


def _request(env, suffix, sequence, project, contract, settlement, partner, state, amount):
    name = "FE-%s-PR-%03d" % (suffix, sequence)
    category = _ref(env, "smart_construction_core.business_category_finance_payment_apply_pay")
    return _upsert(
        env,
        "payment.request",
        "fe_request_%s_%03d" % (suffix.lower(), sequence),
        [("name", "=", name), ("project_id", "=", project.id)],
        {
            "name": name,
            "type": "pay",
            "business_category_id": category.id,
            "project_id": project.id,
            "contract_id": contract.id,
            "settlement_id": settlement.id,
            "partner_id": partner.id,
            "currency_id": project.company_id.currency_id.id,
            "amount": amount,
            "state": state,
            "note": "FE-%s deterministic payment request" % suffix,
        },
    )


def _execution(env, suffix, project, contract, request, partner, state, amount):
    name = "FE-%s-PE-001" % suffix
    return _upsert(
        env,
        "sc.payment.execution",
        "fe_execution_%s" % suffix.lower(),
        [("name", "=", name), ("project_id", "=", project.id)],
        {
            "name": name,
            "project_id": project.id,
            "contract_id": contract.id,
            "payment_request_id": request.id,
            "partner_id": partner.id,
            "currency_id": project.company_id.currency_id.id,
            "planned_amount": amount,
            "paid_amount": amount if state == "paid" else 0.0,
            "state": state,
            "document_no": name,
            "note": "FE-%s deterministic payment execution" % suffix,
            "active": True,
        },
    )


def ensure_fixture(env) -> Dict[str, Any]:
    """Create or reconcile the fixed dataset and return a secret-free summary."""
    module = env["ir.module.module"].sudo().search([("name", "=", MODULE)], limit=1)
    if not module or module.state != "installed":
        raise RuntimeError("smart_construction_demo must be installed before fixture initialization")

    company_a = _company(env, "A")
    company_b = _company(env, "B")

    finance = _user(
        env,
        "demo_role_finance",
        "Demo Role Finance",
        company_a,
        [company_a, company_b],
        ["smart_construction_custom.group_sc_role_finance"],
    )
    project_member = _user(
        env,
        "demo_role_project_a_member",
        "Demo Project A Member",
        company_a,
        [company_a],
        [
            "smart_construction_core.group_sc_cap_project_read",
            "smart_construction_core.group_sc_cap_business_initiator",
        ],
    )
    pm = _user(
        env,
        "demo_role_pm",
        "Demo Role PM",
        company_a,
        [company_a],
        ["smart_construction_custom.group_sc_role_pm"],
    )
    owner = _user(
        env,
        "demo_role_owner",
        "Demo Role Owner",
        company_a,
        [company_a],
        ["smart_construction_custom.group_sc_role_owner"],
    )

    partner_a = _partner(env, "A", company_a)
    partner_b = _partner(env, "B", company_a)
    partner_c = _partner(env, "C", company_b)
    tax_a = _tax(env, "A", company_a)
    tax_b = _tax(env, "B", company_b)
    project_a = _project(env, "A", company_a, pm, partner_a)
    project_b = _project(env, "B", company_a, pm, partner_b)
    project_c = _project(env, "C", company_b, finance, partner_c)

    # Keep the PM journey deterministic even when the database previously carried
    # unrelated demo projects assigned to the same fixed login.
    historical_pm_projects = env["project.project"].sudo().search(
        [
            ("id", "not in", [project_a.id, project_b.id]),
            "|",
            ("user_id", "=", pm.id),
            ("manager_id", "=", pm.id),
        ]
    )
    if historical_pm_projects:
        historical_pm_projects.write({"user_id": False, "manager_id": False})

    follower_model = env["mail.followers"].sudo()
    fixture_partners = [project_member.partner_id.id, pm.partner_id.id]
    follower_model.search(
        [("res_model", "=", "project.project"), ("partner_id", "in", fixture_partners)]
    ).unlink()
    project_a.message_subscribe(partner_ids=[project_member.partner_id.id, pm.partner_id.id])
    project_b.message_subscribe(partner_ids=[pm.partner_id.id])

    _funding_baseline(env, "A", project_a)
    _funding_baseline(env, "B", project_b)
    _funding_baseline(env, "C", project_c)

    contract_a, _ = _contract(env, "A", project_a, partner_a, tax_a, "confirmed", 1000.0)
    contract_b, _ = _contract(env, "B", project_b, partner_b, tax_a, "draft", 1000.0)
    contract_c, _ = _contract(env, "C", project_c, partner_c, tax_b, "confirmed", 1000.0)
    settlement_a = _settlement(env, "A", project_a, contract_a, partner_a, "approve", 1000.0)
    settlement_b = _settlement(env, "B", project_b, contract_b, partner_b, "draft", 1000.0)
    settlement_c = _settlement(env, "C", project_c, contract_c, partner_c, "approve", 1000.0)
    request_a = _request(env, "A", 1, project_a, contract_a, settlement_a, partner_a, "approved", 1000.0)
    _request(env, "A", 2, project_a, contract_a, settlement_a, partner_a, "draft", 250.0)
    request_b = _request(env, "B", 1, project_b, contract_b, settlement_b, partner_b, "draft", 1000.0)
    request_c = _request(env, "C", 1, project_c, contract_c, settlement_c, partner_c, "approved", 1000.0)
    _execution(env, "A", project_a, contract_a, request_a, partner_a, "paid", 1000.0)
    _execution(env, "B", project_b, contract_b, request_b, partner_b, "draft", 1000.0)
    _execution(env, "C", project_c, contract_c, request_c, partner_c, "confirmed", 1000.0)

    env.cr.commit()
    return {
        "db": env.cr.dbname,
        "users": [finance.login, project_member.login, pm.login, owner.login],
        "companies": [company_a.name, company_b.name],
        "projects": [project_a.name, project_b.name, project_c.name],
        "records": {
            "contracts": 3,
            "settlements": 3,
            "payment_requests": 4,
            "payment_executions": 3,
        },
    }
