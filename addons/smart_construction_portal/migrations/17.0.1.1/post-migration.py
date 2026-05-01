# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


LEGACY_MENU_XMLIDS = (
    "smart_construction_portal.menu_sc_portal_lifecycle",
    "smart_construction_portal.menu_sc_portal_capability_matrix",
    "smart_construction_portal.menu_sc_portal_dashboard",
)

LEGACY_ACTION_XMLIDS = (
    "smart_construction_portal.action_sc_portal_lifecycle",
    "smart_construction_portal.action_sc_portal_capability_matrix",
    "smart_construction_portal.action_sc_portal_dashboard",
)


def _unlink_xmlids(env, xmlids):
    imd = env["ir.model.data"].sudo()
    for xmlid in xmlids:
        record = env.ref(xmlid, raise_if_not_found=False)
        if record:
            record.sudo().unlink()
        module, name = xmlid.split(".", 1)
        imd.search([("module", "=", module), ("name", "=", name)]).unlink()


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _unlink_xmlids(env, LEGACY_MENU_XMLIDS)
    _unlink_xmlids(env, LEGACY_ACTION_XMLIDS)
