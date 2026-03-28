# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "page_orchestration_defaults.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("page_orchestration_defaults_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
build_default_page_actions = TARGET.build_default_page_actions
build_default_page_audience = TARGET.build_default_page_audience
build_default_page_type = TARGET.build_default_page_type


class TestPageOrchestrationDefaults(unittest.TestCase):
    def test_build_default_page_type(self):
        self.assertEqual(build_default_page_type("home"), "workspace")
        self.assertEqual(build_default_page_type("action"), "detail")

    def test_build_default_page_audience(self):
        self.assertIn("internal_user", build_default_page_audience("home"))
        self.assertIn("reviewer", build_default_page_audience("my_work"))

    def test_build_default_page_actions(self):
        self.assertEqual(build_default_page_actions("my_work")[0]["key"], "refresh_page")
        self.assertEqual(build_default_page_actions("home")[0]["key"], "open_my_work")


if __name__ == "__main__":
    unittest.main()
