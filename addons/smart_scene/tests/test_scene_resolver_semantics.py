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

    def test_resolver_marks_page_readonly_from_permission_surface(self):
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

        self.assertEqual((resolved.get("page") or {}).get("page_status"), "readonly")

    def test_resolver_marks_page_restricted_when_permission_surface_hides_page(self):
        resolved = TARGET.resolve_scene_identity(
            scene_hint={"key": "workspace.home"},
            page_hint={"key": "workspace.home", "title": "工作台"},
            semantic_surface={
                "permission_surface": {
                    "visible": False,
                    "allowed": False,
                    "reason_code": "hidden_by_policy",
                }
            },
        )

        self.assertEqual((resolved.get("page") or {}).get("page_status"), "restricted")

    def test_resolver_uses_workflow_surface_when_view_type_hints_are_missing(self):
        resolved = TARGET.resolve_scene_identity(
            scene_hint={"key": "workspace.record"},
            page_hint={"key": "workspace.record", "title": "记录"},
            semantic_surface={
                "workflow_surface": {
                    "state_field": "state",
                    "states": ["draft", "approved"],
                    "transitions": [{"from": "draft", "to": "approved"}],
                }
            },
        )

        self.assertEqual((resolved.get("scene") or {}).get("layout_mode"), "detail_focus")
        self.assertEqual((resolved.get("scene") or {}).get("interaction_mode"), "record_focus")
        self.assertEqual((resolved.get("page") or {}).get("view_type"), "form")

    def test_resolver_uses_validation_surface_when_view_type_hints_are_missing(self):
        resolved = TARGET.resolve_scene_identity(
            scene_hint={"key": "workspace.form"},
            page_hint={"key": "workspace.form", "title": "表单"},
            semantic_surface={
                "validation_surface": {
                    "required_fields": ["name"],
                    "field_rules": [{"field": "name", "rule": "required"}],
                }
            },
        )

        self.assertEqual((resolved.get("scene") or {}).get("layout_mode"), "detail_focus")
        self.assertEqual((resolved.get("scene") or {}).get("interaction_mode"), "record_focus")
        self.assertEqual((resolved.get("page") or {}).get("view_type"), "form")

    def test_resolver_marks_page_empty_when_validation_required_fields_missing_on_empty_record(self):
        resolved = TARGET.resolve_scene_identity(
            scene_hint={"key": "workspace.form"},
            page_hint={"key": "workspace.form", "title": "表单"},
            semantic_surface={
                "record": {},
                "validation_surface": {
                    "required_fields": ["name"],
                    "field_rules": [{"field": "name", "rule": "required"}],
                }
            },
        )

        self.assertEqual((resolved.get("page") or {}).get("page_status"), "empty")

    def test_resolver_marks_page_ready_when_workflow_and_validation_are_satisfied(self):
        resolved = TARGET.resolve_scene_identity(
            scene_hint={"key": "workspace.record"},
            page_hint={"key": "workspace.record", "title": "记录"},
            semantic_surface={
                "record": {"state": "draft", "name": "ready"},
                "workflow_surface": {
                    "state_field": "state",
                    "states": ["draft", "approved"],
                    "transitions": [{"from": "draft", "to": "approved"}],
                },
                "validation_surface": {
                    "required_fields": ["name"],
                },
            },
        )

        self.assertEqual((resolved.get("page") or {}).get("page_status"), "ready")

    def test_resolver_marks_page_readonly_from_semantic_page_closed_state(self):
        resolved = TARGET.resolve_scene_identity(
            scene_hint={"key": "workspace.record"},
            page_hint={"key": "workspace.record", "title": "记录"},
            semantic_surface={
                "record": {"state": "done"},
                "semantic_page": {
                    "action_gating": {
                        "record_state": {"field": "state", "value": "done", "source": "record"},
                        "policy": {"closed_states": ["done"]},
                        "verdict": {"is_closed_state": True, "reason_code": "closed_state"},
                    }
                },
            },
        )

        self.assertEqual((resolved.get("page") or {}).get("page_status"), "readonly")


if __name__ == "__main__":
    unittest.main()
