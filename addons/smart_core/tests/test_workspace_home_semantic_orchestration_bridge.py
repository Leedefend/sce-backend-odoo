# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "workspace_home_semantic_orchestration_bridge.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("workspace_home_semantic_orchestration_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()


class TestWorkspaceHomeSemanticOrchestrationBridge(unittest.TestCase):
    def test_bridge_projects_tree_semantics_into_list_layout_and_actions(self):
        payload = TARGET.apply_workspace_home_semantic_orchestration_bridge(
            {
                "page_orchestration_v1": {
                    "page": {
                        "layout_mode": "dashboard",
                        "global_actions": [{"key": "refresh", "label": "刷新", "intent": "api.data"}],
                    },
                    "render_hints": {"preferred_columns": 4},
                    "meta": {
                        "parser_semantic_surface": {
                            "parser_contract": {"view_type": "tree"},
                            "view_semantics": {"source_view": "tree"},
                            "native_view": {
                                "views": {
                                    "search": {
                                        "filters": [{"name": "mine", "string": "我的"}],
                                        "group_bys": [{"name": "by_stage", "string": "按阶段", "group_by": "stage_id"}],
                                    }
                                }
                            },
                            "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
                        }
                    },
                }
            }
        )

        page = (payload.get("page_orchestration_v1") or {}).get("page") or {}
        render_hints = (payload.get("page_orchestration_v1") or {}).get("render_hints") or {}

        self.assertEqual(page.get("layout_mode"), "list_flow")
        self.assertEqual(page.get("priority_model"), "task_first")
        self.assertEqual(render_hints.get("preferred_columns"), 2)
        self.assertEqual(render_hints.get("semantic_page_type"), "list")
        self.assertEqual([row.get("key") for row in (page.get("global_actions") or [])], ["apply_filters", "reset_filters", "refresh"])


if __name__ == "__main__":
    unittest.main()
