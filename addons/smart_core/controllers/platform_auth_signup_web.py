# -*- coding: utf-8 -*-

from odoo import http
from .platform_auth_signup_logic import ScAuthSignup as _ScAuthSignupLogic


class PlatformAuthSignupWeb(_ScAuthSignupLogic):
    @http.route("/web/signup", type="http", auth="public", website=True, sitemap=False)
    def web_auth_signup(self, *args, **kwargs):
        return super().web_auth_signup(*args, **kwargs)

    @http.route("/sc/auth/activate/<string:token>", type="http", auth="public", website=False, csrf=False)
    def sc_activate_account(self, token, **kwargs):
        return super().sc_activate_account(token, **kwargs)
