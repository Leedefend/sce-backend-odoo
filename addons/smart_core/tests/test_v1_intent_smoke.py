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
            "params": {"login": self.test_login, "password": self.test_password},
        }
        data = self._post_intent(
            payload,
            headers={"X-Anonymous-Intent": "true"},
            with_db=True,
        )
        self.assertTrue(data.get("ok"), data)
        self.assertTrue(data.get("data", {}).get("token"), data)

    def test_anon_login_intent_without_db_query_param(self):
        payload = {
            "intent": "login",
            "params": {"login": self.test_login, "password": self.test_password},
        }
        data = self._post_intent(
            payload,
            headers={"X-Anonymous-Intent": "true"},
            with_db=False,
        )
        self.assertTrue(data.get("ok"), data)
        self.assertTrue(data.get("data", {}).get("token"), data)

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
        token = login_data.get("data", {}).get("token")
        self.assertTrue(token, login_data)

        payload = {"intent": "system.init", "params": {}}
        data = self._post_intent(payload, headers={"Authorization": f"Bearer {token}"})
        self.assertTrue(data.get("ok"), data)
        self.assertIn("user", data.get("data", {}))
        self.assertIn("nav", data.get("data", {}))
        self.assertIn("intents", data.get("data", {}))
