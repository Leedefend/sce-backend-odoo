# -*- coding: utf-8 -*-
from odoo import fields

from ..registry import SeedStep, register


SHOWROOM_PROJECTS = [
    {"name": "展厅-智能制造示范项目", "state": "in_progress", "with_chain": True},
    {"name": "展厅-市政工程样板段", "state": "closing", "with_chain": True},
    {"name": "展厅-工业园区建设一期", "state": "warranty", "with_chain": True},
    {"name": "展厅-绿色建材基地", "state": "in_progress", "with_chain": True},
    {"name": "展厅-智慧园区运营中心", "state": "in_progress", "with_chain": False},
    {"name": "展厅-产线升级改造工程", "state": "done", "with_chain": False},
    {"name": "展厅-城市更新综合体", "state": "closing", "with_chain": False},
    {"name": "展厅-科技研发中心", "state": "warranty", "with_chain": False},
    {"name": "展厅-海绵城市示范区", "state": "done", "with_chain": False},
    {"name": "展厅-装配式住宅试点", "state": "in_progress", "with_chain": False},
]

TASKS_PER_PROJECT = 12


def _get_demo_user(env, login):
    return env["res.users"].sudo().search([("login", "=", login)], limit=1)


def _ensure_boq(env, project, idx):
    Boq = env["project.boq.line"].sudo()
    if Boq.search_count([("project_id", "=", project.id)]) > 0:
        return
    uom_unit = env.ref("uom.product_uom_unit")
    code_prefix = f"SR-{idx:02d}"
    Boq.create(
        {
            "project_id": project.id,
            "code": f"{code_prefix}-001",
            "name": f"{project.name}-清单项",
            "uom_id": uom_unit.id,
            "quantity": 10.0,
            "price": 120.0,
            "section_type": "building",
        }
    )


def _ensure_tasks(env, project, user, target):
    Task = env["project.task"].sudo()
    existing = Task.search([("project_id", "=", project.id)])
    if len(existing) >= target:
        return
    start = len(existing) + 1
    for i in range(start, target + 1):
        vals = {
            "name": f"{project.name}-任务 {i:02d}",
            "project_id": project.id,
        }
        if user:
            vals["user_ids"] = [(6, 0, [user.id])]
        Task.create(vals)


def _ensure_lifecycle(project, target_state):
    if project.lifecycle_state != "draft":
        return
    if target_state == "in_progress":
        project.action_set_lifecycle_state("in_progress")
    elif target_state == "closing":
        project.action_set_lifecycle_state("in_progress")
        project.action_set_lifecycle_state("closing")
    elif target_state == "done":
        project.action_set_lifecycle_state("in_progress")
        project.action_set_lifecycle_state("done")
    elif target_state == "warranty":
        project.action_set_lifecycle_state("in_progress")
        project.action_set_lifecycle_state("done")
        project.action_set_lifecycle_state("warranty")


def _ensure_contract_chain(env, project, idx):
    partner = env.ref("smart_construction_seed.seed_partner_contract", raise_if_not_found=False)
    if not partner:
        partner = env["res.partner"].sudo().create({"name": "Demo-合同相对方"})

    Contract = env["construction.contract"].sudo()
    tax = env.ref("smart_construction_seed.tax_purchase_13", raise_if_not_found=False)
    if not tax:
        tax = Contract._get_default_tax("in")

    subject = f"展厅合同-支出-{idx:02d}"
    contract = Contract.search(
        [("subject", "=", subject), ("project_id", "=", project.id)],
        limit=1,
    )
    if not contract:
        contract = Contract.create(
            {
                "subject": subject,
                "type": "in",
                "project_id": project.id,
                "partner_id": partner.id,
                "tax_id": tax.id if tax else False,
                "date_contract": fields.Date.context_today(env.user),
            }
        )

    Settlement = env["sc.settlement.order"].sudo()
    Line = env["sc.settlement.order.line"].sudo()
    settle_name = f"SHOW-SO-{idx:02d}"
    settlement = Settlement.search([("name", "=", settle_name)], limit=1)
    if not settlement:
        settlement = Settlement.create(
            {
                "name": settle_name,
                "project_id": project.id,
                "contract_id": contract.id,
                "partner_id": partner.id,
                "settlement_type": "out",
                "note": "seed:demo_showroom",
            }
        )
    if not settlement.line_ids:
        Line.create(
            {
                "settlement_id": settlement.id,
                "name": "展厅-结算行",
                "qty": 1.0,
                "price_unit": 100.0,
            }
        )
    if settlement.state != "done":
        settlement.action_done()

    Payment = env["payment.request"].sudo()
    pay_name = f"SHOW-PR-{idx:02d}"
    payment = Payment.search([("name", "=", pay_name)], limit=1)
    if not payment:
        Payment.create(
            {
                "name": pay_name,
                "type": "pay",
                "project_id": project.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "partner_id": partner.id,
                "amount": 50.0,
                "note": "seed:demo_showroom",
            }
        )


def run(env):
    Project = env["project.project"].sudo()
    demo_pm = _get_demo_user(env, "demo_pm")
    for idx, spec in enumerate(SHOWROOM_PROJECTS, start=1):
        project = Project.search([("name", "=", spec["name"])], limit=1)
        created = False
        if not project:
            project = Project.create({"name": spec["name"]})
            created = True
        _ensure_boq(env, project, idx)
        _ensure_tasks(env, project, demo_pm, TASKS_PER_PROJECT)
        if created or project.lifecycle_state == "draft":
            _ensure_lifecycle(project, spec["state"])
        if spec["with_chain"]:
            _ensure_contract_chain(env, project, idx)

    env["ir.config_parameter"].sudo().set_param("sc.seed.demo_showroom", "1")
    return {"ok": True, "projects": len(SHOWROOM_PROJECTS)}


register(
    SeedStep(
        name="demo_showroom",
        description="Create showroom-friendly projects, tasks, and happy-path docs.",
        run=run,
    )
)
