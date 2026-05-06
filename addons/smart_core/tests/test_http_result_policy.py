# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _load_policy():
    root = Path(__file__).resolve().parents[1]
    addons_mod = types.ModuleType("odoo.addons")
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    core_mod = types.ModuleType("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    core_mod.__path__ = [str(root / "core")]
    sys.modules.update(
        {
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.core": core_mod,
        }
    )
    policy_name = "odoo.addons.smart_core.core.intent_operation_policy"
    sys.modules.pop(policy_name, None)
    policy_spec = importlib.util.spec_from_file_location(policy_name, root / "core" / "intent_operation_policy.py")
    policy_module = importlib.util.module_from_spec(policy_spec)
    sys.modules[policy_name] = policy_module
    policy_spec.loader.exec_module(policy_module)

    module_name = "odoo.addons.smart_core.core.http_result_policy"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "core" / "http_result_policy.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestHttpResultPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = _load_policy()

    def test_valid_int_or_string_status_is_preserved(self):
        self.assertEqual(self.policy.result_http_status({"code": 201}), 201)
        self.assertEqual(self.policy.result_http_status({"code": "404"}), 404)

    def test_invalid_success_status_falls_back_to_default(self):
        self.assertEqual(self.policy.result_http_status({"ok": True, "code": "bad"}), 200)
        self.assertEqual(self.policy.result_http_status({"ok": True, "code": 999}), 200)

    def test_invalid_error_status_becomes_internal_error(self):
        self.assertEqual(self.policy.result_http_status({"ok": False, "code": "bad"}), 500)
        self.assertEqual(self.policy.result_http_status({"ok": False, "code": 0}), 500)

    def test_error_status_can_come_from_nested_error_code(self):
        self.assertEqual(
            self.policy.result_http_status({"ok": False, "error": {"code": 404, "message": "missing"}}),
            404,
        )
        self.assertEqual(
            self.policy.result_http_status({"ok": False, "error": {"code": "PERMISSION_DENIED", "message": "denied"}}),
            200,
        )

    def test_success_flag_normalizes_common_false_values(self):
        self.assertFalse(self.policy.result_is_success({"ok": "false"}))
        self.assertFalse(self.policy.result_is_success({"ok": "0"}))
        self.assertFalse(self.policy.result_is_success({"ok": 0}))
        self.assertTrue(self.policy.result_is_success({"ok": "true"}))
        self.assertTrue(self.policy.result_is_success({}))

    def test_invalid_string_false_status_becomes_internal_error(self):
        self.assertEqual(self.policy.result_http_status({"ok": "false", "code": "bad"}), 500)

    def test_normalize_result_ok_rewrites_string_flags_to_booleans(self):
        payload = {"ok": "false"}
        self.policy.normalize_result_ok(payload)
        self.assertIs(payload["ok"], False)

        payload = {"ok": "true"}
        self.policy.normalize_result_ok(payload)
        self.assertIs(payload["ok"], True)

    def test_write_transaction_action_commits_only_successful_writes(self):
        self.assertEqual(
            self.policy.result_transaction_action("api.data.write", {"model": "x.model"}, {"ok": True}, 200),
            "commit",
        )
        self.assertEqual(
            self.policy.result_transaction_action("api.data.write", {"model": "x.model"}, {"ok": False}, 400),
            "rollback",
        )
        self.assertEqual(
            self.policy.result_transaction_action("api.data.write", {"model": "x.model"}, {"ok": "false"}, 200),
            "rollback",
        )

    def test_read_transaction_action_does_not_touch_cursor(self):
        self.assertEqual(
            self.policy.result_transaction_action("api.data", {"op": "list", "model": "x.model"}, {"ok": True}, 200),
            "none",
        )


if __name__ == "__main__":
    unittest.main()
