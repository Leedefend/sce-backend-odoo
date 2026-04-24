# -*- coding: utf-8 -*-
from odoo import fields

from ..registry import SeedStep, register


MARKER = "SC_DEMO_FULL_MY_WORK"
PROJECT_LIMIT = 6
TASKS_PER_PROJECT = 4


def _get_user(env, login):
    return env["res.users"].sudo().search([("login", "=", login)], limit=1)


def _demo_projects(env, limit=PROJECT_LIMIT):
    Project = env["project.project"].sudo().with_context(active_test=False)
    domain = [
        "|",
        "|",
        ("name", "ilike", "展厅-"),
        ("name", "ilike", "演示项目"),
        ("project_code", "ilike", "DEMO-"),
    ]
    return Project.search(domain, order="id asc", limit=max(1, int(limit or PROJECT_LIMIT)))


def _ensure_doc_manager(project, demo_full):
    if "doc_manager_id" not in project._fields:
        return False
    if project.doc_manager_id.id == demo_full.id:
        return False
    project.write({"doc_manager_id": demo_full.id})
    return True


def _ensure_project_follow(project, partner):
    if not partner:
        return False
    try:
        project.message_subscribe(partner_ids=[partner.id])
        return True
    except Exception:
        return False


def _ensure_project_mention(project, demo_full):
    if not demo_full.partner_id:
        return False
    Message = project.env["mail.message"].sudo()
    existing = Message.search_count(
        [
            ("model", "=", project._name),
            ("res_id", "=", project.id),
            ("body", "ilike", MARKER),
            ("partner_ids", "in", demo_full.partner_id.id),
        ]
    )
    if existing:
        return False
    try:
        project.message_post(
            body=f"{MARKER}: 请关注该演示项目的关键事项。",
            partner_ids=[demo_full.partner_id.id],
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )
        return True
    except Exception:
        return False


def _ensure_project_activity(project, demo_full):
    Activity = project.env["mail.activity"].sudo()
    todo_type = project.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
    model_id = project.env["ir.model"].sudo()._get_id(project._name)
    if not todo_type or not model_id:
        return False
    summary = f"{MARKER}-{project.id}"
    existing = Activity.search_count(
        [
            ("res_model", "=", project._name),
            ("res_id", "=", project.id),
            ("user_id", "=", demo_full.id),
            ("summary", "=", summary),
        ]
    )
    if existing:
        return False
    Activity.create(
        {
            "activity_type_id": todo_type.id,
            "res_model_id": model_id,
            "res_id": project.id,
            "summary": summary,
            "note": f"{MARKER}: 请处理演示项目跟进行动。",
            "user_id": demo_full.id,
            "date_deadline": fields.Date.today(),
        }
    )
    return True


def _ensure_task_assignment(project, demo_full, task_limit=TASKS_PER_PROJECT):
    Task = project.env["project.task"].sudo()
    if "user_ids" not in Task._fields:
        return 0
    safe_limit = max(1, int(task_limit or TASKS_PER_PROJECT))
    tasks = Task.search([("project_id", "=", project.id)], order="id asc", limit=safe_limit)
    if not tasks:
        created = []
        for index in range(1, safe_limit + 1):
            created.append(
                Task.create(
                    {
                        "name": f"{MARKER}-{project.id}-任务{index:02d}",
                        "project_id": project.id,
                        "user_ids": [(6, 0, [demo_full.id])],
                    }
                )
            )
        return len(created)
    updated = 0
    for task in tasks:
        user_ids = set(task.user_ids.ids)
        if demo_full.id in user_ids:
            continue
        task.write({"user_ids": [(6, 0, list(user_ids | {demo_full.id}))]})
        updated += 1
    return updated


def run(env):
    demo_full = _get_user(env, "demo_full")
    if not demo_full:
        return {"skipped": True, "reason": "demo_full not found"}

    projects = _demo_projects(env)
    if not projects:
        return {"ok": True, "projects": 0}

    stats = {
        "projects": len(projects),
        "doc_manager_updates": 0,
        "followers": 0,
        "mentions": 0,
        "activities": 0,
        "task_assignments": 0,
    }
    for project in projects:
        stats["doc_manager_updates"] += int(bool(_ensure_doc_manager(project, demo_full)))
        stats["followers"] += int(bool(_ensure_project_follow(project, demo_full.partner_id)))
        stats["mentions"] += int(bool(_ensure_project_mention(project, demo_full)))
        stats["activities"] += int(bool(_ensure_project_activity(project, demo_full)))
        stats["task_assignments"] += int(_ensure_task_assignment(project, demo_full))

    env["ir.config_parameter"].sudo().set_param("sc.seed.demo_full_my_work", "1")
    return {"ok": True, **stats}


register(
    SeedStep(
        name="z_demo_full_my_work",
        description="Attach demo_full to demo my-work facts (projects/tasks/activities/followers).",
        run=run,
    )
)
