# -*- coding: utf-8 -*-
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

USER_ACCEPTANCE_MENU_KEY_TOKENS = (
    "_acceptance",
    "user_acceptance",
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

        service = ProductPolicyCatalogSyncService(self.env)
        for product_key in ("construction.standard", "construction.preview"):
            policy = service.sync_policy(product_key=product_key, preserve_state=True, preserve_access_level=True)
            self._apply_formal_contract_product_menu_domain(policy)
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
