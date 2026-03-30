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


sys.modules.setdefault("odoo", types.ModuleType("odoo"))
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
core_pkg.__path__ = [str(CORE_DIR)]
smart_core_pkg.core = core_pkg

target = _load_module(
    "odoo.addons.smart_core.core.system_init_payload_builder",
    CORE_DIR / "system_init_payload_builder.py",
)


class TestSystemInitPayloadBuilderSemantics(unittest.TestCase):
    def test_build_startup_surface_preserves_runtime_semantics(self):
        payload = target.SystemInitPayloadBuilder.build_startup_surface(
            {
                "user": {"id": 1},
                "nav": [],
                "nav_meta": {
                    "nav_source": "scene_contract_v1",
                    "semantic_scene_key": "workspace.home",
                    "semantic_source_view": "kanban",
                    "semantic_view_type": "kanban",
                },
                "default_route": {"scene_key": "workspace.home"},
                "intents": [],
                "feature_flags": {},
                "role_surface": {"landing_scene_key": "workspace.home"},
                "contract_version": "1.0.0",
                "schema_version": "1.0.0",
                "scene_version": "v1",
                "semantic_runtime": {
                    "scene_key": "workspace.home",
                    "view_type": "kanban",
                    "semantic_view": {"source_view": "kanban"},
                    "semantic_page": {"kanban_semantics": {"lane_count": 3}},
                    "parser_semantic_surface": {"parser_contract": {"view_type": "kanban"}},
                    "search_surface": {
                        "filters": [{"name": "mine", "string": "我的"}],
                        "searchpanel": [{"name": "stage_id", "string": "阶段"}],
                        "default_state": {
                            "filters": [{"key": "mine", "label": "我的", "kind": "filter"}],
                        },
                        "mode": "faceted",
                    },
                    "permission_surface": {
                        "visible": True,
                        "allowed": False,
                        "reason_code": "missing_capability",
                        "required_capabilities": ["project.write"],
                    },
                    "workflow_surface": {
                        "state_field": "state",
                        "states": [{"key": "draft"}],
                    },
                    "validation_surface": {
                        "required_fields": ["name"],
                        "field_rules": [{"field": "name", "rule": "required"}],
                    },
                    "debug_blob": {"drop_me": True},
                },
                "released_scene_semantic_surface": {
                    "scene_key": "workspace.home",
                    "page_surface": {"view_type": "kanban", "semantic_view": {"source_view": "kanban"}},
                    "parser_semantic_surface": {"parser_contract": {"view_type": "kanban"}},
                    "search_surface": {"mode": "faceted", "searchpanel": [{"name": "stage_id", "string": "阶段"}]},
                    "permission_surface": {"allowed": False, "reason_code": "missing_capability"},
                    "workflow_surface": {"state_field": "state"},
                    "validation_surface": {"required_fields": ["name"]},
                    "debug_blob": {"drop_me": True},
                },
                "scene_ready_contract_v1": {
                    "contract_version": "v1",
                    "scene_channel": "portal",
                    "scenes": [
                        {
                            "scene": {"key": "workspace.home"},
                            "page": {"context": {"scene_key": "workspace.home"}},
                            "parser_semantic_surface": {"parser_contract": {"view_type": "kanban"}},
                            "semantic_view": {"source_view": "kanban"},
                            "semantic_page": {"kanban_semantics": {"lane_count": 3}},
                            "view_type": "kanban",
                            "search_surface": {
                                "filters": [{"name": "mine", "string": "我的"}],
                                "searchpanel": [{"name": "stage_id", "string": "阶段"}],
                                "default_state": {
                                    "filters": [{"key": "mine", "label": "我的", "kind": "filter"}],
                                },
                                "mode": "faceted",
                            },
                            "list_surface": {
                                "columns": [{"field": "name", "label": "项目名称"}],
                                "default_sort": {"raw": "write_date desc", "display_label": "更新时间 降序"},
                                "available_view_modes": [{"key": "tree", "label": "列表"}],
                                "default_mode": "tree",
                            },
                            "action_surface": {
                                "primary_actions": ["open"],
                                "groups": [{"key": "list_actions", "actions": ["open"]}],
                                "selection_mode": "multi",
                                "counts": {"total": 1, "primary": 1, "groups": 1},
                                "batch_capabilities": {
                                    "can_delete": True,
                                    "can_archive": True,
                                    "can_activate": True,
                                    "selection_required": True,
                                    "native_basis": {"has_active_field": True},
                                },
                            },
                            "permission_surface": {
                                "visible": True,
                                "allowed": False,
                                "reason_code": "missing_capability",
                                "required_capabilities": ["project.write"],
                            },
                            "workflow_surface": {
                                "state_field": "state",
                                "states": [{"key": "draft"}],
                                "transitions": [{"key": "submit"}],
                            },
                            "validation_surface": {
                                "required_fields": ["name"],
                                "field_rules": [{"field": "name", "rule": "required"}],
                            },
                            "meta": {"target": {"route": "/my-work"}},
                        }
                    ],
                    "meta": {"generated_by": "test"},
                },
            }
        )

        self.assertEqual((payload.get("semantic_runtime") or {}).get("view_type"), "kanban")
        self.assertEqual(((payload.get("semantic_runtime") or {}).get("search_surface") or {}).get("mode"), "faceted")
        self.assertEqual(((((payload.get("semantic_runtime") or {}).get("search_surface") or {}).get("default_state") or {}).get("filters") or [])[0].get("key"), "mine")
        self.assertEqual(((payload.get("semantic_runtime") or {}).get("permission_surface") or {}).get("reason_code"), "missing_capability")
        self.assertEqual(((payload.get("semantic_runtime") or {}).get("workflow_surface") or {}).get("state_field"), "state")
        self.assertEqual((((payload.get("semantic_runtime") or {}).get("validation_surface") or {}).get("required_fields") or [])[0], "name")
        self.assertNotIn("debug_blob", payload.get("semantic_runtime") or {})
        self.assertEqual(((payload.get("nav_meta") or {}).get("semantic_source_view")), "kanban")
        self.assertEqual(((payload.get("released_scene_semantic_surface") or {}).get("search_surface") or {}).get("mode"), "faceted")
        self.assertEqual(((payload.get("released_scene_semantic_surface") or {}).get("permission_surface") or {}).get("reason_code"), "missing_capability")
        self.assertNotIn("debug_blob", payload.get("released_scene_semantic_surface") or {})
        scene = ((payload.get("scene_ready_contract_v1") or {}).get("scenes") or [])[0]
        self.assertEqual(scene.get("view_type"), "kanban")
        self.assertIn("parser_semantic_surface", scene)
        self.assertEqual(((scene.get("search_surface") or {}).get("mode")), "faceted")
        self.assertEqual((((scene.get("search_surface") or {}).get("searchpanel") or [])[0].get("name")), "stage_id")
        self.assertEqual(((((scene.get("search_surface") or {}).get("default_state") or {}).get("filters") or [])[0].get("key")), "mine")
        self.assertEqual((((scene.get("list_surface") or {}).get("columns") or [])[0].get("field")), "name")
        self.assertEqual((((scene.get("list_surface") or {}).get("default_sort") or {}).get("display_label")), "更新时间 降序")
        self.assertEqual((((scene.get("list_surface") or {}).get("available_view_modes") or [])[0].get("key")), "tree")
        self.assertTrue((((scene.get("action_surface") or {}).get("batch_capabilities") or {}).get("can_archive")))
        self.assertTrue((((scene.get("action_surface") or {}).get("batch_capabilities") or {}).get("selection_required")))
        self.assertEqual(((scene.get("permission_surface") or {}).get("reason_code")), "missing_capability")
        self.assertEqual((((scene.get("permission_surface") or {}).get("required_capabilities") or [])[0]), "project.write")
        self.assertEqual(((scene.get("workflow_surface") or {}).get("state_field")), "state")
        self.assertEqual((((scene.get("workflow_surface") or {}).get("states") or [])[0].get("key")), "draft")
        self.assertEqual((((scene.get("validation_surface") or {}).get("required_fields") or [])[0]), "name")
        self.assertEqual((((scene.get("validation_surface") or {}).get("field_rules") or [])[0].get("field")), "name")


if __name__ == "__main__":
    unittest.main()
