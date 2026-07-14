# -*- coding: utf-8 -*-
{
    "name": "Smart Construction Bundle",
    "summary": "Product delivery bundle for construction domain",
    "version": "0.1.0",
    "category": "Smart Construction",
    "license": "LGPL-3",
    "depends": ["smart_core"],
    "data": [
        "data/construction_bundle_product_profile.xml",
        "data/product_delivery_extension_modules.xml",
    ],
    "application": False,
    "installable": True
    ,"post_init_hook": "post_init_hook"
}
