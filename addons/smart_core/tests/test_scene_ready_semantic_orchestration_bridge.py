# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_ready_semantic_orchestration_bridge.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scene_ready_semantic_orchestration_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bridge_module = _load_module()


class TestSceneReadySemanticOrchestrationBridge(unittest.TestCase):
    def test_bridge_overrides_legacy_view_modes_from_parser_semantics(self):
        payload = {
            "view_modes": [{"key": "kanban", "label": "看板", "enabled": True}],
            "action_surface": {"selection_mode": "single"},
            "parser_semantic_surface": {
                "parser_contract": {"view_type": "form"},
                "view_semantics": {"source_view": "form", "capability_flags": {"is_editable": True}},
                "native_view": {"views": {"form": {"layout": []}, "search": {"layout": []}}},
                "semantic_page": {"title_node": {"text": "项目"}},
            },
        }

        bridged = bridge_module.apply_scene_ready_semantic_orchestration_bridge(payload)

        self.assertEqual((bridged.get("view_modes") or [])[0]["key"], "form")
        self.assertEqual(((bridged.get("action_surface") or {}).get("selection_mode")), "single")

    def test_bridge_uses_multi_selection_for_list_like_semantics(self):
        payload = {
            "action_surface": {"selection_mode": "single"},
            "parser_semantic_surface": {
                "parser_contract": {"view_type": "tree"},
                "view_semantics": {"source_view": "tree", "capability_flags": {"is_editable": True}},
                "native_view": {"views": {"tree": {"layout": []}, "kanban": {"cards": []}}},
                "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
            },
        }

        bridged = bridge_module.apply_scene_ready_semantic_orchestration_bridge(payload)

        self.assertEqual((bridged.get("view_modes") or [])[0]["key"], "tree")
        self.assertEqual(((bridged.get("action_surface") or {}).get("selection_mode")), "multi")

    def test_bridge_materializes_action_surface_when_missing(self):
        payload = {
            "parser_semantic_surface": {
                "parser_contract": {"view_type": "tree"},
                "view_semantics": {"source_view": "tree", "capability_flags": {"is_editable": True}},
                "native_view": {"views": {"tree": {"layout": []}}},
                "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
            },
        }

        bridged = bridge_module.apply_scene_ready_semantic_orchestration_bridge(payload)

        self.assertEqual(((bridged.get("action_surface") or {}).get("selection_mode")), "multi")


if __name__ == "__main__":
    unittest.main()
