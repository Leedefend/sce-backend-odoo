# -*- coding: utf-8 -*-
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_merge_resolver.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scene_merge_resolver_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


resolver_module = _load_module()


class TestSceneMergeResolverSearchpanelSemantics(unittest.TestCase):
    def test_policy_projects_default_searchpanel(self):
        compiled = {
            "search_surface": {},
            "meta": {},
        }
        policies = {
            "search_policy": {
                "default_searchpanel": [{"name": "stage_id", "label": "阶段"}],
            }
        }

        out = resolver_module.apply_policy(compiled, policies, {"role_code": "pm"})

        self.assertEqual(((out.get("search_surface") or {}).get("searchpanel") or [])[0]["name"], "stage_id")

    def test_provider_conflict_tracks_searchpanel_override(self):
        compiled = {
            "search_surface": {
                "searchpanel": [{"name": "stage_id", "label": "阶段"}],
            },
            "meta": {},
        }
        ctx = resolver_module.MergeContext(scene_key="projects.list", runtime={"role_code": "pm"}, provider_registry={})
        providers = [
            {
                "key": "inline",
                "payload": {
                    "search_surface": {
                        "searchpanel": [{"name": "manager_id", "label": "负责人"}],
                    }
                },
            }
        ]

        out = resolver_module.apply_provider_merge(compiled, providers, ctx)

        self.assertEqual(((out.get("search_surface") or {}).get("searchpanel") or [])[0]["name"], "manager_id")
        conflicts = (((out.get("meta") or {}).get("merge_resolver") or {}).get("conflicts") or [])
        self.assertEqual(conflicts[0]["field"], "search_surface.searchpanel")


if __name__ == "__main__":
    unittest.main()
