from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.smart_construction_core import hooks

    hooks._ensure_signup_defaults(env)
