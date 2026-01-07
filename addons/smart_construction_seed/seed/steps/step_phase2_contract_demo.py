# -*- coding: utf-8 -*-
from odoo.exceptions import UserError

from ..registry import SeedStep, register


def _find_demo_project(env):
    try:
        return env.ref("smart_construction_demo.sc_demo_project_001")
    except ValueError:
        return env["project.project"].sudo().search([], limit=1)


def _find_demo_partner(env):
    partner = env.ref("smart_construction_seed.seed_partner_contract", raise_if_not_found=False)
    if partner:
        return partner
    partner = env.ref("smart_construction_demo.sc_demo_partner_owner_001", raise_if_not_found=False)
    if partner:
        return partner
    Partner = env["res.partner"].sudo()
    existing = Partner.search([("name", "=", "Demo-合同相对方")], limit=1)
    if existing:
        return existing
    return Partner.create({"name": "Demo-合同相对方"})


def run(env):
    Contract = env["construction.contract"].sudo()
    project = _find_demo_project(env)
    if not project:
        raise UserError("缺少 demo 项目，无法创建示例合同。")

    partner = _find_demo_partner(env)
    tax = env.ref("smart_construction_seed.tax_sale_9", raise_if_not_found=False)
    subject = "Demo 合同-收入"

    existing = Contract.search(
        [("subject", "=", subject), ("project_id", "=", project.id)],
        limit=1,
    )
    if existing:
        return {"ok": True, "contract_id": existing.id}

    Contract.create(
        {
            "subject": subject,
            "type": "out",
            "project_id": project.id,
            "partner_id": partner.id,
            "tax_id": tax.id if tax else False,
            "date_contract": "2025-02-01",
        }
    )
    env["ir.config_parameter"].sudo().set_param("sc.seed.phase2_contract_demo", "1")
    return {"ok": True, "created": 1}


register(
    SeedStep(
        name="phase2_contract_demo",
        description="Create demo contract bound to a demo project.",
        run=run,
    )
)
