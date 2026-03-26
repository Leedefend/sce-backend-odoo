# -*- coding: utf-8 -*-
from odoo import fields

from odoo.addons.smart_construction_core.services.project_task_state_support import (
    ProjectTaskStateSupport,
)

from ..registry import SeedStep, register


SHOWROOM_PROJECTS = [
    {"name": "展厅-智能制造示范项目", "state": "in_progress", "with_chain": True, "demo_profile": "showroom"},
    {"name": "展厅-市政工程样板段", "state": "closing", "with_chain": True, "demo_profile": "showroom"},
    {"name": "展厅-工业园区建设一期", "state": "warranty", "with_chain": True, "demo_profile": "showroom"},
    {"name": "展厅-绿色建材基地", "state": "in_progress", "with_chain": True, "demo_profile": "showroom"},
    {"name": "展厅-智慧园区运营中心", "state": "in_progress", "with_chain": False, "demo_profile": "execution"},
    {"name": "展厅-产线升级改造工程", "state": "done", "with_chain": True, "demo_profile": "full_journey"},
    {"name": "展厅-城市更新综合体", "state": "closing", "with_chain": False, "demo_profile": "showroom"},
    {"name": "展厅-科技研发中心", "state": "warranty", "with_chain": False, "demo_profile": "showroom"},
    {"name": "展厅-海绵城市示范区", "state": "done", "with_chain": False, "demo_profile": "showroom"},
    {"name": "展厅-装配式住宅试点", "state": "in_progress", "with_chain": False, "demo_profile": "payment"},
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


def _apply_task_profile(project, profile):
    Task = project.env["project.task"].sudo()
    tasks = Task.search([("project_id", "=", project.id)], order="id asc")
    if not tasks:
        return

    progress_field = ""
    sample = tasks[:1]
    if sample:
        if "progress_rate" in sample._fields:
            progress_field = "progress_rate"
        elif "progress" in sample._fields:
            progress_field = "progress"

    def _mark_done(task):
        state = ProjectTaskStateSupport.normalize(getattr(task, "sc_state", "draft"))
        if state == "draft":
            task.action_prepare_task()
            state = "ready"
        if state == "ready":
            task.action_start_task()
            state = "in_progress"
        if state == "in_progress":
            if progress_field:
                task.sudo().write({progress_field: 1.0})
            task.action_mark_done()

    if profile == "full_journey":
        for task in tasks:
            _mark_done(task)
        return

    if profile == "payment":
        cutoff = max(int(len(tasks) * 0.75), 1)
        for idx, task in enumerate(tasks, start=1):
            if idx <= cutoff:
                _mark_done(task)
                continue
            state = ProjectTaskStateSupport.normalize(getattr(task, "sc_state", "draft"))
            if state == "draft":
                task.action_prepare_task()
                state = "ready"
            if state == "ready":
                task.action_start_task()
        return

    if profile == "execution":
        first_task = tasks[:1]
        if first_task:
            state = ProjectTaskStateSupport.normalize(getattr(first_task, "sc_state", "draft"))
            if state == "draft":
                first_task.action_prepare_task()
                state = "ready"
            if state == "ready":
                first_task.action_start_task()


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


def _ensure_project_prereqs(env, project):
    vals = {}
    if not project.owner_id:
        partner = env.ref("smart_construction_seed.seed_partner_contract", raise_if_not_found=False)
        if not partner:
            partner = env["res.partner"].sudo().create({"name": "Demo-业主单位"})
        vals["owner_id"] = partner.id
    if not project.location:
        vals["location"] = "示范区"
    if vals:
        project.write(vals)


def _ensure_showcase_flags(project, ready=False):
    vals = {"sc_demo_showcase": True, "sc_demo_showcase_ready": bool(ready)}
    if "health_state" in project._fields and not project.health_state:
        vals["health_state"] = "warn"
    project.write(vals)


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


def _ensure_cockpit_costs(env, project):
    CostLedger = env["project.cost.ledger"].sudo()
    CostCode = env["project.cost.code"].sudo()
    Partner = env["res.partner"].sudo()
    marker = "DEMO_COCKPIT_R2"
    if CostLedger.search_count([("project_id", "=", project.id), ("note", "ilike", f"{marker}-%")]) >= 4:
        return
    cost_code = CostCode.search([], order="id asc", limit=1)
    partner = project.partner_id or Partner.search([("is_company", "=", True)], order="id asc", limit=1)
    if not cost_code or not partner:
        return
    samples = [
        ("材料采购", 1_180_000.0, 5),
        ("人工费用", 820_000.0, 15),
        ("机械费用", 430_000.0, 25),
        ("分包结算", 1_650_000.0, 35),
    ]
    today = fields.Date.context_today(env.user)
    for note_text, amount, delta in samples:
        note = f"{marker}-{note_text}"
        existing = CostLedger.search([("project_id", "=", project.id), ("note", "=", note)], limit=1)
        vals = {
            "project_id": project.id,
            "cost_code_id": cost_code.id,
            "date": fields.Date.subtract(today, days=delta),
            "period": fields.Date.subtract(today, days=delta).strftime("%Y-%m"),
            "amount": amount,
            "partner_id": partner.id,
            "note": note,
        }
        if existing:
            existing.write(vals)
        else:
            CostLedger.create(vals)


def _ensure_cockpit_settlement(env, project):
    Settlement = env["sc.settlement.order"].sudo()
    Line = env["sc.settlement.order.line"].sudo()
    Contract = env["construction.contract"].sudo()
    Partner = env["res.partner"].sudo()
    marker = "DEMO_COCKPIT_R2"
    partner = project.partner_id or Partner.search([("is_company", "=", True)], order="id asc", limit=1)
    if not partner:
        return False
    contract = Contract.search([("project_id", "=", project.id), ("type", "=", "in")], order="id asc", limit=1)
    settlement = Settlement.search([("project_id", "=", project.id), ("name", "=", f"{marker}-SO-{project.id}")], limit=1)
    if not settlement:
        settlement = Settlement.create(
            {
                "name": f"{marker}-SO-{project.id}",
                "project_id": project.id,
                "contract_id": contract.id if contract else False,
                "partner_id": partner.id,
                "settlement_type": "out",
                "note": marker,
            }
        )
    if not settlement.line_ids:
        Line.create(
            {
                "settlement_id": settlement.id,
                "name": "Demo-样板结算行",
                "qty": 1.0,
                "price_unit": 2_200_000.0,
            }
        )
    if settlement.state != "done":
        settlement.action_done()
    return settlement


def _ensure_cockpit_payments(env, project, settlement=False):
    Payment = env["payment.request"].sudo()
    Contract = env["construction.contract"].sudo()
    Partner = env["res.partner"].sudo()
    marker = "DEMO_COCKPIT_R2"
    partner = project.partner_id or Partner.search([("is_company", "=", True)], order="id asc", limit=1)
    if not partner:
        return
    pay_contract = Contract.search([("project_id", "=", project.id), ("type", "=", "in")], order="id asc", limit=1)
    samples = [
        ("receive", "approved", 2_800_000.0, "节点回款A"),
        ("receive", "done", 1_650_000.0, "节点回款B"),
        ("pay", "draft", 1_200_000.0, "分包付款A"),
        ("pay", "draft", 860_000.0, "材料付款B"),
    ]
    for req_type, state, amount, note_text in samples:
        name = f"{marker}-{project.id}-{note_text}"
        existing = Payment.search([("project_id", "=", project.id), ("name", "=", name)])
        # Demo seed must be replayable. Rebuild marker-owned payment records instead of
        # mutating their workflow state in place, which would trip payment guards.
        if existing:
            existing.unlink()
        vals = {
            "name": name,
            "project_id": project.id,
            "partner_id": partner.id,
            "type": req_type,
            "state": state,
            "amount": amount,
            "note": marker,
        }
        if req_type == "pay":
            vals["contract_id"] = pay_contract.id if pay_contract else False
            vals["settlement_id"] = settlement.id if settlement else False
        Payment.create(vals)


def _finalize_cockpit_payments(env, project):
    Payment = env["payment.request"].sudo()
    marker = "DEMO_COCKPIT_R2"
    payments = Payment.search(
        [
            ("project_id", "=", project.id),
            ("type", "=", "pay"),
            ("name", "ilike", f"{marker}-%"),
            ("settlement_id", "!=", False),
        ],
        order="id asc",
    )
    for idx, payment in enumerate(payments, start=1):
        if payment.state != "approved":
            env.cr.execute(
                "UPDATE payment_request SET state=%s, validation_status=%s WHERE id=%s",
                ("approved", "validated", payment.id),
            )
            env.invalidate_all()
            payment = Payment.browse(payment.id)
        payment._ensure_payment_ledger(
            paid_at=fields.Datetime.now(),
            ref=f"DEMO_COCKPIT_LEDGER-{project.id}-{idx:02d}",
            note=marker,
        )
        env.cr.execute(
            "UPDATE payment_request SET state=%s, validation_status=%s WHERE id=%s",
            ("done", "validated", payment.id),
        )
        env.invalidate_all()


def _cleanup_cockpit_costs(env, project):
    CostLedger = env["project.cost.ledger"].sudo()
    CostLedger.search([("project_id", "=", project.id), ("note", "ilike", "DEMO_COCKPIT_R2-%")]).unlink()


def _cleanup_cockpit_payments(env, project):
    Payment = env["payment.request"].sudo()
    Payment.search(
        [
            ("project_id", "=", project.id),
            "|",
            ("note", "=", "DEMO_COCKPIT_R2"),
            ("name", "ilike", "DEMO_COCKPIT_R2-%"),
        ]
    ).unlink()


def _apply_demo_profile(env, project, spec):
    profile = spec.get("demo_profile") or "showroom"
    if profile == "execution":
        _cleanup_cockpit_costs(env, project)
        _cleanup_cockpit_payments(env, project)
        _apply_task_profile(project, profile)
        project.write({
            "sc_demo_showcase": True,
            "sc_demo_showcase_ready": True,
            "sc_execution_state": "in_progress",
            "health_state": "warn",
        })
        return
    if profile == "payment":
        _ensure_cockpit_costs(env, project)
        _cleanup_cockpit_payments(env, project)
        _apply_task_profile(project, profile)
        project.write({
            "sc_demo_showcase": True,
            "sc_demo_showcase_ready": True,
            "sc_execution_state": "done",
            "health_state": "warn",
        })
        return
    if profile == "full_journey":
        _ensure_cockpit_costs(env, project)
        _cleanup_cockpit_payments(env, project)
        settlement = _ensure_cockpit_settlement(env, project)
        _ensure_cockpit_payments(env, project, settlement=settlement)
        _finalize_cockpit_payments(env, project)
        _apply_task_profile(project, profile)
        project.write({
            "sc_demo_showcase": True,
            "sc_demo_showcase_ready": True,
            "sc_execution_state": "done",
            "health_state": "good",
        })
        return
    _ensure_showcase_flags(project, ready=False)


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
            _ensure_project_prereqs(env, project)
            _ensure_lifecycle(project, spec["state"])
        if spec["with_chain"]:
            _ensure_contract_chain(env, project, idx)
        _apply_demo_profile(env, project, spec)

    env["ir.config_parameter"].sudo().set_param("sc.seed.demo_showroom", "1")
    return {"ok": True, "projects": len(SHOWROOM_PROJECTS)}


register(
    SeedStep(
        name="demo_showroom",
        description="Create showroom-friendly projects, tasks, and happy-path docs.",
        run=run,
    )
)
