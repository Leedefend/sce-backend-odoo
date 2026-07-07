# -*- coding: utf-8 -*-
{
    "name": "Smart Construction Seed",
    "summary": "Production-safe baseline seed scaffolding with guarded scenario steps",
    "version": "17.0.0.2.1",
    "category": "Tools",
    "license": "LGPL-3",
    "author": "SCE",
    "depends": ["smart_construction_bootstrap", "account", "smart_construction_core"],
    "data": [
        "data/sc_seed_dictionary_contract.xml",
        "data/sc_seed_tax.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
