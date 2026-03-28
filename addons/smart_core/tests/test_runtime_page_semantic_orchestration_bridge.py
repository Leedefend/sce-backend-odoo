# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "runtime_page_semantic_orchestration_bridge.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("runtime_page_semantic_orchestration_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bridge_module = _load_module()


class TestRuntimePageSemanticOrchestrationBridge(unittest.TestCase):
    def test_bridge_projects_runtime_filters_and_mode(self):
        payload = {
            "runtime_context": {},
            "runtime_semantic_surface": {
                "parser_contract": {"view_type": "tree"},
                "view_semantics": {"source_view": "tree"},
                "native_view": {
                    "views": {
                        "search": {
                            "filters": [{"name": "mine", "string": "我的"}],
                            "group_bys": [{"name": "by_stage", "string": "按阶段", "group_by": "stage_id"}],
                            "searchpanel": [{"name": "stage_id", "string": "阶段"}],
                        }
                    }
                },
                "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
            },
            "page_orchestration_v1": {"page": {"filters": []}, "render_hints": {}},
        }

        bridged = bridge_module.apply_runtime_page_semantic_orchestration_bridge(payload)

        self.assertEqual((bridged.get("runtime_context") or {}).get("runtime_mode"), "list_focus")
        self.assertEqual((bridged.get("runtime_context") or {}).get("search_mode"), "faceted")
        self.assertEqual((((bridged.get("page_orchestration_v1") or {}).get("render_hints") or {}).get("runtime_preferred_columns")), 2)
        self.assertEqual((((bridged.get("page_orchestration_v1") or {}).get("render_hints") or {}).get("runtime_search_profile")), "faceted")
        self.assertEqual(((((bridged.get("page_orchestration_v1") or {}).get("page") or {}).get("filters")) or [])[0]["kind"], "filter")
        self.assertEqual(((((bridged.get("page_orchestration_v1") or {}).get("page") or {}).get("filters")) or [])[2]["kind"], "searchpanel")
        self.assertEqual(
            [row.get("key") for row in ((((bridged.get("page_orchestration_v1") or {}).get("page") or {}).get("global_actions")) or [])],
            ["apply_filters", "reset_filters"],
        )

    def test_bridge_projects_runtime_actions_from_searchpanel_only(self):
        payload = {
            "runtime_context": {},
            "runtime_semantic_surface": {
                "parser_contract": {"view_type": "search"},
                "view_semantics": {"source_view": "search"},
                "native_view": {
                    "views": {
                        "search": {
                            "searchpanel": [{"name": "stage_id", "string": "阶段"}],
                        }
                    }
                },
                "semantic_page": {},
            },
            "page_orchestration_v1": {"page": {"filters": []}, "render_hints": {}},
        }

        bridged = bridge_module.apply_runtime_page_semantic_orchestration_bridge(payload)

        self.assertEqual((bridged.get("runtime_context") or {}).get("search_mode"), "faceted")
        self.assertEqual(((((bridged.get("page_orchestration_v1") or {}).get("page") or {}).get("filters")) or [])[0]["kind"], "searchpanel")
        self.assertEqual(
            [row.get("key") for row in ((((bridged.get("page_orchestration_v1") or {}).get("page") or {}).get("global_actions")) or [])],
            ["apply_filters", "reset_filters"],
        )


if __name__ == "__main__":
    unittest.main()
