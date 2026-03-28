# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_delivery_surface_defaults.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("scene_delivery_surface_defaults_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
coerce_surface_input = TARGET.coerce_surface_input
is_demo_surface = TARGET.is_demo_surface
is_internal_surface = TARGET.is_internal_surface
normalize_surface = TARGET.normalize_surface
normalize_surfaces = TARGET.normalize_surfaces
to_bool = TARGET.to_bool


class TestSceneDeliverySurfaceDefaults(unittest.TestCase):
    def test_to_bool(self):
        self.assertTrue(to_bool("true"))
        self.assertFalse(to_bool("false", default=True))
        self.assertTrue(to_bool(None, default=True))

    def test_surface_normalization_and_coercion(self):
        self.assertEqual(normalize_surface(" Demo "), "demo")
        self.assertEqual(coerce_surface_input("null"), "")
        self.assertEqual(coerce_surface_input("workspace_default_v1"), "workspace_default_v1")

    def test_surface_classifiers_and_list_normalization(self):
        self.assertTrue(is_internal_surface("debug"))
        self.assertTrue(is_demo_surface("showcase"))
        self.assertEqual(normalize_surfaces(["demo", " Demo ", "internal"]), ["demo", "internal"])


if __name__ == "__main__":
    unittest.main()
