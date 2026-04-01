# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate", "customer_admin_path")
class TestBusinessAdminAuthorityPath(TransactionCase):
    def _group_xmlids(self, groups):
        ext_map = groups.sudo().get_external_id()
        return {xmlid for xmlid in ext_map.values() if xmlid}

    def test_config_admin_no_longer_implies_base_group_system(self):
        group = self.env.ref("smart_construction_core.group_sc_cap_config_admin")
        implied_xmlids = self._group_xmlids(group.implied_ids)
        self.assertIn("smart_construction_core.group_sc_internal_user", implied_xmlids)
        self.assertNotIn("base.group_system", implied_xmlids)

    def test_business_admin_group_implies_business_full_without_platform_admin(self):
        group = self.env.ref("smart_construction_custom.group_sc_role_business_admin")
        implied_xmlids = self._group_xmlids(group.implied_ids)
        self.assertIn("smart_construction_core.group_sc_business_full", implied_xmlids)
        self.assertNotIn("base.group_system", implied_xmlids)

    def test_customer_role_mapping_points_to_business_admin_and_owner_paths(self):
        mapping = self.env["sc.security.policy"].customer_system_role_group_xmlids()
        self.assertEqual(mapping.get("管理员角色"), ["smart_construction_custom.group_sc_role_business_admin"])
        self.assertEqual(mapping.get("通用角色"), ["smart_construction_custom.group_sc_role_owner"])

    def test_owner_group_now_carries_project_facing_operation_surface_and_cross_domain_read(self):
        owner_group = self.env.ref("smart_construction_custom.group_sc_role_owner")
        implied_xmlids = self._group_xmlids(owner_group.implied_ids)
        self.assertIn("smart_construction_custom.group_sc_role_project_user", implied_xmlids)
        self.assertIn("smart_construction_custom.group_sc_role_contract_user", implied_xmlids)
        self.assertIn("smart_construction_custom.group_sc_role_payment_read", implied_xmlids)
        self.assertIn("smart_construction_custom.group_sc_role_settlement_read", implied_xmlids)
        self.assertIn("smart_construction_core.group_sc_cap_cost_user", implied_xmlids)
        self.assertIn("smart_construction_core.group_sc_cap_material_user", implied_xmlids)
        self.assertIn("smart_construction_core.group_sc_cap_purchase_user", implied_xmlids)
        self.assertIn("smart_construction_custom.group_sc_role_data_read", implied_xmlids)

    def test_pm_group_now_carries_project_facing_approval_without_finance_authority(self):
        pm_group = self.env.ref("smart_construction_custom.group_sc_role_pm")
        implied_xmlids = self._group_xmlids(pm_group.implied_ids)
        self.assertIn("smart_construction_custom.group_sc_role_contract_manager", implied_xmlids)
        self.assertIn("smart_construction_core.group_sc_cap_material_manager", implied_xmlids)
        self.assertIn("smart_construction_core.group_sc_cap_purchase_manager", implied_xmlids)
        self.assertNotIn("smart_construction_core.group_sc_cap_finance_user", implied_xmlids)
        self.assertNotIn("smart_construction_core.group_sc_cap_finance_manager", implied_xmlids)

    def test_customer_user_system_role_bootstrap_attaches_groups(self):
        result = self.env["sc.security.policy"].bootstrap_customer_user_system_roles()
        self.assertFalse(result.get("unresolved_users"), result)

        finance_admin = self.env["res.users"].sudo().search([("login", "=", "wennan")], limit=1)
        owner_user = self.env["res.users"].sudo().search([("login", "=", "wutao")], limit=1)

        self.assertTrue(finance_admin.has_group("smart_construction_custom.group_sc_role_business_admin"))
        self.assertTrue(finance_admin.has_group("smart_construction_custom.group_sc_role_finance"))
        self.assertFalse(finance_admin.has_group("smart_construction_custom.group_sc_role_owner"))
        self.assertTrue(owner_user.has_group("smart_construction_custom.group_sc_role_owner"))

    def test_enterprise_maintenance_actions_shift_to_business_full_but_user_settings_stay_system_only(self):
        business_full = self.env.ref("smart_construction_core.group_sc_business_full")
        system_group = self.env.ref("base.group_system")
        company_action = self.env.ref("smart_enterprise_base.action_enterprise_company")
        department_action = self.env.ref("smart_enterprise_base.action_enterprise_department")
        post_action = self.env.ref("smart_enterprise_base.action_enterprise_post")
        user_action = self.env.ref("smart_enterprise_base.action_enterprise_user")

        self.assertIn(business_full, company_action.groups_id)
        self.assertIn(business_full, department_action.groups_id)
        self.assertIn(business_full, post_action.groups_id)
        self.assertIn(business_full, user_action.groups_id)
        self.assertIn(system_group, user_action.groups_id)

    def test_payment_request_my_action_requires_finance_write_not_finance_read(self):
        action = self.env.ref("smart_construction_core.action_payment_request_my")
        group_xmlids = self._group_xmlids(action.groups_id)

        self.assertIn("smart_construction_core.group_sc_cap_finance_user", group_xmlids)
        self.assertIn("smart_construction_core.group_sc_cap_finance_manager", group_xmlids)
        self.assertNotIn("smart_construction_core.group_sc_cap_finance_read", group_xmlids)

    def test_project_progress_entry_action_requires_cost_write_not_cost_read(self):
        action = self.env.ref("smart_construction_core.action_project_progress_entry")
        group_xmlids = self._group_xmlids(action.groups_id)

        self.assertIn("smart_construction_core.group_sc_cap_cost_user", group_xmlids)
        self.assertIn("smart_construction_core.group_sc_cap_cost_manager", group_xmlids)
        self.assertNotIn("smart_construction_core.group_sc_cap_cost_read", group_xmlids)

    def test_enterprise_maintenance_acl_shifts_to_business_full_including_res_users(self):
        Access = self.env["ir.model.access"].sudo()
        business_full = self.env.ref("smart_construction_core.group_sc_business_full")
        company_model = self.env["ir.model"]._get("res.company")
        department_model = self.env["ir.model"]._get("hr.department")
        post_model = self.env["ir.model"]._get("sc.enterprise.post")
        users_model = self.env["ir.model"]._get("res.users")

        self.assertTrue(Access.search_count([("model_id", "=", company_model.id), ("group_id", "=", business_full.id)]))
        self.assertTrue(Access.search_count([("model_id", "=", department_model.id), ("group_id", "=", business_full.id)]))
        self.assertTrue(Access.search_count([("model_id", "=", post_model.id), ("group_id", "=", business_full.id)]))
        self.assertTrue(Access.search_count([("model_id", "=", users_model.id), ("group_id", "=", business_full.id)]))

    def test_customer_user_primary_post_bootstrap_attaches_posts(self):
        self.env["sc.security.policy"].bootstrap_customer_users_primary_departments()
        result = self.env["sc.security.policy"].bootstrap_customer_user_primary_posts()
        self.assertFalse(result.get("unresolved_users"), result)

        finance_admin = self.env["res.users"].sudo().search([("login", "=", "wennan")], limit=1)
        chairman = self.env["res.users"].sudo().search([("login", "=", "wutao")], limit=1)

        self.assertEqual(finance_admin.sc_post_id.name, "财务经理")
        self.assertEqual(chairman.sc_post_id.name, "董事长")

    def test_customer_user_extra_post_bootstrap_attaches_extra_posts(self):
        policy = self.env["sc.security.policy"]
        policy.bootstrap_customer_users_primary_departments()
        policy.bootstrap_customer_user_primary_posts()
        result = policy.bootstrap_customer_user_extra_posts()
        self.assertFalse(result.get("unresolved_users"), result)

        finance_admin = self.env["res.users"].sudo().search([("login", "=", "wennan")], limit=1)
        project_manager = self.env["res.users"].sudo().search([("login", "=", "hujun")], limit=1)

        self.assertIn("副总经理", finance_admin.sc_post_ids.mapped("name"))
        self.assertIn("总经理", project_manager.sc_post_ids.mapped("name"))

    def test_customer_user_extra_department_bootstrap_attaches_departments(self):
        policy = self.env["sc.security.policy"]
        policy.bootstrap_customer_users_primary_departments()
        result = policy.bootstrap_customer_user_extra_departments()
        self.assertFalse(result.get("unresolved_users"), result)

        general_manager = self.env["res.users"].sudo().search([("login", "=", "duanyijun")], limit=1)
        estimator = self.env["res.users"].sudo().search([("login", "=", "chenshuai")], limit=1)

        self.assertIn("行政部", general_manager.sc_department_ids.mapped("name"))
        self.assertIn("项目部", estimator.sc_department_ids.mapped("name"))
