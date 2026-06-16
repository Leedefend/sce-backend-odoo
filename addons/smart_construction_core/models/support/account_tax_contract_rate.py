# -*- coding: utf-8 -*-
import re

from odoo import api, models
from odoo.exceptions import ValidationError


class AccountTax(models.Model):
    _inherit = "account.tax"

    @staticmethod
    def _sc_m2o_id(value):
        if hasattr(value, "id"):
            return value.id
        if isinstance(value, (list, tuple)):
            return int(value[0] or 0) if value else 0
        return int(value or 0)

    @api.model
    def _sc_parse_contract_rate_amount(self, value):
        text = str(value or "").strip()
        match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*%?", text)
        if not match:
            return None
        amount = float(match.group(1))
        if amount < 0 or amount > 100:
            raise ValidationError("税率必须在 0% 到 100% 之间。")
        return amount

    @api.model
    def _sc_is_contract_rate_vals(self, vals):
        vals = vals or {}
        if vals.get("type_tax_use") == "none" and vals.get("amount_type", "percent") == "percent":
            return True
        group_id = self._sc_m2o_id(vals.get("tax_group_id"))
        if group_id:
            group = self.env["account.tax.group"].sudo().browse(group_id).exists()
            if group and group.name == "合同税率":
                return True
        return False

    @api.model
    def _sc_prepare_contract_rate_vals(self, vals):
        vals = dict(vals or {})
        if not self._sc_is_contract_rate_vals(vals):
            return vals

        company = self.env["res.company"].sudo().browse(self._sc_m2o_id(vals.get("company_id"))).exists() or self.env.company
        helper = self.env["construction.contract"].sudo().with_company(company)
        group = helper._sc_contract_tax_group(company)
        country = company.account_fiscal_country_id or company.partner_id.country_id or self.env.ref(
            "base.cn",
            raise_if_not_found=False,
        )
        amount = self._sc_parse_contract_rate_amount(vals.get("name"))
        if amount is None:
            amount = self._sc_parse_contract_rate_amount(vals.get("amount"))
        if amount is None:
            raise ValidationError("请输入税率百分比，例如：3%、9%、13%。")

        vals.update(
            {
                "name": helper._sc_format_contract_tax_name(amount),
                "amount": amount,
                "amount_type": "percent",
                "type_tax_use": "none",
                "price_include": False,
                "company_id": company.id,
                "tax_group_id": group.id,
            }
        )
        if country:
            vals["country_id"] = country.id
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        prepared_list = [self._sc_prepare_contract_rate_vals(vals) for vals in vals_list]
        records = self.browse()
        for vals in prepared_list:
            if self._sc_is_contract_rate_vals(vals):
                existing = self.sudo().with_context(active_test=False).search(
                    [
                        ("company_id", "=", vals.get("company_id")),
                        ("type_tax_use", "=", "none"),
                        ("amount_type", "=", "percent"),
                        ("amount", "=", float(vals.get("amount") or 0.0)),
                        ("price_include", "=", False),
                    ],
                    order="active desc, id asc",
                    limit=1,
                )
                if existing:
                    write_vals = {
                        key: value
                        for key, value in vals.items()
                        if key in {"name", "tax_group_id", "country_id", "active"}
                        and (
                            self._sc_m2o_id(existing[key]) != self._sc_m2o_id(value)
                            if key in {"tax_group_id", "country_id"}
                            else existing[key] != value
                        )
                    }
                    write_vals["active"] = True
                    existing.write(write_vals)
                    records |= existing
                    continue
            records |= super(AccountTax, self).create([vals])
        return records

    def write(self, vals):
        vals = dict(vals or {})
        if vals and len(self) == 1 and self.type_tax_use == "none" and self.amount_type == "percent":
            base_vals = {
                "name": vals.get("name", self.name),
                "amount": vals.get("amount", self.amount),
                "type_tax_use": vals.get("type_tax_use", self.type_tax_use),
                "amount_type": vals.get("amount_type", self.amount_type),
                "company_id": vals.get("company_id", self.company_id.id),
                "tax_group_id": vals.get("tax_group_id", self.tax_group_id.id),
                "price_include": vals.get("price_include", self.price_include),
            }
            prepared = self._sc_prepare_contract_rate_vals(base_vals)
            vals.update({key: value for key, value in prepared.items() if key in vals or key in {"name", "amount"}})
        return super().write(vals)
