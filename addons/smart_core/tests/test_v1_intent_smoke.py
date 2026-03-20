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
        self.assertIn("bootstrap", row)
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
        self.assertIn("user", data.get("data", {}))
        self.assertIn("nav", data.get("data", {}))
        self.assertIn("intents", data.get("data", {}))
        self.assertIn("capabilities", data.get("data", {}))
        self.assertIn("capability_groups", data.get("data", {}))
        self.assertIn("init_contract_v1", data.get("data", {}))
        init_contract = data.get("data", {}).get("init_contract_v1") or {}
        self.assertIn("session", init_contract)
        self.assertIn("nav", init_contract)
        self.assertIn("surface", init_contract)
        self.assertIn("bootstrap_refs", init_contract)
        row = data.get("data", {}) or {}
        role_surface = row.get("role_surface") or {}
        role_surface_code = str(role_surface.get("role_code") or "").strip().lower()
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

        self.assertIsInstance(data.get("data", {}).get("capability_groups"), list)
        capabilities = data.get("data", {}).get("capabilities") or []
        self.assertIsInstance(capabilities, list)
        if capabilities:
            first_cap = capabilities[0]
            self.assertIn("capability_state", first_cap)
            self.assertIn("capability_state_reason", first_cap)
            self.assertIn(first_cap.get("capability_state"), {"allow", "readonly", "deny", "pending", "coming_soon"})
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
