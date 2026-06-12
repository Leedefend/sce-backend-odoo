# -*- coding: utf-8 -*-
import json
from pathlib import Path

from odoo import api, models


FORMAL_CONTRACT_PRODUCT_MENU_XMLIDS = {
    "smart_construction_core.menu_sc_contract_income",
    "smart_construction_core.menu_sc_project_income_contract",
    "smart_construction_core.menu_sc_income_contract_execution",
    "smart_construction_core.menu_sc_contract_event",
    "smart_construction_core.menu_sc_general_contract",
    "smart_construction_core.menu_sc_contract_expense",
    "smart_construction_core.menu_sc_expense_contract_execution",
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
FINANCE_HANDLING_ENTRY_MENU_XMLID = "smart_construction_core.menu_sc_finance_center"
FINANCE_HANDLING_ENTRY_SCENE_KEY = "finance.workspace"
FINANCE_HANDLING_ENTRY_ROUTE = "/s/finance.workspace"

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


def _text(value):
    return str(value or "").strip()


def _is_user_acceptance_menu_key(value):
    key = _text(value)
    return key in USER_ACCEPTANCE_PRODUCT_MENU_XMLIDS or any(token in key for token in USER_ACCEPTANCE_MENU_KEY_TOKENS)


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
    def _formal_user_confirmed_menu_groups(self, menu_groups):
        out = []
        for group in menu_groups or []:
            if not self._is_user_confirmed_formal_group(group):
                continue
            next_group = dict(group)
            next_group["menus"] = [
                self._hydrate_user_confirmed_formal_menu(menu)
                for menu in (group.get("menus") or [])
                if isinstance(menu, dict)
            ]
            out.append(next_group)
        return out

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
    def _hydrate_finance_handling_entry_menu(self):
        menu_record = self.env.ref(FINANCE_HANDLING_ENTRY_MENU_XMLID, raise_if_not_found=False)
        action = menu_record.action if menu_record else None
        action_id = int(action.id or 0) if action else 0
        res_model = _text(getattr(action, "res_model", "") if action else "")
        view_modes = [_text(item) for item in _text(getattr(action, "view_mode", "")).split(",") if _text(item)]
        return {
            "menu_key": "construction.finance.handling_entry",
            "label": "财务综合办理",
            "page_key": FINANCE_HANDLING_ENTRY_SCENE_KEY,
            "page_label": "财务综合办理",
            "route": FINANCE_HANDLING_ENTRY_ROUTE,
            "scene_key": FINANCE_HANDLING_ENTRY_SCENE_KEY,
            "product_key": "财务中心",
            "capability_key": "construction.scene.finance_workspace.handling_entry",
            "target_scene_key": FINANCE_HANDLING_ENTRY_SCENE_KEY,
            "visible_menu_path": "智慧施工管理平台 / 财务中心 / 财务综合办理",
            "control_granularity": "finance_handling_entry_catalog",
            "enabled": True,
            "release_state": "released",
            "access_level": "public",
            "control_object": "财务综合办理入口",
            "source_kind": "finance_handling_entry_catalog_release_overlay",
            "menu_id": int(menu_record.id) if menu_record else 0,
            "menu_xmlid": FINANCE_HANDLING_ENTRY_MENU_XMLID,
            "action_id": action_id,
            "action_model": _text(getattr(action, "_name", "")),
            "res_model": res_model,
            "view_modes": view_modes,
            "release_domain": "finance_handling_entry",
            "policy_note": "collapsed_finance_legacy_pages_into_handling_entry_catalog",
            "entry_target": {
                "type": "scene",
                "scene_key": FINANCE_HANDLING_ENTRY_SCENE_KEY,
                "route": FINANCE_HANDLING_ENTRY_ROUTE,
                "compatibility_refs": {
                    "menu_xmlid": FINANCE_HANDLING_ENTRY_MENU_XMLID,
                    **({"menu_id": int(menu_record.id)} if menu_record else {}),
                    **({"action_id": action_id} if action_id else {}),
                },
            },
        }

    @api.model
    def _collapse_finance_product_menu_group_to_handling_entry(self, menu_groups):
        out = []
        finance_seen = False
        for group in menu_groups or []:
            if not isinstance(group, dict):
                continue
            next_group = dict(group)
            if _text(next_group.get("group_label") or next_group.get("label")) == "财务中心":
                next_group.update(
                    {
                        "group_key": _text(next_group.get("group_key")) or "construction.财务中心",
                        "group_label": "财务中心",
                        "category": "user_visible_menu",
                        "menus": [self._hydrate_finance_handling_entry_menu()],
                        "policy_note": "finance_group_collapsed_to_scene_handling_entry",
                    }
                )
                finance_seen = True
            out.append(next_group)
        if not finance_seen:
            out.append(
                {
                    "group_key": "construction.财务中心",
                    "group_label": "财务中心",
                    "category": "user_visible_menu",
                    "menus": [self._hydrate_finance_handling_entry_menu()],
                    "policy_note": "finance_group_collapsed_to_scene_handling_entry",
                }
            )
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
        model = self.sudo()
        for product_key in ("construction.standard", "construction.preview"):
            item = baseline.get(product_key) or {}
            baseline_menu_groups = item.get("menu_groups") if isinstance(item.get("menu_groups"), list) else []
            menu_groups = self._formal_user_confirmed_menu_groups(baseline_menu_groups)
            menu_groups = self._append_finance_interfund_analysis_product_menus(menu_groups)
            menu_groups = self._collapse_finance_product_menu_group_to_handling_entry(menu_groups)
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
        menu_groups = self._collapse_finance_product_menu_group_to_handling_entry(menu_groups)

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
