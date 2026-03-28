# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "page_contract_parser_semantic_bridge.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("page_contract_parser_semantic_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bridge_module = _load_module()


class TestPageContractParserSemanticBridge(unittest.TestCase):
    def test_bridge_projects_parser_surface_into_page_contract(self):
        payload = {
            "page": {"context": {}},
            "render_hints": {},
            "meta": {},
        }
        source = {
            "parser_contract": {"view_type": "kanban"},
            "view_semantics": {"source_view": "kanban", "capability_flags": {"has_menu": True}},
            "native_view": {"views": {"kanban": {"layout": []}}},
            "semantic_page": {"kanban_semantics": {"lane_count": 3}},
        }

        bridged = bridge_module.apply_page_contract_parser_semantic_bridge(payload, source)

        self.assertEqual(((bridged.get("page") or {}).get("context") or {}).get("view_type"), "kanban")
        self.assertEqual(((bridged.get("page") or {}).get("context") or {}).get("semantic_source_view"), "kanban")
        self.assertTrue((((bridged.get("render_hints") or {}).get("semantic_view") or {}).get("capability_flags") or {}).get("has_menu"))
        self.assertIn("parser_semantic_surface", bridged.get("meta") or {})


if __name__ == "__main__":
    unittest.main()
