# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "workspace_home_capability_helper.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("workspace_home_capability_helper_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
capability_state = TARGET.capability_state
is_urgent_capability = TARGET.is_urgent_capability
metric_level = TARGET.metric_level


class TestWorkspaceHomeCapabilityHelper(unittest.TestCase):
    def test_capability_state_prefers_explicit_state(self):
        self.assertEqual(capability_state({"state": "READY"}), "READY")
        self.assertEqual(capability_state({"state": "LOCKED"}), "LOCKED")

    def test_capability_state_maps_capability_state_values(self):
        self.assertEqual(capability_state({"capability_state": "allow"}), "READY")
        self.assertEqual(capability_state({"capability_state": "deny"}), "LOCKED")
        self.assertEqual(capability_state({"capability_state": "coming_soon"}), "PREVIEW")

    def test_metric_level_applies_thresholds(self):
        self.assertEqual(metric_level(1, 3, 6), "green")
        self.assertEqual(metric_level(3, 3, 6), "amber")
        self.assertEqual(metric_level(6, 3, 6), "red")

    def test_is_urgent_capability_matches_risk_keywords(self):
        self.assertTrue(is_urgent_capability("风险跟进", "workspace.risk"))
        self.assertTrue(is_urgent_capability("Approval Queue", "workspace.approval"))
        self.assertFalse(is_urgent_capability("Overview", "workspace.home"))


if __name__ == "__main__":
    unittest.main()
