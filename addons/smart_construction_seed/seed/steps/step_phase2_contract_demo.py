# -*- coding: utf-8 -*-
from odoo.exceptions import UserError

from ..registry import SeedStep, register


def _find_demo_project(env):
    try:
        return env.ref("smart_construction_demo.sc_demo_project_001")
    except ValueError:
        return env["project.project"].sudo().search([], limit=1)


def _find_demo_partner(env):
    try:
        return env.ref("smart_construction_demo.sc_demo_partner_owner_001")
    except ValueError:
        Partner = env["res.partner"].sudo()
        partner = Partner.search([("name", "=", "Demo-合同相对方")], limit=1)
        if partner:
            return partner
        return Partner.create({"name": "Demo-合同相对方"})


def run(env):
    Contract = env["construction.contract"].sudo()
    project = _find_demo_project(env)
    if not project:
        raise UserError("缺少 demo 项目，无法创建示例合同。")

    partner = _find_demo_partner(env)
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
