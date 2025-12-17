# -*- coding: utf-8 -*-
{
    "name": "Smart Construction Demo Data",
    "version": "0.1.1",
    "summary": "Demo dataset for Smart Construction Core",
    "category": "Smart Construction",
    "depends": [
        "smart_construction_core",
    ],
    "data": [
        "data/demo_dictionary.xml",
        "data/demo_master.xml",
        "data/demo_project_boq.xml",
        "data/demo_project_revenue.xml",
        "data/demo_business.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
