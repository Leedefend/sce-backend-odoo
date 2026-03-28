# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "page_contract_semantic_orchestration_bridge.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("page_contract_semantic_orchestration_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bridge_module = _load_module()


class TestPageContractSemanticOrchestrationBridge(unittest.TestCase):
    def test_bridge_projects_form_semantics_into_detail_page_type(self):
        payload = {
            "page": {"page_type": "approval", "layout_mode": "single_flow", "priority_model": "task_first"},
            "render_hints": {},
            "meta": {
                "parser_semantic_surface": {
                    "parser_contract": {"view_type": "form"},
                    "view_semantics": {"source_view": "form"},
                    "semantic_page": {"title_node": {"text": "详情"}},
                }
            },
        }

        bridged = bridge_module.apply_page_contract_semantic_orchestration_bridge(payload)

        self.assertEqual((bridged.get("page") or {}).get("page_type"), "detail")
        self.assertEqual((bridged.get("page") or {}).get("layout_mode"), "detail_focus")
        self.assertEqual((bridged.get("render_hints") or {}).get("semantic_page_type"), "detail")

    def test_bridge_projects_tree_semantics_into_list_page_type(self):
        payload = {
            "page": {
                "page_type": "workspace",
                "layout_mode": "single_flow",
                "priority_model": "role_first",
                "global_actions": [{"key": "open_default", "label": "默认动作", "intent": "ui.contract"}],
            },
            "render_hints": {},
            "meta": {
                "parser_semantic_surface": {
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
                }
            },
        }

        bridged = bridge_module.apply_page_contract_semantic_orchestration_bridge(payload)

        self.assertEqual((bridged.get("page") or {}).get("page_type"), "list")
        self.assertEqual((bridged.get("page") or {}).get("layout_mode"), "list_flow")
        self.assertEqual((bridged.get("page") or {}).get("priority_model"), "task_first")
        self.assertEqual((bridged.get("render_hints") or {}).get("preferred_columns"), 2)
        self.assertEqual(((bridged.get("page") or {}).get("filters") or [])[0]["kind"], "filter")
        self.assertEqual([row.get("key") for row in ((bridged.get("page") or {}).get("global_actions") or [])], ["apply_filters", "reset_filters"])


if __name__ == "__main__":
    unittest.main()
