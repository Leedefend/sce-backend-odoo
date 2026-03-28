# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "page_orchestration_action_defaults.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("page_orchestration_action_defaults_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
build_default_action_templates = TARGET.build_default_action_templates
build_default_action_templates_for_page = TARGET.build_default_action_templates_for_page


class TestPageOrchestrationActionDefaults(unittest.TestCase):
    def test_build_default_action_templates(self):
        self.assertEqual(build_default_action_templates("risk_table")[0]["key"], "open_workspace_overview")
        self.assertEqual(build_default_action_templates("todo_focus")[0]["key"], "open_my_work")

    def test_build_default_action_templates_for_page(self):
        self.assertEqual(build_default_action_templates_for_page("my_work", "todo_focus")[0]["key"], "open_list")
        self.assertEqual(build_default_action_templates_for_page("my_work", "hero"), [])


if __name__ == "__main__":
    unittest.main()
