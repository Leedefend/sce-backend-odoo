# -*- coding: utf-8 -*-
from odoo import api, models


REQUIRED_TAXES = [
    ("销项VAT 9%", 9.0, "sale"),
    ("进项VAT 13%", 13.0, "purchase"),
]
DEFAULT_LANG = "zh_CN"
DEFAULT_TZ = "Asia/Shanghai"


class ScPlatformInitialization(models.TransientModel):
    _name = "sc.platform.initialization"
    _description = "SC Platform Initialization"

    @api.model
    def apply_baseline(self):
        from odoo.addons.smart_construction_core.hooks import ensure_core_taxes

        self._ensure_default_language()
        self._normalize_internal_user_preferences()
        ensure_core_taxes(self.env)
        self._ensure_core_taxes_for_all_companies()
        self.env["ir.config_parameter"].sudo().set_param("sc.platform.core_taxes_ready", "1")
        self.env["ir.config_parameter"].sudo().set_param("sc.platform.default_lang", DEFAULT_LANG)
        self.env["ir.config_parameter"].sudo().set_param("sc.platform.default_tz", DEFAULT_TZ)
        return True

    @api.model
    def _ensure_default_language(self):
        Lang = self.env["res.lang"].sudo().with_context(active_test=False)
        lang = Lang.search([("code", "=", DEFAULT_LANG)], limit=1)
        if lang and not lang.active:
            lang.write({"active": True})
        return lang

    @api.model
    def _normalize_internal_user_preferences(self):
        lang = self._ensure_default_language()
        if not lang:
            return False

        Users = self.env["res.users"].sudo().with_context(active_test=False)
        internal_users = Users.search([("share", "=", False)])
        for user in internal_users:
            write_vals = {}
            if user.lang != DEFAULT_LANG:
                write_vals["lang"] = DEFAULT_LANG
            if user.tz != DEFAULT_TZ:
                write_vals["tz"] = DEFAULT_TZ
            if write_vals:
                user.write(write_vals)
        self.env["ir.config_parameter"].sudo().set_param(
            "sc.platform.internal_user_preferences_count",
            str(len(internal_users)),
        )
        return True

    @api.model
    def _ensure_core_taxes_for_all_companies(self):
        Company = self.env["res.company"].sudo()
        for company in Company.search([]):
            self._ensure_company_core_taxes(company)
        return True

    @api.model
    def _ensure_company_core_taxes(self, company):
        country = company.account_fiscal_country_id or company.partner_id.country_id
        if not country:
            country = self.env.ref("base.cn", raise_if_not_found=False)
            if country:
                company.write({"account_fiscal_country_id": country.id})
                if company.partner_id:
                    company.partner_id.write({"country_id": country.id})

        Group = self.env["account.tax.group"].sudo().with_context(active_test=False)
        tax_group = Group.search([("company_id", "=", company.id), ("name", "=", "增值税")], limit=1)
        if not tax_group:
            vals = {"name": "增值税", "company_id": company.id}
            if country:
                vals["country_id"] = country.id
            tax_group = Group.create(vals)

        Tax = self.env["account.tax"].sudo().with_context(active_test=False)
        for name, amount, tax_use in REQUIRED_TAXES:
            domain = [
                ("company_id", "=", company.id),
                ("name", "=", name),
                ("amount", "=", float(amount)),
                ("type_tax_use", "=", tax_use),
                ("amount_type", "=", "percent"),
                ("price_include", "=", False),
            ]
            tax = Tax.search(domain, limit=1)
            if tax:
                if not tax.active:
                    tax.write({"active": True})
                continue
            vals = {
                "name": name,
                "company_id": company.id,
                "tax_group_id": tax_group.id,
                "amount": float(amount),
                "amount_type": "percent",
                "type_tax_use": tax_use,
                "price_include": False,
                "active": True,
            }
            if country:
                vals["country_id"] = country.id
            Tax.create(vals)
        return True

    @api.model
    def assert_baseline_ready(self):
        Tax = self.env["account.tax"].sudo().with_context(active_test=False)
        missing = []
        for company in self.env["res.company"].sudo().search([]):
            for name, amount, tax_use in REQUIRED_TAXES:
                tax = Tax.search(
                    [
                        ("company_id", "=", company.id),
                        ("name", "=", name),
                        ("amount", "=", float(amount)),
                        ("type_tax_use", "=", tax_use),
                        ("amount_type", "=", "percent"),
                        ("price_include", "=", False),
                        ("active", "=", True),
                    ],
                    limit=1,
                )
                if not tax:
                    missing.append(f"{company.display_name}: {name} {amount}% {tax_use}")
        if missing:
            raise AssertionError("platform baseline missing core taxes: " + ", ".join(missing))
        return True
