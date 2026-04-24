# -*- coding: utf-8 -*-
from odoo import fields
from odoo.exceptions import UserError

from ..registry import SeedStep, register


PROJECT_INIT_CODE = "DEMO-PJ-INIT"
PROJECT_TENDER_CODE = "DEMO-PJ-TENDER"
PROJECT_EXEC_CODE = "DEMO-PJ-EXEC"
STAGE_PROJECT_CODES = [
    "DEMO-PJ-STAGE-DRAFT",
    "DEMO-PJ-STAGE-RUN",
    "DEMO-PJ-STAGE-PAUSE",
    "DEMO-PJ-STAGE-CLOSING",
    "DEMO-PJ-STAGE-DONE",
    "DEMO-PJ-STAGE-WARRANTY",
    "DEMO-PJ-STAGE-CLOSED",
]
WARN_PROJECT_CODES = {
    "DEMO-PJ-INIT",
    "DEMO-PJ-TENDER",
}
ALL_DEMO_PROJECT_CODES = [
    "DEMO-PJ-INIT",
    "DEMO-PJ-TENDER",
    "DEMO-PJ-EXEC",
] + STAGE_PROJECT_CODES
RATIO_TARGETS = [0.0, 0.7, 0.95, 1.0]


def _get_project(env, code):
    return env["project.project"].sudo().search([("project_code", "=", code)], limit=1)


def _get_showroom_projects(env):
    Project = env["project.project"].sudo()
    domain = [
        "|",
        "|",
        ("name", "ilike", "展厅-"),
        ("name", "ilike", "演示项目"),
        ("project_code", "ilike", "DEMO-"),
    ]
    return Project.search(domain)


def _verify_demo_full_my_work(env):
    Users = env["res.users"].sudo()
    demo_full = Users.search([("login", "=", "demo_full")], limit=1)
    if not demo_full:
        raise UserError("demo_full missing for my_work verification.")

    partner = demo_full.partner_id
    Project = env["project.project"].sudo()
    Task = env["project.task"].sudo()
    Activity = env["mail.activity"].sudo()
    Message = env["mail.message"].sudo()
    Followers = env["mail.followers"].sudo()

    project_count = Project.search_count([("doc_manager_id", "=", demo_full.id)]) if "doc_manager_id" in Project._fields else 0
    task_count = Task.search_count([("user_ids", "in", demo_full.id)]) if "user_ids" in Task._fields else 0
    activity_count = Activity.search_count([("user_id", "=", demo_full.id)])
    mention_count = Message.search_count([("partner_ids", "in", partner.id)]) if partner else 0
    follow_count = Followers.search_count([("partner_id", "=", partner.id)]) if partner else 0

    if project_count <= 0:
        raise UserError("demo_full my_work verification failed: no responsible demo projects.")
    if task_count <= 0:
        raise UserError("demo_full my_work verification failed: no assigned demo tasks.")
    if activity_count <= 0:
        raise UserError("demo_full my_work verification failed: no assigned activities.")
    if mention_count <= 0:
        raise UserError("demo_full my_work verification failed: no mentions.")
    if follow_count <= 0:
        raise UserError("demo_full my_work verification failed: no follows.")


def _collect_missing(env, project):
    missing = []
    if not project.partner_id:
        missing.append("customer")
    if not project.manager_id:
        missing.append("pm")

    Tender = env["tender.bid"].sudo()
    Contract = env["construction.contract"].sudo()
    if (Tender.search_count([("project_id", "=", project.id)]) +
            Contract.search_count([("project_id", "=", project.id)])) == 0:
        missing.append("contract_or_tender")

    Boq = env["project.boq.line"].sudo()
    Work = env["construction.work.breakdown"].sudo()
    Structure = env["sc.project.structure"].sudo()
    if Boq.search_count([("project_id", "=", project.id)]) == 0:
        missing.append("boq")
    if Boq.search_count([("project_id", "=", project.id), ("work_id", "!=", False)]) > 0:
        missing.append("boq_has_wbs")
    boq_no_structure_domain = [("project_id", "=", project.id), ("structure_id", "=", False)]
    if "is_group" in Boq._fields:
        boq_no_structure_domain.append(("is_group", "=", False))
    if Boq.search_count(boq_no_structure_domain) > 0:
        missing.append("boq_no_structure")
    work_count = Work.search_count([("project_id", "=", project.id)])
    if work_count == 0:
        missing.append("wbs")
    elif work_count < 3:
        missing.append("wbs_lt_3")
    structure_count = Structure.search_count([("project_id", "=", project.id)])
    if structure_count == 0:
        missing.append("structure")
    elif structure_count < 3:
        missing.append("structure_lt_3")

    Document = env["sc.project.document"].sudo()
    if Document.search_count([("project_id", "=", project.id)]) == 0:
        missing.append("documents")

    return missing


def run(env):
    init_project = _get_project(env, PROJECT_INIT_CODE)
    tender_project = _get_project(env, PROJECT_TENDER_CODE)
    exec_project = _get_project(env, PROJECT_EXEC_CODE)

    missing = [code for code, rec in [
        (PROJECT_INIT_CODE, init_project),
        (PROJECT_TENDER_CODE, tender_project),
        (PROJECT_EXEC_CODE, exec_project),
    ] if not rec]
    if missing:
        raise UserError(f"Demo projects missing: {missing}")

    showroom_projects = _get_showroom_projects(env)
    if showroom_projects:
        incomplete = []
        for project in showroom_projects:
            missing_items = _collect_missing(env, project)
            if missing_items:
                incomplete.append((project, missing_items))
                project.write({"sc_demo_showcase": True, "sc_demo_showcase_ready": False})
            else:
                project.write({"sc_demo_showcase": True, "sc_demo_showcase_ready": True})
        if incomplete:
            lines = [
                f"- {p.project_code or p.name}: {p.name} -> {', '.join(items)}"
                for p, items in incomplete
            ]
            raise UserError(
                "Showroom projects incomplete:\n"
                f"showroom={len(showroom_projects)} complete={len(showroom_projects) - len(incomplete)}\n"
                + "\n".join(lines)
            )

    Tender = env["tender.bid"].sudo()
    if Tender.search_count([("project_id", "=", tender_project.id)]) < 2:
        raise UserError("Demo tenders missing or insufficient for tender project.")

    Contract = env["construction.contract"].sudo()
    if Contract.search_count([("project_id", "=", exec_project.id)]) < 2:
        raise UserError("Demo contracts missing or insufficient for exec project.")

    Budget = env["project.budget"].sudo()
    if Budget.search_count([("project_id", "=", exec_project.id)]) < 1:
        raise UserError("Demo budget missing for exec project.")

    CostLedger = env["project.cost.ledger"].sudo()
    if CostLedger.search_count([("project_id", "=", exec_project.id)]) < 1:
        raise UserError("Demo cost ledger missing for exec project.")

    Progress = env["project.progress.entry"].sudo()
    if Progress.search_count([("project_id", "=", exec_project.id)]) < 1:
        raise UserError("Demo progress entries missing for exec project.")

    Document = env["sc.project.document"].sudo()
    if Document.search_count([("project_id", "=", exec_project.id)]) < 5:
        raise UserError("Demo project documents missing for exec project.")

    Boq = env["project.boq.line"].sudo()
    if Boq.search_count([("project_id", "=", exec_project.id)]) < 2:
        raise UserError("Demo BOQ entries missing for exec project.")

    Tender = env["tender.bid"].sudo()
    Contract = env["construction.contract"].sudo()
    Budget = env["project.budget"].sudo()
    CostLedger = env["project.cost.ledger"].sudo()
    Progress = env["project.progress.entry"].sudo()
    Document = env["sc.project.document"].sudo()
    Settlement = env["sc.settlement.order"].sudo()
    Payment = env["payment.request"].sudo()
    PurchaseLine = env["purchase.order.line"].sudo()
    Project = env["project.project"].sudo()
    for code in STAGE_PROJECT_CODES:
        project = _get_project(env, code)
        if not project:
            raise UserError(f"Stage demo project missing: {code}")
        if Tender.search_count([("project_id", "=", project.id)]) < 1:
            raise UserError(f"Stage project missing tender: {project.display_name}")
        if Contract.search_count([("project_id", "=", project.id)]) < 1:
            raise UserError(f"Stage project missing contract: {project.display_name}")
        if Budget.search_count([("project_id", "=", project.id)]) < 1:
            raise UserError(f"Stage project missing budget: {project.display_name}")
        if Boq.search_count([("project_id", "=", project.id)]) < 1:
            raise UserError(f"Stage project missing BOQ: {project.display_name}")
        if CostLedger.search_count([("project_id", "=", project.id)]) < 1:
            raise UserError(f"Stage project missing cost ledger: {project.display_name}")
        if Progress.search_count([("project_id", "=", project.id)]) < 1:
            raise UserError(f"Stage project missing progress: {project.display_name}")
        if Document.search_count([("project_id", "=", project.id)]) < 1:
            raise UserError(f"Stage project missing documents: {project.display_name}")
        if Settlement.search_count([("project_id", "=", project.id)]) < 1:
            raise UserError(f"Stage project missing settlement: {project.display_name}")
        if Payment.search_count([("project_id", "=", project.id), ("type", "=", "pay")]) < 1:
            raise UserError(f"Stage project missing payment: {project.display_name}")
        if Payment.search_count([("project_id", "=", project.id), ("type", "=", "receive")]) < 1:
            raise UserError(f"Stage project missing receive: {project.display_name}")
        settlement = Settlement.search([("project_id", "=", project.id)], limit=1)
        if not settlement.purchase_order_ids:
            raise UserError(f"Stage project missing purchase order: {project.display_name}")
        if not settlement.invoice_ref:
            raise UserError(f"Stage project missing invoice ref: {project.display_name}")
        if settlement.invoice_amount is None:
            raise UserError(f"Stage project missing invoice amount: {project.display_name}")
        po_amount = sum(
            PurchaseLine.search([("order_id", "in", settlement.purchase_order_ids.ids)]).mapped(
                lambda l: (l.product_qty or 0.0) * (l.price_unit or 0.0)
            )
        )
        if abs((settlement.amount_total or 0.0) - po_amount) > 0.01:
            raise UserError(f"Stage project PO amount mismatch: {project.display_name}")

    ratio_samples = []
    for code in ALL_DEMO_PROJECT_CODES:
        project = _get_project(env, code)
        if not project:
            continue
        settlement = Settlement.search([("project_id", "=", project.id)], limit=1)
        total = settlement.amount_total or sum(settlement.line_ids.mapped("amount")) or 0.0
        if total <= 0.0:
            continue
        ratio = round((settlement.invoice_amount or 0.0) / total, 2)
        ratio_samples.append(ratio)

    for target in RATIO_TARGETS:
        if not any(abs(r - target) <= 0.02 for r in ratio_samples):
            raise UserError(f"Missing invoice ratio sample: {target}")

    demo_projects = Project.search([("project_code", "in", ALL_DEMO_PROJECT_CODES)])
    if demo_projects:
        warn_count = len(demo_projects.filtered(lambda p: p.project_code in WARN_PROJECT_CODES))
        warn_ratio = warn_count / len(demo_projects)
        if warn_ratio < 0.15 or warn_ratio > 0.25:
            raise UserError(f"Warn ratio out of range: {warn_ratio:.2f}")

    _verify_demo_full_my_work(env)

    stage_xmlids = [
        "smart_construction_core.project_stage_planning",
        "smart_construction_core.project_stage_running",
        "smart_construction_core.project_stage_paused",
        "smart_construction_core.project_stage_closing",
        "smart_construction_core.project_stage_closed",
        "smart_construction_core.project_stage_warranty",
        "smart_construction_core.project_stage_archived",
    ]
    for xmlid in stage_xmlids:
        if not env.ref(xmlid, raise_if_not_found=False):
            raise UserError(f"Project stage missing: {xmlid}")

    lifecycle_samples = {
        "draft": ["DEMO-PJ-INIT", "DEMO-PJ-TENDER", "DEMO-PJ-STAGE-DRAFT"],
        "in_progress": ["DEMO-PJ-EXEC", "DEMO-PJ-STAGE-RUN"],
        "paused": ["DEMO-PJ-STAGE-PAUSE"],
        "closing": ["DEMO-PJ-STAGE-CLOSING"],
        "done": ["DEMO-PJ-STAGE-DONE"],
        "warranty": ["DEMO-PJ-STAGE-WARRANTY"],
        "closed": ["DEMO-PJ-STAGE-CLOSED"],
    }
    for lifecycle_state, codes in lifecycle_samples.items():
        count = env["project.project"].sudo().search_count(
            [
                ("project_code", "in", codes),
                ("lifecycle_state", "=", lifecycle_state),
            ]
        )
        if count < 1:
            raise UserError(f"Demo projects missing lifecycle sample: {lifecycle_state}")

    ICP = env["ir.config_parameter"].sudo()
    ICP.set_param("sc.seed.demo.verify", fields.Datetime.now().isoformat())


register(
    SeedStep(
        name="demo_90_verify",
        description="Verify demo_full data completeness.",
        run=run,
    )
)
