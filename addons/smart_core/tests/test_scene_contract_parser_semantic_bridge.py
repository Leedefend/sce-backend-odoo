# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_contract_parser_semantic_bridge.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scene_contract_parser_semantic_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bridge_module = _load_module()


class TestSceneContractParserSemanticBridge(unittest.TestCase):
    def test_bridge_projects_parser_surface_into_scene_contract(self):
        payload = {"page": {}, "governance": {}}
        source = {
            "parser_contract": {"view_type": "form"},
            "view_semantics": {"source_view": "form", "capability_flags": {"is_editable": True}},
            "native_view": {"views": {"form": {"layout": []}}},
            "semantic_page": {"title_node": {"text": "工单"}},
        }

        bridged = bridge_module.apply_scene_contract_parser_semantic_bridge(payload, source)

        self.assertEqual((((bridged.get("page") or {}).get("surface") or {}).get("view_type")), "form")
        self.assertEqual(
            (((((bridged.get("page") or {}).get("surface") or {}).get("semantic_view") or {}).get("source_view"))),
            "form",
        )
        self.assertIn("parser_semantic_surface", bridged.get("governance") or {})


if __name__ == "__main__":
    unittest.main()
