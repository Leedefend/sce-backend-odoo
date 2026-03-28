# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "runtime_page_parser_semantic_bridge.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("runtime_page_parser_semantic_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bridge_module = _load_module()


class TestRuntimePageParserSemanticBridge(unittest.TestCase):
    def test_bridge_projects_parser_surface_into_runtime_page(self):
        page_payload = {
            "page_orchestration_v1": {
                "page": {"context": {}},
                "render_hints": {},
                "meta": {
                    "parser_semantic_surface": {
                        "parser_contract": {"view_type": "kanban"},
                        "view_semantics": {"source_view": "kanban", "capability_flags": {"has_menu": True}},
                        "native_view": {"views": {"kanban": {"layout": []}}},
                        "semantic_page": {"kanban_semantics": {"lane_count": 3}},
                    }
                },
            }
        }

        bridged = bridge_module.apply_runtime_page_parser_semantic_bridge(page_payload, page_key="home")

        self.assertEqual((bridged.get("runtime_context") or {}).get("page_key"), "home")
        self.assertEqual((bridged.get("runtime_context") or {}).get("view_type"), "kanban")
        self.assertEqual(
            (((bridged.get("page_orchestration_v1") or {}).get("render_hints") or {}).get("runtime_semantic_view") or {}).get("source_view"),
            "kanban",
        )
        self.assertIn("runtime_semantic_surface", bridged)


if __name__ == "__main__":
    unittest.main()
