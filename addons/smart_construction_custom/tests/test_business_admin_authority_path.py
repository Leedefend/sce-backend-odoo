# -*- coding: utf-8 -*-

from lxml import etree

from odoo import fields
from odoo.tests.common import TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval


@tagged("post_install", "-at_install", "sc_gate", "customer_admin_path")
class TestBusinessAdminAuthorityPath(TransactionCase):
    def _group_xmlids(self, groups):
        ext_map = groups.sudo().get_external_id()
        return {xmlid for xmlid in ext_map.values() if xmlid}

    def _create_user(self, login, groups):
        return self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": login,
                "login": login,
                "email": f"{login}@example.test",
                "groups_id": [(6, 0, [group.id for group in groups])],
            }
        )

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

    def test_security_policy_action_carrier_is_writable_through_capability_path_only(self):
        business_admin = self.env.ref("smart_construction_custom.group_sc_role_business_admin")
        config_admin = self.env.ref("smart_construction_core.group_sc_cap_config_admin")
        ordinary_user = self._create_user("security_policy_ordinary_user", [self.env.ref("base.group_user")])
        system_user = self._create_user(
            "security_policy_system_only_user",
            [self.env.ref("base.group_user"), self.env.ref("base.group_system")],
        )
        policy_model = self.env["sc.security.policy"]

        self.assertTrue(policy_model.with_user(system_user).check_access_rights("read", raise_exception=False))
        self.assertFalse(policy_model.with_user(system_user).check_access_rights("write", raise_exception=False))
        self.assertFalse(policy_model.with_user(ordinary_user).check_access_rights("write", raise_exception=False))

        business_admin_user = self._create_user(
            "security_policy_business_admin_user",
            [self.env.ref("base.group_user"), business_admin],
        )
        self.assertTrue(policy_model.with_user(business_admin_user).check_access_rights("read", raise_exception=False))
        self.assertTrue(policy_model.with_user(business_admin_user).check_access_rights("write", raise_exception=False))
        self.assertTrue(policy_model.with_user(business_admin_user).check_access_rights("create", raise_exception=False))
        self.assertFalse(policy_model.with_user(business_admin_user).check_access_rights("unlink", raise_exception=False))

        capability_user = self._create_user(
            "security_policy_config_admin_user",
            [self.env.ref("base.group_user"), config_admin],
        )
        self.assertTrue(policy_model.with_user(capability_user).check_access_rights("write", raise_exception=False))

        Access = self.env["ir.model.access"].sudo()
        policy_model_meta = self.env["ir.model"]._get("sc.security.policy")
        write_access = Access.search(
            [
                ("model_id", "=", policy_model_meta.id),
                ("perm_write", "=", True),
            ]
        )
        self.assertIn(config_admin, write_access.mapped("group_id"))
        self.assertNotIn(business_admin, write_access.mapped("group_id"))

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

        business_admin = self.env["res.users"].sudo().search([("login", "=", "wutao")], limit=1)
        finance_manager = self.env["res.users"].sudo().search([("login", "=", "wennan")], limit=1)
        general_manager = self.env["res.users"].sudo().search([("login", "=", "duanyijun")], limit=1)

        self.assertTrue(business_admin.has_group("smart_construction_custom.group_sc_role_business_admin"))
        self.assertTrue(business_admin.has_group("smart_construction_core.group_sc_business_full"))
        self.assertTrue(business_admin.has_group("smart_construction_custom.group_sc_role_owner"))
        self.assertFalse(finance_manager.has_group("smart_construction_custom.group_sc_role_business_admin"))
        self.assertFalse(finance_manager.has_group("smart_construction_core.group_sc_business_full"))
        self.assertTrue(finance_manager.has_group("smart_construction_custom.group_sc_role_finance"))
        self.assertTrue(finance_manager.has_group("smart_construction_custom.group_sc_role_owner"))
        self.assertFalse(general_manager.has_group("smart_construction_custom.group_sc_role_business_admin"))
        self.assertFalse(general_manager.has_group("smart_construction_core.group_sc_business_full"))
        self.assertTrue(general_manager.has_group("smart_construction_custom.group_sc_role_owner"))

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

    def test_customer_legacy_frequent_entry_aliases_reuse_capability_groups(self):
        root = self.env.ref("smart_construction_custom.menu_legacy_frequent_entries_root")
        self.assertEqual(root.parent_id, self.env.ref("smart_construction_core.menu_sc_root"))

        cases = {
            "menu_legacy_entry_project_overview": (
                "action_legacy_entry_project_overview",
                "project.project",
                {"smart_construction_core.group_sc_cap_project_read"},
            ),
            "menu_legacy_entry_construction_contract": (
                "action_legacy_entry_construction_contract",
                "construction.contract",
                {"smart_construction_core.group_sc_cap_contract_read"},
            ),
            "menu_legacy_entry_supplier_contract": (
                "action_legacy_entry_supplier_contract",
                "construction.contract",
                {"smart_construction_core.group_sc_cap_contract_read"},
            ),
            "menu_legacy_entry_payment_request": (
                "action_legacy_entry_payment_request",
                "payment.request",
                {"smart_construction_core.group_sc_cap_finance_read"},
            ),
            "menu_legacy_entry_counterparty_payment": (
                "action_legacy_entry_counterparty_payment",
                "payment.request",
                {"smart_construction_core.group_sc_cap_finance_read"},
            ),
            "menu_legacy_entry_progress_receipt": (
                "action_legacy_entry_progress_receipt",
                "payment.request",
                {"smart_construction_core.group_sc_cap_finance_read"},
            ),
            "menu_legacy_entry_tender_registration": (
                "action_legacy_entry_tender_registration",
                "tender.bid",
                {"smart_construction_core.group_sc_cap_project_read"},
            ),
            "menu_legacy_entry_fund_daily": (
                "action_legacy_entry_fund_daily",
                "sc.legacy.fund.daily.snapshot.fact",
                {"smart_construction_core.group_sc_cap_finance_read"},
            ),
            "menu_legacy_entry_input_tax_report": (
                "action_legacy_entry_input_tax_report",
                "sc.legacy.invoice.tax.fact",
                {"smart_construction_core.group_sc_cap_finance_read"},
            ),
            "menu_legacy_entry_invoice_register": (
                "action_legacy_entry_invoice_register",
                "sc.legacy.invoice.tax.fact",
                {"smart_construction_core.group_sc_cap_finance_read"},
            ),
        }
        for menu_xmlid, (action_xmlid, res_model, expected_group_xmlids) in cases.items():
            menu = self.env.ref(f"smart_construction_custom.{menu_xmlid}")
            action = self.env.ref(f"smart_construction_custom.{action_xmlid}")
            self.assertEqual(menu.parent_id, root, menu_xmlid)
            self.assertEqual(action.res_model, res_model, action_xmlid)
            self.assertTrue(expected_group_xmlids.issubset(self._group_xmlids(menu.groups_id)), menu_xmlid)
            self.assertTrue(expected_group_xmlids.issubset(self._group_xmlids(action.groups_id)), action_xmlid)
            self.assertNotIn("base.group_system", self._group_xmlids(menu.groups_id), menu_xmlid)
            self.assertNotIn("base.group_system", self._group_xmlids(action.groups_id), action_xmlid)

        self.assertEqual(self.env.ref("smart_construction_custom.action_legacy_entry_payment_request").domain, "[('type', '=', 'pay')]")
        self.assertEqual(self.env.ref("smart_construction_custom.action_legacy_entry_progress_receipt").domain, "[('type', '=', 'receive')]")
        self.assertEqual(self.env.ref("smart_construction_custom.action_legacy_entry_construction_contract").domain, "[('type', '=', 'out')]")
        self.assertEqual(self.env.ref("smart_construction_custom.action_legacy_entry_supplier_contract").domain, "[('type', '=', 'in')]")

    def test_customer_invoice_tax_entries_use_business_service_labels(self):
        input_tax_menu = self.env.ref("smart_construction_custom.menu_legacy_entry_input_tax_report")
        invoice_register_menu = self.env.ref("smart_construction_custom.menu_legacy_entry_invoice_register")
        input_tax_action = self.env.ref("smart_construction_custom.action_legacy_entry_input_tax_report")
        invoice_register_action = self.env.ref("smart_construction_custom.action_legacy_entry_invoice_register")

        self.assertEqual(input_tax_menu.name, "进项上报")
        self.assertEqual(invoice_register_menu.name, "开票登记")
        self.assertEqual(input_tax_action.name, "进项上报")
        self.assertEqual(invoice_register_action.name, "开票登记")
        self.assertEqual(input_tax_action.res_model, "sc.legacy.invoice.tax.fact")
        self.assertEqual(invoice_register_action.res_model, "sc.legacy.invoice.tax.fact")

    def test_core_business_service_pages_hide_historical_provenance_in_user_labels(self):
        action_cases = {
            "smart_construction_core.action_sc_legacy_fact_workflow_audit": "审批记录查询",
            "smart_construction_core.action_sc_legacy_fact_expense_deposit": "费用/保证金查询",
            "smart_construction_core.action_sc_legacy_fact_invoice_tax": "发票/税务查询",
            "smart_construction_core.action_sc_legacy_fact_receipt_income": "收款/收入查询",
            "smart_construction_core.action_sc_legacy_fact_financing_loan": "借款/贷款查询",
            "smart_construction_core.action_sc_legacy_fact_fund_daily_snapshot": "资金日报",
        }
        menu_cases = {
            "smart_construction_core.menu_sc_legacy_fact_assets": "业务资料查询",
            "smart_construction_core.menu_sc_legacy_fact_workflow_audit": "审批记录查询",
            "smart_construction_core.menu_sc_legacy_fact_expense_deposit": "费用/保证金查询",
            "smart_construction_core.menu_sc_legacy_fact_invoice_tax": "发票/税务查询",
            "smart_construction_core.menu_sc_legacy_fact_receipt_income": "收款/收入查询",
            "smart_construction_core.menu_sc_legacy_fact_financing_loan": "借款/贷款查询",
            "smart_construction_core.menu_sc_legacy_fact_fund_daily_snapshot": "资金日报",
        }
        view_cases = {
            "smart_construction_core.view_sc_legacy_workflow_audit_tree": "审批记录查询",
            "smart_construction_core.view_sc_legacy_expense_deposit_fact_tree": "费用/保证金查询",
            "smart_construction_core.view_sc_legacy_invoice_tax_fact_tree": "发票/税务查询",
            "smart_construction_core.view_sc_legacy_receipt_income_fact_tree": "收款/收入查询",
            "smart_construction_core.view_sc_legacy_financing_loan_fact_tree": "借款/贷款查询",
            "smart_construction_core.view_sc_legacy_fund_daily_snapshot_fact_tree": "资金日报",
        }

        for xmlid, expected_name in action_cases.items():
            self.assertEqual(self.env.ref(xmlid).name, expected_name, xmlid)
        for xmlid, expected_name in menu_cases.items():
            self.assertEqual(self.env.ref(xmlid).name, expected_name, xmlid)
        for xmlid, expected_title in view_cases.items():
            arch = self.env.ref(xmlid).arch_db
            self.assertIn(f'string="{expected_title}"', arch, xmlid)
            self.assertNotIn("历史", arch, xmlid)
            self.assertNotIn("旧系统", arch, xmlid)
            self.assertNotIn("事实", arch, xmlid)

    def test_core_business_service_fields_hide_technical_provenance_labels(self):
        view_xmlids = [
            "smart_construction_core.view_sc_legacy_workflow_audit_tree",
            "smart_construction_core.view_sc_legacy_workflow_audit_form",
            "smart_construction_core.view_sc_legacy_workflow_audit_search",
            "smart_construction_core.view_sc_legacy_expense_deposit_fact_tree",
            "smart_construction_core.view_sc_legacy_expense_deposit_fact_form",
            "smart_construction_core.view_sc_legacy_expense_deposit_fact_search",
            "smart_construction_core.view_sc_legacy_invoice_tax_fact_tree",
            "smart_construction_core.view_sc_legacy_invoice_tax_fact_form",
            "smart_construction_core.view_sc_legacy_invoice_tax_fact_search",
            "smart_construction_core.view_sc_legacy_receipt_income_fact_tree",
            "smart_construction_core.view_sc_legacy_receipt_income_fact_form",
            "smart_construction_core.view_sc_legacy_receipt_income_fact_search",
            "smart_construction_core.view_sc_legacy_financing_loan_fact_tree",
            "smart_construction_core.view_sc_legacy_financing_loan_fact_form",
            "smart_construction_core.view_sc_legacy_financing_loan_fact_search",
            "smart_construction_core.view_sc_legacy_fund_daily_snapshot_fact_tree",
            "smart_construction_core.view_sc_legacy_fund_daily_snapshot_fact_form",
            "smart_construction_core.view_sc_legacy_fund_daily_snapshot_fact_search",
        ]
        forbidden_label_tokens = ("来源", "旧系统", "历史", "事实", "迁移", "业务家族")
        technical_fields = {
            "actor_legacy_user_id",
            "legacy_business_id",
            "legacy_counterparty_id",
            "legacy_djid",
            "legacy_partner_id",
            "legacy_pid",
            "legacy_project_id",
            "legacy_record_id",
            "legacy_source_table",
            "legacy_workflow_id",
            "source_amount_field",
            "target_external_id",
            "target_model",
        }

        for xmlid in view_xmlids:
            arch = etree.fromstring(self.env.ref(xmlid).arch_db.encode())
            for node in arch.xpath(".//*[@string]"):
                label = node.attrib["string"]
                for token in forbidden_label_tokens:
                    self.assertNotIn(token, label, f"{xmlid}: {label}")
            for field in arch.xpath(".//field[@name]"):
                if field.attrib["name"] in technical_fields:
                    self.assertEqual(field.attrib.get("invisible"), "1", f"{xmlid}: {field.attrib['name']}")

    def test_customer_todo_center_reuses_existing_work_carriers_without_act_url(self):
        root = self.env.ref("smart_construction_custom.menu_legacy_frequent_entries_root")
        todo_center = self.env.ref("smart_construction_custom.menu_legacy_entry_todo_center")
        activity_menu = self.env.ref("smart_construction_custom.menu_legacy_entry_todo_activity")
        payment_review_menu = self.env.ref("smart_construction_custom.menu_legacy_entry_todo_payment_review")
        material_review_menu = self.env.ref("smart_construction_custom.menu_legacy_entry_todo_material_review")
        activity_action = self.env.ref("smart_construction_custom.action_legacy_entry_todo_activity")

        self.assertEqual(todo_center.parent_id, root)
        self.assertEqual(activity_menu.parent_id, todo_center)
        self.assertEqual(payment_review_menu.parent_id, todo_center)
        self.assertEqual(material_review_menu.parent_id, todo_center)
        self.assertEqual(activity_action._name, "ir.actions.act_window")
        self.assertEqual(activity_action.res_model, "mail.activity")
        self.assertEqual(activity_action.domain, "[('user_id', '=', uid)]")
        self.assertEqual(payment_review_menu.action, self.env.ref("smart_construction_core.action_sc_tier_review_my_payment_request"))
        self.assertEqual(material_review_menu.action, self.env.ref("smart_construction_core.action_sc_tier_review_my_material_plan"))

        self.assertIn("base.group_user", self._group_xmlids(activity_menu.groups_id))
        self.assertIn("base.group_user", self._group_xmlids(activity_action.groups_id))
        self.assertIn("smart_construction_core.group_sc_cap_finance_manager", self._group_xmlids(payment_review_menu.groups_id))
        self.assertIn("smart_construction_core.group_sc_cap_material_manager", self._group_xmlids(material_review_menu.groups_id))

    def test_customer_report_aliases_reuse_operating_metrics_projection(self):
        root = self.env.ref("smart_construction_custom.menu_legacy_frequent_entries_root")
        metrics_action = self.env.ref("smart_construction_core.action_sc_operating_metrics_project")
        cases = [
            "menu_legacy_entry_project_ar_ap_report",
            "menu_legacy_entry_company_operation_report",
        ]

        for menu_xmlid in cases:
            menu = self.env.ref(f"smart_construction_custom.{menu_xmlid}")
            group_xmlids = self._group_xmlids(menu.groups_id)
            self.assertEqual(menu.parent_id, root)
            self.assertEqual(menu.action, metrics_action)
            self.assertIn("smart_construction_core.group_sc_cap_project_read", group_xmlids)
            self.assertIn("smart_construction_core.group_sc_cap_cost_read", group_xmlids)
            self.assertIn("smart_construction_core.group_sc_cap_finance_read", group_xmlids)
            self.assertNotIn("base.group_system", group_xmlids)

    def test_customer_historical_fact_service_entries_are_scoped_native_business_services(self):
        root = self.env.ref("smart_construction_custom.menu_legacy_frequent_entries_root")
        cases = {
            "menu_legacy_entry_receipt_confirmation": (
                "action_legacy_entry_receipt_confirmation",
                "sc.legacy.receipt.income.fact",
                "[('source_family', '=', 'receipt_confirmation')]",
                "smart_construction_core.view_sc_legacy_receipt_income_fact_search",
                {"default_source_family": "receipt_confirmation", "default_direction": "inflow"},
            ),
            "menu_legacy_entry_pay_guarantee_deposit": (
                "action_legacy_entry_pay_guarantee_deposit",
                "sc.legacy.expense.deposit.fact",
                "[('source_family', '=', 'pay_guarantee_deposit')]",
                "smart_construction_core.view_sc_legacy_expense_deposit_fact_search",
                {"default_source_family": "pay_guarantee_deposit", "default_direction": "outflow"},
            ),
            "menu_legacy_entry_received_guarantee_deposit": (
                "action_legacy_entry_received_guarantee_deposit",
                "sc.legacy.expense.deposit.fact",
                "[('source_family', '=', 'received_guarantee_deposit_register')]",
                "smart_construction_core.view_sc_legacy_expense_deposit_fact_search",
                {"default_source_family": "received_guarantee_deposit_register", "default_direction": "inflow"},
            ),
            "menu_legacy_entry_guarantee_refund": (
                "action_legacy_entry_guarantee_refund",
                "sc.legacy.expense.deposit.fact",
                "[('source_family', 'in', ('pay_guarantee_deposit_refund', 'received_guarantee_deposit_refund', 'project_deduction_refund', 'self_funded_income_refund'))]",
                "smart_construction_core.view_sc_legacy_expense_deposit_fact_search",
                {"default_source_family": "pay_guarantee_deposit_refund", "default_direction": "inflow_or_refund"},
            ),
            "menu_legacy_entry_financing_loan_registration": (
                "action_legacy_entry_financing_loan_registration",
                "sc.legacy.financing.loan.fact",
                "[]",
                "smart_construction_core.view_sc_legacy_financing_loan_fact_search",
                {"default_source_family": "loan_registration", "default_source_direction": "financing_in"},
            ),
        }

        for menu_xmlid, (action_xmlid, res_model, domain, search_view_xmlid, expected_context) in cases.items():
            menu = self.env.ref(f"smart_construction_custom.{menu_xmlid}")
            action = self.env.ref(f"smart_construction_custom.{action_xmlid}")
            menu_group_xmlids = self._group_xmlids(menu.groups_id)
            action_group_xmlids = self._group_xmlids(action.groups_id)
            context = safe_eval(action.context or "{}")
            self.assertEqual(menu.parent_id, root, menu_xmlid)
            self.assertEqual(menu.action, action, menu_xmlid)
            self.assertEqual(action._name, "ir.actions.act_window", action_xmlid)
            self.assertEqual(action.res_model, res_model, action_xmlid)
            self.assertEqual(action.domain or "[]", domain, action_xmlid)
            self.assertEqual(action.search_view_id, self.env.ref(search_view_xmlid), action_xmlid)
            self.assertEqual(context.get("sc_manual_entry"), 1, action_xmlid)
            self.assertEqual(context.get("search_default_group_project"), 1, action_xmlid)
            for key, expected_value in expected_context.items():
                self.assertEqual(context.get(key), expected_value, action_xmlid)
            self.assertIn("smart_construction_core.group_sc_cap_finance_read", menu_group_xmlids, menu_xmlid)
            self.assertIn("smart_construction_core.group_sc_cap_finance_read", action_group_xmlids, action_xmlid)
            self.assertIn("smart_construction_core.group_sc_cap_finance_user", menu_group_xmlids, menu_xmlid)
            self.assertIn("smart_construction_core.group_sc_cap_finance_user", action_group_xmlids, action_xmlid)
            self.assertIn("smart_construction_core.group_sc_cap_finance_manager", menu_group_xmlids, menu_xmlid)
            self.assertIn("smart_construction_core.group_sc_cap_finance_manager", action_group_xmlids, action_xmlid)
            self.assertNotIn("base.group_system", menu_group_xmlids, menu_xmlid)
            self.assertNotIn("base.group_system", action_group_xmlids, action_xmlid)

    def test_frequent_entry_business_carrier_views_allow_native_create_edit_without_delete(self):
        view_xmlids = [
            "smart_construction_core.view_sc_legacy_expense_deposit_fact_tree",
            "smart_construction_core.view_sc_legacy_expense_deposit_fact_form",
            "smart_construction_core.view_sc_legacy_invoice_tax_fact_tree",
            "smart_construction_core.view_sc_legacy_invoice_tax_fact_form",
            "smart_construction_core.view_sc_legacy_receipt_income_fact_tree",
            "smart_construction_core.view_sc_legacy_receipt_income_fact_form",
            "smart_construction_core.view_sc_legacy_financing_loan_fact_tree",
            "smart_construction_core.view_sc_legacy_financing_loan_fact_form",
            "smart_construction_core.view_sc_legacy_fund_daily_snapshot_fact_tree",
            "smart_construction_core.view_sc_legacy_fund_daily_snapshot_fact_form",
        ]
        for xmlid in view_xmlids:
            arch = etree.fromstring(self.env.ref(xmlid).arch_db.encode())
            root = arch
            self.assertNotEqual(root.attrib.get("create"), "false", xmlid)
            self.assertNotEqual(root.attrib.get("edit"), "false", xmlid)
            self.assertEqual(root.attrib.get("delete"), "false", xmlid)

    def test_frequent_entry_business_carrier_create_defaults_hide_legacy_identifiers(self):
        project = self.env["project.project"].create({"name": "常用入口办理测试项目"})
        today = fields.Date.context_today(self.env.user)
        cases = [
            (
                "sc.legacy.expense.deposit.fact",
                {
                    "source_family": "pay_guarantee_deposit",
                    "direction": "outflow",
                    "project_id": project.id,
                    "source_amount": 100.0,
                },
                "manual.sc.legacy.expense.deposit.fact",
                "source_amount_field",
            ),
            (
                "sc.legacy.invoice.tax.fact",
                {
                    "source_family": "input_invoice_handover",
                    "direction": "input_invoice",
                    "project_id": project.id,
                    "legacy_partner_name": "测试相对方",
                    "source_amount": 100.0,
                },
                "manual.sc.legacy.invoice.tax.fact",
                "source_amount_field",
            ),
            (
                "sc.legacy.receipt.income.fact",
                {
                    "source_family": "receipt_confirmation",
                    "direction": "inflow",
                    "project_id": project.id,
                    "source_amount": 100.0,
                },
                "manual.sc.legacy.receipt.income.fact",
                None,
            ),
            (
                "sc.legacy.financing.loan.fact",
                {
                    "source_family": "loan_registration",
                    "source_direction": "financing_in",
                    "document_date": today,
                    "project_id": project.id,
                    "legacy_counterparty_name": "测试借款方",
                    "source_amount": 100.0,
                },
                "manual.sc.legacy.financing.loan.fact",
                "source_amount_field",
            ),
            (
                "sc.legacy.fund.daily.snapshot.fact",
                {
                    "snapshot_date": today,
                    "project_id": project.id,
                    "source_account_balance_total": 100.0,
                },
                "manual.sc.legacy.fund.daily.snapshot.fact",
                None,
            ),
        ]

        for model_name, vals, expected_source_table, source_field in cases:
            record = self.env[model_name].create(vals)
            self.assertEqual(record.legacy_source_table, expected_source_table, model_name)
            self.assertTrue(record.legacy_record_id.startswith("MANUAL-"), model_name)
            self.assertEqual(record.legacy_project_id, project.legacy_project_id or project.project_code or str(project.id), model_name)
            self.assertEqual(record.legacy_project_name, project.name, model_name)
            if source_field:
                self.assertEqual(record[source_field], "manual_source_amount", model_name)

    def test_frequent_entry_business_carrier_write_acl_is_bound_to_finance_user_not_read(self):
        finance_read = self.env.ref("smart_construction_core.group_sc_cap_finance_read")
        finance_user = self.env.ref("smart_construction_core.group_sc_cap_finance_user")
        read_user = self._create_user("legacy_fact_read_user", [self.env.ref("base.group_user"), finance_read])
        write_user = self._create_user("legacy_fact_write_user", [self.env.ref("base.group_user"), finance_user])
        model_names = [
            "sc.legacy.expense.deposit.fact",
            "sc.legacy.invoice.tax.fact",
            "sc.legacy.receipt.income.fact",
            "sc.legacy.financing.loan.fact",
            "sc.legacy.fund.daily.snapshot.fact",
        ]
        for model_name in model_names:
            self.assertFalse(self.env[model_name].with_user(read_user).check_access_rights("create", raise_exception=False), model_name)
            self.assertFalse(self.env[model_name].with_user(read_user).check_access_rights("write", raise_exception=False), model_name)
            self.assertTrue(self.env[model_name].with_user(write_user).check_access_rights("create", raise_exception=False), model_name)
            self.assertTrue(self.env[model_name].with_user(write_user).check_access_rights("write", raise_exception=False), model_name)
            self.assertFalse(self.env[model_name].with_user(write_user).check_access_rights("unlink", raise_exception=False), model_name)

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
