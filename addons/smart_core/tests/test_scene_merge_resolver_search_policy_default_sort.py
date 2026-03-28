# -*- coding: utf-8 -*-
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_merge_resolver.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scene_merge_resolver_policy_sort_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


resolver_module = _load_module()


class TestSceneMergeResolverSearchPolicyDefaultSort(unittest.TestCase):
    def test_policy_projects_default_sort(self):
        compiled = {
            "search_surface": {
                "default_sort": "name asc",
            },
            "meta": {},
        }
        policies = {
            "search_policy": {
                "default_sort": "priority desc",
            }
        }

        out = resolver_module.apply_policy(compiled, policies, {"role_code": "pm"})

        self.assertEqual(((out.get("search_surface") or {}).get("default_sort")), "priority desc")
        conflicts = (((out.get("meta") or {}).get("merge_resolver") or {}).get("conflicts") or [])
        self.assertEqual(conflicts[0]["field"], "search_surface.default_sort")


if __name__ == "__main__":
    unittest.main()
