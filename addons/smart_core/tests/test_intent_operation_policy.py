# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


def _load_policy():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "core" / "intent_operation_policy.py"
    spec = importlib.util.spec_from_file_location("intent_operation_policy_test_module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestIntentOperationPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = _load_policy()

    def test_api_data_read_stays_read(self):
        self.assertEqual(self.policy.access_mode_for_intent("api.data", {"op": "list"}), "read")
        self.assertFalse(self.policy.is_write_intent("api.data", {"op": "list"}))

    def test_api_data_mutations_are_write_intents(self):
        self.assertEqual(self.policy.access_mode_for_intent("api.data.create", {}), "create")
        self.assertEqual(self.policy.access_mode_for_intent("api.data.write", {}), "write")
        self.assertEqual(self.policy.access_mode_for_intent("api.data.unlink", {}), "unlink")
        self.assertTrue(self.policy.is_write_intent("api.data", {"op": "batch"}))

    def test_nested_params_are_supported(self):
        params = {"params": {"op": "write"}}
        self.assertEqual(self.policy.access_mode_for_intent("api.data", params), "write")
        self.assertTrue(self.policy.is_write_intent("api.data", params))

    def test_batch_actions_map_to_record_write_or_unlink_modes(self):
        self.assertEqual(self.policy.access_mode_for_intent("api.data.batch", {"action": "archive"}), "write")
        self.assertEqual(self.policy.access_mode_for_intent("api.data.batch", {"action": "delete"}), "unlink")

    def test_non_api_write_verbs_are_write_intents(self):
        self.assertTrue(self.policy.is_write_intent("execute_button", {}))
        self.assertEqual(self.policy.access_mode_for_intent("execute_button", {}), "write")
        self.assertTrue(self.policy.is_write_intent("ui.business_config.contract.save", {}))
        self.assertTrue(self.policy.is_write_intent("ui.business_config.contract.publish", {}))

    def test_write_detection_uses_intent_tokens_not_substrings(self):
        self.assertFalse(self.policy.is_write_intent("settlement.enter", {}))
        self.assertEqual(self.policy.access_mode_for_intent("settlement.block.fetch", {}), "read")


if __name__ == "__main__":
    unittest.main()
