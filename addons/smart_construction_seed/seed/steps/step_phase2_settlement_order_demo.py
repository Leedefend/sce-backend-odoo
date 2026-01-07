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


def _ensure_demo_contract(env):
    Contract = env["construction.contract"].sudo()
    subject = "Demo 合同-收入"
    contract = Contract.search([("subject", "=", subject)], limit=1)
    if contract:
        return contract

    project = _find_demo_project(env)
    if not project:
        raise UserError("缺少 demo 项目，无法创建示例合同。")

    partner = _find_demo_partner(env)
    return Contract.create(
        {
            "subject": subject,
            "type": "out",
            "project_id": project.id,
            "partner_id": partner.id,
            "date_contract": "2025-02-01",
        }
    )


def run(env):
    Settlement = env["sc.settlement.order"].sudo()
    name_prefix = "DEMO-SO-"
    marker = "seed:phase2_settlement_order_demo"

    existing = Settlement.search([("name", "=like", f"{name_prefix}%")], limit=1)
    if existing:
        env["ir.config_parameter"].sudo().set_param("sc.seed.settlement_order_count", "1")
        return {"ok": True, "settlement_id": existing.id}

    contract = _ensure_demo_contract(env)
    project = contract.project_id
    if not project:
        raise UserError("示例合同缺少项目，无法创建结算单。")

    partner = contract.partner_id or _find_demo_partner(env)
    settlement_type = "in" if contract.type == "out" else "out"

    record = Settlement.create(
        {
            "name": f"{name_prefix}001",
            "project_id": project.id,
            "contract_id": contract.id,
            "partner_id": partner.id,
            "settlement_type": settlement_type,
            "note": marker,
        }
    )
    env["ir.config_parameter"].sudo().set_param("sc.seed.settlement_order_count", "1")
    return {"ok": True, "created": 1, "settlement_id": record.id}


register(
    SeedStep(
        name="phase2_settlement_order_demo",
        description="Create demo settlement order bound to demo contract.",
        run=run,
    )
)
