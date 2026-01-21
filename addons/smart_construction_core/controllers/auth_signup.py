# -*- coding: utf-8 -*-
import logging
import time
from urllib.parse import urlencode

from werkzeug.exceptions import Forbidden, NotFound

from odoo import http
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

_logger = logging.getLogger(__name__)


class ScAuthSignup(AuthSignupHome):
    def _get_signup_mode(self):
        icp = request.env["ir.config_parameter"].sudo()
        mode = (icp.get_param("sc.signup.mode") or "").strip().lower()
        if mode:
            return mode
        login_env = icp.get_param("sc.login.env", "prod").strip().lower()
        return "invite" if login_env in ("prod", "production") else "open"

    def _require_email_verify(self):
        icp = request.env["ir.config_parameter"].sudo()
        return icp.get_param("sc.signup.require_email_verify", "true").lower() in ("1", "true", "yes")

    def _get_domain_whitelist(self):
        icp = request.env["ir.config_parameter"].sudo()
        raw = icp.get_param("sc.signup.domain_whitelist", "")
        domains = [d.strip().lower() for d in raw.split(",") if d.strip()]
        return set(domains)

    def _get_default_group_xmlids(self):
        icp = request.env["ir.config_parameter"].sudo()
        raw = icp.get_param("sc.signup.default_group_xmlids", "base.group_portal")
        xmlids = [x.strip() for x in raw.split(",") if x.strip()]
        if "base.group_portal" not in xmlids:
            xmlids.insert(0, "base.group_portal")
        return xmlids

    def _assert_open_allowed(self, token=None):
        mode = self._get_signup_mode()
        if token:
            return
        if mode in ("off", "invite"):
            raise NotFound()

    def _assert_rate_limit(self):
        now = int(time.time())
        last = request.session.get("sc_signup_last_ts")
        if last and now - int(last) < 60:
            raise Forbidden("Too many signup attempts")
        request.session["sc_signup_last_ts"] = now

    def _assert_password_strength(self, password):
        if not password or len(password) < 8:
            raise Forbidden("Password too short")
        has_alpha = any(ch.isalpha() for ch in password)
        has_digit = any(ch.isdigit() for ch in password)
        if not (has_alpha and has_digit):
            raise Forbidden("Password too weak")

    def _assert_email_allowed(self, email):
        if not email:
            return
        whitelist = self._get_domain_whitelist()
        if not whitelist:
            return
        domain = email.split("@")[-1].lower()
        if domain not in whitelist:
            raise Forbidden("Email domain not allowed")

    def _apply_user_defaults(self, user):
        if not user:
            return
        vals = {}
        if not user.lang:
            vals["lang"] = "zh_CN"
        if not user.tz:
            vals["tz"] = "Asia/Shanghai"
        if request.env.company and user.company_id != request.env.company:
            vals["company_id"] = request.env.company.id
            vals["company_ids"] = [(4, request.env.company.id)]
        if vals:
            user.sudo().write(vals)

        groups = []
        for xmlid in self._get_default_group_xmlids():
            group = request.env.ref(xmlid, raise_if_not_found=False)
            if group:
                groups.append(group.id)
        if groups:
            user.sudo().write({"groups_id": [(4, gid) for gid in groups]})

    def _send_activation_email(self, user):
        partner = user.partner_id.sudo()
        if hasattr(partner, "signup_prepare"):
            partner.signup_prepare()
        token = partner.signup_token
        if not token:
            _logger.warning("signup token missing for user %s", user.id)
            return

        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        activate_url = f"{base_url}/sc/auth/activate/{token}"

        mail_vals = {
            "subject": "请激活您的账户",
            "body_html": (
                "<p>您的账户已创建，请点击下方链接完成激活：</p>"
                f"<p><a href=\"{activate_url}\">{activate_url}</a></p>"
            ),
            "email_to": user.email or user.login,
            "auto_delete": True,
        }
        request.env["mail.mail"].sudo().create(mail_vals).send()

    def get_auth_signup_qcontext(self):
        qcontext = super().get_auth_signup_qcontext()
        token = qcontext.get("token")
        self._assert_open_allowed(token=token)
        return qcontext

    def do_signup(self, qcontext):
        token = qcontext.get("token")
        self._assert_open_allowed(token=token)
        self._assert_rate_limit()

        password = qcontext.get("password")
        login = qcontext.get("login") or qcontext.get("email")
        self._assert_password_strength(password)
        self._assert_email_allowed(login)

        res = super().do_signup(qcontext)

        user = request.env["res.users"].sudo().search([("login", "=", login)], order="id desc", limit=1)
        self._apply_user_defaults(user)

        if not token and self._require_email_verify():
            user.sudo().write({"active": False})
            self._send_activation_email(user)
        return res

    @http.route("/sc/auth/activate/<string:token>", type="http", auth="public", website=True, csrf=False)
    def sc_activate_account(self, token, **kwargs):
        partner = request.env["res.partner"].sudo().search([("signup_token", "=", token)], limit=1)
        if not partner or not partner.user_ids:
            raise NotFound()
        user = partner.user_ids[0]
        user.sudo().write({"active": True})
        partner.sudo().write({"signup_token": False, "signup_expiration": False, "signup_type": False})

        params = {"login": user.login}
        return request.redirect("/web/login?" + urlencode(params))
