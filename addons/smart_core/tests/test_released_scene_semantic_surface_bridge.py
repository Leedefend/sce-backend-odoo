# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "released_scene_semantic_surface_bridge.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("released_scene_semantic_surface_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bridge_module = _load_module()


class TestReleasedSceneSemanticSurfaceBridge(unittest.TestCase):
    def test_bridge_projects_scene_contract_surface_into_runtime_payload(self):
        payload = {}
        scene_contract = {
            "identity": {"scene_key": "workspace.home"},
            "page": {
                "surface": {
                    "view_type": "kanban",
                    "semantic_view": {"source_view": "kanban"},
                    "semantic_page": {"kanban_semantics": {"lane_count": 3}},
                }
            },
            "search_surface": {"mode": "faceted", "searchpanel": [{"name": "stage_id"}]},
            "permission_surface": {"allowed": False, "reason_code": "missing_capability"},
            "workflow_surface": {"state_field": "state", "states": [{"key": "draft"}]},
            "validation_surface": {"required_fields": ["name"]},
            "governance": {
                "parser_semantic_surface": {
                    "parser_contract": {"view_type": "kanban"},
                    "view_semantics": {"source_view": "kanban"},
                }
            },
        }

        bridged = bridge_module.apply_released_scene_semantic_surface_bridge(payload, scene_contract)

        self.assertEqual((bridged.get("semantic_runtime") or {}).get("view_type"), "kanban")
        self.assertEqual(
            (((bridged.get("semantic_runtime") or {}).get("semantic_view") or {}).get("source_view")),
            "kanban",
        )
        self.assertEqual(((bridged.get("semantic_runtime") or {}).get("search_surface") or {}).get("mode"), "faceted")
        self.assertEqual(((bridged.get("semantic_runtime") or {}).get("permission_surface") or {}).get("reason_code"), "missing_capability")
        self.assertEqual(((bridged.get("semantic_runtime") or {}).get("workflow_surface") or {}).get("state_field"), "state")
        self.assertEqual((((bridged.get("semantic_runtime") or {}).get("validation_surface") or {}).get("required_fields") or [])[0], "name")
        self.assertIn("released_scene_semantic_surface", bridged)


if __name__ == "__main__":
    unittest.main()
