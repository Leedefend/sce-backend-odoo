# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_delivery_policy_map_helper.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("scene_delivery_policy_map_helper_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
load_surface_policy_map_from_payload = TARGET.load_surface_policy_map_from_payload
normalize_allowlist_values = TARGET.normalize_allowlist_values
resolve_builtin_surface_policy = TARGET.resolve_builtin_surface_policy


class TestSceneDeliveryPolicyMapHelper(unittest.TestCase):
    def test_normalize_allowlist_values(self):
        self.assertEqual(
            normalize_allowlist_values(["workspace.home", " workspace.home ", "", None, "workspace.list"]),
            {"workspace.home", "workspace.list"},
        )

    def test_load_surface_policy_map_from_payload(self):
        payload = {
            "surfaces": {
                "Showcase": {
                    "nav_allowlist": ["workspace.home", ""],
                    "deep_link_allowlist": ["workspace.risk"],
                }
            }
        }
        normalize = lambda value: str(value or "").strip().lower() or "default"
        result = load_surface_policy_map_from_payload(payload, normalize_surface=normalize)
        self.assertEqual(result["showcase"]["nav_allowlist"], {"workspace.home"})
        self.assertEqual(result["showcase"]["deep_link_allowlist"], {"workspace.risk"})

    def test_resolve_builtin_surface_policy(self):
        policy = resolve_builtin_surface_policy(
            "workspace_default_v1",
            nav_allowlist_map={"workspace_default_v1": {"workspace.home", "workspace.list"}},
            deep_link_allowlist_map={"workspace_default_v1": ("workspace.risk",)},
        )
        self.assertTrue(policy["enabled"])
        self.assertEqual(policy["source"], "builtin")
        self.assertEqual(policy["nav_allowlist"], {"workspace.home", "workspace.list"})


if __name__ == "__main__":
    unittest.main()
