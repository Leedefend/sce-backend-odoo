# -*- coding: utf-8 -*-
from odoo import api, models


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
            ("smart_construction_custom.group_sc_role_settlement_manager", "smart_construction_core.group_sc_cap_settlement_manager"),
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

        user_map = {
            "demo_role_project_read": [
                "smart_construction_custom.group_sc_role_project_read",
                "smart_construction_custom.group_sc_role_contract_read",
                "smart_construction_core.group_sc_cap_contract_read",
                "smart_construction_custom.group_sc_role_settlement_read",
                "smart_construction_core.group_sc_cap_settlement_read",
                "smart_construction_custom.group_sc_role_payment_read",
                "smart_construction_core.group_sc_cap_finance_read",
            ],
            "demo_role_project_user": [
                "smart_construction_custom.group_sc_role_project_user",
                "smart_construction_custom.group_sc_role_contract_user",
                "smart_construction_core.group_sc_cap_contract_user",
                "smart_construction_custom.group_sc_role_settlement_user",
                "smart_construction_core.group_sc_cap_settlement_user",
                "smart_construction_custom.group_sc_role_payment_user",
                "smart_construction_core.group_sc_cap_finance_user",
            ],
            "demo_role_project_manager": [
                "smart_construction_custom.group_sc_role_project_manager",
                "smart_construction_custom.group_sc_role_contract_manager",
                "smart_construction_core.group_sc_cap_contract_manager",
                "smart_construction_custom.group_sc_role_settlement_manager",
                "smart_construction_core.group_sc_cap_settlement_manager",
                "smart_construction_custom.group_sc_role_payment_manager",
                "smart_construction_core.group_sc_cap_finance_manager",
            ],
            "demo_role_owner": [
                "smart_construction_custom.group_sc_role_owner",
            ],
            "demo_role_pm": [
                "smart_construction_custom.group_sc_role_pm",
            ],
            "demo_role_finance": [
                "smart_construction_custom.group_sc_role_finance",
            ],
            "demo_role_executive": [
                "smart_construction_custom.group_sc_role_executive",
            ],
        }
        Users = self.env["res.users"].sudo()
        for login, groups in user_map.items():
            user = Users.search([("login", "=", login)], limit=1)
            if not user:
                continue
            to_add = []
            for xmlid in groups:
                group = self.env.ref(xmlid, raise_if_not_found=False)
                if group and group not in user.groups_id:
                    to_add.append(group.id)
            if to_add:
                user.write({"groups_id": [(4, gid) for gid in to_add]})
                updated = True
        return updated or True
