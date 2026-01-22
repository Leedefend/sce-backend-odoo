# -*- coding: utf-8 -*-
import logging
import time
from urllib.parse import urlencode

from werkzeug.exceptions import Forbidden, NotFound

from dateutil.relativedelta import relativedelta

from odoo import _, fields, http
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome, SignupError, UserError

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

    def _get_token_expiration_hours(self):
        icp = request.env["ir.config_parameter"].sudo()
        try:
            hours = int(icp.get_param("sc.signup.token_expiration_hours", "24") or 24)
        except ValueError:
            hours = 24
        return max(hours, 0)

    def _get_recaptcha_mode(self):
        icp = request.env["ir.config_parameter"].sudo()
        mode = (icp.get_param("sc.signup.recaptcha.mode") or "soft").strip().lower()
        return mode if mode in ("off", "soft", "hard") else "soft"

    def _assert_open_allowed(self, token=None):
        mode = self._get_signup_mode()
        if token:
            return
        if mode in ("off", "invite"):
            raise NotFound()

    def _get_rate_limit_config(self):
        icp = request.env["ir.config_parameter"].sudo()
        window_sec = int(icp.get_param("sc.signup.ratelimit.window_sec", "60") or 60)
        max_per_ip = int(icp.get_param("sc.signup.ratelimit.max_per_ip", "3") or 3)
        max_per_email = int(icp.get_param("sc.signup.ratelimit.max_per_email", "2") or 2)
        return window_sec, max_per_ip, max_per_email

    def _get_client_ip(self):
        req = request.httprequest
        remote_addr = (req.remote_addr or "").strip()
        xff = (req.headers.get("X-Forwarded-For") or "").strip()
        if remote_addr in ("127.0.0.1", "::1") and xff:
            return xff.split(",")[0].strip()
        return remote_addr or "unknown"

    def _assert_rate_limit(self, login=None):
        window_sec, max_per_ip, max_per_email = self._get_rate_limit_config()
        if window_sec <= 0:
            return
        Throttle = request.env["sc.signup.throttle"].sudo()
        ip = self._get_client_ip()
        if max_per_ip > 0:
            ok = Throttle.check_and_bump(f"ip:{ip}", window_sec, max_per_ip)
            if not ok:
                raise Forbidden(_("操作过于频繁，请稍后再试"))
        if login and max_per_email > 0:
            ok = Throttle.check_and_bump(f"email:{login.lower()}", window_sec, max_per_email)
            if not ok:
                raise Forbidden(_("操作过于频繁，请稍后再试"))

    def _assert_password_strength(self, password):
        if not password or len(password) < 8:
            raise Forbidden(_("密码太短，请至少包含 8 位字符"))
        has_alpha = any(ch.isalpha() for ch in password)
        has_digit = any(ch.isdigit() for ch in password)
        if not (has_alpha and has_digit):
            raise Forbidden(_("密码强度不足，请至少包含字母和数字"))

    def _assert_email_allowed(self, email):
        if not email:
            return
        whitelist = self._get_domain_whitelist()
        if not whitelist:
            return
        domain = email.split("@")[-1].lower()
        if domain not in whitelist:
            raise Forbidden(_("该邮箱域名不在允许范围"))

    def _apply_user_defaults(self, user):
        if not user:
            return
        vals = {}
        if not user.lang or user.lang == "en_US":
            vals["lang"] = "zh_CN"
        if not user.tz:
            vals["tz"] = "Asia/Shanghai"
        if request.env.company and user.company_id != request.env.company:
            vals["company_id"] = request.env.company.id
            vals["company_ids"] = [(4, request.env.company.id)]
        if vals:
            user.sudo().write(vals)
            partner_vals = {k: v for k, v in vals.items() if k in ("lang", "tz")}
            if partner_vals and user.partner_id:
                user.partner_id.sudo().write(partner_vals)

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
            hours = self._get_token_expiration_hours()
            expiration = fields.Datetime.now() + relativedelta(hours=hours) if hours else False
            partner.signup_prepare(expiration=expiration)
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

    @http.route("/web/signup", type="http", auth="public", website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        token = qcontext.get("token")
        mode = self._get_signup_mode()
        recaptcha_mode = self._get_recaptcha_mode()

        if not token and mode in ("off", "invite"):
            raise NotFound()

        if "error" not in qcontext and request.httprequest.method == "POST":
            try:
                if recaptcha_mode != "off":
                    ok = request.env["ir.http"]._verify_request_recaptcha_token("signup")
                    if not ok:
                        if recaptcha_mode == "hard":
                            raise UserError(_("验证码校验失败，请稍后再试"))
                        _logger.warning("signup recaptcha failed (mode=soft), allow proceed")
                        qcontext["warning"] = _("验证码未通过，本次已放行")

                self.do_signup(qcontext)

                if (not token) and self._require_email_verify():
                    login = qcontext.get("login") or qcontext.get("email")
                    return request.redirect("/web/login?" + urlencode({"login": login or "", "signup": "1"}))

                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext["error"] = e.args[0]
            except (SignupError, AssertionError, Forbidden) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("该邮箱已注册，请直接登录或找回密码")
                else:
                    _logger.warning("%s", e)
                    qcontext["error"] = _("无法创建新账号") + "\n" + str(e)

        response = request.render("auth_signup.signup", qcontext)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
        return response

    def get_auth_signup_qcontext(self):
        qcontext = super().get_auth_signup_qcontext()
        token_param = request.params.get("token")
        if not token_param and self._get_signup_mode() == "open":
            qcontext.pop("token", None)
            qcontext.pop("invalid_token", None)
        token = qcontext.get("token")
        self._assert_open_allowed(token=token)
        return qcontext

    def do_signup(self, qcontext):
        token = qcontext.get("token")
        self._assert_open_allowed(token=token)
        password = qcontext.get("password")
        login = qcontext.get("login") or qcontext.get("email")
        self._assert_rate_limit(login)
        self._assert_password_strength(password)
        self._assert_email_allowed(login)

        require_verify = (not token) and self._require_email_verify()
        if require_verify:
            values = self._prepare_signup_values(qcontext)
            values["active"] = False
            login, password = request.env["res.users"].sudo().signup(values, token)
        else:
            super().do_signup(qcontext)

        user = request.env["res.users"].sudo().search([("login", "=", login)], order="id desc", limit=1)
        self._apply_user_defaults(user)

        if require_verify:
            user.sudo().write({"active": False})
            self._send_activation_email(user)
        return True

    @http.route("/sc/auth/activate/<string:token>", type="http", auth="public", website=False, csrf=False)
    def sc_activate_account(self, token, **kwargs):
        try:
            partner = request.env["res.partner"].sudo()._signup_retrieve_partner(token, check_validity=True, raise_exception=True)
        except UserError:
            qcontext = self.get_auth_signup_qcontext()
            qcontext["error"] = _("激活链接已失效或已使用，请重新发送激活邮件。")
            response = request.render("auth_signup.signup", qcontext)
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
            return response
        user = partner.with_context(active_test=False).user_ids[:1] if partner else False
        if not partner or not user:
            raise NotFound()
        user.sudo().write({"active": True})
        partner.sudo().write({"signup_token": False, "signup_expiration": False, "signup_type": False})

        params = {"login": user.login}
        return request.redirect("/web/login?" + urlencode(params))
