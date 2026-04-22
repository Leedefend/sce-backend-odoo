# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_ready_semantic_orchestration_bridge.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scene_ready_semantic_orchestration_bridge_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bridge_module = _load_module()


class TestSceneReadySemanticOrchestrationBridge(unittest.TestCase):
    def test_bridge_overrides_legacy_view_modes_from_parser_semantics(self):
        payload = {
            "view_modes": [{"key": "kanban", "label": "看板", "enabled": True}],
            "action_surface": {"selection_mode": "single"},
            "parser_semantic_surface": {
                "parser_contract": {"view_type": "form"},
                "view_semantics": {"source_view": "form", "capability_flags": {"is_editable": True}},
                "native_view": {"views": {"form": {"layout": []}, "search": {"layout": []}}},
                "semantic_page": {"title_node": {"text": "项目"}},
            },
        }

        bridged = bridge_module.apply_scene_ready_semantic_orchestration_bridge(payload)

        self.assertEqual((bridged.get("view_modes") or [])[0]["key"], "form")
        self.assertEqual(((bridged.get("action_surface") or {}).get("selection_mode")), "single")

    def test_bridge_uses_multi_selection_for_list_like_semantics(self):
        payload = {
            "action_surface": {"selection_mode": "single"},
            "parser_semantic_surface": {
                "parser_contract": {"view_type": "tree"},
                "view_semantics": {"source_view": "tree", "capability_flags": {"is_editable": True}},
                "native_view": {"views": {"tree": {"layout": []}, "kanban": {"cards": []}}},
                "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
            },
        }

        bridged = bridge_module.apply_scene_ready_semantic_orchestration_bridge(payload)

        self.assertEqual((bridged.get("view_modes") or [])[0]["key"], "tree")
        self.assertEqual(((bridged.get("action_surface") or {}).get("selection_mode")), "multi")

    def test_bridge_materializes_action_surface_when_missing(self):
        payload = {
            "parser_semantic_surface": {
                "parser_contract": {"view_type": "tree"},
                "view_semantics": {"source_view": "tree", "capability_flags": {"is_editable": True}},
                "native_view": {"views": {"tree": {"layout": []}}},
                "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
            },
        }

        bridged = bridge_module.apply_scene_ready_semantic_orchestration_bridge(payload)

        self.assertEqual(((bridged.get("action_surface") or {}).get("selection_mode")), "multi")

    def test_bridge_normalizes_direct_runtime_handoff_surface(self):
        payload = {
            "scene": {"key": "projects.list"},
            "delivery_handoff_v1": {
                "family": "projects",
                "runtime_entry_type": "governed_user_flow",
                "runtime_consumer": "family_runtime_consumer",
                "runtime_mode": "direct",
                "user_entry": "menu:smart_construction_core.menu_sc_root",
                "final_scene": "projects.list",
                "primary_action": {"action_xmlid": "smart_construction_core.action_sc_project_list"},
                "required_provider": "construction.projects_ledger_provider.v1|construction.projects_detail_provider.v1",
                "fallback_policy": {"type": "native_action_compat"},
                "acceptance": {"runtime_ready": True, "workflow_ready": True, "advisory_only": True},
            },
        }

        bridged = bridge_module.apply_scene_ready_semantic_orchestration_bridge(payload)
        handoff = bridged.get("runtime_handoff_surface") or {}

        self.assertEqual(handoff.get("family"), "projects")
        self.assertEqual(handoff.get("consume_mode"), "direct")
        self.assertEqual(handoff.get("runtime_consumer"), "family_runtime_consumer")
        self.assertEqual(handoff.get("final_scene"), "projects.list")
        self.assertTrue(handoff.get("workflow_ready"))

    def test_bridge_marks_payment_handoff_as_advisory_consume(self):
        payload = {
            "scene": {"key": "payments.approval"},
            "delivery_handoff_v1": {
                "family": "payment_approval",
                "runtime_entry_type": "governed_user_flow",
                "runtime_consumer": "family_runtime_consumer",
                "runtime_mode": "direct",
                "user_entry": "menu:smart_construction_core.menu_sc_tier_review_my_payment_request",
                "final_scene": "payments.approval",
                "primary_action": {"action_xmlid": "smart_construction_core.action_sc_tier_review_my_payment_request"},
                "required_provider": "construction.approval_workbench_provider.v1",
                "fallback_policy": {"type": "native_action_compat"},
                "acceptance": {"runtime_ready": True, "workflow_ready": True, "advisory_only": True},
            },
        }

        bridged = bridge_module.apply_scene_ready_semantic_orchestration_bridge(payload)
        handoff = bridged.get("runtime_handoff_surface") or {}

        self.assertEqual(handoff.get("family"), "payment_approval")
        self.assertEqual(handoff.get("consume_mode"), "advisory")
        self.assertTrue(handoff.get("runtime_ready"))
        self.assertTrue(handoff.get("advisory_only"))

    def test_bridge_builds_product_delivery_surface_for_direct_family(self):
        payload = {
            "scene": {"key": "projects.list"},
            "delivery_handoff_v1": {
                "family": "projects",
                "runtime_entry_type": "governed_user_flow",
                "runtime_consumer": "family_runtime_consumer",
                "runtime_mode": "direct",
                "user_entry": "menu:smart_construction_core.menu_sc_root",
                "final_scene": "projects.list",
                "primary_action": {"action_xmlid": "smart_construction_core.action_sc_project_list"},
                "required_provider": "construction.projects_ledger_provider.v1|construction.projects_detail_provider.v1",
                "fallback_policy": {"type": "native_action_compat"},
                "acceptance": {"runtime_ready": True, "workflow_ready": True, "advisory_only": True},
            },
        }

        bridged = bridge_module.apply_scene_ready_semantic_orchestration_bridge(payload)
        delivery = bridged.get("product_delivery_surface") or {}

        self.assertEqual(delivery.get("family"), "projects")
        self.assertEqual(delivery.get("delivery_mode"), "direct_delivery")
        self.assertEqual(delivery.get("entry_kind"), "primary_action")
        self.assertEqual(delivery.get("final_scene"), "projects.list")
        self.assertFalse(((delivery.get("advisory") or {}).get("enabled")))

    def test_bridge_builds_product_delivery_surface_for_advisory_family(self):
        payload = {
            "scene": {"key": "payments.approval"},
            "delivery_handoff_v1": {
                "family": "payment_approval",
                "runtime_entry_type": "governed_user_flow",
                "runtime_consumer": "family_runtime_consumer",
                "runtime_mode": "direct",
                "user_entry": "menu:smart_construction_core.menu_sc_tier_review_my_payment_request",
                "final_scene": "payments.approval",
                "primary_action": {"action_xmlid": "smart_construction_core.action_sc_tier_review_my_payment_request"},
                "required_provider": "construction.approval_workbench_provider.v1",
                "fallback_policy": {"type": "native_action_compat"},
                "acceptance": {"runtime_ready": True, "workflow_ready": True, "advisory_only": True},
            },
        }

        bridged = bridge_module.apply_scene_ready_semantic_orchestration_bridge(payload)
        delivery = bridged.get("product_delivery_surface") or {}

        self.assertEqual(delivery.get("family"), "payment_approval")
        self.assertEqual(delivery.get("delivery_mode"), "advisory_only")
        self.assertTrue(((delivery.get("advisory") or {}).get("enabled")))
        self.assertEqual(((delivery.get("acceptance") or {}).get("advisory_only")), True)


if __name__ == "__main__":
    unittest.main()
