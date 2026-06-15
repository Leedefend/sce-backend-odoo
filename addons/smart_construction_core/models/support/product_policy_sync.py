# -*- coding: utf-8 -*-
import json
import importlib.util
from pathlib import Path

from odoo import api, models


FORMAL_CONTRACT_PRODUCT_MENU_XMLIDS = {
    "smart_construction_core.menu_sc_construction_contract",
    "smart_construction_core.menu_sc_contract_handling",
    "smart_construction_core.menu_sc_contract_income",
    "smart_construction_core.menu_sc_project_income_contract",
    "smart_construction_core.menu_sc_income_contract_execution",
    "smart_construction_core.menu_sc_contract_event",
    "smart_construction_core.menu_sc_general_contract",
    "smart_construction_core.menu_sc_contract_expense",
    "smart_construction_core.menu_sc_expense_contract_execution",
    "smart_construction_core.menu_sc_expense_contract_supplement",
}

FORMAL_SETTLEMENT_PRODUCT_MENU_XMLIDS = {
    "smart_construction_core.menu_sc_settlement_order",
    "smart_construction_core.menu_sc_settlement_adjustment",
    "smart_construction_core.menu_sc_income_contract_settlement",
    "smart_construction_core.menu_sc_expense_contract_settlement",
    "smart_construction_core.menu_sc_material_settlement",
    "smart_construction_core.menu_sc_labor_settlement",
    "smart_construction_core.menu_sc_equipment_settlement",
    "smart_construction_core.menu_sc_material_rental_settlement",
    "smart_construction_core.menu_sc_subcontract_settlement",
}

USER_ACCEPTANCE_PRODUCT_MENU_XMLIDS = {
    "smart_construction_core.menu_sc_customer_partner",
    "smart_construction_core.menu_sc_supplier_partner",
}

FINANCE_INTERFUND_ANALYSIS_PRODUCT_MENU_XMLIDS = (
    "smart_construction_core.menu_sc_finance_project_capital_position",
    "smart_construction_core.menu_sc_finance_counterparty_position_summary",
    "smart_construction_core.menu_sc_finance_project_counterparty_position",
    "smart_construction_core.menu_sc_company_contractor_responsibility_summary",
    "smart_construction_core.menu_sc_company_contractor_responsibility_fact",
)
FINANCE_CASH_NONCASH_PRODUCT_MENU_OVERRIDES = {
    "smart_construction_core.menu_sc_deduction_bill": {
        "label": "扣款登记",
        "visible_menu_path": "智慧施工管理平台 / 财务中心 / 非现金业务管理 / 扣款登记",
        "product_domain": "finance_noncash",
        "product_domain_label": "非现金业务管理",
        "entry_intent": "handling",
        "entry_intent_label": "办理",
        "fact_model": "sc.expense.claim",
        "disposition_policy": "keep_list_form",
        "integration_target": "sc.expense.claim 扣款登记",
        "default_business_category_code": "finance.deduction.bill",
        "allowed_business_category_codes": ["finance.deduction.bill"],
        "required_relationships": ["project_id", "partner_id"],
        "entry_target_policy": "keep_list_form",
        "locked_data_policy": "read_only_source_facts_no_rewrite",
        "productization_source": "finance_cash_noncash_menu_split",
        "business_entry_contract_version": "business_entry_disposition.v1",
    },
    "smart_construction_core.menu_sc_reimbursement_request": {
        "visible_menu_path": "智慧施工管理平台 / 财务中心 / 费用/保证金现金办理 / 报销申请",
        "product_domain": "finance_cash",
        "product_domain_label": "费用/保证金现金办理",
    },
    "smart_construction_core.menu_sc_project_expense_claim": {
        "visible_menu_path": "智慧施工管理平台 / 财务中心 / 费用/保证金现金办理 / 项目费用报销单",
        "product_domain": "finance_cash",
        "product_domain_label": "费用/保证金现金办理",
    },
    "smart_construction_core.menu_sc_deduction_paid": {
        "visible_menu_path": "智慧施工管理平台 / 财务中心 / 费用/保证金现金办理 / 扣款实缴登记",
        "product_domain": "finance_cash",
        "product_domain_label": "费用/保证金现金办理",
        "disposition_policy": "keep_list_form",
        "integration_target": "sc.expense.claim 扣款实缴登记",
        "allowed_business_category_codes": ["finance.deduction.paid"],
        "entry_target_policy": "keep_list_form",
        "productization_source": "finance_cash_noncash_menu_split",
    },
    "smart_construction_core.menu_sc_deduction_paid_refund": {
        "visible_menu_path": "智慧施工管理平台 / 财务中心 / 费用/保证金现金办理 / 扣款实缴退回",
        "product_domain": "finance_cash",
        "product_domain_label": "费用/保证金现金办理",
        "disposition_policy": "keep_list_form",
        "integration_target": "sc.expense.claim 扣款实缴退回",
        "allowed_business_category_codes": ["finance.deduction.refund"],
        "entry_target_policy": "keep_list_form",
        "productization_source": "finance_cash_noncash_menu_split",
    },
}
FINANCE_CASH_EXPENSE_DEPOSIT_TARGET = "sc.expense.claim 费用/保证金申请"
FINANCE_CASH_EXPENSE_DEPOSIT_CATEGORY_CODES = {
    "finance.expense.reimbursement",
    "finance.expense.project",
    "finance.deposit.bid.pay",
    "finance.deposit.bid.return",
    "finance.deposit.contract.pay",
    "finance.deposit.contract.return",
}
FINANCE_DEDUCTION_CATEGORY_CODES = {
    "finance.deduction.bill",
    "finance.deduction.paid",
    "finance.deduction.refund",
}
USER_ACCEPTANCE_MENU_KEY_TOKENS = (
    "_acceptance",
    "user_acceptance",
)

INTERNAL_CONFIG_ONLY_GROUP_XMLIDS = {
    "base.group_no_one",
    "smart_core.group_smart_core_admin",
    "smart_construction_core.group_sc_cap_config_admin",
}

USER_CONFIRMED_POLICY_LOCK_NOTE = "user_confirmed_formal_menu_policy_62_locked"
USER_CONFIRMED_POLICY_BASELINE_PATHS = (
    "/mnt/scripts/verify/baselines/user_confirmed_formal_menu_policy_62.json",
    "scripts/verify/baselines/user_confirmed_formal_menu_policy_62.json",
)
USER_CONFIRMED_ENTRY_MATRIX_SCRIPT_PATHS = (
    "/mnt/scripts/verify/user_confirmed_62_business_entry_integration_matrix.py",
    "scripts/verify/user_confirmed_62_business_entry_integration_matrix.py",
)
USER_CONFIRMED_FORMAL_HIDDEN_GROUP_LABELS = {"用户核对菜单", "用户验收", "用户数据验收"}
USER_CONFIRMED_FORMAL_VISIBLE_PARENT_XMLIDS = {
    "smart_construction_core.menu_sc_material_management_group",
    "smart_construction_core.menu_sc_labor_management_group",
    "smart_construction_core.menu_sc_equipment_management_group",
    "smart_construction_core.menu_sc_subcontract_management_group",
}
USER_CONFIRMED_FORMAL_HIDE_PATH_TOKENS = (
    "/用户验收",
    "/用户数据验收",
    "/用户核对菜单",
)
USER_CONFIRMED_FORMAL_HIDE_MENU_XMLIDS = (
    "smart_construction_core.menu_sc_legacy_engineering_progress_receipt",
    "smart_construction_core.menu_scbsly_direct_project_acceptance_root",
    "smart_construction_core.menu_scbsly_acceptance_engineering_progress_receipt",
)
MERGE_BY_CATEGORY_INTEGRATION_ACTION_XMLIDS_BY_MODEL = {
    "construction.contract": "smart_construction_core.action_construction_contract_handling",
    "construction.contract.income": "smart_construction_core.action_construction_contract_income",
    "construction.contract.expense": "smart_construction_core.action_construction_contract_expense",
    "sc.settlement.order": "smart_construction_core.action_sc_settlement_order",
    "sc.labor.usage": "smart_construction_core.action_sc_labor_usage",
    "sc.material.outbound": "smart_construction_core.action_sc_material_outbound",
    "sc.receipt.income": "smart_construction_core.action_sc_receipt_income",
    "payment.request": "smart_construction_core.action_payment_request",
    "sc.payment.execution": "smart_construction_core.action_sc_payment_execution",
    "sc.expense.claim": "smart_construction_core.action_sc_expense_claim",
    "sc.financing.loan": "smart_construction_core.action_sc_financing_loan",
    "sc.invoice.registration": "smart_construction_core.action_sc_invoice_registration",
    "sc.self.funding.registration": "smart_construction_core.action_sc_self_funding_registration",
}
SELF_FUNDING_REFUND_MENU_XMLID = "smart_construction_core.menu_sc_self_funding_advance_refund"
SELF_FUNDING_REFUND_CODE = "finance.self_funding.refund"

CONTRACT_HANDLING_CATEGORY_CODES = (
    "contract.income",
    "contract.income.supplement",
    "contract.expense",
    "contract.expense.supplement",
)


def _text(value):
    return str(value or "").strip()


def _is_user_acceptance_menu_key(value):
    key = _text(value)
    return key in USER_ACCEPTANCE_PRODUCT_MENU_XMLIDS or any(token in key for token in USER_ACCEPTANCE_MENU_KEY_TOKENS)


def _integration_model_from_target(target):
    first_token = _text(target).split(" ", 1)[0].split("/", 1)[0]
    if first_token in MERGE_BY_CATEGORY_INTEGRATION_ACTION_XMLIDS_BY_MODEL:
        return first_token
    return ""


class ScProductPolicy(models.Model):
    _inherit = "sc.product.policy"

    @api.model
    def sync_construction_menu_product_policies(self):
        from odoo.addons.smart_core.delivery.product_policy_catalog_sync_service import ProductPolicyCatalogSyncService

        self._ensure_formal_product_navigation_runtime_params()
        if self._sync_user_confirmed_locked_construction_product_policies():
            return True

        service = ProductPolicyCatalogSyncService(self.env)
        for product_key in ("construction.standard", "construction.preview"):
            policy = service.sync_policy(product_key=product_key, preserve_state=True, preserve_access_level=True)
            self._release_all_construction_product_menus(policy)
        return True

    @api.model
    def _ensure_formal_product_navigation_runtime_params(self):
        Param = self.env["ir.config_parameter"].sudo()
        Param.set_param("smart_core.nav.user_data_acceptance_only", "0")
        Param.set_param("smart_core.nav.user_menu_config.enabled", "0")
        return True

    @api.model
    def _load_user_confirmed_policy_baseline(self):
        candidates = []
        for raw_path in USER_CONFIRMED_POLICY_BASELINE_PATHS:
            path = Path(raw_path)
            if not path.is_absolute():
                path = Path(__file__).resolve().parents[4] / path
            candidates.append(path)
        for path in candidates:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            products = payload.get("products") if isinstance(payload, dict) else payload
            if not isinstance(products, list):
                continue
            by_key = {
                _text(item.get("product_key")): item
                for item in products
                if isinstance(item, dict) and _text(item.get("product_key"))
            }
            if {"construction.standard", "construction.preview"}.issubset(set(by_key)):
                return by_key
        return {}

    @api.model
    def _load_user_confirmed_entry_matrix_index(self):
        candidates = []
        for raw_path in USER_CONFIRMED_ENTRY_MATRIX_SCRIPT_PATHS:
            path = Path(raw_path)
            if not path.is_absolute():
                path = Path(__file__).resolve().parents[4] / path
            candidates.append(path)
        for path in candidates:
            if not path.is_file():
                continue
            try:
                spec = importlib.util.spec_from_file_location("user_confirmed_business_entry_matrix_runtime", path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                payload = module._build_matrix()
            except Exception:
                continue
            rows = payload.get("rows") if isinstance(payload, dict) else []
            index = {}
            for row in rows:
                if not isinstance(row, dict):
                    continue
                menu_xmlid = _text(row.get("menu_xmlid"))
                if menu_xmlid:
                    index[menu_xmlid] = row
            if index:
                return index
        return {}

    @api.model
    def _annotate_user_confirmed_business_entry(self, row, matrix_index):
        if not isinstance(row, dict):
            return row
        menu_xmlid = _text(row.get("menu_xmlid") or row.get("page_key") or row.get("menu_key"))
        matrix = matrix_index.get(menu_xmlid) if isinstance(matrix_index, dict) else None
        if not isinstance(matrix, dict):
            self._normalize_self_funding_refund_business_entry(row)
            return row
        next_row = dict(row)
        category_code = _text(matrix.get("default_business_category_code"))
        product_domain = _text(matrix.get("product_domain"))
        entry_intent = _text(matrix.get("entry_intent"))
        disposition_policy = _text(matrix.get("disposition_policy"))
        integration_target = _text(matrix.get("integration_target"))
        next_row.update(
            {
                "product_domain": product_domain,
                "product_domain_label": _text(matrix.get("product_domain_label")),
                "entry_intent": entry_intent,
                "entry_intent_label": _text(matrix.get("entry_intent_label")),
                "fact_model": _text(matrix.get("fact_model") or matrix.get("model")),
                "disposition_policy": disposition_policy,
                "integration_target": integration_target,
                "default_business_category_code": category_code,
                "allowed_business_category_codes": matrix.get("allowed_business_category_codes") if isinstance(matrix.get("allowed_business_category_codes"), list) else [],
                "required_relationships": matrix.get("required_relationships") if isinstance(matrix.get("required_relationships"), list) else [],
                "locked_data_policy": _text(matrix.get("locked_data_policy")) or "read_only_source_facts_no_rewrite",
                "productization_source": "user_confirmed_62_business_entry_integration_matrix",
                "business_entry_contract_version": "business_entry_disposition.v1",
            }
        )
        if category_code:
            next_row.setdefault("context_defaults", {})
            if isinstance(next_row["context_defaults"], dict):
                next_row["context_defaults"].setdefault("default_business_category_code", category_code)
        if disposition_policy == "merge_by_category":
            next_row["entry_target_policy"] = "merge_to_list_form_by_business_category"
            self._annotate_merge_by_category_integration_target(next_row)
        elif entry_intent in {"query", "analysis", "config", "master_data", "source_fact"}:
            next_row["entry_target_policy"] = "keep_separate_%s" % entry_intent
        else:
            next_row["entry_target_policy"] = "keep_list_form"
        self._normalize_contract_handling_business_entry(next_row)
        self._normalize_self_funding_refund_business_entry(next_row)
        return next_row

    @api.model
    def _normalize_self_funding_refund_business_entry(self, row):
        if not isinstance(row, dict):
            return row
        menu_xmlid = _text(row.get("menu_xmlid") or row.get("page_key") or row.get("menu_key"))
        if menu_xmlid != SELF_FUNDING_REFUND_MENU_XMLID:
            return row
        row.update(
            {
                "label": "自筹退回办理",
                "page_label": "自筹退回办理",
                "product_domain": "finance",
                "product_domain_label": "资金财务域",
                "entry_intent": "handling",
                "entry_intent_label": "办理",
                "fact_model": "sc.legacy.self.funding.fact",
                "disposition_policy": "merge_by_category",
                "integration_target": "sc.self.funding.registration 自筹退回办理",
                "default_business_category_code": SELF_FUNDING_REFUND_CODE,
                "allowed_business_category_codes": [SELF_FUNDING_REFUND_CODE],
                "required_relationships": ["project_id", "partner_id"],
                "entry_target_policy": "merge_to_list_form_by_business_category",
                "locked_data_policy": "read_only_source_facts_no_rewrite",
                "productization_source": "self_funding_refund_formal_entry",
                "policy_note": "self_funding_refund_uses_formal_registration_caliber",
                "business_entry_contract_version": "business_entry_disposition.v1",
                "visible_menu_path": "智慧施工管理平台 / 财务中心 / 自筹退回办理",
            }
        )
        context_defaults = row.setdefault("context_defaults", {})
        if isinstance(context_defaults, dict):
            context_defaults.clear()
            context_defaults["default_funding_type"] = "refund"
            context_defaults["default_business_category_code"] = SELF_FUNDING_REFUND_CODE
            context_defaults["allowed_business_category_codes"] = [SELF_FUNDING_REFUND_CODE]
        self._annotate_merge_by_category_integration_target(row)
        action = self.env.ref("smart_construction_core.action_sc_self_funding_registration_refund", raise_if_not_found=False)
        if action and _text(getattr(action, "res_model", "")) == "sc.self.funding.registration":
            action_id = int(action.id or 0)
            view_modes = [_text(item) for item in _text(getattr(action, "view_mode", "")).split(",") if _text(item)]
            row["integration_action_xmlid"] = "smart_construction_core.action_sc_self_funding_registration_refund"
            row["integration_action_id"] = action_id
            row["integration_view_modes"] = view_modes
            row["integration_entry_target"] = {
                "type": "compatibility",
                "route": "/a/%s" % action_id,
                "compatibility_refs": {
                    "action_id": action_id,
                    "model": "sc.self.funding.registration",
                    "view_modes": view_modes,
                    "delivery_mode": "merge_by_category_integration",
                },
            }
        return row

    @api.model
    def _normalize_contract_handling_business_entry(self, row):
        if not isinstance(row, dict):
            return row
        category_code = _text(row.get("default_business_category_code"))
        allowed_codes = row.get("allowed_business_category_codes") if isinstance(row.get("allowed_business_category_codes"), list) else []
        menu_xmlid = _text(row.get("menu_xmlid") or row.get("page_key") or row.get("menu_key"))
        is_contract_category = category_code in CONTRACT_HANDLING_CATEGORY_CODES or any(
            _text(code) in CONTRACT_HANDLING_CATEGORY_CODES for code in allowed_codes
        )
        is_contract_execution_menu = menu_xmlid in {
            "smart_construction_core.menu_sc_construction_contract",
            "smart_construction_core.menu_sc_contract_handling",
            "smart_construction_core.menu_sc_income_contract_execution",
            "smart_construction_core.menu_sc_expense_contract_execution",
            "smart_construction_core.menu_sc_expense_contract_supplement",
        }
        if not (is_contract_category or is_contract_execution_menu):
            return row
        if not category_code:
            category_code = "contract.income"
        row.update(
            {
                "label": "合同办理",
                "page_label": "合同办理",
                "product_domain": "contract",
                "product_domain_label": "合同结算域",
                "entry_intent": "handling",
                "entry_intent_label": "办理",
                "fact_model": "construction.contract",
                "res_model": "construction.contract",
                "model": "construction.contract",
                "disposition_policy": "merge_by_category",
                "integration_target": "construction.contract 合同办理",
                "default_business_category_code": category_code,
                "allowed_business_category_codes": [category_code],
                "required_relationships": ["project_id", "partner_id"],
                "entry_target_policy": "merge_to_list_form_by_business_category",
                "locked_data_policy": "read_only_source_facts_no_rewrite",
                "productization_source": "contract_handling_product_consolidation",
                "business_entry_contract_version": "business_entry_disposition.v1",
            }
        )
        context_defaults = row.setdefault("context_defaults", {})
        if isinstance(context_defaults, dict):
            context_defaults["default_business_category_code"] = category_code
            if category_code in {"contract.income", "contract.income.supplement"}:
                context_defaults["default_type"] = "out"
            elif category_code in {"contract.expense", "contract.expense.supplement"}:
                context_defaults["default_type"] = "in"
        self._annotate_merge_by_category_integration_target(row)
        return row

    @api.model
    def _annotate_merge_by_category_integration_target(self, row):
        source_model = _text(row.get("fact_model") or row.get("res_model"))
        integration_model = _integration_model_from_target(row.get("integration_target")) or source_model
        action_xmlid = MERGE_BY_CATEGORY_INTEGRATION_ACTION_XMLIDS_BY_MODEL.get(integration_model)
        if not action_xmlid:
            return row
        action = self.env.ref(action_xmlid, raise_if_not_found=False)
        if not action or _text(getattr(action, "res_model", "")) != integration_model:
            return row
        action_id = int(action.id or 0)
        if action_id <= 0:
            return row
        view_modes = [_text(item) for item in _text(getattr(action, "view_mode", "")).split(",") if _text(item)]
        row["integration_model"] = integration_model
        row["integration_action_xmlid"] = action_xmlid
        row["integration_action_id"] = action_id
        row["integration_view_modes"] = view_modes
        row["integration_entry_target"] = {
            "type": "compatibility",
            "route": "/a/%s" % action_id,
            "compatibility_refs": {
                "action_id": action_id,
                "model": integration_model,
                "view_modes": view_modes,
                "delivery_mode": "merge_by_category_integration",
            },
        }
        return row

    @api.model
    def _capabilities_from_user_confirmed_menu_groups(self, menu_groups):
        capabilities = []
        seen = set()
        for group in menu_groups or []:
            if not isinstance(group, dict):
                continue
            group_key = _text(group.get("group_key")) or _text(group.get("group_label")) or "construction.locked"
            group_label = _text(group.get("group_label")) or group_key
            for menu in group.get("menus") or []:
                if not isinstance(menu, dict):
                    continue
                page_key = _text(menu.get("page_key") or menu.get("menu_xmlid") or menu.get("menu_key"))
                if not page_key or page_key in seen:
                    continue
                seen.add(page_key)
                capabilities.append(
                    {
                        "capability_key": _text(menu.get("capability_key")) or "construction.menu.%s" % page_key.replace(".", "_"),
                        "label": _text(menu.get("label") or menu.get("page_label")) or page_key,
                        "group_key": group_key,
                        "group_label": group_label,
                        "target_scene_key": _text(menu.get("target_scene_key")),
                        "target_page_key": page_key,
                        "product_key": _text(menu.get("product_key")),
                        "delivery_level": "exclusive",
                        "entry_kind": "user_visible_menu_page",
                        "visible_menu_path": _text(menu.get("visible_menu_path")),
                        "enabled": bool(menu.get("enabled", True)),
                        "release_state": _text(menu.get("release_state")) or "released",
                        "access_level": _text(menu.get("access_level")) or "public",
                        "control_object": "用户已确认正式菜单页面",
                        "source_kind": "user_confirmed_menu_policy_baseline",
                        "menu_xmlid": _text(menu.get("menu_xmlid") or page_key),
                        "action_id": int(menu.get("action_id") or 0),
                        "res_model": _text(menu.get("res_model")),
                        "product_domain": _text(menu.get("product_domain")),
                        "entry_intent": _text(menu.get("entry_intent")),
                        "disposition_policy": _text(menu.get("disposition_policy")),
                        "integration_target": _text(menu.get("integration_target")),
                        "default_business_category_code": _text(menu.get("default_business_category_code")),
                        "allowed_business_category_codes": menu.get("allowed_business_category_codes") if isinstance(menu.get("allowed_business_category_codes"), list) else [],
                        "entry_target_policy": _text(menu.get("entry_target_policy")),
                    }
                )
        return capabilities

    @api.model
    def _is_user_confirmed_formal_group(self, group):
        if not isinstance(group, dict):
            return False
        label = _text(group.get("group_label") or group.get("label") or group.get("title"))
        key = _text(group.get("group_key") or group.get("key"))
        return label not in USER_CONFIRMED_FORMAL_HIDDEN_GROUP_LABELS and "acceptance" not in key.lower()

    @api.model
    def _hydrate_user_confirmed_formal_menu(self, menu):
        row = dict(menu or {})
        menu_xmlid = _text(row.get("menu_xmlid") or row.get("page_key") or row.get("menu_key"))
        menu_record = self.env.ref(menu_xmlid, raise_if_not_found=False) if menu_xmlid else False
        if not menu_record:
            return row
        action = menu_record.action
        action_id = int(action.id or 0) if action else 0
        locked_res_model = _text(row.get("res_model"))
        res_model = locked_res_model or _text(getattr(action, "res_model", "") if action else "")
        view_modes = []
        if action and _text(getattr(action, "view_mode", "")):
            view_modes = [_text(item) for item in action.view_mode.split(",") if _text(item)]
        row.update(
            {
                "menu_id": int(menu_record.id),
                "menu_xmlid": menu_xmlid,
                "menu_key": menu_xmlid,
                "page_key": menu_xmlid,
                "action_id": action_id or int(row.get("action_id") or 0),
                "res_model": res_model,
                "route": "/a/%s?menu_id=%s" % (action_id, menu_record.id) if action_id else _text(row.get("route")),
                "view_modes": view_modes or row.get("view_modes") or [],
                "enabled": True,
                "release_state": "released",
                "access_level": "public",
                "policy_note": "released_as_user_confirmed_formal_product_menu",
            }
        )
        return row

    @api.model
    def _formal_user_confirmed_menu_groups(self, menu_groups, matrix_index=None):
        out = []
        for group in menu_groups or []:
            if not self._is_user_confirmed_formal_group(group):
                continue
            next_group = dict(group)
            next_group["menus"] = [
                self._annotate_user_confirmed_business_entry(
                    self._hydrate_user_confirmed_formal_menu(menu),
                    matrix_index or {},
                )
                for menu in (group.get("menus") or [])
                if isinstance(menu, dict)
            ]
            self._consolidate_contract_handling_menu_entries(next_group)
            out.append(next_group)
        return out

    @api.model
    def _consolidate_contract_handling_menu_entries(self, group):
        if not isinstance(group, dict):
            return group
        if _text(group.get("group_label") or group.get("label")) != "合同中心":
            return group

        old_handling_menu_xmlids = {
            "smart_construction_core.menu_sc_expense_contract_supplement",
            "smart_construction_core.menu_sc_income_contract_execution",
            "smart_construction_core.menu_sc_expense_contract_execution",
        }
        menus = [dict(menu) for menu in (group.get("menus") or []) if isinstance(menu, dict)]
        kept = []
        insertion_index = None
        for idx, menu in enumerate(menus):
            menu_xmlid = _text(menu.get("menu_xmlid") or menu.get("page_key") or menu.get("menu_key"))
            category_code = _text(menu.get("default_business_category_code"))
            if menu_xmlid in old_handling_menu_xmlids or category_code in CONTRACT_HANDLING_CATEGORY_CODES:
                if insertion_index is None:
                    insertion_index = len(kept)
                continue
            kept.append(menu)

        if insertion_index is None:
            group["menus"] = kept
            return group

        handling = self._hydrate_user_confirmed_formal_menu(
            {
                "label": "合同办理",
                "page_label": "合同办理",
                "menu_key": "smart_construction_core.menu_sc_construction_contract",
                "menu_xmlid": "smart_construction_core.menu_sc_construction_contract",
                "page_key": "smart_construction_core.menu_sc_construction_contract",
                "capability_key": "construction.menu.smart_construction_core_menu_sc_construction_contract",
                "product_key": "合同中心",
                "scene_key": "",
                "target_scene_key": "",
                "visible_menu_path": "智慧施工管理平台 / 合同中心 / 合同办理",
                "control_granularity": "user_visible_menu_page",
                "control_object": "用户已确认正式菜单页面",
                "source_kind": "contract_handling_product_consolidation",
                "res_model": "construction.contract",
            }
        )
        handling.update(
            {
                "label": "合同办理",
                "page_label": "合同办理",
                "res_model": "construction.contract",
                "fact_model": "construction.contract",
                "model": "construction.contract",
                "product_domain": "contract",
                "product_domain_label": "合同结算域",
                "entry_intent": "handling",
                "entry_intent_label": "办理",
                "disposition_policy": "merge_by_category",
                "integration_target": "construction.contract 合同办理",
                "default_business_category_code": "contract.income",
                "allowed_business_category_codes": list(CONTRACT_HANDLING_CATEGORY_CODES),
                "required_relationships": ["project_id", "partner_id"],
                "entry_target_policy": "merge_to_list_form_by_business_category",
                "locked_data_policy": "read_only_source_facts_no_rewrite",
                "productization_source": "contract_handling_product_consolidation",
                "business_entry_contract_version": "business_entry_disposition.v1",
                "context_defaults": {
                    "default_business_category_code": "contract.income",
                    "default_type": "out",
                    "allowed_business_category_codes": list(CONTRACT_HANDLING_CATEGORY_CODES),
                },
            }
        )
        self._annotate_merge_by_category_integration_target(handling)
        kept.insert(insertion_index, handling)
        group["menus"] = kept
        return group

    @api.model
    def _hydrate_finance_interfund_analysis_menu(self, menu_xmlid):
        menu_record = self.env.ref(menu_xmlid, raise_if_not_found=False)
        if not menu_record:
            return None
        action = menu_record.action
        action_id = int(action.id or 0) if action else 0
        res_model = _text(getattr(action, "res_model", "") if action else "")
        if not action_id or not res_model:
            return None
        view_modes = [_text(item) for item in _text(getattr(action, "view_mode", "")).split(",") if _text(item)]
        return {
            "menu_key": menu_xmlid,
            "label": _text(menu_record.name),
            "page_key": menu_xmlid,
            "page_label": _text(menu_record.name),
            "route": "/a/%s?menu_id=%s" % (action_id, menu_record.id),
            "scene_key": "",
            "product_key": "财务中心",
            "capability_key": "construction.menu.%s" % menu_xmlid.replace(".", "_"),
            "target_scene_key": "",
            "visible_menu_path": "智慧施工管理平台 / 财务中心 / 资金往来分析 / %s" % _text(menu_record.name),
            "control_granularity": "finance_interfund_analysis_page",
            "enabled": True,
            "release_state": "released",
            "access_level": "public",
            "control_object": "资金往来统一分析入口",
            "source_kind": "finance_interfund_product_release_overlay",
            "menu_id": int(menu_record.id),
            "menu_xmlid": menu_xmlid,
            "action_id": action_id,
            "action_model": _text(getattr(action, "_name", "")),
            "res_model": res_model,
            "view_modes": view_modes,
            "release_domain": "finance_interfund_analysis",
            "policy_note": "released_as_finance_interfund_analysis_product_menu",
            "product_domain": "finance",
            "product_domain_label": "资金财务域",
            "entry_intent": "analysis",
            "entry_intent_label": "分析",
            "fact_model": res_model,
            "disposition_policy": "keep_analysis",
            "integration_target": "资金往来分析",
            "default_business_category_code": "",
            "required_relationships": ["project_id", "partner_id", "fund_account_id"],
            "locked_data_policy": "read_only_source_facts_no_rewrite",
            "productization_source": "finance_interfund_analysis_product_overlay",
            "business_entry_contract_version": "business_entry_disposition.v1",
            "entry_target_policy": "keep_separate_analysis",
        }

    @api.model
    def _append_finance_interfund_analysis_product_menus(self, menu_groups):
        out = [dict(group) for group in (menu_groups or []) if isinstance(group, dict)]
        finance_group = None
        for group in out:
            if _text(group.get("group_label") or group.get("label")) == "财务中心":
                finance_group = group
                break
        if finance_group is None:
            finance_group = {
                "group_key": "construction.财务中心",
                "group_label": "财务中心",
                "category": "user_visible_menu",
                "menus": [],
            }
            out.append(finance_group)
        menus = [dict(menu) for menu in (finance_group.get("menus") or []) if isinstance(menu, dict)]
        existing = {
            _text(menu.get("menu_xmlid") or menu.get("page_key") or menu.get("menu_key"))
            for menu in menus
        }
        for menu_xmlid in FINANCE_INTERFUND_ANALYSIS_PRODUCT_MENU_XMLIDS:
            if menu_xmlid in existing:
                continue
            row = self._hydrate_finance_interfund_analysis_menu(menu_xmlid)
            if row:
                menus.append(row)
                existing.add(menu_xmlid)
        finance_group["menus"] = menus
        return out

    @api.model
    def _apply_finance_cash_noncash_product_menu_overrides(self, menu_groups):
        out = []
        for group in menu_groups or []:
            if not isinstance(group, dict):
                continue
            next_group = dict(group)
            menus = []
            for menu in group.get("menus") or []:
                if not isinstance(menu, dict):
                    continue
                next_menu = dict(menu)
                menu_xmlid = _text(
                    next_menu.get("menu_xmlid")
                    or next_menu.get("page_key")
                    or next_menu.get("menu_key")
                )
                override = FINANCE_CASH_NONCASH_PRODUCT_MENU_OVERRIDES.get(menu_xmlid)
                if override:
                    next_menu.update(override)
                    label = _text(override.get("label"))
                    if label:
                        next_menu["page_label"] = label
                    next_menu["policy_note"] = "finance_cash_noncash_menu_split_released"
                default_code = _text(next_menu.get("default_business_category_code"))
                allowed_codes = next_menu.get("allowed_business_category_codes")
                if isinstance(allowed_codes, list):
                    if default_code in FINANCE_DEDUCTION_CATEGORY_CODES:
                        next_menu["allowed_business_category_codes"] = [default_code]
                    else:
                        next_menu["allowed_business_category_codes"] = [
                            _text(code)
                            for code in allowed_codes
                            if _text(code) and _text(code) not in FINANCE_DEDUCTION_CATEGORY_CODES
                        ]
                next_allowed_codes = next_menu.get("allowed_business_category_codes")
                cash_codes = [
                    _text(code)
                    for code in (next_allowed_codes if isinstance(next_allowed_codes, list) else [default_code])
                    if _text(code) in FINANCE_CASH_EXPENSE_DEPOSIT_CATEGORY_CODES
                ]
                menu_xmlid = _text(next_menu.get("menu_xmlid") or next_menu.get("page_key") or next_menu.get("menu_key"))
                if (
                    cash_codes
                    and default_code not in FINANCE_DEDUCTION_CATEGORY_CODES
                    and menu_xmlid != SELF_FUNDING_REFUND_MENU_XMLID
                ):
                    label = _text(next_menu.get("label") or next_menu.get("page_label"))
                    if label:
                        next_menu["visible_menu_path"] = "智慧施工管理平台 / 财务中心 / 费用/保证金现金办理 / %s" % label
                    next_menu["product_domain"] = "finance_cash"
                    next_menu["product_domain_label"] = "费用/保证金现金办理"
                    next_menu["integration_target"] = FINANCE_CASH_EXPENSE_DEPOSIT_TARGET
                    next_menu["productization_source"] = "finance_cash_noncash_menu_split"
                    next_menu["policy_note"] = "finance_cash_expense_deposit_entry_retargeted"
                menus.append(next_menu)
            next_group["menus"] = menus
            out.append(next_group)
        return out

    @api.model
    def _sync_user_confirmed_formal_menu_overlay(self):
        Policy = self.env["ui.menu.config.policy"].sudo().with_context(active_test=False)
        Menu = self.env["ir.ui.menu"].sudo().with_context(active_test=False)

        def upsert(menu, visible, note):
            if not menu:
                return
            policy = Policy.search([("menu_id", "=", menu.id)], limit=1)
            values = {
                "menu_id": menu.id,
                "visible": bool(visible),
                "active": True,
                "note": note,
            }
            if policy:
                policy.write(values)
            else:
                Policy.create(values)

        for xmlid in USER_CONFIRMED_FORMAL_VISIBLE_PARENT_XMLIDS:
            upsert(self.env.ref(xmlid, raise_if_not_found=False), True, "user_confirmed_formal_parent_required_visible")

        for menu in Menu.search([]):
            complete_name = _text(menu.complete_name)
            if any(token in complete_name for token in USER_CONFIRMED_FORMAL_HIDE_PATH_TOKENS):
                upsert(menu, False, "user_confirmed_formal_release_hide_acceptance_surface")
        for xmlid in USER_CONFIRMED_FORMAL_HIDE_MENU_XMLIDS:
            upsert(self.env.ref(xmlid, raise_if_not_found=False), False, "user_confirmed_formal_release_hide_acceptance_surface")

    @api.model
    def _sync_user_confirmed_locked_construction_product_policies(self):
        baseline = self._load_user_confirmed_policy_baseline()
        if not baseline:
            return False
        matrix_index = self._load_user_confirmed_entry_matrix_index()
        model = self.sudo()
        for product_key in ("construction.standard", "construction.preview"):
            item = baseline.get(product_key) or {}
            baseline_menu_groups = item.get("menu_groups") if isinstance(item.get("menu_groups"), list) else []
            menu_groups = self._formal_user_confirmed_menu_groups(baseline_menu_groups, matrix_index=matrix_index)
            menu_groups = self._append_finance_interfund_analysis_product_menus(menu_groups)
            menu_groups = self._apply_finance_cash_noncash_product_menu_overrides(menu_groups)
            capabilities = self._capabilities_from_user_confirmed_menu_groups(menu_groups)
            values = {
                "active": bool(item.get("active", True)),
                "product_key": product_key,
                "base_product_key": "construction",
                "edition_key": product_key.split(".", 1)[1],
                "state": _text(item.get("state")) or ("preview" if product_key.endswith(".preview") else "stable"),
                "access_level": "public",
                "allowed_role_codes": [],
                "label": "施工管理预览版" if product_key.endswith(".preview") else "施工管理标准版",
                "version": "v1",
                "scene_version_bindings": {},
                "menu_groups": menu_groups,
                "scenes": [],
                "capabilities": capabilities,
                "note": USER_CONFIRMED_POLICY_LOCK_NOTE,
            }
            rec = model.search([("product_key", "=", product_key)], limit=1)
            if rec:
                rec.write(values)
            else:
                model.create(values)
        self._sync_user_confirmed_formal_menu_overlay()
        return True

    @api.model
    def _release_all_construction_product_menus(self, policy):
        if not policy:
            return False

        def _menu_key(row):
            return _text(row.get("menu_xmlid") or row.get("page_key") or row.get("menu_key"))

        def _menu_group_xmlids(row):
            key = _menu_key(row)
            menu = self.env.ref(key, raise_if_not_found=False) if key else False
            if not menu:
                return set()
            return {_text(xmlid) for xmlid in menu.groups_id.get_external_id().values() if _text(xmlid)}

        def _is_internal_config_only(row):
            group_xmlids = _menu_group_xmlids(row)
            return bool(group_xmlids) and group_xmlids.issubset(INTERNAL_CONFIG_ONLY_GROUP_XMLIDS)

        def _release_domain(row):
            key = _menu_key(row)
            if key in FORMAL_CONTRACT_PRODUCT_MENU_XMLIDS:
                return "contract"
            if key in FORMAL_SETTLEMENT_PRODUCT_MENU_XMLIDS:
                return "settlement"
            if _is_user_acceptance_menu_key(key):
                return "user_acceptance"
            group_key = _text(row.get("group_key"))
            if group_key.startswith("construction."):
                return group_key.split(".", 1)[1] or "construction"
            return "construction"

        def _apply_release_state(rows):
            out = []
            for row in rows or []:
                if not isinstance(row, dict):
                    continue
                next_row = dict(row)
                if _is_internal_config_only(next_row):
                    next_row.update(
                        {
                            "enabled": False,
                            "release_state": "hidden",
                            "access_level": "internal",
                            "release_domain": "internal_config",
                            "policy_note": "hidden_from_user_product_release_config_admin_only",
                        }
                    )
                else:
                    next_row.update(
                        {
                            "enabled": True,
                            "release_state": "released",
                            "access_level": "public",
                            "release_domain": _release_domain(next_row),
                            "policy_note": "released_as_construction_product_menu",
                        }
                    )
                out.append(next_row)
            return out

        menu_groups = []
        for group in policy.menu_groups or []:
            if not isinstance(group, dict):
                continue
            next_group = dict(group)
            next_group["menus"] = _apply_release_state(group.get("menus"))
            menu_groups.append(next_group)

        policy.write(
            {
                "menu_groups": menu_groups,
                "scenes": _apply_release_state(policy.scenes),
                "capabilities": _apply_release_state(policy.capabilities),
                "note": "all construction user-facing menu pages are released as product menus; config-admin-only internal pages remain hidden",
            }
        )
        return True

    @api.model
    def _apply_formal_contract_product_menu_domain(self, policy):
        if not policy:
            return False

        formal_domains = {
            xmlid: ("contract", "formal_contract_domain_user_acceptance_released")
            for xmlid in FORMAL_CONTRACT_PRODUCT_MENU_XMLIDS
        }
        formal_domains.update(
            {
                xmlid: ("settlement", "formal_settlement_domain_user_acceptance_released")
                for xmlid in FORMAL_SETTLEMENT_PRODUCT_MENU_XMLIDS
            }
        )

        def _menu_key(row):
            return _text(row.get("menu_xmlid") or row.get("page_key") or row.get("menu_key"))

        def _formal_domain(row_or_key):
            key = row_or_key if isinstance(row_or_key, str) else _menu_key(row_or_key)
            return formal_domains.get(key)

        def _is_user_acceptance(row):
            return _is_user_acceptance_menu_key(_menu_key(row))

        menu_groups = []
        for group in policy.menu_groups or []:
            if not isinstance(group, dict):
                continue
            next_group = dict(group)
            menus = []
            for menu in group.get("menus") or []:
                if not isinstance(menu, dict):
                    continue
                next_menu = dict(menu)
                formal_domain = _formal_domain(next_menu)
                if formal_domain:
                    release_domain, policy_note = formal_domain
                    next_menu.update(
                        {
                            "enabled": True,
                            "release_state": "released",
                            "access_level": "public",
                            "release_domain": release_domain,
                            "policy_note": policy_note,
                        }
                    )
                elif _is_user_acceptance(next_menu):
                    next_menu.update(
                        {
                            "enabled": True,
                            "release_state": "released",
                            "access_level": "public",
                            "release_domain": "user_acceptance",
                            "policy_note": "user_acceptance_surface_preserved_until_formal_domain_release",
                        }
                    )
                else:
                    next_menu.update(
                        {
                            "enabled": False,
                            "release_state": "hidden",
                            "release_domain": "pending_user_acceptance",
                            "policy_note": "hidden_until_domain_user_acceptance_release",
                        }
                    )
                menus.append(next_menu)
            next_group["menus"] = menus
            menu_groups.append(next_group)

        def _apply_release_state(rows):
            out = []
            for row in rows or []:
                if not isinstance(row, dict):
                    continue
                next_row = dict(row)
                page_key = _text(
                    next_row.get("menu_xmlid")
                    or next_row.get("target_page_key")
                    or next_row.get("page_key")
                    or next_row.get("menu_key")
                )
                formal_domain = _formal_domain(page_key)
                if formal_domain:
                    release_domain, _policy_note = formal_domain
                    next_row.update(
                        {
                            "enabled": True,
                            "release_state": "released",
                            "access_level": "public",
                            "release_domain": release_domain,
                        }
                    )
                elif _is_user_acceptance_menu_key(page_key):
                    next_row.update(
                        {
                            "enabled": True,
                            "release_state": "released",
                            "access_level": "public",
                            "release_domain": "user_acceptance",
                        }
                    )
                else:
                    next_row.update(
                        {
                            "enabled": False,
                            "release_state": "hidden",
                            "release_domain": "pending_user_acceptance",
                        }
                    )
                out.append(next_row)
            return out

        policy.write(
            {
                "menu_groups": menu_groups,
                "scenes": _apply_release_state(policy.scenes),
                "capabilities": _apply_release_state(policy.capabilities),
                "note": "formal product menus are released by domain; current released domains=contract,settlement; user acceptance surfaces remain visible",
            }
        )
        return True
