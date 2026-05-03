# -*- coding: utf-8 -*-
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"
    SOURCE_KIND = "odoo_auth_session_extension"
    SOURCE_AUTHORITIES = ("res.users",)

    token_version = fields.Integer(default=0)
