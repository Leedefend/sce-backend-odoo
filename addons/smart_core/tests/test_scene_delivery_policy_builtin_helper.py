# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_delivery_policy_builtin_helper.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("scene_delivery_policy_builtin_helper_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
resolve_builtin_surface_deep_link_allowlist = TARGET.resolve_builtin_surface_deep_link_allowlist
resolve_builtin_surface_nav_allowlist = TARGET.resolve_builtin_surface_nav_allowlist
resolve_surface_policy_default_name = TARGET.resolve_surface_policy_default_name


class TestSceneDeliveryPolicyBuiltinHelper(unittest.TestCase):
    def test_resolve_builtin_surface_nav_allowlist(self):
        hook = lambda env, name, *_: {"demo": {"workspace.home"}} if name == "smart_core_surface_nav_allowlist" else None
        self.assertEqual(
            resolve_builtin_surface_nav_allowlist(None, hook=hook, default_map={"default": {"workspace.list"}}),
            {"demo": {"workspace.home"}},
        )

    def test_resolve_builtin_surface_deep_link_allowlist(self):
        hook = lambda env, name, *_: {"demo": ("workspace.risk",)} if name == "smart_core_surface_deep_link_allowlist" else None
        self.assertEqual(
            resolve_builtin_surface_deep_link_allowlist(None, hook=hook, default_map={"default": ("workspace.list",)}),
            {"demo": ("workspace.risk",)},
        )

    def test_resolve_surface_policy_default_name(self):
        hook = lambda env, name, *_: "showcase" if name == "smart_core_surface_policy_default_name" else None
        self.assertEqual(resolve_surface_policy_default_name(None, hook=hook, default_name="workspace_default_v1"), "showcase")
        self.assertEqual(resolve_surface_policy_default_name(None, hook=lambda *args: "", default_name="workspace_default_v1"), "workspace_default_v1")


if __name__ == "__main__":
    unittest.main()
