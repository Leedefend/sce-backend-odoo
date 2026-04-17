# -*- coding: utf-8 -*-
import copy
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
        list_profile = ((payload.get("page") or {}).get("list_profile")) or {}
        self.assertEqual(list_profile.get("owner_layer"), "scene_orchestration")
        self.assertEqual(list_profile.get("search_mode"), "faceted")
        self.assertEqual(list_profile.get("filter_count"), 1)

    def test_build_scene_contract_from_specs_derives_list_presentation_profile(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "projects.list"},
            page_hint={"key": "projects.list", "title": "项目列表"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "semantic_page": {
                    "list_semantics": {
                        "owner_layer": "scene_orchestration",
                        "columns": [
                            {"name": "name", "label": "项目"},
                            {"name": "stage_id", "label": "阶段"},
                        ],
                        "row_primary": "name",
                        "row_secondary": "stage_id",
                        "status_field": "lifecycle_state",
                    }
                },
                "search_surface": {
                    "mode": "faceted",
                    "filters": [{"key": "active", "label": "有效"}],
                },
            },
        )

        list_profile = ((payload.get("page") or {}).get("list_profile")) or {}
        self.assertEqual(list_profile.get("owner_layer"), "scene_orchestration")
        self.assertEqual([row.get("name") for row in list_profile.get("columns") or []], ["name", "stage_id"])
        self.assertEqual(list_profile.get("row_primary"), "name")
        self.assertEqual(list_profile.get("status_field"), "lifecycle_state")
        self.assertEqual(list_profile.get("filter_count"), 1)

    def test_build_scene_contract_from_specs_derives_relation_entry_envelope(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "projects.form"},
            page_hint={"key": "projects.form", "title": "项目"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "semantic_page": {
                    "relation_entries": [
                        {
                            "field": "project_type_id",
                            "model": "sc.dictionary",
                            "create_mode": "page",
                            "can_read": True,
                            "can_create": False,
                            "reason_code": "PAGE_ENTRY_READONLY",
                            "default_vals": {"type": "project_type"},
                            "action_id": 101,
                            "menu_id": 11,
                        }
                    ]
                }
            },
        )

        entries = ((payload.get("page") or {}).get("relation_entries")) or []
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].get("owner_layer"), "scene_orchestration")
        self.assertEqual(entries[0].get("field"), "project_type_id")
        self.assertEqual(entries[0].get("create_mode"), "page")
        self.assertTrue(entries[0].get("can_read"))
        self.assertFalse(entries[0].get("can_create"))
        self.assertEqual(entries[0].get("reason_code"), "PAGE_ENTRY_READONLY")

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
        lifecycle = ((payload.get("page") or {}).get("lifecycle")) or {}
        self.assertEqual(lifecycle.get("owner_layer"), "scene_orchestration")
        self.assertEqual(lifecycle.get("state_field"), "state")
        self.assertEqual([row.get("key") for row in lifecycle.get("steps") or []], ["draft", "approved"])
        self.assertEqual(lifecycle.get("active_transition_count"), 1)

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

    def test_build_scene_contract_from_specs_marks_page_empty_for_empty_validation_record(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.form"},
            page_hint={"key": "workspace.form", "title": "表单"},
            zone_specs=[],
            built_zones={},
            record={},
            diagnostics={"source": "test"},
            semantic_surface={
                "validation_surface": {
                    "required_fields": ["name"],
                    "field_rules": [{"field": "name", "rule": "required"}],
                }
            },
        )

        self.assertEqual((((payload.get("page") or {}).get("page_status"))), "empty")

    def test_build_scene_contract_from_specs_marks_page_ready_for_satisfied_record(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.record"},
            page_hint={"key": "workspace.record", "title": "记录"},
            zone_specs=[],
            built_zones={},
            record={"state": "draft", "name": "ready"},
            diagnostics={"source": "test"},
            semantic_surface={
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

        self.assertEqual((((payload.get("page") or {}).get("page_status"))), "ready")

    def test_build_scene_contract_from_specs_blocks_closed_state_from_semantic_page_gating(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.record"},
            page_hint={"key": "workspace.record", "title": "记录"},
            zone_specs=[],
            built_zones={},
            record={"state": "done", "name": "ready"},
            diagnostics={"source": "test"},
            semantic_surface={
                "workflow_surface": {
                    "state_field": "state",
                    "states": ["draft", "done"],
                    "transitions": [{"from": "draft", "to": "done"}],
                },
                "semantic_page": {
                    "action_gating": {
                        "record_state": {"field": "state", "value": "done", "source": "record"},
                        "policy": {"closed_states": ["done"]},
                        "verdict": {"is_closed_state": True, "reason_code": "closed_state"},
                    }
                },
            },
        )

        self.assertEqual((((payload.get("page") or {}).get("page_status"))), "readonly")
        self.assertFalse((((payload.get("permissions") or {}).get("can_edit"))))
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("workflow"),
            "closed_state",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("record_state_summary")) or {}).get("is_closed_state"),
            True,
        )

    def test_build_scene_contract_from_specs_projects_permission_verdicts_into_flags_and_reasons(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.record"},
            page_hint={"key": "workspace.record", "title": "记录"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "permission_surface": {
                    "visible": True,
                    "allowed": True,
                },
                "semantic_page": {
                    "permission_verdicts": {
                        "read": {"allowed": True, "reason_code": ""},
                        "create": {"allowed": False, "reason_code": "create_denied"},
                        "write": {"allowed": False, "reason_code": "write_denied"},
                        "unlink": {"allowed": False, "reason_code": "unlink_denied"},
                        "execute": {"allowed": False, "reason_code": "execute_denied"},
                    }
                },
            },
        )

        self.assertTrue((((payload.get("permissions") or {}).get("can_read"))))
        self.assertFalse((((payload.get("permissions") or {}).get("can_edit"))))
        self.assertFalse((((payload.get("permissions") or {}).get("can_create"))))
        self.assertFalse((((payload.get("permissions") or {}).get("can_delete"))))
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("create"),
            "create_denied",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("edit"),
            "write_denied",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("delete"),
            "unlink_denied",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("execute"),
            "execute_denied",
        )

    def test_build_scene_contract_from_specs_projects_action_semantics_into_disabled_actions(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.record"},
            page_hint={"key": "workspace.record", "title": "记录"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "semantic_page": {
                    "actions": {
                        "header_actions": [
                            {"key": "refresh", "label": "刷新", "enabled": False, "reason_code": "header_busy"}
                        ],
                        "record_actions": [
                            {"key": "approve", "label": "批准", "enabled": False, "reason_code": "workflow_blocked"}
                        ],
                        "toolbar_actions": [
                            {"key": "export", "label": "导出", "enabled": False, "reason_code": "toolbar_disabled"}
                        ],
                    }
                }
            },
        )

        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("refresh"),
            "header_busy",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("approve"),
            "workflow_blocked",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("export"),
            "toolbar_disabled",
        )

    def test_build_scene_contract_from_specs_projects_enabled_semantic_actions_into_contract_groups(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.record"},
            page_hint={"key": "workspace.record", "title": "记录"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "semantic_page": {
                    "actions": {
                        "header_actions": [
                            {"key": "refresh", "label": "刷新", "enabled": True},
                            {"key": "sync", "label": "同步", "enabled": False, "reason_code": "header_busy"},
                        ],
                        "record_actions": [
                            {"key": "approve", "label": "批准", "enabled": True},
                            {"key": "reject", "label": "拒绝", "enabled": False, "reason_code": "workflow_blocked"},
                        ],
                        "toolbar_actions": [
                            {"key": "export", "label": "导出", "enabled": True},
                            {"key": "archive", "label": "归档", "enabled": False, "reason_code": "toolbar_disabled"},
                        ],
                    }
                }
            },
        )

        self.assertEqual(
            [row.get("key") for row in ((payload.get("actions") or {}).get("primary_actions") or [])],
            ["refresh"],
        )
        self.assertEqual(
            [row.get("key") for row in ((payload.get("actions") or {}).get("contextual_actions") or [])],
            ["approve"],
        )
        self.assertEqual(
            [row.get("key") for row in ((payload.get("actions") or {}).get("secondary_actions") or [])],
            ["export"],
        )
        self.assertNotIn(
            "sync",
            [row.get("key") for row in ((payload.get("actions") or {}).get("primary_actions") or [])],
        )
        self.assertNotIn(
            "reject",
            [row.get("key") for row in ((payload.get("actions") or {}).get("contextual_actions") or [])],
        )
        self.assertNotIn(
            "archive",
            [row.get("key") for row in ((payload.get("actions") or {}).get("secondary_actions") or [])],
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("sync"),
            "header_busy",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("reject"),
            "workflow_blocked",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("archive"),
            "toolbar_disabled",
        )

    def test_scene_action_grouping_preserves_source_action_and_permission_facts(self):
        semantic_surface = {
            "semantic_page": {
                "permission_verdicts": {
                    "execute": {"allowed": True},
                },
                "actions": {
                    "header_actions": [
                        {"key": "submit", "label": "提交", "semantic": "primary_action", "enabled": True},
                        {"key": "sync", "label": "同步", "enabled": False, "reason_code": "busy"},
                    ],
                    "record_actions": [
                        {"key": "delete", "label": "删除", "semantic": "danger", "enabled": True},
                    ],
                    "toolbar_actions": [
                        {"key": "export", "label": "导出", "enabled": True},
                    ],
                },
            }
        }
        original = copy.deepcopy(semantic_surface)

        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.record"},
            page_hint={"key": "workspace.record", "title": "记录"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface=semantic_surface,
        )

        self.assertEqual(semantic_surface, original)
        self.assertEqual(
            [row.get("key") for row in ((payload.get("actions") or {}).get("primary_actions") or [])],
            ["submit"],
        )
        self.assertEqual(
            [row.get("key") for row in ((payload.get("actions") or {}).get("secondary_actions") or [])],
            ["export"],
        )
        self.assertEqual(
            [row.get("key") for row in ((payload.get("actions") or {}).get("danger_actions") or [])],
            ["delete"],
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("sync"),
            "busy",
        )

    def test_build_scene_contract_from_specs_projects_semantic_action_classification_into_overlay_groups(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.record"},
            page_hint={"key": "workspace.record", "title": "记录"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "semantic_page": {
                    "actions": {
                        "header_actions": [
                            {"key": "submit", "label": "提交", "semantic": "primary_action", "enabled": True},
                        ],
                        "record_actions": [
                            {"key": "delete", "label": "删除", "semantic": "danger", "enabled": True},
                            {"key": "cancel", "label": "作废", "semantic": "danger", "enabled": False, "reason_code": "closed_state"},
                        ],
                        "toolbar_actions": [
                            {"key": "refresh", "label": "刷新", "semantic": "secondary", "enabled": True},
                        ],
                    }
                }
            },
        )

        self.assertEqual(
            [row.get("key") for row in ((payload.get("actions") or {}).get("primary_actions") or [])],
            ["submit"],
        )
        self.assertEqual(
            [row.get("key") for row in ((payload.get("actions") or {}).get("secondary_actions") or [])],
            ["refresh"],
        )
        self.assertEqual(
            [row.get("key") for row in ((payload.get("actions") or {}).get("contextual_actions") or [])],
            ["delete"],
        )
        self.assertEqual(
            [row.get("key") for row in ((payload.get("actions") or {}).get("recommended_actions") or [])],
            ["submit"],
        )
        self.assertEqual(
            [row.get("key") for row in ((payload.get("actions") or {}).get("danger_actions") or [])],
            ["delete"],
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("cancel"),
            "closed_state",
        )

    def test_build_scene_contract_from_specs_jointly_applies_action_gates_and_permission_verdicts(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.record"},
            page_hint={"key": "workspace.record", "title": "记录"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "permission_surface": {
                    "visible": True,
                    "allowed": True,
                },
                "semantic_page": {
                    "permission_verdicts": {
                        "read": {"allowed": True, "reason_code": ""},
                        "create": {"allowed": True, "reason_code": ""},
                        "write": {"allowed": False, "reason_code": "write_denied"},
                        "unlink": {"allowed": True, "reason_code": ""},
                        "execute": {"allowed": False, "reason_code": "execute_denied"},
                    },
                    "actions": {
                        "header_actions": [
                            {
                                "key": "archive",
                                "label": "归档",
                                "enabled": True,
                                "gate": {"allowed": True, "requires_write": True, "reason_code": "OK"},
                            }
                        ],
                        "record_actions": [
                            {
                                "key": "approve",
                                "label": "批准",
                                "enabled": True,
                                "gate": {"allowed": False, "requires_write": True, "reason_code": "STATE_BLOCKED"},
                            }
                        ],
                        "toolbar_actions": [
                            {
                                "key": "sync",
                                "label": "同步",
                                "enabled": True,
                                "gate": {"allowed": True, "requires_write": False, "reason_code": "OK"},
                            }
                        ],
                    },
                },
            },
        )

        self.assertEqual(((payload.get("actions") or {}).get("primary_actions") or []), [])
        self.assertEqual(((payload.get("actions") or {}).get("contextual_actions") or []), [])
        self.assertEqual(((payload.get("actions") or {}).get("secondary_actions") or []), [])
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("archive"),
            "write_denied",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("approve"),
            "STATE_BLOCKED",
        )
        self.assertEqual(
            (((payload.get("permissions") or {}).get("disabled_actions")) or {}).get("sync"),
            "execute_denied",
        )

    def test_build_scene_contract_from_specs_projects_runtime_state_consistently(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.record"},
            page_hint={"key": "workspace.record", "title": "记录"},
            zone_specs=[],
            built_zones={},
            record={"state": "draft", "name": "ready"},
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
                "semantic_page": {
                    "action_gating": {
                        "record_state": {"field": "state", "value": "draft", "source": "record"},
                        "policy": {"closed_states": ["done"]},
                        "verdict": {"is_closed_state": False, "reason_code": "OK"},
                    }
                },
            },
        )

        summary = ((payload.get("permissions") or {}).get("record_state_summary")) or {}
        self.assertEqual((payload.get("page") or {}).get("page_status"), "ready")
        self.assertEqual(summary.get("page_status"), "ready")
        self.assertEqual(summary.get("current_state"), "draft")
        self.assertEqual(summary.get("active_transition_count"), 1)
        self.assertEqual(summary.get("missing_required_fields"), [])
        self.assertEqual(summary.get("closed_states"), ["done"])

    def test_build_scene_contract_reports_scene_envelope_observability(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "projects.form"},
            page_hint={"key": "projects.form", "title": "项目"},
            zone_specs=[],
            built_zones={},
            record={"state": "draft"},
            diagnostics={"source": "test"},
            semantic_surface={
                "workflow_surface": {
                    "state_field": "state",
                    "states": ["draft", "approved"],
                    "transitions": [{"from": "draft", "to": "approved"}],
                },
                "search_surface": {"mode": "faceted", "filters": [{"key": "mine"}]},
                "semantic_page": {
                    "lifecycle": {"state_field": "stage_id"},
                    "list_profile": {"columns": ["name"]},
                    "action_groups": [{"key": "workflow", "actions": ["submit"]}],
                    "actions": {
                        "header_actions": [
                            {"key": "submit", "label": "提交", "enabled": True},
                        ],
                    },
                    "list_semantics": {
                        "columns": [{"name": "name", "label": "项目"}],
                        "row_primary": "name",
                    },
                    "relation_entries": [
                        {
                            "field": "project_type_id",
                            "model": "sc.dictionary",
                            "create_mode": "page",
                            "can_read": True,
                            "can_create": False,
                        }
                    ],
                },
            },
        )

        observability = ((payload.get("diagnostics") or {}).get("scene_envelope_observability")) or {}
        scene_presence = observability.get("scene_envelope_presence") or {}
        compatibility_presence = observability.get("compatibility_field_presence") or {}
        self.assertTrue(scene_presence.get("action_surface"))
        self.assertTrue(scene_presence.get("lifecycle"))
        self.assertTrue(scene_presence.get("list_profile"))
        self.assertTrue(scene_presence.get("relation_entries"))
        self.assertTrue(compatibility_presence.get("action_groups"))
        self.assertTrue(compatibility_presence.get("lifecycle"))
        self.assertTrue(compatibility_presence.get("list_profile"))
        self.assertTrue(compatibility_presence.get("field_relation_entry"))


if __name__ == "__main__":
    unittest.main()
