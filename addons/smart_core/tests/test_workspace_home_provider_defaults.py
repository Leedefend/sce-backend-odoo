# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "workspace_home_provider_defaults.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("workspace_home_provider_defaults_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
build_default_advice_items = TARGET.build_default_advice_items
build_default_role_focus_config = TARGET.build_default_role_focus_config
build_default_v1_data_sources = TARGET.build_default_v1_data_sources
build_default_v1_focus_map = TARGET.build_default_v1_focus_map
build_default_v1_page_profile = TARGET.build_default_v1_page_profile
build_default_v1_state_schema = TARGET.build_default_v1_state_schema


class TestWorkspaceHomeProviderDefaults(unittest.TestCase):
    def test_build_default_role_focus_config(self):
        payload = build_default_role_focus_config()
        self.assertIn("zone_order", payload)
        self.assertIn("focus_blocks", payload)

    def test_build_default_v1_focus_map(self):
        payload = build_default_v1_focus_map()
        self.assertIn("pm", payload)
        self.assertIn("owner", payload)

    def test_build_default_v1_page_profile(self):
        payload = build_default_v1_page_profile("finance")
        self.assertEqual(payload["priority_model"], "metric_first")

    def test_build_default_v1_data_sources_and_state_schema(self):
        self.assertIn("ds_hero", build_default_v1_data_sources())
        self.assertIn("pending", build_default_v1_state_schema())

    def test_build_default_advice_items(self):
        payload = build_default_advice_items()
        self.assertEqual(payload[0]["id"], "stable")


if __name__ == "__main__":
    unittest.main()
