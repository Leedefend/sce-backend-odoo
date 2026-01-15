# -*- coding: utf-8 -*-
{
    "name": "Smart Construction Seed",
    "summary": "Seed data scaffolding for demo/test environments (idempotent hooks)",
    "version": "17.0.0.1.0",
    "category": "Tools",
    "license": "LGPL-3",
    "author": "SCE",
    "depends": ["smart_construction_bootstrap", "account", "smart_construction_core"],
    "data": [
        "data/sc_demo_showcase_actions.xml",
        "data/sc_seed_dictionary_contract.xml",
        "data/sc_seed_login_env.xml",
        "data/sc_seed_partner.xml",
        "data/sc_seed_tax.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
