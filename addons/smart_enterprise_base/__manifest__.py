# -*- coding: utf-8 -*-
{
    "name": "Smart Enterprise Base",
    "summary": "Enterprise bootstrap base for company and organization enablement",
    "version": "17.0.0.1.0",
    "category": "Administration",
    "license": "LGPL-3",
    "author": "SCE",
    "depends": [
        "base",
        "hr",
        "smart_core",
    ],
    "data": [
        "data/runtime_params.xml",
        "security/ir.model.access.csv",
        "views/res_company_views.xml",
        "views/hr_department_views.xml",
        "views/res_users_views.xml",
        "views/menu_enterprise_base.xml",
    ],
    "installable": True,
    "application": False,
}
