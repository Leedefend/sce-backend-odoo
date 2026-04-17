# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.services import capability_registry


@tagged("sc_smoke", "capability_registry")
class TestCapabilityRegistryService(TransactionCase):
    def _registry_surface_user(self):
        group_xmlids = [
            "smart_construction_core.group_sc_role_project_manager",
            "smart_construction_core.group_sc_role_finance_manager",
            "smart_construction_core.group_sc_role_contract_admin",
            "smart_construction_core.group_sc_role_cost_user",
        ]
        group_ids = [
            group.id
            for group in (self.env.ref(xmlid, raise_if_not_found=False) for xmlid in group_xmlids)
            if group
        ]
        return self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "capability-registry-surface",
                "login": "capability_registry_surface",
                "email": "capability_registry_surface@example.com",
                "groups_id": [(6, 0, group_ids)],
            }
        )

    def test_registry_lint_passes(self):
        issues = capability_registry.lint_registry(self.env)
        self.assertFalse(issues, f"registry lint issues: {issues}")

    def test_registry_surface_count(self):
        rows = capability_registry.list_capabilities_for_user(self.env, self._registry_surface_user())
        self.assertGreaterEqual(len(rows), 30)
        self.assertTrue(any((row.get("group_key") == "project_management") for row in rows))

    def test_capability_matrix_sections(self):
        matrix = capability_registry.build_capability_matrix_for_user(self.env, self.env.user)
        sections = matrix.get("sections") if isinstance(matrix, dict) else None
        self.assertIsInstance(sections, list)
        self.assertTrue(bool(sections))
        self.assertTrue(all(isinstance(section.get("items"), list) for section in sections if isinstance(section, dict)))

    def test_custom_project_manager_role_maps_to_pm(self):
        role_group = self.env.ref("smart_construction_custom.group_sc_role_project_manager", raise_if_not_found=False)
        if not role_group:
            self.skipTest("smart_construction_custom not installed")
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "role-map-pm",
                "login": "role_map_pm",
                "email": "role_map_pm@example.com",
                "groups_id": [(6, 0, [role_group.id])],
            }
        )
        roles = capability_registry._resolve_role_codes_for_user(user)
        self.assertIn("pm", roles)
