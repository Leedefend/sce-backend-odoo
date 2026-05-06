# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


def _load_policy():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "core" / "http_result_policy.py"
    spec = importlib.util.spec_from_file_location("http_result_policy_test_module", module_path)
    module = importlib.util.module_from_spec(spec)
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


if __name__ == "__main__":
    unittest.main()
