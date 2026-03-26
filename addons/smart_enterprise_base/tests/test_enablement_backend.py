# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_enterprise_base.core_extension import smart_core_extend_system_init
from odoo.addons.smart_core.core.system_init_payload_builder import SystemInitPayloadBuilder


@tagged("sc_smoke", "enterprise_enablement_backend")
class TestEnterpriseEnablementBackend(TransactionCase):
    def test_extension_module_registration_includes_enterprise_base(self):
        raw = self.env["ir.config_parameter"].sudo().get_param("sc.core.extension_modules") or ""
        modules = [item.strip() for item in str(raw).split(",") if item.strip()]

        self.assertIn("smart_enterprise_base", modules)

    def test_company_action_opens_department_next_step(self):
        company = self.env["res.company"].create({"name": "Enterprise Enablement Company"})
        action = company.action_open_enterprise_departments()

        self.assertEqual(action.get("res_model"), "hr.department")
        self.assertEqual((action.get("context") or {}).get("default_company_id"), company.id)

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

    def test_system_init_contract_exposes_sprint0_enablement(self):
        payload = {}
        smart_core_extend_system_init(payload, self.env, self.env.user)

        mainline = (((payload.get("ext_facts") or {}).get("enterprise_enablement") or {}).get("mainline") or {})
        steps = mainline.get("steps") or []

        self.assertEqual(mainline.get("phase"), "sprint0")
        self.assertGreaterEqual(len(steps), 2)
        self.assertGreater(int(((mainline.get("primary_action") or {}).get("action_id") or 0)), 0)

        startup_surface = SystemInitPayloadBuilder.build_startup_surface(payload, params={"with_preload": False})
        startup_mainline = ((((startup_surface.get("ext_facts") or {}).get("enterprise_enablement")) or {}).get("mainline") or {})

        self.assertEqual(startup_mainline.get("phase"), "sprint0")
        self.assertGreaterEqual(len(startup_mainline.get("steps") or []), 2)
