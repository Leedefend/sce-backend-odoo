# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_ready_parser_semantic_bridge.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scene_ready_parser_semantic_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bridge_module = _load_module()


class TestSceneReadyParserSemanticBridge(unittest.TestCase):
    def test_bridge_projects_parser_surface_into_scene_ready_payload(self):
        compiled = {"surface": {}, "meta": {}}
        contract = {
            "parser_contract": {"view_type": "tree"},
            "view_semantics": {"source_view": "tree", "capability_flags": {"is_editable": True}},
            "native_view": {"views": {"tree": {"layout": []}, "search": {"layout": []}}},
            "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
        }

        bridged = bridge_module.apply_scene_ready_parser_semantic_bridge(compiled, contract)

        self.assertEqual(bridged["view_modes"][0]["key"], "tree")
        self.assertEqual(bridged["surface"]["semantic_view"]["source_view"], "tree")
        self.assertTrue(bridged["surface"]["semantic_view"]["capability_flags"]["is_editable"])
        self.assertIn("parser_semantic_surface", bridged["meta"])
        self.assertEqual(((((bridged["meta"]["parser_semantic_surface"]).get("semantic_page") or {}).get("list_semantics") or {}).get("columns") or [])[0]["name"], "name")


if __name__ == "__main__":
    unittest.main()
