# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


def _load_policy():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "core" / "intent_access_policy.py"
    spec = importlib.util.spec_from_file_location("intent_access_policy_test_module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestIntentAccessPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = _load_policy()

    def test_anonymous_allowlist_is_explicit(self):
        self.assertTrue(self.policy.is_anonymous_allowed_intent("login"))
        self.assertTrue(self.policy.is_anonymous_allowed_intent("session.bootstrap"))
        self.assertFalse(self.policy.is_anonymous_allowed_intent("system.init"))

    def test_bootstrap_alias_is_public_context_only(self):
        self.assertTrue(self.policy.is_public_context_intent("bootstrap"))
        self.assertFalse(self.policy.is_anonymous_allowed_intent("bootstrap"))

    def test_permission_check_keeps_public_context_gate_behavior(self):
        self.assertTrue(self.policy.is_public_context_intent("permission.check"))
        self.assertFalse(self.policy.is_anonymous_allowed_intent("permission.check"))


if __name__ == "__main__":
    unittest.main()
