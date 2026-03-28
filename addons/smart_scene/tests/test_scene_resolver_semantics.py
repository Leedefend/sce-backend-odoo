# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_resolver.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("scene_resolver_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()


class TestSceneResolverSemantics(unittest.TestCase):
    def test_resolver_prefers_parser_semantics_for_layout_and_interaction(self):
        resolved = TARGET.resolve_scene_identity(
            scene_hint={"key": "workspace.home"},
            page_hint={"key": "workspace.home", "title": "工作台"},
            semantic_surface={
                "parser_contract": {"view_type": "tree"},
                "view_semantics": {"source_view": "tree", "capability_flags": {"is_editable": True}},
                "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
            },
        )

        self.assertEqual((resolved.get("scene") or {}).get("layout_mode"), "list_flow")
        self.assertEqual((resolved.get("scene") or {}).get("interaction_mode"), "multi_select")
        self.assertEqual((resolved.get("page") or {}).get("view_type"), "tree")

    def test_resolver_uses_search_surface_when_view_type_hints_are_missing(self):
        resolved = TARGET.resolve_scene_identity(
            scene_hint={"key": "workspace.search"},
            page_hint={"key": "workspace.search", "title": "搜索"},
            semantic_surface={
                "search_surface": {
                    "mode": "faceted",
                    "searchpanel": [{"name": "stage_id"}],
                }
            },
        )

        self.assertEqual((resolved.get("scene") or {}).get("layout_mode"), "entry_flow")
        self.assertEqual((resolved.get("scene") or {}).get("interaction_mode"), "query")
        self.assertEqual((resolved.get("page") or {}).get("view_type"), "search")

    def test_resolver_marks_page_restricted_from_permission_surface(self):
        resolved = TARGET.resolve_scene_identity(
            scene_hint={"key": "workspace.home"},
            page_hint={"key": "workspace.home", "title": "工作台"},
            semantic_surface={
                "permission_surface": {
                    "visible": True,
                    "allowed": False,
                    "reason_code": "missing_capability",
                }
            },
        )

        self.assertEqual((resolved.get("page") or {}).get("page_status"), "restricted")


if __name__ == "__main__":
    unittest.main()
