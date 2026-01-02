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
        "data/base/00_dictionary.xml",
        "data/base/10_partners.xml",
        "data/base/20_projects.xml",
        "data/scenario/s00_min_path/10_project_boq.xml",
        "data/scenario/s00_min_path/20_project_links.xml",
        "data/scenario/s00_min_path/30_project_revenue.xml",
    ],
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
