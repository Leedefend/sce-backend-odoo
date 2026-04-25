# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.app_config_engine.services.assemblers.page_assembler import PageAssembler


@tagged("post_install", "-at_install", "perm_runtime_uid")
class TestPermissionContractRuntimeUid(TransactionCase):
    def test_page_assembler_uses_runtime_user_for_effective_permissions(self):
        company = self.env.ref("base.main_company")
        manager_group = self.env.ref("smart_construction_core.group_sc_cap_project_manager")
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "perm.runtime.project.manager",
                "login": "perm.runtime.project.manager",
                "email": "perm.runtime.project.manager@example.com",
                "company_id": company.id,
                "company_ids": [(6, 0, [company.id])],
                "groups_id": [(6, 0, [manager_group.id])],
            }
        )

        user_env = api.Environment(self.env.cr, user.id, dict(self.env.context or {}))
        su_env = api.Environment(self.env.cr, SUPERUSER_ID, dict(self.env.context or {}))
        payload = {"model": "sc.project.stage.requirement.item", "view_types": ["form"]}

        data, _versions = PageAssembler(user_env, su_env).assemble_page_contract(payload)
        effective = ((data.get("permissions") or {}).get("effective") or {}).get("rights") or {}

        self.assertTrue(effective.get("read"), effective)
        self.assertTrue(effective.get("write"), effective)
        self.assertTrue(effective.get("create"), effective)
        self.assertTrue(effective.get("unlink"), effective)
