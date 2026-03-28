# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "page_orchestration_role_defaults.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("page_orchestration_role_defaults_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
build_default_role_focus_sections = TARGET.build_default_role_focus_sections
build_default_role_section_policy = TARGET.build_default_role_section_policy
build_default_role_zone_order = TARGET.build_default_role_zone_order


class TestPageOrchestrationRoleDefaults(unittest.TestCase):
    def test_build_default_role_section_policy(self):
        payload = build_default_role_section_policy("owner")
        self.assertIn("workbench", payload)

    def test_build_default_role_zone_order(self):
        self.assertEqual(build_default_role_zone_order("finance", "detail", "action")[0], "secondary")

    def test_build_default_role_focus_sections(self):
        self.assertIn("todo_focus", build_default_role_focus_sections("pm", "my_work"))


if __name__ == "__main__":
    unittest.main()
