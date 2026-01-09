# -*- coding: utf-8 -*-
from odoo import fields

from ..registry import SeedStep, register


PROJECT_TENDER_CODE = "DEMO-PJ-TENDER"
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


def _get_or_create_partner(env, name):
    Partner = env["res.partner"].sudo()
    partner = Partner.search([("name", "=", name)], limit=1)
    if partner:
        if partner.company_type != "company":
            partner.company_type = "company"
        return partner
    return Partner.create({"name": name, "company_type": "company"})


def run(env):
    projects = [
        _get_project(env, PROJECT_TENDER_CODE),
    ]
    for code in STAGE_PROJECT_CODES:
        projects.append(_get_project(env, code))
    projects = [p for p in projects if p]

    owner = _get_or_create_partner(env, "演示业主 · 城市建设集团")
    uom_unit = env.ref("uom.product_uom_unit", raise_if_not_found=False)
    if not uom_unit:
        uom_unit = env["uom.uom"].sudo().search([], limit=1)

    Tender = env["tender.bid"].sudo()
    TenderLine = env["tender.bid.line"].sudo()
    now = fields.Datetime.now()
    state_map = {
        "draft": "prepare",
        "in_progress": "submitted",
        "paused": "waiting",
        "closing": "won",
        "done": "won",
        "warranty": "won",
        "closed": "lost",
    }

    for project in projects:
        state = state_map.get(project.lifecycle_state, "prepare")
        bids = [
            {
                "name": f"TB-{project.project_code}-01",
                "tender_name": f"{project.name} 投标",
                "project_id": project.id,
                "tender_round": 1,
                "owner_id": owner.id,
                "bid_amount": 880000.0,
                "deadline": now,
                "open_date": now,
                "state": state,
            },
        ]
        if project.project_code == PROJECT_TENDER_CODE:
            bids.append(
                {
                    "name": f"TB-{project.project_code}-02",
                    "tender_name": f"{project.name} 投标（二次）",
                    "project_id": project.id,
                    "tender_round": 2,
                    "owner_id": owner.id,
                    "bid_amount": 930000.0,
                    "deadline": now,
                    "open_date": now,
                    "state": state,
                }
            )

        for bid_vals in bids:
            bid = Tender.search(
                [("project_id", "=", project.id), ("name", "=", bid_vals["name"])], limit=1
            )
            if bid:
                bid.write(bid_vals)
            else:
                bid = Tender.create(bid_vals)

            line_vals = [
                {
                    "bid_id": bid.id,
                    "sequence": 10,
                    "code": f"{project.project_code}-BID-01",
                    "name": "路基填筑",
                    "uom_id": uom_unit.id if uom_unit else False,
                    "quantity": 120,
                    "price": 820,
                },
                {
                    "bid_id": bid.id,
                    "sequence": 20,
                    "code": f"{project.project_code}-BID-02",
                    "name": "桥梁下部结构",
                    "uom_id": uom_unit.id if uom_unit else False,
                    "quantity": 60,
                    "price": 1500,
                },
            ]
            for vals in line_vals:
                existing = TenderLine.search(
                    [("bid_id", "=", bid.id), ("code", "=", vals["code"])], limit=1
                )
                if existing:
                    existing.write(vals)
                else:
                    TenderLine.create(vals)


register(
    SeedStep(
        name="demo_30_tenders",
        description="Seed tender records for demo project.",
        run=run,
    )
)
