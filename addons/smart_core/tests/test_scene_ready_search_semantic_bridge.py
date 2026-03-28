# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_ready_search_semantic_bridge.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scene_ready_search_semantic_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bridge_module = _load_module()


class TestSceneReadySearchSemanticBridge(unittest.TestCase):
    def test_bridge_backfills_search_surface_from_native_search_view(self):
        payload = {
            "search_surface": {"default_sort": "write_date desc"},
            "parser_semantic_surface": {
                "native_view": {
                    "views": {
                        "search": {
                            "fields": [{"name": "name"}],
                            "filters": [{"name": "mine", "string": "我的"}],
                            "group_bys": [{"name": "by_stage", "string": "按阶段", "group_by": "stage_id"}],
                            "searchpanel": [{"name": "stage_id", "string": "阶段"}],
                        }
                    }
                }
            },
        }

        bridged = bridge_module.apply_scene_ready_search_semantic_bridge(payload)

        self.assertEqual(((bridged.get("search_surface") or {}).get("fields") or [])[0]["name"], "name")
        self.assertEqual(((bridged.get("search_surface") or {}).get("filters") or [])[0]["name"], "mine")
        self.assertEqual(((bridged.get("search_surface") or {}).get("group_by") or [])[0]["field"], "stage_id")
        self.assertEqual(((bridged.get("search_surface") or {}).get("searchpanel") or [])[0]["name"], "stage_id")


if __name__ == "__main__":
    unittest.main()
