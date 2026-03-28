# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "page_orchestration_data_source_defaults.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("page_orchestration_data_source_defaults_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
build_base_data_sources = TARGET.build_base_data_sources
build_section_data_source = TARGET.build_section_data_source
build_section_data_source_key = TARGET.build_section_data_source_key


class TestPageOrchestrationDataSourceDefaults(unittest.TestCase):
    def test_build_section_data_source_key(self):
        self.assertEqual(build_section_data_source_key("Risk Panel"), "ds_section_risk_panel")
        self.assertEqual(build_section_data_source_key(""), "ds_section_section")

    def test_build_base_data_sources(self):
        self.assertIn("ds_sections", build_base_data_sources())

    def test_build_section_data_source(self):
        payload = build_section_data_source("my_work", "todo_focus", "Section")
        self.assertEqual(payload["page_key"], "my_work")
        self.assertEqual(payload["section_tag"], "section")


if __name__ == "__main__":
    unittest.main()
