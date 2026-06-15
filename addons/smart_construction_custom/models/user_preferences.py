# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.tools.safe_eval import safe_eval


PARTNER_ACTIONS = {
    "customer": {
        "xmlid": "smart_construction_core.action_sc_customer_partner",
        "title": "客户",
        "name_label": "客户名称",
        "fields": [
            ("name", "客户名称"),
            ("company_type", "客户类型"),
            ("active", "启用"),
            ("vat", "统一社会信用代码"),
            ("sc_legal_representative", "法定代表人"),
            ("sc_contact_name", "联系人"),
            ("phone", "电话"),
            ("mobile", "手机"),
            ("email", "电子邮件"),
            ("sc_registered_capital", "注册资本"),
            ("sc_establishment_date", "成立日期"),
            ("sc_business_term", "营业期限"),
            ("sc_region", "所属地区"),
            ("company_registry", "工商注册号"),
            ("industry_id", "行业"),
            ("sc_account_name", "账户名称"),
            ("sc_bank_name", "开户银行"),
            ("sc_bank_account", "银行账号"),
            ("property_account_position_id", "财政状况"),
            ("user_id", "负责人"),
            ("website", "网站"),
            ("state_id", "省份"),
            ("sc_city_id", "城市"),
            ("zip", "邮编"),
            ("street", "街道地址"),
            ("street2", "详细地址"),
            ("sc_business_scope", "经营范围"),
            ("child_ids", "联系人明细"),
            ("bank_ids", "账户明细"),
            ("sc_attachment_ids", "附件"),
            ("comment", "备注"),
            ("sc_business_fact_line_ids", "关联业务明细"),
        ],
    },
    "supplier": {
        "xmlid": "smart_construction_core.action_sc_supplier_partner",
        "title": "供应商",
        "name_label": "供应商名称",
        "fields": [
            ("name", "供应商名称"),
            ("company_type", "主体类型"),
            ("active", "启用"),
            ("sc_supplier_type_ids", "业务类型"),
            ("vat", "统一社会信用代码"),
            ("sc_legal_representative", "法定代表人"),
            ("sc_contact_name", "联系人"),
            ("phone", "电话"),
            ("mobile", "手机"),
            ("email", "电子邮件"),
            ("sc_registered_capital", "注册资本"),
            ("sc_establishment_date", "成立日期"),
            ("sc_business_term", "营业期限"),
            ("sc_region", "所属地区"),
            ("company_registry", "工商注册号"),
            ("industry_id", "行业"),
            ("sc_account_name", "账户名称"),
            ("sc_bank_name", "开户银行"),
            ("sc_bank_account", "银行账号"),
            ("property_account_position_id", "财政状况"),
            ("user_id", "负责人"),
            ("website", "网站"),
            ("state_id", "省份"),
            ("sc_city_id", "城市"),
            ("zip", "邮编"),
            ("street", "街道地址"),
            ("street2", "详细地址"),
            ("sc_business_scope", "经营范围"),
            ("child_ids", "联系人明细"),
            ("bank_ids", "账户明细"),
            ("sc_attachment_ids", "附件"),
            ("sc_supplier_note", "供应商备注"),
            ("comment", "备注"),
            ("sc_business_fact_line_ids", "关联业务明细"),
        ],
    },
}

PARTNER_EXCLUDED_FORM_FIELDS = {
    "property_account_receivable_id",
    "property_account_payable_id",
    "property_payment_term_id",
    "property_supplier_payment_term_id",
    "category_id",
    "country_id",
    "city",
    "sc_business_role_label",
    "sc_business_fact_basis",
    "sc_default_tax_rate",
    "sc_default_tax_rate_text",
    "sc_supplier_type_label",
    "sc_source_fact_count",
    "sc_source_project_name",
    "sc_source_document_state",
    "sc_source_receipt_amount",
    "sc_source_payment_amount",
    "sc_source_push_result",
    "sc_source_partner_code",
    "sc_source_cooperation_type",
    "sc_source_created_by",
    "sc_source_created_at",
    "sc_source_fact_source",
}


class ScUserPreferenceInitialization(models.TransientModel):
    _name = "sc.user.preference.initialization"
    _description = "SC User Preference Initialization"

    @api.model
    def apply_partner_form_preferences(self):
        if "ui.business.config.contract" not in self.env:
            return False
        for config in PARTNER_ACTIONS.values():
            self._upsert_partner_form_contract(config)
        self.env["ir.config_parameter"].sudo().set_param("sc.custom.partner_form_preferences_ready", "1")
        return True

    @api.model
    def _upsert_partner_form_contract(self, config):
        action = self.env.ref(config["xmlid"], raise_if_not_found=False)
        if not action:
            return False
        form_view = next((row.view_id for row in action.view_ids if row.view_id.type == "form"), self.env["ir.ui.view"])
        fields_map = self.env["res.partner"].fields_get()
        china = self.env["res.country"].search([("code", "=", "CN")], limit=1)
        self._ensure_partner_action_country_context(action, china)
        field_rows = []
        layout_children = []
        for index, (name, label) in enumerate(config["fields"], start=1):
            if name not in fields_map:
                continue
            field_row = {
                "name": name,
                "label": label,
                "visible": True,
                "sequence": index * 10,
            }
            self._enrich_partner_field_contract_row(field_row, name, china=china)
            field_rows.append(field_row)
            layout_children.append(self._field_layout_node(name, label, fields_map[name], china=china))
            if name == "comment":
                layout_children.append({
                    "type": "button",
                    "name": "action_open_sc_partner_business_fact_lines",
                    "label": "查看关联业务明细",
                    "buttonType": "object",
                    "action": {
                        "name": "action_open_sc_partner_business_fact_lines",
                        "type": "object",
                        "label": "查看关联业务明细",
                    },
                })
        for name in sorted(PARTNER_EXCLUDED_FORM_FIELDS):
            if name not in fields_map:
                continue
            field_rows.append({
                "name": name,
                "visible": False,
                "sequence": 9000,
            })
        payload = {
            "view_orchestration": {
                "views": {
                    "form": {
                        "title": config["title"],
                        "fields": field_rows,
                        **({
                            "defaults": {"country_id": [int(china.id), china.name]},
                            "context": {"default_country_id": int(china.id)},
                        } if china else {}),
                        "layout": [
                            {
                                "type": "sheet",
                                "name": "sc_custom_partner_form_sheet",
                                "children": [
                                    {
                                        "type": "group",
                                        "name": "sc_custom_partner_flat_fields",
                                        "columns": 3,
                                        "children": layout_children,
                                    }
                                ],
                            }
                        ],
                    }
                }
            }
        }
        Contract = self.env["ui.business.config.contract"].sudo()
        name = "view_orchestration:res.partner:form:action:%s:view:0" % int(action.id)
        rec = Contract.search([("name", "=", name), ("company_id", "=", self.env.company.id)], limit=1)
        vals = {
            "name": name,
            "model": "res.partner",
            "view_type": "form",
            "action_id": action.id,
            "view_id": False,
            "company_id": self.env.company.id,
            "priority": 100,
            "active": True,
            "contract_json": payload,
        }
        if rec:
            changed = (
                rec.contract_json != payload
                or rec.status != "published"
                or not rec.active
                or rec.action_id != action
                or rec.company_id != self.env.company
            )
            if changed:
                rec.write(vals)
                rec.action_publish()
        else:
            rec = Contract.create(vals)
            rec.action_publish()
        return rec

    @api.model
    def _enrich_partner_field_contract_row(self, row, name, *, china=None):
        if name == "state_id" and china:
            china_domain = [["country_id", "=", int(china.id)]]
            relation_entry = {
                "model": "res.country.state",
                "domain": china_domain,
                "order": "name asc",
            }
            row["domain"] = china_domain
            row["relation_entry"] = relation_entry
            row["componentConfig"] = {
                "domain": china_domain,
                "relation_entry": relation_entry,
            }
        if name == "sc_city_id":
            city_domain = "[('state_id', '=', state_id)]"
            empty_city_domain = [["id", "=", -1]]
            relation_entry = {
                "model": "sc.partner.city",
                "domain": empty_city_domain,
                "order": "sequence asc, name asc",
            }
            row["domain"] = city_domain
            row["relation_entry"] = relation_entry
            row["componentConfig"] = {
                "domain": city_domain,
                "relation_entry": relation_entry,
            }
        return row

    @api.model
    def _ensure_partner_action_country_context(self, action, china):
        if not action or not china:
            return
        try:
            context = safe_eval(action.context or "{}")
        except Exception:
            context = {}
        if not isinstance(context, dict):
            context = {}
        if context.get("default_country_id") == int(china.id):
            return
        updated = dict(context)
        updated["default_country_id"] = int(china.id)
        action.sudo().write({"context": repr(updated)})

    @api.model
    def _field_layout_node(self, name, label, descriptor, *, china=None):
        node = {
            "type": "field",
            "name": name,
            "string": label,
            "label": label,
            "fieldInfo": {
                "name": name,
                "label": label,
                "type": descriptor.get("type") or descriptor.get("ttype") or "char",
            },
        }
        widget = self._field_widget(name, descriptor)
        if widget:
            node["fieldInfo"]["widget"] = widget
        if name == "state_id" and china:
            china_domain = [["country_id", "=", int(china.id)]]
            relation_entry = {
                "model": "res.country.state",
                "domain": china_domain,
                "order": "name asc",
            }
            node["fieldInfo"]["domain"] = china_domain
            node["fieldInfo"]["relation_entry"] = relation_entry
            node["componentConfig"] = {
                "domain": china_domain,
                "relation_entry": relation_entry,
            }
        if name == "sc_city_id":
            city_domain = "[('state_id', '=', state_id)]"
            empty_city_domain = [["id", "=", -1]]
            relation_entry = {
                "model": "sc.partner.city",
                "domain": empty_city_domain,
                "order": "sequence asc, name asc",
            }
            node["fieldInfo"]["domain"] = city_domain
            node["fieldInfo"]["relation_entry"] = relation_entry
            node["componentConfig"] = {
                "domain": city_domain,
                "relation_entry": relation_entry,
            }
        if descriptor.get("readonly") or name.startswith("sc_source_") or name in {
            "sc_business_role_label",
            "sc_business_fact_basis",
            "sc_supplier_type_label",
            "sc_business_fact_line_ids",
        }:
            node["readonly"] = True
        return node

    @api.model
    def _field_widget(self, name, descriptor):
        if name == "category_id" or name == "sc_supplier_type_ids":
            return "many2many_tags"
        if name == "sc_attachment_ids":
            return "many2many_binary"
        field_type = descriptor.get("type") or descriptor.get("ttype")
        return {
            "many2one": "many2one",
            "one2many": "one2many_list",
            "many2many": "many2many_tags",
            "boolean": "boolean",
            "date": "date",
            "datetime": "datetime",
            "text": "textarea",
            "html": "html",
        }.get(field_type)
