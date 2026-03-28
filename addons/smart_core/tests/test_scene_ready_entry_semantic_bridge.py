# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_ready_entry_semantic_bridge.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scene_ready_entry_semantic_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bridge_module = _load_module()


class TestSceneReadyEntrySemanticBridge(unittest.TestCase):
    def test_bridge_projects_parser_surface_into_scene_ready_entry(self):
        payload = {
            "surface": {},
            "render_hints": {},
            "meta": {
                "parser_semantic_surface": {
                    "parser_contract": {"view_type": "tree"},
                    "view_semantics": {
                        "source_view": "tree",
                        "capability_flags": {"is_editable": True},
                        "semantic_meta": {"editable_mode": "bottom"},
                    },
                    "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
                }
            },
        }

        bridged = bridge_module.apply_scene_ready_entry_semantic_bridge(payload)

        self.assertEqual(bridged.get("view_type"), "tree")
        self.assertEqual(((bridged.get("semantic_view") or {}).get("source_view")), "tree")
        self.assertTrue((((bridged.get("surface") or {}).get("semantic_view") or {}).get("capability_flags") or {}).get("is_editable"))
        self.assertIn("semantic_page", bridged.get("render_hints") or {})


if __name__ == "__main__":
    unittest.main()
