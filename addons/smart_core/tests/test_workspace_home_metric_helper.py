# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "workspace_home_metric_helper.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("workspace_home_metric_helper_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
build_metric_sets = TARGET.build_metric_sets


def _metric_level(value, amber, red):
    if value >= red:
        return "red"
    if value >= amber:
        return "amber"
    return "green"


def _tone(level):
    return {"green": "success", "amber": "warning", "red": "danger"}.get(level, "info")


class TestWorkspaceHomeMetricHelper(unittest.TestCase):
    def test_build_metric_sets_keeps_business_and_platform_sections(self):
        business, platform = build_metric_sets(
            ready_count=5,
            locked_count=1,
            preview_count=2,
            scene_count=8,
            today_action_count=4,
            risk_action_count=1,
            metric_level_resolver=_metric_level,
            tone_from_level_resolver=_tone,
        )

        self.assertEqual(len(business), 4)
        self.assertEqual(len(platform), 4)
        self.assertEqual(business[0]["key"], "biz.today_actions")
        self.assertEqual(platform[0]["key"], "platform.ready_caps")


if __name__ == "__main__":
    unittest.main()
