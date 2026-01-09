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
        return updated or True
