# -*- coding: utf-8 -*-

from pathlib import Path
import re
from unittest.mock import patch
from xml.etree import ElementTree as ET

from odoo.addons.smart_core.handlers.api_data import ApiDataHandler
from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler
from odoo.addons.smart_core.identity.identity_resolver import IdentityResolver
from odoo.tests.common import TransactionCase, tagged


@tagged("sc_smoke", "sprint1_user_role_backend")
class TestUserRoleProfileBackend(TransactionCase):
    def _unwrap_handler_result(self, result):
        if isinstance(result, tuple):
            data = result[0] if len(result) > 0 else None
            meta = result[1] if len(result) > 1 and isinstance(result[1], dict) else {}
            return {"ok": True, "data": data, "meta": meta}
        return result

    def _group_xmlids(self, group):
        ext_map = group.sudo().get_external_id()
        return {xmlid for xmlid in ext_map.values() if xmlid}

    def _xml_declared_implied_refs(self, relative_path, record_id):
        addons_root = Path(__file__).resolve().parents[2]
        subpath = Path(relative_path)
        if subpath.parts and subpath.parts[0] == "addons":
            subpath = Path(*subpath.parts[1:])
        xml_path = addons_root / subpath
        tree = ET.parse(str(xml_path))
        for record in tree.findall(".//record"):
            if str(record.get("id") or "").strip() != str(record_id or "").strip():
                continue
            for field in record.findall("./field[@name='implied_ids']"):
                eval_text = str(field.get("eval") or "")
                return set(re.findall(r"ref\('([^']+)'\)", eval_text))
        return set()

    def _record_xmlid(self, record):
        ext_map = record.sudo().get_external_id()
        return str(ext_map.get(record.id) or "")

    def test_api_data_create_syncs_password_company_scope_and_role_groups(self):
        company = self.env.company
        handler = ApiDataHandler(self.env, payload={})
        model_cls = type(self.env["res.users"])
        with patch.object(model_cls, "_change_password", autospec=True, wraps=model_cls._change_password) as password_mock:
            result = handler.handle(
                params={
                    "op": "create",
                    "model": "res.users",
                    "vals": {
                        "name": "Sprint1 API User",
                        "login": "sprint1-api-user@example.com",
                        "password": "Pass1234",
                        "company_id": company.id,
                        "sc_role_profile": "executive",
                        "active": True,
                    },
                }
            )

            result = self._unwrap_handler_result(result)
            self.assertTrue(result.get("ok"), result)
            user_id = int((result.get("data") or {}).get("id") or 0)
            user = self.env["res.users"].sudo().browse(user_id)
            self.assertTrue(user.exists())
            self.assertEqual(user.company_id, company)
            self.assertIn(company, user.company_ids)
            self.assertEqual(user.sc_role_effective, "executive")
            self.assertIn("smart_construction_core.group_sc_super_admin", IdentityResolver(self.env).user_group_xmlids(user))
            password_mock.assert_called_once()
            self.assertEqual(password_mock.call_args.args[1], "Pass1234")

    def test_api_data_write_syncs_password_company_scope_and_role_groups(self):
        company = self.env.company
        other_company = self.env["res.company"].sudo().create({"name": "Sprint1 Other Company"})
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Sprint1 API Update",
                "login": "sprint1-api-update@example.com",
                "password": "Pass1234",
                "company_id": company.id,
                "company_ids": [(6, 0, [company.id])],
                "sc_role_profile": "owner",
            }
        )
        handler = ApiDataHandler(self.env, payload={})
        model_cls = type(self.env["res.users"])
        with patch.object(model_cls, "_change_password", autospec=True, wraps=model_cls._change_password) as password_mock:
            result = handler.handle(
                params={
                    "op": "write",
                    "model": "res.users",
                    "ids": [user.id],
                    "vals": {
                        "company_id": other_company.id,
                        "password": "Pass5678",
                        "sc_role_profile": "executive",
                    },
                }
            )

            result = self._unwrap_handler_result(result)
            self.assertTrue(result.get("ok"), result)
            user.invalidate_recordset()
            self.assertEqual(user.company_id, other_company)
            self.assertIn(other_company, user.company_ids)
            self.assertEqual(user.sc_role_effective, "executive")
            self.assertIn("smart_construction_core.group_sc_super_admin", IdentityResolver(self.env).user_group_xmlids(user))
            password_mock.assert_called_once()
            self.assertEqual(password_mock.call_args.args[1], "Pass5678")

    def test_user_action_open_contract_includes_role_profile_fields(self):
        action = self.env.ref("smart_enterprise_base.action_enterprise_user")
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

        self.assertTrue(result.get("ok"), result)
        data = result.get("data") or {}
        form_view = ((data.get("views") or {}).get("form") or {})
        layout = form_view.get("layout") or []
        field_names = set()
        field_strings = {}

        def collect_fields(nodes):
            for node in nodes or []:
                if not isinstance(node, dict):
                    continue
                if node.get("type") == "field" and node.get("name"):
                    name = str(node.get("name"))
                    field_names.add(name)
                    field_strings[name] = str(node.get("string") or "")
                collect_fields(node.get("children") or [])

        collect_fields(layout)

        self.assertIn("password", field_names)
        self.assertIn("sc_role_profile", field_names)
        self.assertIn("sc_role_effective", field_names)
        self.assertIn("sc_role_landing_label", field_names)
        self.assertEqual(field_strings.get("name"), "姓名")
        self.assertEqual(field_strings.get("password"), "初始密码")
        self.assertEqual(field_strings.get("sc_role_profile"), "产品角色")
        field_policies = data.get("field_policies") or {}
        role_profile_policy = field_policies.get("sc_role_profile") or {}
        role_effective_policy = field_policies.get("sc_role_effective") or {}
        self.assertIn("create", role_profile_policy.get("visible_profiles") or [])
        self.assertIn("create", role_effective_policy.get("readonly_profiles") or [])
        self.assertEqual(role_profile_policy.get("group"), "secondary")

    def test_role_profile_syncs_pm_groups_and_role_surface(self):
        company = self.env.company
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Sprint1 PM",
                "login": "sprint1-pm@example.com",
                "password": "Pass1234",
                "company_id": company.id,
                "company_ids": [(6, 0, [company.id])],
                "sc_role_profile": "pm",
            }
        )

        resolver = IdentityResolver(self.env)
        role_code = resolver.resolve_role_code(resolver.user_group_xmlids(user))

        self.assertEqual(user.sc_role_profile, "pm")
        self.assertEqual(role_code, "pm")
        self.assertIn("smart_construction_core.group_sc_cap_project_manager", resolver.user_group_xmlids(user))

    def test_create_with_company_id_adds_allowed_company_scope(self):
        company = self.env.company
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Sprint1 Executive",
                "login": "sprint1-executive@example.com",
                "password": "Pass1234",
                "company_id": company.id,
                "sc_role_profile": "executive",
            }
        )

        self.assertEqual(user.company_id, company)
        self.assertIn(company, user.company_ids)
        resolver = IdentityResolver(self.env)
        group_xmlids = resolver.user_group_xmlids(user)
        self.assertIn("smart_construction_core.group_sc_cap_project_read", group_xmlids)
        self.assertIn("project.group_project_stages", group_xmlids)

    def test_role_profile_syncs_finance_groups_and_role_surface(self):
        company = self.env.company
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Sprint1 Finance",
                "login": "sprint1-finance@example.com",
                "password": "Pass1234",
                "company_id": company.id,
                "company_ids": [(6, 0, [company.id])],
                "sc_role_profile": "finance",
            }
        )

        resolver = IdentityResolver(self.env)
        role_code = resolver.resolve_role_code(resolver.user_group_xmlids(user))

        self.assertEqual(user.sc_role_profile, "finance")
        self.assertEqual(role_code, "finance")
        self.assertTrue(
            {
                "smart_construction_custom.group_sc_role_finance",
                "smart_construction_core.group_sc_cap_finance_manager",
            }
            & resolver.user_group_xmlids(user)
        )

    def test_custom_acl_and_role_matrix_still_route_permissions_through_capability_groups(self):
        acl_rows = self.env["ir.model.access"].sudo().search(
            [("name", "in", ["role.contract.read", "role.contract.user", "role.contract.manager",
                             "role.settlement.read", "role.settlement.user", "role.settlement.manager",
                             "role.payment.request.read", "role.payment.request.user", "role.payment.request.manager"])]
        )
        self.assertTrue(acl_rows, "expected custom role-matrix ACL rows to exist")
        self.assertFalse(
            any(self._record_xmlid(row.group_id).startswith("smart_construction_custom.group_sc_role_") for row in acl_rows),
            "ACL rows must bind to capability groups instead of role groups",
        )

        implied_xmlids = self._xml_declared_implied_refs(
            "addons/smart_construction_custom/security/role_matrix_groups.xml",
            "group_sc_role_executive",
        )
        self.assertIn("smart_construction_custom.group_sc_role_config_admin", implied_xmlids)
        self.assertNotIn("smart_construction_core.group_sc_cap_config_admin", implied_xmlids)

    def test_legacy_core_role_groups_use_bridge_groups_instead_of_direct_capability_inheritance(self):
        role_to_bridge = {
            "smart_construction_core.group_sc_role_project_manager": "smart_construction_core.group_sc_role_bridge_project_manager",
            "smart_construction_core.group_sc_role_material_user": "smart_construction_core.group_sc_role_bridge_material_user",
            "smart_construction_core.group_sc_role_material_manager": "smart_construction_core.group_sc_role_bridge_material_manager",
            "smart_construction_core.group_sc_role_purchase_user": "smart_construction_core.group_sc_role_bridge_purchase_user",
            "smart_construction_core.group_sc_role_finance_user": "smart_construction_core.group_sc_role_bridge_finance_user",
            "smart_construction_core.group_sc_role_finance_manager": "smart_construction_core.group_sc_role_bridge_finance_manager",
            "smart_construction_core.group_sc_role_contract_admin": "smart_construction_core.group_sc_role_bridge_contract_admin",
            "smart_construction_core.group_sc_role_cost_user": "smart_construction_core.group_sc_role_bridge_cost_user",
        }
        for role_xmlid, bridge_xmlid in role_to_bridge.items():
            implied_xmlids = self._xml_declared_implied_refs(
                "addons/smart_construction_core/security/sc_role_groups.xml",
                role_xmlid.split(".")[-1],
            )
            self.assertIn(bridge_xmlid, implied_xmlids)
            self.assertFalse(
                any(xmlid.startswith("smart_construction_core.group_sc_cap_") for xmlid in implied_xmlids),
                "%s should not imply capability groups directly" % role_xmlid,
            )

    def test_base_group_system_no_longer_resolves_to_executive_without_formal_role_group(self):
        company = self.env.company
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "System Admin Surface Only",
                "login": "system-admin-surface@example.com",
                "password": "Pass1234",
                "company_id": company.id,
                "company_ids": [(6, 0, [company.id])],
                "groups_id": [(6, 0, [self.env.ref("base.group_system").id])],
            }
        )
        resolver = IdentityResolver(self.env)
        group_xmlids = resolver.user_group_xmlids(user)
        self.assertEqual(resolver.resolve_role_code(group_xmlids), "owner")

    def test_capability_registry_does_not_treat_base_group_system_as_executive_role(self):
        from odoo.addons.smart_construction_core.services import capability_registry

        company = self.env.company
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "System Admin Registry",
                "login": "system-admin-registry@example.com",
                "password": "Pass1234",
                "company_id": company.id,
                "company_ids": [(6, 0, [company.id])],
                "groups_id": [(6, 0, [self.env.ref("base.group_system").id])],
            }
        )
        roles = capability_registry._resolve_role_codes_for_user(user)
        self.assertNotIn("executive", roles)
