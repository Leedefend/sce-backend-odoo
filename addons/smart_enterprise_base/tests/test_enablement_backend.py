# -*- coding: utf-8 -*-

import re

from odoo.exceptions import ValidationError
from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler
from odoo.tests.common import TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval

from odoo.addons.smart_enterprise_base.core_extension import smart_core_extend_system_init
from odoo.addons.smart_core.core.system_init_payload_builder import SystemInitPayloadBuilder


@tagged("sc_smoke", "enterprise_enablement_backend")
class TestEnterpriseEnablementBackend(TransactionCase):
    def _unwrap_handler_result(self, result):
        if hasattr(result, "to_legacy_dict"):
            return result.to_legacy_dict()
        return result or {}

    def _collect_contract_field_names(self, node):
        field_names = set()

        def collect(current):
            if isinstance(current, list):
                for item in current:
                    collect(item)
                return
            if not isinstance(current, dict):
                return
            if current.get("type") == "field" and current.get("name"):
                field_names.add(str(current.get("name")))
            for value in current.values():
                if isinstance(value, (dict, list)):
                    collect(value)

        collect(node)
        return field_names

    def _action_open_form_field_names(self, action, model_name):
        handler = UiContractHandler(self.env)
        result = handler.handle(
            payload={
                "params": {
                    "op": "action_open",
                    "action_id": int(action.id),
                    "render_profile": "create",
                }
            }
        )

        result = self._unwrap_handler_result(result)
        self.assertTrue(result.get("ok"), result)
        data = result.get("data") or {}
        form_view = ((data.get("views") or {}).get("form") or {})
        field_names = self._collect_contract_field_names(form_view.get("layout") or [])
        field_names |= self._collect_contract_field_names(data)
        if not field_names:
            parsed = self.env["app.view.config"].with_context(
                contract_action_id=int(action.id),
            )._generate_from_fields_view_get(model_name, "form")
            field_names = self._collect_contract_field_names(parsed or {})
        if not field_names:
            view_data = self.env["app.view.config"].with_context(
                contract_action_id=int(action.id),
            )._safe_get_view_data(model_name, "form")
            arch = (view_data or {}).get("arch") or ""
            field_names = {str(name) for name in re.findall(r'<field[^>]+name="([^"]+)"', arch)}
        return field_names

    def test_extension_module_registration_includes_enterprise_base(self):
        raw = self.env["ir.config_parameter"].sudo().get_param("sc.core.extension_modules") or ""
        modules = [item.strip() for item in str(raw).split(",") if item.strip()]

        self.assertIn("smart_enterprise_base", modules)

    def test_company_action_opens_department_next_step(self):
        company = self.env["res.company"].create({"name": "Enterprise Enablement Company"})
        action = company.action_open_enterprise_departments()

        self.assertEqual(action.get("res_model"), "hr.department")
        self.assertEqual((action.get("context") or {}).get("default_company_id"), company.id)

    def test_company_action_uses_enterprise_base_views(self):
        action = self.env.ref("smart_enterprise_base.action_enterprise_company")
        action_context = safe_eval(action.context or "{}")

        self.assertEqual(action.view_id, self.env.ref("smart_enterprise_base.view_company_tree_enterprise_base"))
        self.assertEqual(action_context.get("form_view_ref"), "smart_enterprise_base.view_company_form_enterprise_base")

    def test_company_action_open_contract_prefers_enterprise_base_form(self):
        action = self.env.ref("smart_enterprise_base.action_enterprise_company")
        field_names = self._action_open_form_field_names(action, "res.company")

        self.assertIn("sc_short_name", field_names)
        self.assertIn("sc_credit_code", field_names)
        self.assertNotIn("partner_id", field_names)

    def test_department_action_opens_user_next_step(self):
        company = self.env["res.company"].create({"name": "Enterprise Enablement Company"})
        self.env.user.write({"company_ids": [(4, company.id)]})
        department = self.env["hr.department"].create(
            {
                "name": "Engineering",
                "company_id": company.id,
                "sc_manager_user_id": self.env.user.id,
            }
        )

        action = department.action_open_enterprise_users()

        self.assertEqual(action.get("res_model"), "res.users")
        self.assertEqual((action.get("context") or {}).get("default_company_id"), company.id)
        self.assertEqual((action.get("context") or {}).get("default_sc_department_id"), department.id)

    def test_user_action_uses_enterprise_base_views(self):
        action = self.env.ref("smart_enterprise_base.action_enterprise_user")
        action_context = safe_eval(action.context or "{}")

        self.assertIn(
            action.view_id,
            [
                self.env.ref("smart_enterprise_base.view_users_tree_enterprise_base"),
                self.env.ref("smart_construction_core.view_users_tree_enterprise_role_profile"),
            ],
        )
        self.assertIn(
            action_context.get("form_view_ref"),
            [
                "smart_enterprise_base.view_users_form_enterprise_base",
                "smart_construction_core.view_users_form_enterprise_role_profile",
            ],
        )

    def test_user_action_open_contract_prefers_enterprise_base_form(self):
        action = self.env.ref("smart_enterprise_base.action_enterprise_user")
        field_names = self._action_open_form_field_names(action, "res.users")

        self.assertIn("sc_department_id", field_names)
        self.assertIn("sc_manager_user_id", field_names)
        self.assertIn("company_id", field_names)
        self.assertNotIn("avatar_128", field_names)

    def test_enterprise_root_menu_is_nested_under_smart_construction_root(self):
        menu = self.env.ref("smart_enterprise_base.menu_enterprise_base_root")

        self.assertEqual(menu.parent_id, self.env.ref("smart_construction_core.menu_sc_root"))

    def test_department_parent_must_stay_in_same_company(self):
        company = self.env["res.company"].create({"name": "Company A"})
        other_company = self.env["res.company"].create({"name": "Company B"})
        root = self.env["hr.department"].create({"name": "Root", "company_id": company.id})

        with self.assertRaises(ValidationError):
            self.env["hr.department"].create(
                {
                    "name": "Cross Company Child",
                    "company_id": other_company.id,
                    "parent_id": root.id,
                }
            )

    def test_user_department_must_stay_in_same_company(self):
        company = self.env["res.company"].create({"name": "Company A"})
        other_company = self.env["res.company"].create({"name": "Company B"})
        department = self.env["hr.department"].create({"name": "工程管理部", "company_id": company.id})

        with self.assertRaises(ValidationError):
            self.env["res.users"].with_context(no_reset_password=True).create(
                {
                    "name": "Cross Company User",
                    "login": "cross-company-user@example.com",
                    "company_id": other_company.id,
                    "company_ids": [(6, 0, [other_company.id])],
                    "sc_department_id": department.id,
                }
            )

    def test_system_init_contract_exposes_sprint0_enablement(self):
        payload = {}
        smart_core_extend_system_init(payload, self.env, self.env.user)

        mainline = (((payload.get("ext_facts") or {}).get("enterprise_enablement") or {}).get("mainline") or {})
        steps = mainline.get("steps") or []

        self.assertIn(mainline.get("phase"), {"sprint0", "sprint1"})
        self.assertGreaterEqual(len(steps), 3)
        self.assertGreater(int(((mainline.get("primary_action") or {}).get("action_id") or 0)), 0)
        self.assertEqual((steps[2] or {}).get("key"), "user")

        startup_surface = SystemInitPayloadBuilder.build_startup_surface(payload, params={"with_preload": False})
        startup_mainline = ((((startup_surface.get("ext_facts") or {}).get("enterprise_enablement")) or {}).get("mainline") or {})

        self.assertIn(startup_mainline.get("phase"), {"sprint0", "sprint1"})
        self.assertGreaterEqual(len(startup_mainline.get("steps") or []), 3)

    def test_system_init_enters_sprint1_when_department_exists(self):
        company = self.env.company
        self.env["hr.department"].create({"name": "Sprint1 Department", "company_id": company.id})

        payload = {}
        smart_core_extend_system_init(payload, self.env, self.env.user)

        mainline = (((payload.get("ext_facts") or {}).get("enterprise_enablement") or {}).get("mainline") or {})
        self.assertEqual(mainline.get("phase"), "sprint1")
        self.assertEqual(((mainline.get("primary_action") or {}).get("action_xmlid") or ""), "smart_enterprise_base.action_enterprise_user")
        self.assertIn("产品角色", ((mainline.get("steps") or [None, None, {}])[2] or {}).get("next_hint") or "")
