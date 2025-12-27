# -*- coding: utf-8 -*-
{
    "name": "Smart Construction Demo Data",
    "version": "0.2.0",
    "summary": "Demo dataset for Smart Construction Core (projects, partners, light links)",
    "category": "Smart Construction",
    "depends": [
        "smart_construction_core",
        "account",
    ],
    "data": [
        "data/demo_dictionary.xml",
        "data/demo_partners.xml",
        "data/demo_projects.xml",
        "data/demo_project_boq.xml",
        "data/demo_project_links.xml",
        "data/demo_project_revenue.xml",
    ],
    "post_init_hook": "ensure_demo_taxes",
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
