# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "page_orchestration_zone_defaults.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("page_orchestration_zone_defaults_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
build_default_block_title = TARGET.build_default_block_title
build_default_zone_for_section = TARGET.build_default_zone_for_section
build_default_zone_from_tag = TARGET.build_default_zone_from_tag


class TestPageOrchestrationZoneDefaults(unittest.TestCase):
    def test_build_default_zone_from_tag(self):
        self.assertEqual(build_default_zone_from_tag("header")["key"], "hero")
        self.assertEqual(build_default_zone_from_tag("div")["key"], "secondary")

    def test_build_default_zone_for_section(self):
        payload = build_default_zone_for_section("my_work", "todo_focus", "section")
        self.assertEqual(payload["key"], "primary")
        self.assertEqual(payload["title"], "待处理事项")

    def test_build_default_block_title(self):
        self.assertEqual(build_default_block_title("my_work", "list_main"), "事项清单")
        self.assertEqual(build_default_block_title("home", "hero"), "hero")


if __name__ == "__main__":
    unittest.main()
