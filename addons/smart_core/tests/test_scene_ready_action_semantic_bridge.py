# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_ready_action_semantic_bridge.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scene_ready_action_semantic_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bridge_module = _load_module()


class TestSceneReadyActionSemanticBridge(unittest.TestCase):
    def test_bridge_uses_record_group_for_form_semantics(self):
        payload = {
            "actions": [
                {"key": "save"},
                {"key": "submit"},
                {"key": "archive"},
            ],
            "action_surface": {"selection_mode": "single"},
            "parser_semantic_surface": {
                "parser_contract": {"view_type": "form"},
                "view_semantics": {"source_view": "form"},
            },
        }

        bridged = bridge_module.apply_scene_ready_action_semantic_bridge(payload)

        self.assertEqual(((bridged.get("action_surface") or {}).get("groups") or [])[0]["key"], "record_actions")
        self.assertEqual(len((bridged.get("action_surface") or {}).get("primary_actions") or []), 2)

    def test_bridge_uses_list_group_for_tree_semantics(self):
        payload = {
            "actions": [
                {"key": "open"},
                {"key": "bulk_approve"},
                {"key": "export"},
            ],
            "action_surface": {"selection_mode": "multi"},
            "parser_semantic_surface": {
                "parser_contract": {"view_type": "tree"},
                "view_semantics": {"source_view": "tree"},
            },
        }

        bridged = bridge_module.apply_scene_ready_action_semantic_bridge(payload)

        self.assertEqual(((bridged.get("action_surface") or {}).get("groups") or [])[0]["key"], "list_actions")
        self.assertEqual(len((bridged.get("action_surface") or {}).get("primary_actions") or []), 3)

    def test_bridge_derives_batch_capabilities_from_native_truth(self):
        payload = {
            "actions": [{"key": "open"}],
            "action_surface": {"selection_mode": "multi"},
            "permission_surface": {"allowed": True},
            "meta": {
                "ui_base_orchestrator_input": {
                    "field_fact": {"fields": {"active": {"type": "boolean"}}},
                    "permission_fact": {"write": True, "unlink": True},
                }
            },
            "parser_semantic_surface": {
                "parser_contract": {"view_type": "tree"},
                "view_semantics": {
                    "source_view": "tree",
                    "capability_flags": {"can_delete": True},
                },
                "semantic_page": {
                    "list_semantics": {
                        "editable": {"can_delete": True},
                    }
                },
            },
        }

        bridged = bridge_module.apply_scene_ready_action_semantic_bridge(payload)
        batch_capabilities = ((bridged.get("action_surface") or {}).get("batch_capabilities") or {})

        self.assertTrue(batch_capabilities.get("selection_required"))
        self.assertTrue(batch_capabilities.get("can_delete"))
        self.assertTrue(batch_capabilities.get("can_archive"))
        self.assertTrue(batch_capabilities.get("can_activate"))
        self.assertTrue(((batch_capabilities.get("native_basis") or {}).get("has_active_field")))

    def test_bridge_preserves_batch_capabilities_without_action_items(self):
        payload = {
            "action_surface": {"selection_mode": "multi"},
            "meta": {
                "ui_base_orchestrator_input": {
                    "field_fact": {"fields": {"active": {"type": "boolean"}}},
                    "permission_fact": {"write": True, "unlink": False},
                }
            },
            "parser_semantic_surface": {
                "parser_contract": {"view_type": "tree"},
                "view_semantics": {
                    "source_view": "tree",
                    "capability_flags": {"can_delete": False},
                },
            },
        }

        bridged = bridge_module.apply_scene_ready_action_semantic_bridge(payload)
        batch_capabilities = ((bridged.get("action_surface") or {}).get("batch_capabilities") or {})

        self.assertEqual((bridged.get("action_surface") or {}).get("primary_actions"), None)
        self.assertTrue(batch_capabilities.get("selection_required"))
        self.assertFalse(batch_capabilities.get("can_delete"))
        self.assertTrue(batch_capabilities.get("can_archive"))


if __name__ == "__main__":
    unittest.main()
