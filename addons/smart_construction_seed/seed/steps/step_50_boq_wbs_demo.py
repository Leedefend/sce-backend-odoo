# -*- coding: utf-8 -*-
from odoo import fields

from ..registry import SeedStep, register


PROJECT_EXEC_CODE = "DEMO-PJ-EXEC"


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


def run(env):
    projects = [_get_project(env, PROJECT_EXEC_CODE)]
    projects.extend(_get_showroom_projects(env))
    projects = list({p.id: p for p in projects if p}.values())
    if not projects:
        return

    uom_unit = env.ref("uom.product_uom_unit", raise_if_not_found=False)
    if not uom_unit:
        uom_unit = env["uom.uom"].sudo().search([], limit=1)
    Work = env["construction.work.breakdown"].sudo()
    Structure = env["sc.project.structure"].sudo()
    Boq = env["project.boq.line"].sudo()

    for project in projects:
        wbs_count = Work.search_count([("project_id", "=", project.id)])
        code_prefix = project.project_code or f"SHOW-{project.id}"
        if wbs_count < 3:
            root = _ensure_wbs(env, project, f"{code_prefix}-WBS", "示例结构", "unit", None)
            section = _ensure_wbs(env, project, f"{code_prefix}-WBS-01", "示例分部", "sub_division", root)
            sub_section = _ensure_wbs(env, project, f"{code_prefix}-WBS-01-01", "示例分项", "sub_section", section)
        else:
            root = Work.search([("project_id", "=", project.id)], limit=1)
            section = root
            sub_section = root

        if Boq.search_count([("project_id", "=", project.id)]) == 0:
            code_prefix = project.project_code or f"SHOW-{project.id}"
            header_vals = {
                "project_id": project.id,
                "code": f"{code_prefix}-G",
                "name": "示例清单",
                "section_type": "building",
                "is_group": True,
                "uom_id": uom_unit.id if uom_unit else False,
                "quantity": 0.0,
                "price": 0.0,
            }
            header = Boq.create(header_vals)
            Boq.create(
                {
                    "project_id": project.id,
                    "parent_id": header.id,
                    "code": f"{code_prefix}-001",
                    "name": "示例清单项",
                    "section_type": "building",
                    "uom_id": uom_unit.id if uom_unit else False,
                    "quantity": 120,
                    "price": 3200.0,
                }
            )

        structure_count = Structure.search_count([("project_id", "=", project.id)])
        code_prefix = project.project_code or f"SHOW-{project.id}"
        if structure_count < 3:
            unit = _ensure_structure(env, project, f"{code_prefix}-S-UNIT", "示例单位工程", "unit", None)
            division = _ensure_structure(env, project, f"{code_prefix}-S-DIV", "示例分部", "division", unit)
            item = _ensure_structure(env, project, f"{code_prefix}-S-ITEM", "示例清单项目", "item", division)
        else:
            item = Structure.search(
                [("project_id", "=", project.id), ("structure_type", "=", "item")],
                limit=1,
            )
            if not item:
                unit = _ensure_structure(env, project, f"{code_prefix}-S-UNIT", "示例单位工程", "unit", None)
                division = _ensure_structure(env, project, f"{code_prefix}-S-DIV", "示例分部", "division", unit)
                item = _ensure_structure(env, project, f"{code_prefix}-S-ITEM", "示例清单项目", "item", division)

        if item:
            lines = Boq.search([("project_id", "=", project.id), ("structure_id", "=", False)])
            if lines:
                lines.write({"structure_id": item.id, "work_id": False})

    ICP = env["ir.config_parameter"].sudo()
    ICP.set_param("sc.seed.demo.boq_wbs", fields.Datetime.now().isoformat())


register(
    SeedStep(
        name="demo_50_boq_wbs",
        description="Seed BOQ/WBS hierarchy for demo project.",
        run=run,
    )
)
