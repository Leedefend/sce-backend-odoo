# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "core"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


smart_scene_pkg = sys.modules.setdefault("addons.smart_scene", types.ModuleType("addons.smart_scene"))
smart_scene_pkg.__path__ = [str(CORE_DIR.parent)]
core_pkg = sys.modules.setdefault("addons.smart_scene.core", types.ModuleType("addons.smart_scene.core"))
core_pkg.__path__ = [str(CORE_DIR)]
smart_scene_pkg.core = core_pkg

for name in ("layout_orchestrator", "scene_resolver", "structure_mapper", "scene_parser_semantic_bridge", "scene_contract_builder"):
    module = _load_module(f"addons.smart_scene.core.{name}", CORE_DIR / f"{name}.py")
    setattr(core_pkg, name, module)

target = _load_module("addons.smart_scene.core.scene_engine", CORE_DIR / "scene_engine.py")


class TestSceneEngineSemantics(unittest.TestCase):
    def test_build_scene_contract_from_specs_projects_parser_surface(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.home"},
            page_hint={"key": "workspace.home", "title": "工作台"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "parser_contract": {"view_type": "kanban"},
                "view_semantics": {"source_view": "kanban", "capability_flags": {"has_menu": True}},
                "native_view": {"views": {"kanban": {"layout": []}}},
                "semantic_page": {"kanban_semantics": {"lane_count": 3}},
            },
        )

        self.assertEqual((((payload.get("page") or {}).get("surface") or {}).get("view_type")), "kanban")
        self.assertEqual((((payload.get("scene") or {}).get("layout_mode"))), "workspace_flow")
        self.assertEqual((((payload.get("scene") or {}).get("interaction_mode"))), "multi_select")
        self.assertIn("parser_semantic_surface", payload.get("diagnostics") or {})

    def test_build_scene_contract_from_specs_uses_search_surface_without_view_type(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.search"},
            page_hint={"key": "workspace.search", "title": "搜索"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "search_surface": {
                    "mode": "faceted",
                    "searchpanel": [{"name": "stage_id"}],
                }
            },
        )

        self.assertEqual((((payload.get("page") or {}).get("surface") or {}).get("view_type")), "search")
        self.assertEqual((((payload.get("scene") or {}).get("layout_mode"))), "entry_flow")
        self.assertEqual((((payload.get("scene") or {}).get("interaction_mode"))), "query")

    def test_build_scene_contract_from_specs_projects_readonly_permission_surface_into_permissions(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.home"},
            page_hint={"key": "workspace.home", "title": "工作台"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "permission_surface": {
                    "visible": True,
                    "allowed": False,
                    "reason_code": "missing_capability",
                }
            },
        )

        self.assertEqual((((payload.get("page") or {}).get("page_status"))), "readonly")
        self.assertTrue((((payload.get("permissions") or {}).get("can_read"))))
        self.assertFalse((((payload.get("permissions") or {}).get("can_edit"))))
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("edit"),
            "missing_capability",
        )

    def test_build_scene_contract_from_specs_projects_hidden_permission_surface_into_permissions(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.home"},
            page_hint={"key": "workspace.home", "title": "工作台"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "permission_surface": {
                    "visible": False,
                    "allowed": False,
                    "reason_code": "hidden_by_policy",
                }
            },
        )

        self.assertEqual((((payload.get("page") or {}).get("page_status"))), "restricted")
        self.assertFalse((((payload.get("permissions") or {}).get("can_read"))))
        self.assertFalse((((payload.get("permissions") or {}).get("can_edit"))))

    def test_build_scene_contract_from_specs_projects_workflow_and_validation_surfaces_into_permissions(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.home"},
            page_hint={"key": "workspace.home", "title": "工作台"},
            zone_specs=[],
            built_zones={},
            record={"state": "draft", "name": ""},
            diagnostics={"source": "test"},
            semantic_surface={
                "workflow_surface": {
                    "state_field": "state",
                    "states": ["draft", "approved"],
                    "transitions": [{"from": "draft", "to": "approved"}],
                    "highlight_states": ["approved"],
                },
                "validation_surface": {
                    "required_fields": ["name"],
                    "field_rules": [{"field": "name", "rule": "required"}],
                },
            },
        )

        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("submit"),
            "validation_required",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("record_state_summary")) or {}).get("state_field"),
            "state",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("record_state_summary")) or {}).get("states"),
            ["draft", "approved"],
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("record_state_summary")) or {}).get("workflow_transition_count"),
            1,
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("record_state_summary")) or {}).get("validation_required_count"),
            1,
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("record_state_summary")) or {}).get("validation_required_fields"),
            ["name"],
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("record_state_summary")) or {}).get("validation_rule_count"),
            1,
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("record_state_summary")) or {}).get("current_state"),
            "draft",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("record_state_summary")) or {}).get("active_transition_count"),
            1,
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("record_state_summary")) or {}).get("missing_required_fields"),
            ["name"],
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("record_state_summary")) or {}).get("missing_required_count"),
            1,
        )

    def test_build_scene_contract_from_specs_projects_workflow_gate_when_transitions_missing(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.home"},
            page_hint={"key": "workspace.home", "title": "工作台"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "workflow_surface": {
                    "state_field": "state",
                    "states": ["draft", "approved"],
                    "highlight_states": ["approved"],
                }
            },
        )

        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("workflow"),
            "action_permission_workflow_gate",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("record_state_summary")) or {}).get("workflow_transition_count"),
            0,
        )

    def test_build_scene_contract_from_specs_projects_workflow_gate_when_permission_denied(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.home"},
            page_hint={"key": "workspace.home", "title": "工作台"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "permission_surface": {
                    "visible": True,
                    "allowed": False,
                    "reason_code": "missing_capability",
                },
                "workflow_surface": {
                    "state_field": "state",
                    "states": ["draft", "approved"],
                    "transitions": [{"from": "draft", "to": "approved"}],
                }
            },
        )

        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("workflow"),
            "permission_workflow_gate",
        )

    def test_build_scene_contract_from_specs_uses_workflow_surface_for_form_identity_without_view_type(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.record"},
            page_hint={"key": "workspace.record", "title": "记录"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "workflow_surface": {
                    "state_field": "state",
                    "states": ["draft", "approved"],
                    "transitions": [{"from": "draft", "to": "approved"}],
                }
            },
        )

        self.assertEqual((((payload.get("page") or {}).get("surface") or {}).get("view_type")), "form")
        self.assertEqual((((payload.get("scene") or {}).get("layout_mode"))), "detail_focus")
        self.assertEqual((((payload.get("scene") or {}).get("interaction_mode"))), "record_focus")

    def test_build_scene_contract_from_specs_does_not_disable_submit_when_required_fields_present(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.form"},
            page_hint={"key": "workspace.form", "title": "表单"},
            zone_specs=[],
            built_zones={},
            record={"name": "ready"},
            diagnostics={"source": "test"},
            semantic_surface={
                "validation_surface": {
                    "required_fields": ["name"],
                    "field_rules": [{"field": "name", "rule": "required"}],
                }
            },
        )

        self.assertIsNone((((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("submit"))
        self.assertEqual(
            (((payload.get("permissions") or {}).get("record_state_summary")) or {}).get("missing_required_count"),
            0,
        )


if __name__ == "__main__":
    unittest.main()
