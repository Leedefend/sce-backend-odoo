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
        "security/role_matrix_groups.xml",
        "security/ir.model.access.csv",
        "data/customer_company_departments.xml",
        "data/customer_posts.xml",
        "data/customer_users.xml",
        "data/customer_user_relations.xml",
        "data/customer_user_authorization.xml",
        "data/security_policy_actions.xml",
        "data/customer_project_seed.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
