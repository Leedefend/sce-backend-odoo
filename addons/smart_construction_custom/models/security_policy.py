# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.addons.smart_core.security.platform_admin import (
    platform_admin_group_xmlids,
    platform_admin_groups,
)

ROLE_LOGIN_GROUPS = {
    "sc_role_project_read": [
        "smart_construction_custom.group_sc_role_project_read",
        "smart_construction_custom.group_sc_role_contract_read",
        "smart_construction_core.group_sc_cap_contract_read",
        "smart_construction_custom.group_sc_role_settlement_read",
        "smart_construction_core.group_sc_cap_settlement_read",
        "smart_construction_custom.group_sc_role_payment_read",
        "smart_construction_core.group_sc_cap_finance_read",
    ],
    "sc_role_project_user": [
        "smart_construction_custom.group_sc_role_project_user",
        "smart_construction_custom.group_sc_role_contract_user",
        "smart_construction_core.group_sc_cap_contract_user",
        "smart_construction_custom.group_sc_role_settlement_user",
        "smart_construction_core.group_sc_cap_settlement_user",
        "smart_construction_custom.group_sc_role_payment_user",
        "smart_construction_core.group_sc_cap_finance_user",
    ],
    "sc_role_project_manager": [
        "smart_construction_custom.group_sc_role_project_manager",
        "smart_construction_custom.group_sc_role_contract_manager",
        "smart_construction_core.group_sc_cap_contract_manager",
        "smart_construction_custom.group_sc_role_settlement_manager",
        "smart_construction_core.group_sc_cap_settlement_manager",
        "smart_construction_custom.group_sc_role_payment_manager",
        "smart_construction_core.group_sc_cap_finance_manager",
    ],
    "sc_role_owner": [
        "smart_construction_custom.group_sc_role_owner",
    ],
    "sc_role_pm": [
        "smart_construction_custom.group_sc_role_pm",
    ],
    "sc_role_finance": [
        "smart_construction_custom.group_sc_role_finance",
    ],
    "sc_role_executive": [
        "smart_construction_custom.group_sc_role_executive",
    ],
}

LEGACY_ROLE_LOGIN_ALIASES = {
    "sc_role_project_read": ("demo_role_project_read",),
    "sc_role_project_user": ("demo_role_project_user",),
    "sc_role_project_manager": ("demo_role_project_manager",),
    "sc_role_owner": ("demo_role_owner",),
    "sc_role_pm": ("demo_role_pm",),
    "sc_role_finance": ("demo_role_finance",),
    "sc_role_executive": ("demo_role_executive",),
}


class ScSecurityPolicy(models.TransientModel):
    _name = "sc.security.policy"
    _description = "SC Security Policy"

    @api.model
    def apply_business_full_policy(self):
        group = self.env.ref("smart_construction_core.group_sc_business_full", raise_if_not_found=False)
        if not group:
            return False

        implied_xmlids = [
            "smart_construction_core.group_sc_internal_user",
            "smart_construction_core.group_sc_cap_contact_manager",
            "smart_construction_core.group_sc_cap_project_manager",
            "smart_construction_core.group_sc_cap_contract_manager",
            "smart_construction_core.group_sc_cap_cost_manager",
            "smart_construction_core.group_sc_cap_material_manager",
            "smart_construction_core.group_sc_cap_purchase_manager",
            "smart_construction_core.group_sc_cap_finance_manager",
            "smart_construction_core.group_sc_cap_settlement_manager",
            "smart_construction_core.group_sc_cap_data_read",
        ]

        to_add = []
        for xmlid in implied_xmlids:
            ref = self.env.ref(xmlid, raise_if_not_found=False)
            if ref and ref not in group.implied_ids:
                to_add.append(ref.id)

        if to_add:
            group.write({"implied_ids": [(4, gid) for gid in to_add]})
        return True

    @api.model
    def apply_role_matrix(self):
        role_specs = [
            ("smart_construction_custom.group_sc_role_project_read", "smart_construction_core.group_sc_cap_project_read"),
            ("smart_construction_custom.group_sc_role_project_user", "smart_construction_core.group_sc_cap_project_user"),
            ("smart_construction_custom.group_sc_role_project_manager", "smart_construction_core.group_sc_cap_project_manager"),
            ("smart_construction_custom.group_sc_role_contract_read", "smart_construction_core.group_sc_cap_contract_read"),
            ("smart_construction_custom.group_sc_role_contract_user", "smart_construction_core.group_sc_cap_contract_user"),
            ("smart_construction_custom.group_sc_role_contract_manager", "smart_construction_core.group_sc_cap_contract_manager"),
            ("smart_construction_custom.group_sc_role_settlement_read", "smart_construction_core.group_sc_cap_settlement_read"),
            ("smart_construction_custom.group_sc_role_settlement_user", "smart_construction_core.group_sc_cap_settlement_user"),
            ("smart_construction_custom.group_sc_role_settlement_user", "smart_construction_core.group_sc_cap_purchase_user"),
            ("smart_construction_custom.group_sc_role_settlement_manager", "smart_construction_core.group_sc_cap_settlement_manager"),
            ("smart_construction_custom.group_sc_role_settlement_manager", "smart_construction_core.group_sc_cap_purchase_user"),
            ("smart_construction_custom.group_sc_role_payment_read", "smart_construction_core.group_sc_cap_finance_read"),
            ("smart_construction_custom.group_sc_role_payment_user", "smart_construction_core.group_sc_cap_finance_user"),
            ("smart_construction_custom.group_sc_role_payment_manager", "smart_construction_core.group_sc_cap_finance_manager"),
        ]
        updated = False
        for role_xmlid, cap_xmlid in role_specs:
            role = self.env.ref(role_xmlid, raise_if_not_found=False)
            cap = self.env.ref(cap_xmlid, raise_if_not_found=False)
            if not role or not cap:
                continue
            if cap not in role.implied_ids:
                role.write({"implied_ids": [(4, cap.id)]})
                updated = True

        executive = self.env.ref("smart_construction_custom.group_sc_role_executive", raise_if_not_found=False)
        if executive:
            platform_groups = platform_admin_groups(self.env, include_legacy=True)
            to_remove = [group.id for group in platform_groups if group in executive.implied_ids]
            if to_remove:
                executive.write({"implied_ids": [(3, gid) for gid in to_remove]})
                updated = True

        forbidden_by_role_login = {
            "sc_role_executive": platform_admin_group_xmlids(include_legacy=True, include_system=False) + [
                "base.group_erp_manager",
                "base.group_system",
                "base.group_no_one",
                "project.group_project_manager",
                "smart_construction_core.group_sc_cap_business_config_admin",
                "smart_construction_core.group_sc_super_admin",
                "smart_construction_core.group_sc_task_entry_access",
            ],
        }
        Users = self.env["res.users"].sudo()
        for canonical_login, groups in ROLE_LOGIN_GROUPS.items():
            logins = (canonical_login,) + LEGACY_ROLE_LOGIN_ALIASES.get(canonical_login, ())
            for login in logins:
                user = Users.search([("login", "=", login)], limit=1)
                if not user:
                    continue
                to_remove = []
                for xmlid in forbidden_by_role_login.get(canonical_login, []):
                    group = self.env.ref(xmlid, raise_if_not_found=False)
                    if group and group in user.groups_id:
                        to_remove.append(group.id)
                if to_remove:
                    user.write({"groups_id": [(3, gid) for gid in to_remove]})
                    updated = True
                to_add = []
                for xmlid in groups:
                    group = self.env.ref(xmlid, raise_if_not_found=False)
                    if group and group not in user.groups_id:
                        to_add.append(group.id)
                if to_add:
                    user.write({"groups_id": [(4, gid) for gid in to_add]})
                    updated = True
        return updated or True
