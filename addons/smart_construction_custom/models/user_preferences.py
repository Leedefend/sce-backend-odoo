# -*- coding: utf-8 -*-
import json
import xml.etree.ElementTree as ET

from odoo import api, models
from odoo.addons.smart_core.utils.backend_contract_boundaries import ensure_lowcode_contract_source_status
from odoo.tools.safe_eval import safe_eval


PARTNER_FORM_PREFERENCE_SOURCE = "smart_construction_custom.partner_form_preference"
USER_FORM_PREFERENCE_SOURCE = "smart_construction_custom.user_form_preference"

PARTNER_ACTIONS = {
    "customer": {
        "xmlid": "smart_construction_core.action_sc_customer_partner",
        "title": "客户",
        "name_label": "客户名称",
        "required_fields": ["name"],
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
        "required_fields": ["name"],
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

FORMAL_HANDLING_MENU_XMLIDS = (
    "smart_construction_core.menu_project_material_plan",
    "smart_construction_core.menu_sc_company_document_archive",
    "smart_construction_core.menu_sc_company_finance_expense",
    "smart_construction_core.menu_sc_construction_contract",
    "smart_construction_core.menu_sc_construction_diary",
    "smart_construction_core.menu_sc_contractor_project_borrow",
    "smart_construction_core.menu_sc_contractor_project_repay",
    "smart_construction_core.menu_sc_deduction_bill",
    "smart_construction_core.menu_sc_deduction_paid",
    "smart_construction_core.menu_sc_deduction_paid_refund",
    "smart_construction_core.menu_sc_engineering_progress_income",
    "smart_construction_core.menu_sc_equipment_shift_acceptance",
    "smart_construction_core.menu_sc_expense_contract_settlement",
    "smart_construction_core.menu_sc_fund_account_between_user",
    "smart_construction_core.menu_sc_general_contract",
    "smart_construction_core.menu_sc_income_contract_settlement",
    "smart_construction_core.menu_sc_invoice_application_user",
    "smart_construction_core.menu_sc_invoice_input",
    "smart_construction_core.menu_sc_invoice_prepaid_tax_user",
    "smart_construction_core.menu_sc_invoice_registration_user",
    "smart_construction_core.menu_sc_labor_casual_acceptance",
    "smart_construction_core.menu_sc_labor_usage_acceptance",
    "smart_construction_core.menu_sc_leave_request",
    "smart_construction_core.menu_sc_material_inbound",
    "smart_construction_core.menu_sc_material_outbound",
    "smart_construction_core.menu_sc_material_quote_acceptance",
    "smart_construction_core.menu_sc_partner_payment",
    "smart_construction_core.menu_sc_payment_deposit_return",
    "smart_construction_core.menu_sc_payment_deposit_return_refund_formal",
    "smart_construction_core.menu_sc_project_borrow_company",
    "smart_construction_core.menu_sc_project_expense_claim",
    "smart_construction_core.menu_sc_project_repay_company",
    "smart_construction_core.menu_sc_reimbursement_request",
    "smart_construction_core.menu_sc_salary_registration",
    "smart_construction_core.menu_sc_salary_registration_scbs55_formal",
    "smart_construction_core.menu_sc_self_funding_advance_income",
    "smart_construction_core.menu_sc_self_funding_advance_refund",
    "smart_construction_core.menu_sc_self_funding_deposit",
    "smart_construction_core.menu_sc_self_funding_deposit_refund",
    "smart_construction_core.menu_sc_social_person_registration",
    "smart_construction_core.menu_sc_social_registration",
    "smart_construction_core.menu_sc_subcontract_request_acceptance",
    "smart_construction_core.menu_sc_subsidy",
    "smart_construction_core.menu_sc_tax_certificate_registration_user",
    "smart_construction_core.menu_sc_tax_deduction_registration_user",
    "smart_construction_core.menu_sc_tender_registration",
    "smart_construction_core.menu_sc_tender_registration_fee",
    "smart_construction_core.menu_sc_user_income",
    "smart_construction_core.menu_sc_user_payment_apply_acceptance",
)

FORMAL_HANDLING_MENU_CATEGORY_CODES = {
    "smart_construction_core.menu_project_material_plan": "material.plan",
    "smart_construction_core.menu_sc_company_document_archive": "",
    "smart_construction_core.menu_sc_company_finance_expense": "finance.payment.execution.company",
    "smart_construction_core.menu_sc_construction_contract": "contract.income",
    "smart_construction_core.menu_sc_construction_diary": "site.construction.diary",
    "smart_construction_core.menu_sc_contractor_project_borrow": "finance.loan.contractor_project_borrow",
    "smart_construction_core.menu_sc_contractor_project_repay": "finance.repayment.contractor_project",
    "smart_construction_core.menu_sc_deduction_bill": "finance.deduction.bill",
    "smart_construction_core.menu_sc_deduction_paid": "finance.deduction.paid",
    "smart_construction_core.menu_sc_deduction_paid_refund": "finance.deduction.refund",
    "smart_construction_core.menu_sc_engineering_progress_income": "finance.receipt.income.progress",
    "smart_construction_core.menu_sc_equipment_shift_acceptance": "",
    "smart_construction_core.menu_sc_expense_contract_settlement": "settlement.expense",
    "smart_construction_core.menu_sc_fund_account_between_user": "finance.fund.transfer",
    "smart_construction_core.menu_sc_general_contract": "",
    "smart_construction_core.menu_sc_income_contract_settlement": "settlement.income",
    "smart_construction_core.menu_sc_invoice_application_user": "invoice.output.application",
    "smart_construction_core.menu_sc_invoice_input": "invoice.input.report",
    "smart_construction_core.menu_sc_invoice_prepaid_tax_user": "invoice.prepaid_tax",
    "smart_construction_core.menu_sc_invoice_registration_user": "invoice.output.registration",
    "smart_construction_core.menu_sc_labor_casual_acceptance": "labor.usage.casual",
    "smart_construction_core.menu_sc_labor_usage_acceptance": "labor.usage.ticket",
    "smart_construction_core.menu_sc_leave_request": "",
    "smart_construction_core.menu_sc_material_inbound": "material.inbound",
    "smart_construction_core.menu_sc_material_outbound": "material.outbound",
    "smart_construction_core.menu_sc_material_quote_acceptance": "material.rfq",
    "smart_construction_core.menu_sc_partner_payment": "finance.payment.execution.partner",
    "smart_construction_core.menu_sc_payment_deposit_return": "finance.deposit.bid.return",
    "smart_construction_core.menu_sc_payment_deposit_return_refund_formal": "finance.deposit.bid.return",
    "smart_construction_core.menu_sc_project_borrow_company": "finance.loan.project_borrow_company",
    "smart_construction_core.menu_sc_project_expense_claim": "finance.expense.project",
    "smart_construction_core.menu_sc_project_repay_company": "finance.repayment.project_company",
    "smart_construction_core.menu_sc_reimbursement_request": "finance.expense.reimbursement",
    "smart_construction_core.menu_sc_salary_registration": "hr.payroll.salary",
    "smart_construction_core.menu_sc_salary_registration_scbs55_formal": "hr.payroll.salary",
    "smart_construction_core.menu_sc_self_funding_advance_income": "finance.self_funding.income",
    "smart_construction_core.menu_sc_self_funding_advance_refund": "finance.self_funding.refund",
    "smart_construction_core.menu_sc_self_funding_deposit": "finance.deposit.bid.pay",
    "smart_construction_core.menu_sc_self_funding_deposit_refund": "finance.deposit.bid.return",
    "smart_construction_core.menu_sc_social_person_registration": "hr.payroll.social.person",
    "smart_construction_core.menu_sc_social_registration": "hr.payroll.social.registration",
    "smart_construction_core.menu_sc_subcontract_request_acceptance": "",
    "smart_construction_core.menu_sc_subsidy": "hr.payroll.subsidy",
    "smart_construction_core.menu_sc_tax_certificate_registration_user": "tax.certificate.registration",
    "smart_construction_core.menu_sc_tax_deduction_registration_user": "tax.deduction.registration",
    "smart_construction_core.menu_sc_tender_registration": "",
    "smart_construction_core.menu_sc_tender_registration_fee": "",
    "smart_construction_core.menu_sc_user_income": "finance.receipt.income.project",
    "smart_construction_core.menu_sc_user_payment_apply_acceptance": "finance.payment.apply.pay",
}

USER_FORM_PREFERENCE_ROOT_MENU_XMLID = "smart_construction_core.menu_sc_root"
USER_FORM_PREFERENCE_EXCLUDED_MENU_KEYWORDS = (
    "首页",
    "配置",
    "设置",
    "字典",
    "权限",
    "工作流",
    "审批配置",
    "菜单配置",
    "字段配置",
    "低代码",
    "报表",
    "统计",
    "分析",
)
USER_FORM_PREFERENCE_EXCLUDED_MODEL_PREFIXES = (
    "ir.",
    "ui.",
    "bus.",
    "mail.",
)
USER_FORM_PREFERENCE_EXCLUDED_MODELS = {
    "res.config.settings",
    "res.groups",
    "res.users",
    "sc.product.policy",
    "sc.product.policy.version",
    "sc.scene",
    "sc.scene.version",
}
USER_FORM_PREFERENCE_EXCLUDED_FIELDS = {
    "message_ids",
    "message_follower_ids",
    "message_partner_ids",
    "activity_ids",
    "map_ids",
}
USER_FORM_PREFERENCE_EXCLUDED_FIELD_SUFFIXES = (
    "_map_ids",
)

USER_SPLIT_HANDLING_MENU_RULES = {
    "smart_construction_core.menu_sc_reimbursement_request": {
        "label": "报销申请",
        "category_code": "finance.expense.reimbursement",
    },
    "smart_construction_core.menu_sc_project_expense_claim": {
        "label": "项目费用报销单",
        "category_code": "finance.expense.project",
    },
    "smart_construction_core.menu_sc_payment_deposit_return": {
        "label": "付款还保证金",
        "category_code": "finance.deposit.bid.return",
    },
    "smart_construction_core.menu_sc_payment_deposit_return_refund_formal": {
        "label": "付款还保证金退回",
        "category_code": "finance.deposit.bid.return",
    },
}
USER_SPLIT_HANDLING_CATEGORY_CODES = {
    "finance.expense.reimbursement",
    "finance.expense.project",
    "finance.deposit.bid.pay",
    "finance.deposit.bid.return",
    "finance.deposit.contract.pay",
    "finance.deposit.contract.return",
}
USER_SPLIT_CONTRACT_HANDLING_MENU_RULES = (
    {
        "menu_xmlid": "smart_construction_core.menu_sc_income_contract_execution",
        "label": "收入合同执行",
        "category_code": "contract.income",
        "model": "construction.contract.income",
        "integration_target": "construction.contract.income 收入合同办理",
        "context_defaults": {
            "default_type": "out",
            "default_business_category_code": "contract.income",
            "search_default_visible_income": 1,
        },
    },
    {
        "menu_xmlid": "smart_construction_core.menu_sc_expense_contract_execution",
        "label": "支出合同执行",
        "category_code": "contract.expense",
        "model": "construction.contract.expense",
        "integration_target": "construction.contract.expense 支出合同办理",
        "context_defaults": {
            "default_type": "in",
            "default_business_category_code": "contract.expense",
        },
    },
    {
        "menu_xmlid": "smart_construction_core.menu_sc_expense_contract_supplement",
        "label": "补充合同",
        "category_code": "contract.expense.supplement",
        "model": "construction.contract.expense",
        "integration_target": "construction.contract.expense 补充合同办理",
        "context_defaults": {
            "default_type": "in",
            "default_subject": "补充合同",
            "default_business_category_code": "contract.expense.supplement",
        },
    },
)
USER_SPLIT_CONTRACT_HANDLING_CATEGORY_CODES = {
    str(rule["category_code"]) for rule in USER_SPLIT_CONTRACT_HANDLING_MENU_RULES
}
USER_SPLIT_CONTRACT_SETTLEMENT_CATEGORY_CODES = {
    "settlement.income",
    "settlement.expense",
}

PRODUCT_RUNTIME_INACTIVE_MENU_XMLIDS = (
    "smart_construction_core.menu_sc_company_user_roster_formal",
)

PRODUCTIZED_FORM_RUNTIME_INACTIVE_CONTRACT_NAMES = (
    "view_orchestration:project.material.plan:form:action:525:view:0",
)


class ScUserPreferenceInitialization(models.TransientModel):
    _name = "sc.user.preference.initialization"
    _description = "SC User Preference Initialization"

    @api.model
    def apply_user_data_baseline(self):
        return True

    @api.model
    def apply_partner_form_preferences(self):
        if "ui.business.config.contract" not in self.env:
            return False
        self._deactivate_generic_user_form_preferences()
        for config in PARTNER_ACTIONS.values():
            self._upsert_partner_form_contract(config)
        self.env["ir.config_parameter"].sudo().set_param("sc.custom.partner_form_preferences_ready", "1")
        return True

    @api.model
    def apply_user_form_preferences(self):
        if "ui.business.config.contract" not in self.env:
            return False
        self._deactivate_generic_user_form_preferences()
        applied = []
        skipped = []
        for config in PARTNER_ACTIONS.values():
            rec = self._upsert_partner_form_contract(config)
            if rec:
                applied.append(int(rec.id))
        for item in self._formal_handling_form_targets():
            rec = self._upsert_formal_handling_form_contract(item)
            if rec:
                applied.append(int(rec.id))
            else:
                skipped.append("%s:%s" % (item.get("menu_xmlid"), item.get("category_code") or "-"))
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("sc.custom.user_form_preferences_ready", "1")
        params.set_param("sc.custom.user_form_preferences_contract_count", str(len(applied)))
        params.set_param("sc.custom.user_form_preferences_skipped", json.dumps(skipped, ensure_ascii=False))
        return True

    @api.model
    def apply_user_menu_preferences(self):
        if "sc.product.policy" not in self.env:
            return False
        policies = self.env["sc.product.policy"].sudo().with_context(active_test=False).search([
            ("product_key", "in", ["construction.standard", "construction.preview"]),
        ])
        changed_policy_ids = []
        split_count = 0
        for policy in policies:
            menu_groups, changed, count = self._apply_split_handling_menu_rules(policy.menu_groups or [])
            if not changed:
                continue
            policy.write({"menu_groups": menu_groups})
            changed_policy_ids.append(int(policy.id))
            split_count += count
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("sc.custom.user_menu_preferences_ready", "1")
        params.set_param("sc.custom.user_menu_preferences_policy_ids", json.dumps(changed_policy_ids))
        params.set_param("sc.custom.user_menu_preferences_split_count", str(split_count))
        return True

    @api.model
    def backfill_lowcode_contract_source_status(self):
        if "ui.business.config.contract" not in self.env:
            return False
        Contract = self.env["ui.business.config.contract"].sudo()
        updated = 0
        for rec in Contract.search([], order="id"):
            payload = rec.contract_json if isinstance(rec.contract_json, dict) else {}
            next_payload = ensure_lowcode_contract_source_status(payload)
            if next_payload == payload:
                continue
            rec.write({"contract_json": next_payload})
            updated += 1
        self.env["ir.config_parameter"].sudo().set_param(
            "sc.custom.lowcode_contract_source_status_backfill_count",
            str(updated),
        )
        return True

    @api.model
    def enforce_product_menu_runtime_cleanup(self):
        deactivated = 0
        Menu = self.env["ir.ui.menu"].sudo().with_context(active_test=False)
        for xmlid in PRODUCT_RUNTIME_INACTIVE_MENU_XMLIDS:
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if not menu:
                continue
            menu = Menu.browse(menu.id)
            if not menu.active:
                continue
            menu.write({"active": False})
            deactivated += 1
        Contract = self.env["ui.business.config.contract"].sudo().with_context(active_test=False)
        for contract in Contract.search([("name", "in", PRODUCTIZED_FORM_RUNTIME_INACTIVE_CONTRACT_NAMES)]):
            if not contract.active:
                continue
            contract.write({"active": False})
            deactivated += 1
        self.env["ir.config_parameter"].sudo().set_param(
            "sc.custom.product_menu_runtime_cleanup_count",
            str(deactivated),
        )
        return True

    @api.model
    def _apply_split_handling_menu_rules(self, menu_groups):
        changed = False
        split_count = 0
        out = []
        for group in menu_groups if isinstance(menu_groups, list) else []:
            if not isinstance(group, dict):
                out.append(group)
                continue
            next_group = dict(group)
            menus = []
            for menu in group.get("menus") if isinstance(group.get("menus"), list) else []:
                if not isinstance(menu, dict):
                    menus.append(menu)
                    continue
                next_menu = dict(menu)
                menu_xmlid = str(
                    next_menu.get("menu_xmlid")
                    or next_menu.get("page_key")
                    or next_menu.get("menu_key")
                    or ""
                ).strip()
                if self._is_merged_contract_handling_menu(next_menu):
                    replacement = self._split_contract_handling_menus(next_menu)
                    if replacement:
                        menus.extend(replacement)
                        changed = True
                        split_count += len(replacement)
                        continue
                if self._split_contract_settlement_menu(next_menu):
                    changed = True
                    split_count += 1
                rule = USER_SPLIT_HANDLING_MENU_RULES.get(menu_xmlid) or self._infer_split_handling_menu_rule(next_menu)
                if rule and self._split_handling_menu(next_menu, rule):
                    changed = True
                    split_count += 1
                if self._split_remaining_merged_menu(next_menu):
                    changed = True
                    split_count += 1
                menus.append(next_menu)
            next_group["menus"] = menus
            out.append(next_group)
        return out, changed, split_count

    @api.model
    def _is_merged_contract_handling_menu(self, menu):
        if not isinstance(menu, dict):
            return False
        menu_xmlid = str(menu.get("menu_xmlid") or menu.get("page_key") or menu.get("menu_key") or "").strip()
        return (
            menu_xmlid == "smart_construction_core.menu_sc_construction_contract"
            and str(menu.get("integration_target") or "").strip() == "construction.contract 合同办理"
            and str(menu.get("disposition_policy") or "").strip() == "merge_by_category"
        )

    @api.model
    def _split_contract_handling_menus(self, source_menu):
        out = []
        for offset, rule in enumerate(USER_SPLIT_CONTRACT_HANDLING_MENU_RULES, start=1):
            menu_record = self.env.ref(rule["menu_xmlid"], raise_if_not_found=False)
            action = self._act_window_from_menu(menu_record)
            if not menu_record or not action:
                continue
            label = str(rule["label"])
            category_code = str(rule["category_code"])
            model_name = str(rule["model"])
            view_modes = [
                str(item or "").strip()
                for item in str(getattr(action, "view_mode", "") or "").split(",")
                if str(item or "").strip()
            ]
            sequence = int(getattr(source_menu, "sequence", 0) or source_menu.get("sequence") or 0)
            row = dict(source_menu)
            row.update(
                {
                    "label": label,
                    "page_label": label,
                    "menu_id": int(menu_record.id),
                    "menu_xmlid": rule["menu_xmlid"],
                    "menu_key": rule["menu_xmlid"],
                    "page_key": rule["menu_xmlid"],
                    "capability_key": "construction.menu.%s" % rule["menu_xmlid"].replace(".", "_"),
                    "action_id": int(action.id),
                    "action_xmlid": self._external_id(action),
                    "route": "/a/%s?menu_id=%s" % (int(action.id), int(menu_record.id)),
                    "view_modes": view_modes,
                    "sequence": sequence + offset,
                    "res_model": model_name,
                    "model": model_name,
                    "fact_model": model_name,
                    "integration_model": model_name,
                    "product_domain": "contract",
                    "product_domain_label": "合同结算域",
                    "entry_intent": "handling",
                    "entry_intent_label": "办理",
                    "disposition_policy": "keep_list_form",
                    "integration_target": str(rule["integration_target"]),
                    "default_business_category_code": category_code,
                    "allowed_business_category_codes": [category_code],
                    "required_relationships": ["project_id", "partner_id"],
                    "entry_target_policy": "keep_list_form",
                    "locked_data_policy": "read_only_source_facts_no_rewrite",
                    "productization_source": "smart_construction_custom.user_menu_preference",
                    "policy_note": "custom_user_split_merged_contract_handling_menu",
                    "business_entry_contract_version": "business_entry_disposition.v1",
                    "visible_menu_path": "智慧施工管理平台 / 合同中心 / %s" % label,
                    "context_defaults": dict(rule["context_defaults"]),
                    "entry_target": {
                        "type": "action",
                        "route": "/a/%s?menu_id=%s" % (int(action.id), int(menu_record.id)),
                        "action_id": int(action.id),
                        "model": model_name,
                        "view_modes": view_modes,
                    },
                }
            )
            row.pop("integration_action_id", None)
            row.pop("integration_action_xmlid", None)
            row.pop("integration_view_modes", None)
            row.pop("integration_entry_target", None)
            out.append(row)
        return out

    @api.model
    def _external_id(self, record):
        if not record:
            return ""
        external_ids = record.get_external_id()
        return str(external_ids.get(record.id) or "").strip()

    @api.model
    def _split_contract_settlement_menu(self, menu):
        if not isinstance(menu, dict):
            return False
        category_code = str(menu.get("default_business_category_code") or "").strip()
        if category_code not in USER_SPLIT_CONTRACT_SETTLEMENT_CATEGORY_CODES:
            return False
        if str(menu.get("integration_target") or "").strip() != "sc.settlement.order 结算办理":
            return False
        label = str(menu.get("label") or menu.get("page_label") or "").strip()
        if not label:
            return False
        before = {
            "disposition_policy": menu.get("disposition_policy"),
            "entry_target_policy": menu.get("entry_target_policy"),
            "integration_target": menu.get("integration_target"),
            "allowed_business_category_codes": menu.get("allowed_business_category_codes"),
        }
        menu.update(
            {
                "disposition_policy": "keep_list_form",
                "entry_target_policy": "keep_list_form",
                "integration_target": "sc.settlement.order %s" % label,
                "allowed_business_category_codes": [category_code],
                "productization_source": "smart_construction_custom.user_menu_preference",
                "policy_note": "custom_user_split_merged_contract_settlement_menu",
                "visible_menu_path": "智慧施工管理平台 / 合同中心 / %s" % label,
            }
        )
        menu.pop("integration_entry_target", None)
        after = {
            "disposition_policy": menu.get("disposition_policy"),
            "entry_target_policy": menu.get("entry_target_policy"),
            "integration_target": menu.get("integration_target"),
            "allowed_business_category_codes": menu.get("allowed_business_category_codes"),
        }
        return before != after

    @api.model
    def _split_remaining_merged_menu(self, menu):
        if not isinstance(menu, dict):
            return False
        if str(menu.get("disposition_policy") or "").strip() != "merge_by_category":
            return False
        label = str(menu.get("label") or menu.get("page_label") or "").strip()
        if not label:
            return False
        default_code = str(menu.get("default_business_category_code") or "").strip()
        model_name = str(
            menu.get("integration_model")
            or menu.get("fact_model")
            or menu.get("model")
            or menu.get("res_model")
            or ""
        ).strip()
        if not model_name:
            model_name = str(menu.get("integration_target") or "").strip().split(" ", 1)[0]
        before = {
            "disposition_policy": menu.get("disposition_policy"),
            "entry_target_policy": menu.get("entry_target_policy"),
            "integration_target": menu.get("integration_target"),
            "allowed_business_category_codes": menu.get("allowed_business_category_codes"),
            "integration_entry_target": menu.get("integration_entry_target"),
        }
        menu.update(
            {
                "disposition_policy": "keep_list_form",
                "entry_target_policy": "keep_list_form",
                "productization_source": "smart_construction_custom.user_menu_preference",
                "policy_note": "custom_user_split_all_merged_business_menu",
            }
        )
        if model_name:
            menu["integration_target"] = "%s %s" % (model_name, label)
            menu["integration_model"] = model_name
        if default_code:
            menu["allowed_business_category_codes"] = [default_code]
            context_defaults = menu.setdefault("context_defaults", {})
            if isinstance(context_defaults, dict):
                context_defaults["default_business_category_code"] = default_code
                context_defaults["allowed_business_category_codes"] = [default_code]
        action_id = int(menu.get("action_id") or menu.get("integration_action_id") or 0)
        if action_id:
            route = str(menu.get("route") or "").strip() or "/a/%s" % action_id
            view_modes = menu.get("view_modes") if isinstance(menu.get("view_modes"), list) else []
            menu["entry_target"] = {
                "type": "action",
                "route": route,
                "action_id": action_id,
                "model": model_name,
                "view_modes": view_modes,
            }
        menu.pop("integration_entry_target", None)
        after = {
            "disposition_policy": menu.get("disposition_policy"),
            "entry_target_policy": menu.get("entry_target_policy"),
            "integration_target": menu.get("integration_target"),
            "allowed_business_category_codes": menu.get("allowed_business_category_codes"),
            "integration_entry_target": menu.get("integration_entry_target"),
        }
        return before != after

    @api.model
    def _infer_split_handling_menu_rule(self, menu):
        if not isinstance(menu, dict):
            return {}
        default_code = str(menu.get("default_business_category_code") or "").strip()
        allowed_codes = menu.get("allowed_business_category_codes") if isinstance(menu.get("allowed_business_category_codes"), list) else []
        category_code = default_code if default_code in USER_SPLIT_HANDLING_CATEGORY_CODES else ""
        if not category_code:
            category_code = next((str(code or "").strip() for code in allowed_codes if str(code or "").strip() in USER_SPLIT_HANDLING_CATEGORY_CODES), "")
        if not category_code:
            return {}
        label = str(menu.get("label") or menu.get("page_label") or "").strip()
        if not label:
            return {}
        return {"label": label, "category_code": category_code}

    @api.model
    def _split_handling_menu(self, menu, rule):
        label = str(rule["label"] or "").strip()
        category_code = str(rule["category_code"] or "").strip()
        if not label or not category_code:
            return False
        before = {
            "label": menu.get("label"),
            "page_label": menu.get("page_label"),
            "disposition_policy": menu.get("disposition_policy"),
            "entry_target_policy": menu.get("entry_target_policy"),
            "integration_target": menu.get("integration_target"),
            "allowed_business_category_codes": menu.get("allowed_business_category_codes"),
        }
        menu.update(
            {
                "label": label,
                "page_label": label,
                "product_domain": "finance_cash",
                "product_domain_label": "费用/保证金现金办理",
                "entry_intent": "handling",
                "entry_intent_label": "办理",
                "fact_model": "sc.expense.claim",
                "res_model": "sc.expense.claim",
                "model": "sc.expense.claim",
                "integration_model": "sc.expense.claim",
                "disposition_policy": "keep_list_form",
                "integration_target": "sc.expense.claim %s" % label,
                "default_business_category_code": category_code,
                "allowed_business_category_codes": [category_code],
                "entry_target_policy": "keep_list_form",
                "locked_data_policy": "read_only_source_facts_no_rewrite",
                "productization_source": "smart_construction_custom.user_menu_preference",
                "policy_note": "custom_user_split_merged_handling_menu",
                "business_entry_contract_version": "business_entry_disposition.v1",
                "visible_menu_path": "智慧施工管理平台 / 财务中心 / 费用/保证金现金办理 / %s" % label,
            }
        )
        context_defaults = menu.setdefault("context_defaults", {})
        if isinstance(context_defaults, dict):
            context_defaults["default_business_category_code"] = category_code
            context_defaults["allowed_business_category_codes"] = [category_code]
        action_id = int(menu.get("action_id") or menu.get("integration_action_id") or 0)
        route = str(menu.get("route") or "").strip()
        view_modes = menu.get("view_modes") if isinstance(menu.get("view_modes"), list) else []
        menu.pop("integration_entry_target", None)
        if action_id:
            menu["entry_target"] = {
                "type": "action",
                "route": route or "/a/%s" % action_id,
                "action_id": action_id,
                "model": "sc.expense.claim",
                "view_modes": view_modes,
            }
        after = {
            "label": menu.get("label"),
            "page_label": menu.get("page_label"),
            "disposition_policy": menu.get("disposition_policy"),
            "entry_target_policy": menu.get("entry_target_policy"),
            "integration_target": menu.get("integration_target"),
            "allowed_business_category_codes": menu.get("allowed_business_category_codes"),
        }
        return before != after

    @api.model
    def _deactivate_generic_user_form_preferences(self):
        Contract = self.env["ui.business.config.contract"].sudo()
        rows = Contract.search([
            ("name", "ilike", ":custom_user_default"),
            ("company_id", "=", self.env.company.id),
            ("active", "=", True),
        ])
        if rows:
            rows.write({"active": False})

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
        required_names = []
        configured_required = {
            str(name or "").strip()
            for name in config.get("required_fields", [])
            if str(name or "").strip()
        }
        for index, (name, label) in enumerate(config["fields"], start=1):
            if name not in fields_map:
                continue
            descriptor = dict(fields_map[name])
            if name in configured_required:
                descriptor["required"] = True
                descriptor["source_required"] = True
            required = bool(descriptor.get("required"))
            if required:
                required_names.append(name)
            field_row = {
                "name": name,
                "label": label,
                "visible": True,
                "sequence": index * 10,
                **({"required": True} if required else {}),
            }
            self._enrich_partner_field_contract_row(field_row, name, china=china)
            field_rows.append(field_row)
            layout_children.append(self._field_layout_node(name, label, descriptor, china=china))
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
                },
                "context": {
                    "source": PARTNER_FORM_PREFERENCE_SOURCE,
                    "scope": "partner_master_form_preference",
                },
            }
        }
        if required_names:
            payload["field_policies"] = {
                name: {"source_required": True}
                for name in required_names
            }
            payload["validation_rules"] = [
                {
                    "code": "REQUIRED",
                    "field": name,
                    "source": PARTNER_FORM_PREFERENCE_SOURCE,
                    "when_profiles": ["create", "edit"],
                }
                for name in required_names
            ]
        return self._upsert_form_contract(
            name="view_orchestration:res.partner:form:action:%s:view:0" % int(action.id),
            model_name="res.partner",
            action=action,
            view=False,
            priority=600,
            payload=payload,
        )

    @api.model
    def _formal_handling_form_targets(self):
        targets_by_key = {}
        seen = set()
        for menu, menu_xmlid, source in self._user_form_preference_menu_entries():
            action = self._act_window_from_menu(menu)
            if not self._is_user_business_form_action(menu, action):
                continue
            action_key = (int(action.id), str(action.res_model))
            if action_key in seen:
                continue
            seen.add(action_key)
            context = self._action_context(action)
            category_code = str(
                context.get("default_business_category_code")
                or FORMAL_HANDLING_MENU_CATEGORY_CODES.get(menu_xmlid)
                or ""
            ).strip()
            targets_by_key[action_key] = {
                "menu_xmlid": menu_xmlid,
                "menu_id": int(menu.id),
                "action": action,
                "model": str(action.res_model),
                "title": str(menu.name or action.name or action.res_model),
                "category_code": category_code,
                "context": context,
                "source": source,
            }
        return list(targets_by_key.values())

    @api.model
    def _user_form_preference_menu_entries(self):
        entries = []
        seen_menu_ids = set()
        for menu_xmlid in FORMAL_HANDLING_MENU_XMLIDS:
            menu = self.env.ref(menu_xmlid, raise_if_not_found=False)
            if not menu or not menu.exists():
                continue
            entries.append((menu, menu_xmlid, "confirmed_formal_menu"))
            seen_menu_ids.add(int(menu.id))

        root = self.env.ref(USER_FORM_PREFERENCE_ROOT_MENU_XMLID, raise_if_not_found=False)
        if not root:
            return entries
        menus = self.env["ir.ui.menu"].sudo().search(
            [("id", "child_of", int(root.id)), ("id", "!=", int(root.id))],
            order="sequence,id",
        )
        xmlids_by_id = menus.get_external_id()
        for menu in menus:
            if int(menu.id) in seen_menu_ids:
                continue
            menu_xmlid = str(xmlids_by_id.get(menu.id) or "").strip()
            action = self._act_window_from_menu(menu)
            if not self._is_user_business_form_action(menu, action):
                continue
            entries.append((menu, menu_xmlid, "business_menu_discovery"))
            seen_menu_ids.add(int(menu.id))
        return entries

    @api.model
    def _is_user_business_form_action(self, menu, action):
        if not action or not action.exists() or not action.res_model:
            return False
        model_name = str(action.res_model)
        if model_name == "res.partner":
            return False
        if model_name in USER_FORM_PREFERENCE_EXCLUDED_MODELS:
            return False
        if any(model_name.startswith(prefix) for prefix in USER_FORM_PREFERENCE_EXCLUDED_MODEL_PREFIXES):
            return False
        if model_name not in self.env:
            return False
        model = self.env[model_name]
        if getattr(model, "_transient", False):
            return False
        path = self._menu_path_label(menu)
        if any(keyword in path for keyword in USER_FORM_PREFERENCE_EXCLUDED_MENU_KEYWORDS):
            return False
        view_modes = {
            str(item or "").strip()
            for item in str(getattr(action, "view_mode", "") or "").split(",")
            if str(item or "").strip()
        }
        return "form" in view_modes or bool(self._action_form_view_id(action))

    @api.model
    def _menu_path_label(self, menu):
        names = []
        current = menu
        while current and current.exists():
            if current.name:
                names.append(str(current.name))
            current = current.parent_id
        return " / ".join(reversed(names))

    @api.model
    def _act_window_from_menu(self, menu):
        if not menu or not menu.exists() or not menu.action:
            return False
        action = menu.action
        if action._name == "ir.actions.act_window":
            return action
        try:
            model, record_id = str(action).split(",", 1)
            if model == "ir.actions.act_window":
                return self.env[model].sudo().browse(int(record_id))
        except Exception:
            return False
        return False

    @api.model
    def _action_context(self, action):
        try:
            context = safe_eval(action.context or "{}")
        except Exception:
            context = {}
        return context if isinstance(context, dict) else {}

    @api.model
    def _upsert_formal_handling_form_contract(self, item):
        action = item["action"]
        model_name = str(item["model"])
        fields_map = self.env[model_name].fields_get()
        category_code = str(item.get("category_code") or "").strip()
        field_rows, layout_children = self._formal_policy_flat_fields_for_category(category_code, fields_map)
        source = "sc.business.category.form_policy_json" if layout_children else "ir.ui.view.combined_form"
        if not layout_children:
            field_rows, layout_children = self._native_action_form_flat_fields(action, model_name, fields_map)
        if not layout_children:
            return False
        payload = {
            "view_orchestration": {
                "views": {
                    "form": {
                        "title": item.get("title") or action.name or model_name,
                        "fields": field_rows,
                        "layout": [
                            {
                                "type": "sheet",
                                "name": "sc_custom_user_form_sheet",
                                "children": [
                                    {
                                        "type": "group",
                                        "name": "sc_custom_user_flat_fields",
                                        "columns": 3,
                                        "children": layout_children,
                                    }
                                ],
                            }
                        ],
                    }
                },
                "context": {
                    "source": USER_FORM_PREFERENCE_SOURCE,
                    "scope": "user_confirmed_formal_handling",
                    "field_order_source": source,
                    "menu_xmlid": item.get("menu_xmlid"),
                    "business_category_code": category_code,
                },
            }
        }
        return self._upsert_form_contract(
            name="view_orchestration:%s:form:action:%s:view:0:custom_user_flat" % (model_name, int(action.id)),
            model_name=model_name,
            action=action,
            view=False,
            priority=600,
            payload=payload,
        )

    @api.model
    def _formal_policy_flat_fields_for_category(self, category_code, fields_map):
        category_code = str(category_code or "").strip()
        if not category_code:
            return [], []
        category = self.env["sc.business.category"].sudo().search([("code", "=", category_code)], limit=1)
        if not category or not (category.form_policy_json or "").strip():
            return [], []
        try:
            form_policy = json.loads(category.form_policy_json or "{}")
        except Exception:
            return [], []
        if not isinstance(form_policy, dict):
            return [], []
        return self._formal_policy_flat_fields(form_policy, fields_map)

    @api.model
    def _formal_policy_flat_fields(self, form_policy, fields_map):
        labels = {}
        visible = {}
        for row in form_policy.get("fields") if isinstance(form_policy.get("fields"), list) else []:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or row.get("field") or "").strip()
            if not name:
                continue
            labels[name] = str(row.get("label") or row.get("string") or "").strip()
            if "visible" in row:
                visible[name] = bool(row.get("visible"))

        ordered = []
        for section in form_policy.get("sections") if isinstance(form_policy.get("sections"), list) else []:
            if not isinstance(section, dict):
                continue
            for name in section.get("fields") if isinstance(section.get("fields"), list) else []:
                name = str(name or "").strip()
                if name and name not in ordered:
                    ordered.append(name)
        if not ordered:
            policy_fields = form_policy.get("fields") if isinstance(form_policy.get("fields"), list) else []
            ordered = [
                str(row.get("name") or row.get("field") or "").strip()
                for row in policy_fields
                if isinstance(row, dict) and str(row.get("name") or row.get("field") or "").strip()
            ]

        field_rows = []
        layout_children = []
        for index, name in enumerate(ordered, start=1):
            descriptor = fields_map.get(name)
            if not descriptor or visible.get(name) is False or self._is_user_form_preference_excluded_field(name, descriptor):
                continue
            label = labels.get(name) or str(descriptor.get("string") or name)
            field_rows.append({
                "name": name,
                "label": label,
                "visible": True,
                "sequence": index * 10,
            })
            layout_children.append(self._field_layout_node(name, label, descriptor))
        return field_rows, layout_children

    @api.model
    def _native_action_form_flat_fields(self, action, model_name, fields_map):
        view_id = self._action_form_view_id(action)
        try:
            view_payload = self.env[model_name].sudo().get_view(view_id=view_id or None, view_type="form")
            arch = view_payload.get("arch") if isinstance(view_payload, dict) else ""
        except Exception:
            arch = ""
        if not arch:
            return [], []
        try:
            root = ET.fromstring(arch)
        except Exception:
            return [], []
        ordered = []
        for node in root.findall(".//field[@name]"):
            name = str(node.get("name") or "").strip()
            if not name or name in ordered or name not in fields_map:
                continue
            if self._is_user_form_preference_excluded_field(name, fields_map.get(name) or {}):
                continue
            if str(node.get("invisible") or "").strip() in {"1", "True", "true"}:
                continue
            ordered.append(name)

        field_rows = []
        layout_children = []
        for index, name in enumerate(ordered, start=1):
            descriptor = fields_map.get(name) or {}
            label = str(descriptor.get("string") or name)
            field_rows.append({
                "name": name,
                "label": label,
                "visible": True,
                "sequence": index * 10,
            })
            layout_children.append(self._field_layout_node(name, label, descriptor))
        return field_rows, layout_children

    @api.model
    def _is_user_form_preference_excluded_field(self, name, descriptor):
        field_name = str(name or "").strip()
        if not field_name:
            return True
        if field_name in USER_FORM_PREFERENCE_EXCLUDED_FIELDS:
            return True
        if any(field_name.endswith(suffix) for suffix in USER_FORM_PREFERENCE_EXCLUDED_FIELD_SUFFIXES):
            return True
        relation = str((descriptor or {}).get("relation") or (descriptor or {}).get("comodel_name") or "").strip()
        if relation.startswith("sc.legacy.") and relation.endswith(".map"):
            return True
        return False

    @api.model
    def _action_form_view_id(self, action):
        for row in action.view_ids:
            if row.view_id and row.view_id.type == "form":
                return int(row.view_id.id)
        if action.view_id and action.view_id.type == "form":
            return int(action.view_id.id)
        return 0

    @api.model
    def _upsert_form_contract(self, *, name, model_name, action, view, priority, payload):
        Contract = self.env["ui.business.config.contract"].with_context(active_test=False).sudo()
        rec = Contract.search([("name", "=", name), ("company_id", "=", self.env.company.id)], limit=1)
        payload = ensure_lowcode_contract_source_status(payload)
        vals = {
            "name": name,
            "model": model_name,
            "view_type": "form",
            "action_id": action.id,
            "view_id": view.id if view else False,
            "company_id": self.env.company.id,
            "priority": priority,
            "active": True,
            "contract_json": payload,
        }
        if rec:
            changed = (
                rec.contract_json != payload
                or rec.status != "published"
                or not rec.active
                or rec.action_id != action
                or int(rec.view_id.id or 0) != (int(view.id or 0) if view else 0)
                or rec.company_id != self.env.company
                or int(rec.priority or 0) != int(priority or 0)
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
            **({"required": True} if descriptor.get("required") else {}),
            "fieldInfo": {
                "name": name,
                "label": label,
                "type": descriptor.get("type") or descriptor.get("ttype") or "char",
                **({"required": True} if descriptor.get("required") else {}),
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
