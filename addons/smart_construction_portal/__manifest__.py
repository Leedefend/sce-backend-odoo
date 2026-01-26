# -*- coding: utf-8 -*-
{
    "name": "Smart Construction Portal",
    "version": "17.0.1.0",
    "summary": "Parallel portal shell for lifecycle dashboard",
    "author": "Leedefend",
    "depends": [
        "web",
        "smart_construction_core",
    ],
    "data": [
        "data/portal_params.xml",
        "views/portal_templates.xml",
        "views/portal_menu.xml",
    ],
    "assets": {
        "smart_construction_portal.assets_portal": [
            "smart_construction_portal/static/src/scss/portal.scss",
            "smart_construction_portal/static/src/services/api.js",
            "smart_construction_portal/static/src/pages/lifecycle.js",
            "smart_construction_portal/static/src/app/app.js",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
