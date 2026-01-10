# -*- coding: utf-8 -*-
import base64

from odoo import fields

from ..registry import SeedStep, register


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


def _get_or_create_dict(env, dict_type, name):
    Dictionary = env["sc.dictionary"].sudo()
    record = Dictionary.search([("type", "=", dict_type), ("name", "=", name)], limit=1)
    if record:
        return record
    return Dictionary.create({"type": dict_type, "name": name, "sequence": 10})


def _create_attachment(env, name, content, mimetype="text/plain"):
    Attachment = env["ir.attachment"].sudo()
    data = base64.b64encode(content.encode("utf-8"))
    return Attachment.create(
        {
            "name": name,
            "datas": data,
            "type": "binary",
            "mimetype": mimetype,
        }
    )


def run(env):
    projects = [
        _get_project(env, PROJECT_EXEC_CODE),
    ]
    for code in STAGE_PROJECT_CODES:
        projects.append(_get_project(env, code))
    projects.extend(_get_showroom_projects(env))
    projects = list({p.id: p for p in projects if p}.values())
    if not projects:
        return

    doc_type = _get_or_create_dict(env, "doc_type", "技术资料")
    doc_subtype = _get_or_create_dict(env, "doc_subtype", "合同附件")

    ScDoc = env["sc.project.document"].sudo()

    documents = [
        {
            "name": "施工组织设计",
            "is_mandatory": True,
            "state": "done",
            "date_doc": fields.Date.context_today(env.user),
            "content": "施工组织设计-演示版",
        },
        {
            "name": "监理例会纪要",
            "is_mandatory": True,
            "state": "done",
            "date_doc": fields.Date.context_today(env.user),
            "content": "监理例会纪要-演示版",
        },
        {
            "name": "合同附件清单",
            "is_mandatory": True,
            "state": "review",
            "date_doc": fields.Date.context_today(env.user),
            "content": "合同附件清单-演示版",
        },
        {
            "name": "质量检验记录",
            "is_mandatory": True,
            "state": "draft",
            "date_doc": fields.Date.context_today(env.user),
            "content": "质量检验记录-演示版",
        },
        {
            "name": "安全交底记录",
            "is_mandatory": False,
            "state": "done",
            "date_doc": fields.Date.context_today(env.user),
            "content": "安全交底记录-演示版",
        },
    ]

    for project in projects:
        for doc in documents:
            name = f"{doc['name']} · {project.project_code}"
            existing = ScDoc.search(
                [("project_id", "=", project.id), ("name", "=", name)], limit=1
            )
            attachment = _create_attachment(env, f"{name}.txt", doc["content"])
            vals = {
                "name": name,
                "project_id": project.id,
                "doc_type_id": doc_type.id,
                "doc_subtype_id": doc_subtype.id,
                "date_doc": doc["date_doc"],
                "is_mandatory": doc["is_mandatory"],
                "state": doc["state"],
                "attachment_ids": [(6, 0, [attachment.id])],
            }
            if existing:
                existing.write(vals)
            else:
                ScDoc.create(vals)

    ICP = env["ir.config_parameter"].sudo()
    ICP.set_param("sc.seed.demo.attachments", fields.Datetime.now().isoformat())


register(
    SeedStep(
        name="demo_60_attachments",
        description="Seed attachments and project documents for demo.",
        run=run,
    )
)
