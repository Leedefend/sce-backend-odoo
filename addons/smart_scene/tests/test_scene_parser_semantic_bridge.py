# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_parser_semantic_bridge.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scene_parser_semantic_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bridge_module = _load_module()


class TestSceneParserSemanticBridge(unittest.TestCase):
    def test_bridge_projects_parser_surface_into_scene_contract(self):
        contract = {"page": {}, "diagnostics": {}, "scene_contract_v1": {"page": {}, "diagnostics": {}}}
        bridged = bridge_module.apply_scene_parser_semantic_bridge(
            contract,
            {
                "parser_contract": {"view_type": "form"},
                "view_semantics": {"source_view": "form", "capability_flags": {"is_editable": True}},
                "native_view": {"views": {"form": {"layout": []}}},
                "semantic_page": {"title_node": {"text": "工单"}},
            },
        )

        self.assertEqual((((bridged.get("page") or {}).get("surface") or {}).get("view_type")), "form")
        self.assertIn("parser_semantic_surface", bridged.get("diagnostics") or {})
        view_type = (((bridged.get("scene_contract_v1") or {}).get("page") or {}).get("surface") or {}).get("view_type")
        self.assertEqual(view_type, "form")

    def test_bridge_projects_runtime_state_into_diagnostics(self):
        contract = {"page": {}, "diagnostics": {}, "scene_contract_v1": {"page": {}, "diagnostics": {}}}
        bridged = bridge_module.apply_scene_parser_semantic_bridge(
            contract,
            {
                "semantic_runtime_state": {
                    "page_status": "ready",
                    "current_state": "draft",
                },
                "consumer_runtime": {
                    "page_status": "ready",
                    "runtime_page_status": "ready",
                },
            },
        )

        self.assertEqual(
            (((bridged.get("diagnostics") or {}).get("semantic_runtime_state")) or {}).get("page_status"),
            "ready",
        )
        self.assertEqual(
            ((((bridged.get("diagnostics") or {}).get("parser_semantic_surface")) or {}).get("semantic_runtime_state") or {}).get("current_state"),
            "draft",
        )
        self.assertEqual(
            (((bridged.get("scene_contract_v1") or {}).get("diagnostics") or {}).get("semantic_runtime_state") or {}).get("page_status"),
            "ready",
        )
        self.assertEqual(
            (((bridged.get("diagnostics") or {}).get("consumer_runtime")) or {}).get("runtime_page_status"),
            "ready",
        )
        self.assertEqual(
            ((((bridged.get("diagnostics") or {}).get("parser_semantic_surface")) or {}).get("consumer_runtime") or {}).get("page_status"),
            "ready",
        )
        self.assertEqual(
            (((bridged.get("scene_contract_v1") or {}).get("diagnostics") or {}).get("consumer_runtime") or {}).get("page_status"),
            "ready",
        )

    def test_bridge_backfills_consumer_runtime_from_contract_diagnostics(self):
        contract = {
            "page": {},
            "diagnostics": {
                "consumer_semantics": {
                    "runtime": {
                        "page_status": "readonly",
                        "runtime_page_status": "readonly",
                        "current_state": "done",
                        "alignment": {"page_status_aligned": True},
                    }
                }
            },
            "scene_contract_v1": {"page": {}, "diagnostics": {}},
        }
        bridged = bridge_module.apply_scene_parser_semantic_bridge(
            contract,
            {
                "semantic_runtime_state": {
                    "page_status": "readonly",
                    "current_state": "done",
                },
            },
        )

        self.assertEqual(
            (((bridged.get("diagnostics") or {}).get("consumer_runtime")) or {}).get("runtime_page_status"),
            "readonly",
        )
        self.assertEqual(
            ((((bridged.get("diagnostics") or {}).get("parser_semantic_surface")) or {}).get("consumer_runtime") or {}).get("current_state"),
            "done",
        )
        self.assertEqual(
            (((bridged.get("scene_contract_v1") or {}).get("diagnostics") or {}).get("consumer_runtime") or {}).get("page_status"),
            "readonly",
        )


if __name__ == "__main__":
    unittest.main()
