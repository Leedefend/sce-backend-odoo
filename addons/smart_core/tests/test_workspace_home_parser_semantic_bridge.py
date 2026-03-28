# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "workspace_home_parser_semantic_bridge.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("workspace_home_parser_semantic_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
apply_workspace_home_parser_semantic_bridge = TARGET.apply_workspace_home_parser_semantic_bridge


class TestWorkspaceHomeParserSemanticBridge(unittest.TestCase):
    def test_bridge_projects_parser_surface_into_layout_and_orchestration(self):
        payload = apply_workspace_home_parser_semantic_bridge(
            {
                "layout": {},
                "page_orchestration_v1": {"page": {}, "render_hints": {}, "meta": {}},
                "diagnostics": {},
            },
            {
                "parser_contract": {"view_type": "form"},
                "view_semantics": {
                    "source_view": "form",
                    "capability_flags": {"is_editable": True},
                    "semantic_meta": {"field_count": 3},
                },
                "native_view": {"views": {"form": {"layout": []}}},
                "semantic_page": {"title_node": {"text": "工单"}},
            },
        )

        self.assertEqual((payload.get("layout") or {}).get("view_type"), "form")
        self.assertEqual((((payload.get("layout") or {}).get("semantic_view") or {}).get("source_view")), "form")
        page = (payload.get("page_orchestration_v1") or {}).get("page") or {}
        page_context = page.get("context") or {}
        view_type = page_context.get("view_type")
        self.assertEqual(view_type, "form")
        self.assertIn("parser_semantic_surface", payload.get("diagnostics") or {})


if __name__ == "__main__":
    unittest.main()
