# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    action_contexts = {
        "smart_construction_core.action_sc_customer_partner": "{'default_customer_rank': 1, 'default_is_company': True, 'default_company_type': 'company', 'sc_productized_list': True}",
        "smart_construction_core.action_sc_supplier_partner": "{'default_supplier_rank': 1, 'default_is_company': True, 'default_company_type': 'company', 'sc_productized_list': True}",
    }
    for xmlid, context in action_contexts.items():
        action = env.ref(xmlid, raise_if_not_found=False)
        if action:
            action.write({"context": context})
