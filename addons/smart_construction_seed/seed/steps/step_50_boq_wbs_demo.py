# -*- coding: utf-8 -*-
from odoo import fields

from ..registry import SeedStep, register


PROJECT_EXEC_CODE = "DEMO-PJ-EXEC"


def _get_project(env, code):
    return env["project.project"].sudo().search([("project_code", "=", code)], limit=1)


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


def run(env):
    project = _get_project(env, PROJECT_EXEC_CODE)
    if not project:
        return

    root = _ensure_wbs(env, project, "WBS-002", "桥梁工程", "unit", None)
    section = _ensure_wbs(env, project, "WBS-002-01", "下部结构", "sub_division", root)
    sub_section = _ensure_wbs(env, project, "WBS-002-01-01", "承台施工", "sub_section", section)
    lot = _ensure_wbs(env, project, "WBS-002-01-01-01", "钢筋安装", "inspection_lot", sub_section)

    uom_unit = env.ref("uom.product_uom_unit", raise_if_not_found=False)
    if not uom_unit:
        uom_unit = env["uom.uom"].sudo().search([], limit=1)
    Boq = env["project.boq.line"].sudo()

    header = Boq.search(
        [("project_id", "=", project.id), ("code", "=", "BOQ-G-01"), ("is_group", "=", True)],
        limit=1,
    )
    header_vals = {
        "project_id": project.id,
        "code": "BOQ-G-01",
        "name": "桥梁下部结构",
        "section_type": "building",
        "is_group": True,
        "uom_id": uom_unit.id if uom_unit else False,
        "quantity": 0.0,
        "price": 0.0,
        "work_id": section.id,
    }
    if header:
        header.write(header_vals)
    else:
        header = Boq.create(header_vals)

    line_vals = [
        {
            "project_id": project.id,
            "parent_id": header.id,
            "code": "BOQ-310",
            "name": "承台混凝土",
            "section_type": "building",
            "uom_id": uom_unit.id if uom_unit else False,
            "quantity": 120,
            "price": 3800.0,
            "work_id": sub_section.id,
        },
        {
            "project_id": project.id,
            "parent_id": header.id,
            "code": "BOQ-311",
            "name": "承台钢筋安装",
            "section_type": "building",
            "uom_id": uom_unit.id if uom_unit else False,
            "quantity": 95,
            "price": 2600.0,
            "work_id": lot.id,
        },
    ]
    for vals in line_vals:
        existing = Boq.search(
            [("project_id", "=", project.id), ("code", "=", vals["code"])], limit=1
        )
        if existing:
            existing.write(vals)
        else:
            Boq.create(vals)

    project.sudo().write({"lifecycle_state": "in_progress"})

    ICP = env["ir.config_parameter"].sudo()
    ICP.set_param("sc.seed.demo.boq_wbs", fields.Datetime.now().isoformat())


register(
    SeedStep(
        name="demo_50_boq_wbs",
        description="Seed BOQ/WBS hierarchy for demo project.",
        run=run,
    )
)
