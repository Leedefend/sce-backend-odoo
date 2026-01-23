# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class ScAuthRedirect(http.Controller):
    @http.route("/web/signup", type="http", auth="public", website=False, sitemap=False)
    def sc_web_signup_redirect(self, **kw):
        return request.redirect("/web/login?signup=1")

    @http.route("/web/reset_password", type="http", auth="public", website=False, sitemap=False)
    def sc_web_reset_redirect(self, **kw):
        return request.redirect("/web/login?reset_password=1")
