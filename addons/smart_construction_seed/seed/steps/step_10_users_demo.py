# -*- coding: utf-8 -*-
import os

from odoo import api

from ..registry import SeedStep, register


def _ensure_lang(env, code):
    lang = env["res.lang"].sudo().search([("code", "=", code)], limit=1)
    if lang and not lang.active:
        lang.write({"active": True})


def _resolve_groups(env, xmlids):
    groups = []
    for xmlid in xmlids:
        group = env.ref(xmlid, raise_if_not_found=False)
        if group:
            groups.append(group)
    return groups


def _ensure_user(env, login, name, groups_xmlids, password, lang, tz):
    Users = env["res.users"].sudo()
    user = Users.search([("login", "=", login)], limit=1)
    groups = _resolve_groups(env, groups_xmlids)
    vals = {
        "name": name,
        "login": login,
        "password": password,
        "lang": lang,
        "tz": tz,
        "company_id": env.ref("base.main_company").id,
        "company_ids": [(6, 0, [env.ref("base.main_company").id])],
        "groups_id": [(6, 0, [g.id for g in groups])] if groups else False,
        "share": False,
        "active": True,
    }
    if user:
        user.write(vals)
    else:
        Users.create(vals)


def run(env):
    password = os.getenv("SC_DEMO_PASSWORD", "demo")
    lang = "zh_CN"
    tz = "Asia/Shanghai"
    _ensure_lang(env, lang)

    base_group = "base.group_user"

    _ensure_user(
        env,
        login="demo_full",
        name="Demo-全能力",
        groups_xmlids=[
            base_group,
            "smart_construction_core.group_sc_business_full",
        ],
        password=password,
        lang=lang,
        tz=tz,
    )
    _ensure_user(
        env,
        login="demo_pm",
        name="Demo-项目经理",
        groups_xmlids=[
            base_group,
            "smart_construction_core.group_sc_cap_project_manager",
            "smart_construction_core.group_sc_cap_contract_read",
            "smart_construction_core.group_sc_cap_cost_read",
            "smart_construction_core.group_sc_cap_purchase_read",
            "smart_construction_core.group_sc_cap_material_read",
            "smart_construction_core.group_sc_cap_settlement_read",
            "smart_construction_core.group_sc_cap_finance_read",
            "smart_construction_core.group_sc_cap_data_read",
        ],
        password=password,
        lang=lang,
        tz=tz,
    )
    _ensure_user(
        env,
        login="demo_finance",
        name="Demo-财务经办",
        groups_xmlids=[
            base_group,
            "smart_construction_core.group_sc_cap_finance_user",
        ],
        password=password,
        lang=lang,
        tz=tz,
    )
    _ensure_user(
        env,
        login="demo_cost",
        name="Demo-成控经办",
        groups_xmlids=[
            base_group,
            "smart_construction_core.group_sc_cap_cost_user",
        ],
        password=password,
        lang=lang,
        tz=tz,
    )
    _ensure_user(
        env,
        login="demo_readonly",
        name="Demo-只读",
        groups_xmlids=[
            base_group,
            "smart_construction_core.group_sc_cap_project_read",
        ],
        password=password,
        lang=lang,
        tz=tz,
    )


register(
    SeedStep(
        name="demo_10_users",
        description="Create demo_full/demo_pm/demo_finance/demo_cost/demo_readonly users.",
        run=run,
    )
)
