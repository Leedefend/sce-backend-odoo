# -*- coding: utf-8 -*-
{
    "name": "Smart Construction Custom",
    "summary": "Custom adaptations for Smart Construction without modifying core modules",
    "version": "17.0.1.0",
    "author": "Leedefend",
    "website": "https://example.com",
    "category": "Customization",
    "license": "LGPL-3",
    "depends": [
        "smart_construction_core",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/role_matrix_groups.xml",
        "data/role_matrix_demo_users.xml",
        "data/security_policy_actions.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
