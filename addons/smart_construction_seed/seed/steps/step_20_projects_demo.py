# -*- coding: utf-8 -*-
from odoo import fields
from odoo.exceptions import UserError

from ..registry import SeedStep, register


PROJECT_INIT_CODE = "DEMO-PJ-INIT"
PROJECT_TENDER_CODE = "DEMO-PJ-TENDER"
PROJECT_EXEC_CODE = "DEMO-PJ-EXEC"
STAGE_PROJECTS = [
    ("DEMO-PJ-STAGE-DRAFT", "演示项目 · 立项阶段", "draft", "initiation"),
    ("DEMO-PJ-STAGE-RUN", "演示项目 · 在建阶段", "in_progress", "execution"),
    ("DEMO-PJ-STAGE-PAUSE", "演示项目 · 暂停阶段", "paused", "execution"),
    ("DEMO-PJ-STAGE-CLOSING", "演示项目 · 结算阶段", "closing", "settlement"),
    ("DEMO-PJ-STAGE-DONE", "演示项目 · 完工阶段", "done", "settlement"),
    ("DEMO-PJ-STAGE-WARRANTY", "演示项目 · 质保阶段", "warranty", "archive"),
    ("DEMO-PJ-STAGE-CLOSED", "演示项目 · 归档阶段", "closed", "archive"),
]


def _get_user(env, login):
    return env["res.users"].sudo().search([("login", "=", login)], limit=1)


def _get_or_create_partner(env, name):
    Partner = env["res.partner"].sudo()
    partner = Partner.search([("name", "=", name)], limit=1)
    if partner:
        if partner.company_type != "company":
            partner.company_type = "company"
        return partner
    return Partner.create({"name": name, "company_type": "company"})


def _get_dictionary(env, xmlid, domain):
    rec = env.ref(xmlid, raise_if_not_found=False)
    if rec:
        return rec
    return env["sc.dictionary"].sudo().search(domain, limit=1)


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


def _ensure_project(env, code, vals):
    Project = env["project.project"].sudo()
    project = Project.search([("project_code", "=", code)], limit=1)
    if not project:
        project = Project.search([("name", "=", vals["name"])], limit=1)
    if project:
        update_vals = dict(vals)
        update_vals.pop("lifecycle_state", None)
        project.write(update_vals)
    else:
        vals = dict(vals)
        vals["project_code"] = code
        project = Project.create(vals)
    return project


def _ensure_wbs(env, project, code, name, level_type, parent=None):
    Work = env["construction.work.breakdown"].sudo()
    domain = [("project_id", "=", project.id), ("code", "=", code), ("level_type", "=", level_type)]
    node = Work.search(domain, limit=1)
    vals = {
        "project_id": project.id,
        "code": code,
        "name": name,
        "level_type": level_type,
        "parent_id": parent.id if parent else False,
    }
    if node:
        node.write(vals)
    else:
        node = Work.create(vals)
    return node


def _ensure_structure(env, project, code, name, structure_type, parent=None):
    Structure = env["sc.project.structure"].sudo()
    domain = [
        ("project_id", "=", project.id),
        ("code", "=", code),
        ("structure_type", "=", structure_type),
    ]
    node = Structure.search(domain, limit=1)
    vals = {
        "project_id": project.id,
        "code": code,
        "name": name,
        "structure_type": structure_type,
        "biz_scope": "work",
        "parent_id": parent.id if parent else False,
    }
    if node:
        node.write(vals)
    else:
        node = Structure.create(vals)
    return node


def _ensure_boq(env, project, code_prefix, uom_unit):
    unit = _ensure_structure(env, project, f"{code_prefix}-S-UNIT", "基础单位工程", "unit", None)
    item = _ensure_structure(env, project, f"{code_prefix}-S-ITEM", "基础清单项目", "item", unit)
    Boq = env["project.boq.line"].sudo()
    header = Boq.search(
        [("project_id", "=", project.id), ("code", "=", f"{code_prefix}-G")], limit=1
    )
    header_vals = {
        "project_id": project.id,
        "code": f"{code_prefix}-G",
        "name": "基础清单",
        "section_type": "building",
        "is_group": True,
        "uom_id": uom_unit.id if uom_unit else False,
        "quantity": 0.0,
        "price": 0.0,
        "structure_id": item.id,
        "work_id": False,
    }
    if header:
        header.write(header_vals)
    else:
        header = Boq.create(header_vals)

    leaf_vals = {
        "project_id": project.id,
        "parent_id": header.id,
        "code": f"{code_prefix}-001",
        "name": "基础工程量",
        "section_type": "building",
        "uom_id": uom_unit.id if uom_unit else False,
        "quantity": 120,
        "price": 3200.0,
        "structure_id": item.id,
        "work_id": False,
    }
    existing = Boq.search(
        [("project_id", "=", project.id), ("code", "=", leaf_vals["code"])], limit=1
    )
    if existing:
        existing.write(leaf_vals)
    else:
        Boq.create(leaf_vals)


def _ensure_budget(env, project, uom_unit, work_node):
    Budget = env["project.budget"].sudo()
    budget = Budget.search(
        [("project_id", "=", project.id), ("version", "=", "DEMO-V1")], limit=1
    )
    if not budget:
        budget = Budget.create(
            {
                "name": "控制版 V1",
                "project_id": project.id,
                "version": "DEMO-V1",
                "version_date": fields.Date.context_today(env.user),
                "amount_revenue_target": 1200000.0,
                "amount_cost_target": 900000.0,
                "is_active": True,
                "note": "演示用控制预算版本",
            }
        )
    else:
        budget.write(
            {
                "amount_revenue_target": 1200000.0,
                "amount_cost_target": 900000.0,
                "is_active": True,
            }
        )

    BudgetLine = env["project.budget.boq.line"].sudo()
    line_vals = {
        "budget_id": budget.id,
        "sequence": 10,
        "boq_code": f"{project.project_code}-B1",
        "name": "预算清单项",
        "wbs_id": work_node.id,
        "qty_bidded": 100,
        "uom_id": uom_unit.id if uom_unit else False,
        "price_bidded": 3000,
        "measure_rule": "qty",
    }
    existing = BudgetLine.search(
        [("budget_id", "=", budget.id), ("boq_code", "=", line_vals["boq_code"])], limit=1
    )
    if existing:
        existing.write(line_vals)
    else:
        BudgetLine.create(line_vals)


def _ensure_cost_progress(env, project, cost_material, cost_sub, uom_unit, work_node):
    today = fields.Date.context_today(env.user)
    CostLedger = env["project.cost.ledger"].sudo()
    Progress = env["project.progress.entry"].sudo()

    has_ledger = CostLedger.search_count([("project_id", "=", project.id)]) > 0
    has_progress = Progress.search_count([("project_id", "=", project.id)]) > 0
    if has_ledger and has_progress:
        return

    original_state = project.lifecycle_state
    temp_state = None
    if original_state == "paused":
        project.action_set_lifecycle_state("in_progress")
    elif original_state in ("closing", "warranty", "closed") and (not has_progress or not has_ledger):
        temp_state = "in_progress"
        env.cr.execute(
            "UPDATE project_project SET lifecycle_state=%s WHERE id=%s",
            (temp_state, project.id),
        )
        env.invalidate_all()
    ledger_vals = [
        {
            "project_id": project.id,
            "wbs_id": work_node.id,
            "cost_code_id": cost_material.id,
            "date": today,
            "qty": 200,
            "uom_id": uom_unit.id if uom_unit else False,
            "amount": 120000.0,
            "source_model": "purchase.order",
            "source_id": 1,
            "note": "演示材料成本",
        },
        {
            "project_id": project.id,
            "wbs_id": work_node.id,
            "cost_code_id": cost_sub.id,
            "date": today,
            "qty": 1,
            "uom_id": uom_unit.id if uom_unit else False,
            "amount": 80000.0,
            "source_model": "account.move",
            "source_id": 1,
            "note": "演示分包成本",
        },
    ]
    for vals in ledger_vals:
        existing = CostLedger.search(
            [("project_id", "=", project.id), ("note", "=", vals["note"])], limit=1
        )
        if existing:
            existing.write(vals)
        else:
            CostLedger.create(vals)

    if original_state != "closing" or temp_state:
        progress_vals = {
            "project_id": project.id,
            "wbs_id": work_node.id,
            "date": today,
            "qty_done": 60,
            "qty_cum": 160,
            "progress_rate": 45.0,
            "note": "演示进度计量",
        }
        existing = Progress.search(
            [("project_id", "=", project.id), ("wbs_id", "=", work_node.id)], limit=1
        )
        if existing:
            existing.write(progress_vals)
        else:
            Progress.create(progress_vals)

    if original_state == "paused":
        project.action_set_lifecycle_state("paused")
    elif temp_state:
        env.cr.execute(
            "UPDATE project_project SET lifecycle_state=%s WHERE id=%s",
            (original_state, project.id),
        )
        env.invalidate_all()


def _apply_lifecycle(project, target_state):
    if project.lifecycle_state == target_state:
        return
    if project.lifecycle_state != "draft":
        return
    path_map = {
        "draft": [],
        "in_progress": ["in_progress"],
        "paused": ["paused"],
        "closing": ["in_progress", "closing"],
        "done": ["in_progress", "done"],
        "warranty": ["in_progress", "done", "warranty"],
        "closed": ["in_progress", "closed"],
    }
    for state in path_map.get(target_state, []):
        if project.lifecycle_state != state:
            project.action_set_lifecycle_state(state)


def run(env):
    ICP = env["ir.config_parameter"].sudo()

    demo_pm = _get_user(env, "demo_pm")
    demo_cost = _get_user(env, "demo_cost")

    owner = _get_or_create_partner(env, "演示业主 · 城市建设集团")
    supplier = _get_or_create_partner(env, "演示供应商 · 建材科技")
    subcontract = _get_or_create_partner(env, "演示分包 · 桥梁施工队")

    project_type = _get_dictionary(
        env,
        "smart_construction_seed.seed_dict_project_type_base",
        [("type", "=", "project_type")],
    )
    project_category = _get_dictionary(
        env,
        "smart_construction_seed.seed_dict_project_category_base",
        [("type", "=", "project_category")],
    )

    today = fields.Date.context_today(env.user)

    init_project = _ensure_project(
        env,
        PROJECT_INIT_CODE,
        {
            "name": "演示项目 · 立项待完善",
            "partner_id": False,
            "owner_id": owner.id,
            "manager_id": demo_pm.id if demo_pm else False,
            "cost_manager_id": demo_cost.id if demo_cost else False,
            "doc_manager_id": demo_pm.id if demo_pm else False,
            "project_type_id": project_type.id if project_type else False,
            "project_category_id": project_category.id if project_category else False,
            "lifecycle_state": "draft",
            "phase_key": "initiation",
            "location": "华东区",
            "start_date": today,
        },
    )

    tender_project = _ensure_project(
        env,
        PROJECT_TENDER_CODE,
        {
            "name": "演示项目 · 市政道路提升工程",
            "partner_id": owner.id,
            "owner_id": owner.id,
            "manager_id": demo_pm.id if demo_pm else False,
            "cost_manager_id": demo_cost.id if demo_cost else False,
            "doc_manager_id": demo_pm.id if demo_pm else False,
            "project_type_id": project_type.id if project_type else False,
            "project_category_id": project_category.id if project_category else False,
            "lifecycle_state": "draft",
            "phase_key": "initiation",
            "location": "华南区",
            "plan_percent": 20.0,
            "actual_percent": 10.0,
            "start_date": today,
        },
    )

    exec_project = _ensure_project(
        env,
        PROJECT_EXEC_CODE,
        {
            "name": "演示项目 · 城市快速路提升工程",
            "partner_id": owner.id,
            "owner_id": owner.id,
            "manager_id": demo_pm.id if demo_pm else False,
            "cost_manager_id": demo_cost.id if demo_cost else False,
            "doc_manager_id": demo_pm.id if demo_pm else False,
            "project_type_id": project_type.id if project_type else False,
            "project_category_id": project_category.id if project_category else False,
            "lifecycle_state": "draft",
            "phase_key": "execution",
            "location": "华北区",
            "contract_no": "HT-2025-001",
            "plan_percent": 65.0,
            "actual_percent": 52.0,
            "start_date": today,
        },
    )

    root = _ensure_wbs(env, exec_project, "WBS-001", "道路工程", "unit", None)
    sub = _ensure_wbs(env, exec_project, "WBS-001-01", "桥梁结构", "sub_division", root)
    leaf = _ensure_wbs(env, exec_project, "WBS-001-01-01", "桩基施工", "sub_section", sub)

    Budget = env["project.budget"].sudo()
    budget = Budget.search(
        [("project_id", "=", exec_project.id), ("version", "=", "DEMO-V1")], limit=1
    )
    if not budget:
        budget = Budget.create(
            {
                "name": "控制版 V1",
                "project_id": exec_project.id,
                "version": "DEMO-V1",
                "version_date": today,
                "amount_revenue_target": 3200000.0,
                "amount_cost_target": 2500000.0,
                "is_active": True,
                "note": "演示用控制预算版本",
            }
        )
    else:
        budget.write(
            {
                "name": "控制版 V1",
                "version_date": today,
                "amount_revenue_target": 3200000.0,
                "amount_cost_target": 2500000.0,
                "is_active": True,
            }
        )

    uom_unit = env.ref("uom.product_uom_unit", raise_if_not_found=False)
    if not uom_unit:
        uom_unit = env["uom.uom"].sudo().search([], limit=1)
    BudgetLine = env["project.budget.boq.line"].sudo()
    line_vals = [
        {
            "budget_id": budget.id,
            "sequence": 10,
            "boq_code": "BOQ-100",
            "name": "路基填筑",
            "wbs_id": leaf.id,
            "qty_bidded": 1200,
            "uom_id": uom_unit.id if uom_unit else False,
            "price_bidded": 800,
            "measure_rule": "qty",
        },
        {
            "budget_id": budget.id,
            "sequence": 20,
            "boq_code": "BOQ-200",
            "name": "桥梁下部结构",
            "wbs_id": sub.id,
            "qty_bidded": 600,
            "uom_id": uom_unit.id if uom_unit else False,
            "price_bidded": 1500,
            "measure_rule": "qty",
        },
    ]
    for vals in line_vals:
        existing = BudgetLine.search(
            [("budget_id", "=", budget.id), ("boq_code", "=", vals["boq_code"])], limit=1
        )
        if existing:
            existing.write(vals)
        else:
            BudgetLine.create(vals)

    CostCode = env["project.cost.code"].sudo()
    cost_material = env.ref("smart_construction_core.sc_cost_code_root_material", raise_if_not_found=False)
    cost_sub = env.ref("smart_construction_core.sc_cost_code_root_subcontract", raise_if_not_found=False)
    if not cost_material:
        cost_material = CostCode.search([("type", "=", "material")], limit=1)
    if not cost_sub:
        cost_sub = CostCode.search([("type", "=", "subcontract")], limit=1)
    if not cost_material or not cost_sub:
        raise UserError("Missing cost codes required for demo cost ledger.")

    CostLedger = env["project.cost.ledger"].sudo()
    ledger_vals = [
        {
            "project_id": exec_project.id,
            "wbs_id": sub.id,
            "cost_code_id": cost_material.id if cost_material else False,
            "date": today,
            "qty": 200,
            "uom_id": uom_unit.id if uom_unit else False,
            "amount": 240000.0,
            "partner_id": supplier.id,
            "source_model": "purchase.order",
            "source_id": 1,
            "note": "钢筋采购入库",
        },
        {
            "project_id": exec_project.id,
            "wbs_id": leaf.id,
            "cost_code_id": cost_sub.id if cost_sub else False,
            "date": today,
            "qty": 1,
            "uom_id": uom_unit.id if uom_unit else False,
            "amount": 420000.0,
            "partner_id": subcontract.id,
            "source_model": "account.move",
            "source_id": 1,
            "note": "桩基分包结算",
        },
    ]
    for vals in ledger_vals:
        existing = CostLedger.search(
            [
                ("project_id", "=", exec_project.id),
                ("note", "=", vals["note"]),
                ("amount", "=", vals["amount"]),
            ],
            limit=1,
        )
        if existing:
            existing.write(vals)
        else:
            CostLedger.create(vals)

    Progress = env["project.progress.entry"].sudo()
    progress_vals = {
        "project_id": exec_project.id,
        "wbs_id": leaf.id,
        "date": today,
        "qty_done": 180,
        "qty_cum": 300,
        "progress_rate": 45.0,
        "note": "桩基完成 45%，已提交监理确认",
    }
    existing_progress = Progress.search(
        [
            ("project_id", "=", exec_project.id),
            ("wbs_id", "=", leaf.id),
            ("progress_rate", "=", progress_vals["progress_rate"]),
        ],
        limit=1,
    )
    if existing_progress:
        existing_progress.write(progress_vals)
    else:
        Progress.create(progress_vals)

    for code, name, state, phase in STAGE_PROJECTS:
        project = _ensure_project(
            env,
            code,
            {
                "name": name,
                "partner_id": owner.id,
                "owner_id": owner.id,
                "manager_id": demo_pm.id if demo_pm else False,
                "cost_manager_id": demo_cost.id if demo_cost else False,
                "doc_manager_id": demo_pm.id if demo_pm else False,
                "project_type_id": project_type.id if project_type else False,
                "project_category_id": project_category.id if project_category else False,
                "lifecycle_state": state,
                "phase_key": phase,
                "location": "演示园区",
                "plan_percent": 50.0,
                "actual_percent": 45.0,
                "start_date": today,
            },
        )
        stage_root = _ensure_wbs(env, project, f"{code}-WBS", "演示结构", "unit", None)
        _ensure_boq(env, project, code, uom_unit)
        _ensure_budget(env, project, uom_unit, stage_root)
        _ensure_cost_progress(env, project, cost_material, cost_sub, uom_unit, stage_root)
        _apply_lifecycle(project, state)

    showroom_projects = _get_showroom_projects(env)
    for project in showroom_projects:
        vals = {}
        if not project.partner_id and owner:
            vals["partner_id"] = owner.id
        if not project.owner_id and owner:
            vals["owner_id"] = owner.id
        if demo_pm and not project.manager_id:
            vals["manager_id"] = demo_pm.id
        if demo_cost and not project.cost_manager_id:
            vals["cost_manager_id"] = demo_cost.id
        if demo_pm and not project.doc_manager_id:
            vals["doc_manager_id"] = demo_pm.id
        vals["sc_demo_showcase"] = True
        if vals:
            project.write(vals)

    ICP.set_param("sc.seed.demo.project_init", str(init_project.id))
    ICP.set_param("sc.seed.demo.project_tender", str(tender_project.id))
    ICP.set_param("sc.seed.demo.project_exec", str(exec_project.id))


register(
    SeedStep(
        name="demo_20_projects",
        description="Seed demo projects with budget/cost/progress baseline.",
        run=run,
    )
)
