# -*- coding: utf-8 -*-
import json

from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install", "smoke", "sc_smoke", "smart_core")
class TestV1IntentSmoke(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_login = "smart_core_tester"
        cls.test_password = "pass1234"
        cls.test_user = cls.env["res.users"].sudo().create({
            "name": "Smart Core Tester",
            "login": cls.test_login,
            "password": cls.test_password,
            "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
        })

    def _json_response(self, resp):
        if hasattr(resp, "read"):
            body = resp.read()
        else:
            body = resp
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        return json.loads(body or "{}")

    def _post_intent(self, payload, headers=None, with_db=False):
        url = "/api/v1/intent"
        if with_db:
            url = f"{url}?db={self.env.cr.dbname}"
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        resp = self.url_open(url, data=json.dumps(payload), headers=req_headers)
        return self._json_response(resp)

    def test_anon_login_intent(self):
        payload = {
            "intent": "login",
            "params": {"login": self.test_login, "password": self.test_password, "contract_mode": "compat"},
        }
        data = self._post_intent(
            payload,
            headers={"X-Anonymous-Intent": "true"},
            with_db=True,
        )
        self.assertTrue(data.get("ok"), data)
        self.assertTrue(data.get("data", {}).get("token"), data)

    def test_anon_login_intent_default_contract_mode(self):
        payload = {
            "intent": "login",
            "params": {
                "login": self.test_login,
                "password": self.test_password,
                "contract_mode": "default",
            },
        }
        data = self._post_intent(
            payload,
            headers={"X-Anonymous-Intent": "true"},
            with_db=True,
        )
        self.assertTrue(data.get("ok"), data)
        row = data.get("data", {}) or {}
        session = row.get("session") or {}
        self.assertTrue(session.get("token"), data)
        contract = row.get("contract") or {}
        self.assertEqual(contract.get("response_mode"), "default")
        self.assertEqual(contract.get("mode"), "default")
        self.assertEqual(contract.get("contract_version"), "1.0.0")
        self.assertEqual(contract.get("schema_version"), "1.0.0")
        self.assertFalse(bool(contract.get("compat_requested")))
        self.assertTrue(bool(contract.get("compat_enabled")))
        self.assertTrue(bool(contract.get("compat_deprecated")))
        self.assertIn("bootstrap", row)
        bootstrap = row.get("bootstrap") or {}
        allowed_exception_intents = bootstrap.get("allowed_exception_intents") or []
        self.assertIn("session.bootstrap", allowed_exception_intents)
        self.assertIn("scene.health", allowed_exception_intents)
        self.assertIn("entitlement", row)
        self.assertNotIn("token", row)
        self.assertNotIn("system", row)
        self.assertNotIn("groups", (row.get("user") or {}))

    def test_anon_login_intent_without_db_query_param(self):
        payload = {
            "intent": "login",
            "params": {"login": self.test_login, "password": self.test_password, "contract_mode": "compat"},
        }
        data = self._post_intent(
            payload,
            headers={"X-Anonymous-Intent": "true"},
            with_db=False,
        )
        self.assertTrue(data.get("ok"), data)
        self.assertTrue(data.get("data", {}).get("token"), data)

    def test_anon_login_intent_compat_disabled_fallbacks_to_default(self):
        self.env["ir.config_parameter"].sudo().set_param("smart_core.login.compat_enabled", "0")
        payload = {
            "intent": "login",
            "params": {
                "login": self.test_login,
                "password": self.test_password,
                "contract_mode": "compat",
            },
        }
        data = self._post_intent(
            payload,
            headers={"X-Anonymous-Intent": "true"},
            with_db=True,
        )
        self.assertTrue(data.get("ok"), data)
        row = data.get("data", {}) or {}
        contract = row.get("contract") or {}
        self.assertEqual(contract.get("response_mode"), "default")
        self.assertEqual(contract.get("mode"), "default")
        self.assertTrue(bool(contract.get("compat_requested")))
        self.assertFalse(bool(contract.get("compat_enabled")))
        self.assertEqual(contract.get("deprecation_notice"), "compat_mode_disabled_fallback_to_default")
        self.assertNotIn("token", row)
        self.env["ir.config_parameter"].sudo().set_param("smart_core.login.compat_enabled", "1")

    def test_anon_login_intent_debug_contract_mode(self):
        payload = {
            "intent": "login",
            "params": {"login": self.test_login, "password": self.test_password, "contract_mode": "debug"},
        }
        data = self._post_intent(
            payload,
            headers={"X-Anonymous-Intent": "true"},
            with_db=True,
        )
        self.assertTrue(data.get("ok"), data)
        row = data.get("data", {}) or {}
        self.assertTrue((row.get("session") or {}).get("token"), data)
        self.assertTrue(row.get("token"), data)
        self.assertIn("debug", row)
        self.assertIn("groups", row.get("debug") or {})
        self.assertIn("intents", row.get("debug") or {})
        self.assertNotIn("system", row)

    def test_anon_login_intent_default_without_contract_mode(self):
        payload = {
            "intent": "login",
            "params": {"login": self.test_login, "password": self.test_password},
        }
        data = self._post_intent(
            payload,
            headers={"X-Anonymous-Intent": "true"},
            with_db=True,
        )
        self.assertTrue(data.get("ok"), data)
        row = data.get("data", {}) or {}
        session = row.get("session") or {}
        self.assertTrue(session.get("token"), data)
        self.assertNotIn("token", row)
        self.assertNotIn("debug", row)

    def test_system_init_intent(self):
        login_payload = {
            "intent": "login",
            "params": {"login": self.test_login, "password": self.test_password},
        }
        login_data = self._post_intent(
            login_payload,
            headers={"X-Anonymous-Intent": "true"},
            with_db=True,
        )
        login_row = login_data.get("data", {}) or {}
        token = (login_row.get("session") or {}).get("token") or login_row.get("token")
        self.assertTrue(token, login_data)

        payload = {"intent": "system.init", "params": {}}
        data = self._post_intent(payload, headers={"Authorization": f"Bearer {token}"})
        self.assertTrue(data.get("ok"), data)
        response_meta = data.get("meta") or {}
        self.assertEqual(response_meta.get("contract_version"), "1.0.0")
        self.assertEqual(response_meta.get("schema_version"), "1.0.0")
        self.assertIn("user", data.get("data", {}))
        self.assertIn("nav", data.get("data", {}))
        self.assertIn("intents", data.get("data", {}))
        self.assertNotIn("intents_meta", data.get("data", {}))
        intents = data.get("data", {}).get("intents") or []
        self.assertIsInstance(intents, list)
        self.assertIn("meta.intent_catalog", intents)
        self.assertIn("intent_catalog_ref", data.get("data", {}))
        self.assertNotIn("api.data", intents)
        self.assertIn("capabilities", data.get("data", {}))
        self.assertIn("capability_groups", data.get("data", {}))
        self.assertIn("init_contract_v1", data.get("data", {}))
        self.assertIn("system_init_sections_v1", data.get("data", {}))
        self.assertIn("workspace_home_ref", data.get("data", {}))
        self.assertNotIn("workspace_home", data.get("data", {}))
        workspace_home_ref = data.get("data", {}).get("workspace_home_ref") or {}
        self.assertFalse(bool(workspace_home_ref.get("loaded")))
        default_route = data.get("data", {}).get("default_route") or {}
        if isinstance(default_route, dict):
            self.assertIn("reason", default_route)
            self.assertIn("route", default_route)
            self.assertIn("scene_key", default_route)
        init_contract = data.get("data", {}).get("init_contract_v1") or {}
        sections_v1 = data.get("data", {}).get("system_init_sections_v1") or {}
        self.assertEqual(sections_v1.get("contract_version"), "1.0.0")
        self.assertEqual(sections_v1.get("schema_version"), "1.0.0")
        self.assertIn("session", sections_v1)
        self.assertIn("nav", sections_v1)
        self.assertIn("surface", sections_v1)
        self.assertIn("bootstrap_refs", sections_v1)
        self.assertEqual(init_contract.get("contract_version"), "1.0.0")
        self.assertEqual(init_contract.get("schema_version"), "1.0.0")
        self.assertIn("session", init_contract)
        self.assertIn("nav", init_contract)
        self.assertIn("surface", init_contract)
        self.assertIn("bootstrap_refs", init_contract)
        scene_governance = data.get("data", {}).get("scene_governance_v1") or {}
        self.assertIn("surface_mapping", scene_governance)
        mapping = scene_governance.get("surface_mapping") or {}
        self.assertIn("before", mapping)
        self.assertIn("after", mapping)
        self.assertIn("removed", mapping)
        scene_metrics = scene_governance.get("scene_metrics") or {}
        self.assertIn("scene_registry_count", scene_metrics)
        self.assertIn("scene_deliverable_count", scene_metrics)
        self.assertIn("scene_navigable_count", scene_metrics)
        self.assertIn("scene_excluded_count", scene_metrics)
        row = data.get("data", {}) or {}
        role_surface = row.get("role_surface") or {}
        role_surface_code = str(role_surface.get("role_code") or "").strip().lower()
        init_meta = row.get("init_meta") if isinstance(row.get("init_meta"), dict) else {}
        page_contract_meta = init_meta.get("page_contract_meta") if isinstance(init_meta.get("page_contract_meta"), dict) else {}
        self.assertIn(str(page_contract_meta.get("intent") or "").strip(), {"scene.page_contract", "page.contract"})
        if role_surface_code:
            workspace_home = row.get("workspace_home") or {}
            workspace_record = workspace_home.get("record") if isinstance(workspace_home.get("record"), dict) else {}
            hero = workspace_record.get("hero") if isinstance(workspace_record.get("hero"), dict) else {}
            hero_role_code = str(hero.get("role_code") or "").strip().lower()
            if hero_role_code:
                self.assertEqual(hero_role_code, role_surface_code)

            page_orchestration_v1 = workspace_home.get("page_orchestration_v1") or {}
            page = page_orchestration_v1.get("page") if isinstance(page_orchestration_v1.get("page"), dict) else {}
            context = page.get("context") if isinstance(page.get("context"), dict) else {}
            context_role_code = str(context.get("role_code") or "").strip().lower()
            if context_role_code:
                self.assertEqual(context_role_code, role_surface_code)

    def test_system_init_with_workspace_home(self):
        login_payload = {
            "intent": "login",
            "params": {"login": self.test_login, "password": self.test_password},
        }
        login_data = self._post_intent(
            login_payload,
            headers={"X-Anonymous-Intent": "true"},
            with_db=True,
        )
        login_row = login_data.get("data", {}) or {}
        token = (login_row.get("session") or {}).get("token") or login_row.get("token")
        self.assertTrue(token, login_data)

        payload = {"intent": "system.init", "params": {"with": ["workspace_home"]}}
        data = self._post_intent(payload, headers={"Authorization": f"Bearer {token}"})
        self.assertTrue(data.get("ok"), data)
        row = data.get("data", {}) or {}
        init_contract = row.get("init_contract_v1") if isinstance(row.get("init_contract_v1"), dict) else {}
        self.assertEqual(init_contract.get("contract_version"), "1.0.0")
        self.assertEqual(init_contract.get("schema_version"), "1.0.0")
        self.assertIn("workspace_home", row)
        self.assertIn("workspace_home_ref", row)
        ref = row.get("workspace_home_ref") or {}
        self.assertTrue(bool(ref.get("loaded")))
        role_surface = row.get("role_surface") if isinstance(row.get("role_surface"), dict) else {}
        role_surface_code = str(role_surface.get("role_code") or "").strip().lower()
        workspace_home = row.get("workspace_home") if isinstance(row.get("workspace_home"), dict) else {}
        workspace_record = workspace_home.get("record") if isinstance(workspace_home.get("record"), dict) else {}
        hero = workspace_record.get("hero") if isinstance(workspace_record.get("hero"), dict) else {}
        self.assertEqual(str(hero.get("role_code") or "").strip().lower(), role_surface_code)
        orchestration_v1 = workspace_home.get("page_orchestration_v1") if isinstance(workspace_home.get("page_orchestration_v1"), dict) else {}
        page_v1 = orchestration_v1.get("page") if isinstance(orchestration_v1.get("page"), dict) else {}
        context_v1 = page_v1.get("context") if isinstance(page_v1.get("context"), dict) else {}
        self.assertEqual(str(context_v1.get("role_code") or "").strip().lower(), role_surface_code)
        blocks = workspace_home.get("blocks") if isinstance(workspace_home.get("blocks"), list) else []
        self.assertTrue(bool(blocks))
        first_block = blocks[0] if blocks else {}
        self.assertIn("type", first_block)
        self.assertIn("data", first_block)
        self.assertIn("actions", first_block)

        self.assertIsInstance(data.get("data", {}).get("capability_groups"), list)
        capabilities = data.get("data", {}).get("capabilities") or []
        self.assertIsInstance(capabilities, list)
        if capabilities:
            first_cap = capabilities[0]
            self.assertIn("capability_state", first_cap)
            self.assertIn("capability_state_reason", first_cap)
            self.assertIn("delivery_level", first_cap)
            self.assertIn("target_scene_key", first_cap)
            self.assertIn("entry_kind", first_cap)
            self.assertIn(first_cap.get("capability_state"), {"allow", "readonly", "deny", "pending", "coming_soon"})
            self.assertIn(first_cap.get("delivery_level"), {"exclusive", "shared", "placeholder"})
            self.assertIn(first_cap.get("entry_kind"), {"exclusive", "alias"})
        capability_groups = data.get("data", {}).get("capability_groups") or []
        if capability_groups:
            first_group = capability_groups[0]
            self.assertIn("key", first_group)
            self.assertIn("label", first_group)
            self.assertIn("icon", first_group)
            self.assertIn("sequence", first_group)
            self.assertIn("capabilities", first_group)
            self.assertIn("capability_count", first_group)
            self.assertIn("state_counts", first_group)
            self.assertIn("capability_state_counts", first_group)
            self.assertIsInstance(first_group.get("capabilities"), list)
            self.assertIsInstance(first_group.get("state_counts"), dict)
            self.assertIsInstance(first_group.get("capability_state_counts"), dict)
            self.assertEqual(
                int(first_group.get("capability_count") or 0),
                len(first_group.get("capabilities") or []),
            )
        scenes = data.get("data", {}).get("scenes") or []
        self.assertIsInstance(scenes, list)
        if scenes:
            first_scene = scenes[0]
            self.assertIn("scene_meta", first_scene)
            self.assertIn("list_profile", first_scene)
            scene_meta = first_scene.get("scene_meta") or {}
            self.assertIn("purpose", scene_meta)
            self.assertIn("core_action", scene_meta)
            self.assertIn("priority_actions", scene_meta)
            self.assertIn("role_relevance_score", scene_meta)
            list_profile = first_scene.get("list_profile") or {}
            self.assertIn("primary_field", list_profile)
            self.assertIn("status_field", list_profile)
            self.assertIn("urgency_score", list_profile)
            self.assertIn("highlight_rule", list_profile)

    def test_ui_contract_meta_semver_schema(self):
        login_payload = {
            "intent": "login",
            "params": {"login": self.test_login, "password": self.test_password},
        }
        login_data = self._post_intent(
            login_payload,
            headers={"X-Anonymous-Intent": "true"},
            with_db=True,
        )
        login_row = login_data.get("data", {}) or {}
        token = (login_row.get("session") or {}).get("token") or login_row.get("token")
        self.assertTrue(token, login_data)

        payload = {"intent": "ui.contract", "params": {"op": "nav"}}
        data = self._post_intent(payload, headers={"Authorization": f"Bearer {token}"})
        self.assertTrue(data.get("ok"), data)
        meta = data.get("meta") or {}
        self.assertEqual(meta.get("contract_version"), "1.0.0")
        self.assertEqual(meta.get("schema_version"), "1.0.0")
        self.assertTrue(bool(meta.get("payload_schema_version")))

    def test_meta_intent_catalog_intent(self):
        login_payload = {
            "intent": "login",
            "params": {"login": self.test_login, "password": self.test_password},
        }
        login_data = self._post_intent(
            login_payload,
            headers={"X-Anonymous-Intent": "true"},
            with_db=True,
        )
        login_row = login_data.get("data", {}) or {}
        token = (login_row.get("session") or {}).get("token") or login_row.get("token")
        self.assertTrue(token, login_data)

        payload = {"intent": "meta.intent_catalog", "params": {}}
        data = self._post_intent(payload, headers={"Authorization": f"Bearer {token}"})
        self.assertTrue(data.get("ok"), data)
        row = data.get("data", {}) or {}
        intents = row.get("intents") or []
        intents_meta = row.get("intents_meta") or {}
        intent_catalog = row.get("intent_catalog") or []
        self.assertIsInstance(intents, list)
        self.assertIsInstance(intents_meta, dict)
        self.assertIsInstance(intent_catalog, list)
        self.assertIn("system.init", intents)
        self.assertIn("ui.contract", intents)
        self.assertIn("api.data", intents)
        self.assertIn("meta.intent_catalog", intents)
        self.assertIn("meta.intent_catalog", intents_meta)
        self.assertEqual((intents_meta.get("system.init") or {}).get("status"), "canonical")
        self.assertEqual((intents_meta.get("system.init") or {}).get("canonical"), "system.init")

        app_init_alias = None
        for item in intent_catalog:
            if isinstance(item, dict) and str(item.get("name") or "") == "app.init":
                app_init_alias = item
                break
        self.assertIsNotNone(app_init_alias)
        self.assertEqual(str((app_init_alias or {}).get("status") or ""), "alias")
        self.assertEqual(str((app_init_alias or {}).get("canonical") or ""), "system.init")
