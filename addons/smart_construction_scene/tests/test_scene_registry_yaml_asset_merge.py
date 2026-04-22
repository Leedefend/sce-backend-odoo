# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scene_registry.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scene_registry_yaml_asset_merge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestSceneRegistryYamlAssetMerge(unittest.TestCase):
    def test_load_scene_configs_merges_yaml_asset_fields_into_registry_row(self):
        target = _load_module()
        original_load_from_db = target._load_from_db
        original_load_imported = target._load_imported_scenes
        original_load_content = target._load_scene_registry_content_entries_with_timings
        try:
            target._load_from_db = lambda env, drift=None: []
            target._load_imported_scenes = lambda env, drift=None: []
            target._load_scene_registry_content_entries_with_timings = lambda: (
                [
                    {
                        "code": "projects.ledger",
                        "name": "项目台账",
                        "target": {
                            "route": "/s/projects.ledger",
                            "menu_xmlid": "smart_construction_core.menu_sc_project_project",
                            "action_xmlid": "smart_construction_core.action_sc_project_kanban_lifecycle",
                        },
                    }
                ],
                {},
            )
            rows, _timings = target.load_scene_configs_with_timings(None)
        finally:
            target._load_from_db = original_load_from_db
            target._load_imported_scenes = original_load_imported
            target._load_scene_registry_content_entries_with_timings = original_load_content

        ledger = next((row for row in rows if row.get("code") == "projects.ledger"), {})
        self.assertEqual(((ledger.get("target") or {}).get("route")), "/s/projects.ledger")
        self.assertEqual(((ledger.get("page") or {}).get("route")), "/s/projects.ledger")
        self.assertEqual([zone.get("name") for zone in (ledger.get("zones") or [])], ["header", "search", "main"])
        self.assertEqual(((ledger.get("blocks") or [])[0] or {}).get("source"), "ui_base_contract.views.tree")
        self.assertEqual(((ledger.get("search_surface") or {}).get("source")), "ui_base_contract.search")
        self.assertEqual(((ledger.get("permission_surface") or {}).get("source")), "ui_base_contract.permissions")

    def test_load_scene_configs_merges_cost_project_budget_yaml_asset_fields(self):
        target = _load_module()
        original_load_from_db = target._load_from_db
        original_load_imported = target._load_imported_scenes
        original_load_content = target._load_scene_registry_content_entries_with_timings
        try:
            target._load_from_db = lambda env, drift=None: []
            target._load_imported_scenes = lambda env, drift=None: []
            target._load_scene_registry_content_entries_with_timings = lambda: (
                [
                    {
                        "code": "cost.project_budget",
                        "name": "预算管理",
                        "target": {
                            "route": "/s/cost.project_budget",
                        },
                    }
                ],
                {},
            )
            rows, _timings = target.load_scene_configs_with_timings(None)
        finally:
            target._load_from_db = original_load_from_db
            target._load_imported_scenes = original_load_imported
            target._load_scene_registry_content_entries_with_timings = original_load_content

        budget = next((row for row in rows if row.get("code") == "cost.project_budget"), {})
        self.assertEqual(((budget.get("target") or {}).get("route")), "/s/cost.project_budget")
        self.assertEqual(((budget.get("page") or {}).get("route")), "/s/cost.project_budget")
        self.assertEqual([zone.get("name") for zone in (budget.get("zones") or [])], ["header", "search", "main"])
        self.assertEqual(((budget.get("blocks") or [])[0] or {}).get("source"), "ui_base_contract.views.tree")
        self.assertEqual(((budget.get("search_surface") or {}).get("source")), "ui_base_contract.search")
        self.assertEqual(((budget.get("permission_surface") or {}).get("source")), "ui_base_contract.permissions")


if __name__ == "__main__":
    unittest.main()
