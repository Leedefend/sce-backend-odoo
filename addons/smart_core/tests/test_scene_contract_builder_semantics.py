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

bridge_module = _load_module(
    "odoo.addons.smart_core.core.scene_contract_parser_semantic_bridge",
    CORE_DIR / "scene_contract_parser_semantic_bridge.py",
)
core_pkg.scene_contract_parser_semantic_bridge = bridge_module
semantic_bridge_module = _load_module(
    "odoo.addons.smart_core.core.scene_contract_semantic_orchestration_bridge",
    CORE_DIR / "scene_contract_semantic_orchestration_bridge.py",
)
core_pkg.scene_contract_semantic_orchestration_bridge = semantic_bridge_module

target = _load_module(
    "odoo.addons.smart_core.core.scene_contract_builder",
    CORE_DIR / "scene_contract_builder.py",
)
release_navigation_target = _load_module(
    "odoo.addons.smart_core.core.release_navigation_contract_builder",
    CORE_DIR / "release_navigation_contract_builder.py",
)


class TestSceneContractBuilderSemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        target.register_legacy_product_title("fr1", "FR-1 项目立项")
        target.register_legacy_product_title("fr4", "FR-4 支付记录")
        target.register_route_only_actions(
            "projects.intake",
            {
                "layout": "entry_cards",
                "primary_actions": [
                    {
                        "key": "quick_project_create",
                        "label": "快速创建（推荐）",
                        "target": {"type": "route", "route": "/s/projects.intake?intake_mode=quick", "scene_key": "projects.intake"},
                    }
                ],
                "secondary_actions": [
                    {
                        "key": "standard_project_intake",
                        "label": "标准立项",
                        "target": {"type": "route", "route": "/s/projects.intake", "scene_key": "projects.intake"},
                    }
                ],
            },
        )

    def test_delivery_entry_projects_intake_actions_publish_scene_ready_routes(self):
        payload = target.build_release_surface_scene_contract_from_delivery_entry(
            {
                "scene_key": "projects.intake",
                "label": "FR-1 项目立项",
                "route": "/s/projects.intake",
                "product_key": "fr1",
                "capability_key": "delivery.fr1.project_intake",
            }
        )

        actions = payload.get("actions") or {}
        primary = (actions.get("primary_actions") or [{}])[0]
        secondary = (actions.get("secondary_actions") or [{}])[0]

        self.assertEqual(((primary.get("target") or {}).get("route")), "/s/projects.intake?intake_mode=quick")
        self.assertEqual(((primary.get("target") or {}).get("scene_key")), "projects.intake")
        self.assertEqual(((secondary.get("target") or {}).get("route")), "/s/projects.intake")
        self.assertEqual(((secondary.get("target") or {}).get("scene_key")), "projects.intake")

    def test_delivery_entry_legacy_product_title_mapping_is_marked_as_projection(self):
        payload = target.build_release_surface_scene_contract_from_delivery_entry(
            {
                "scene_key": "payment",
                "route": "/release/fr4",
                "product_key": "fr4",
                "capability_key": "delivery.fr4.payment_tracking",
            }
        )

        governance = payload.get("governance") or {}
        self.assertEqual((governance.get("source_authority") or {}).get("kind"), "release_surface_scene_contract_projection")
        self.assertTrue(governance.get("no_business_fact_authority"))
        self.assertEqual(
            (governance.get("legacy_product_title_source_authority") or {}).get("kind"),
            "legacy_release_product_title_projection",
        )

    def test_runtime_entry_projects_parser_semantics_into_scene_contract(self):
        payload = target.build_release_surface_scene_contract_from_runtime_entry(
            {
                "scene_key": "workspace.home",
                "title": "工作台",
                "parser_contract": {"view_type": "kanban"},
                "view_semantics": {"source_view": "kanban", "capability_flags": {"has_menu": True}},
                "native_view": {"views": {"kanban": {"layout": []}}},
                "semantic_page": {"kanban_semantics": {"lane_count": 3}},
            },
            product_key="my_work",
            capability="delivery.my_work.workspace",
            route="/my-work",
            diagnostics_ref="runtime.contract:test",
        )

        self.assertEqual((((payload.get("page") or {}).get("surface") or {}).get("view_type")), "kanban")
        self.assertEqual(
            (((((payload.get("page") or {}).get("surface") or {}).get("semantic_view") or {}).get("source_view"))),
            "kanban",
        )
        self.assertEqual(((payload.get("page") or {}).get("layout")), "board")
        self.assertIn("parser_semantic_surface", payload.get("governance") or {})

    def test_page_contract_projects_parser_semantics_into_scene_contract(self):
        payload = target.build_release_surface_scene_contract_from_page_contract(
            {
                "page_orchestration_v1": {
                    "page": {"title": "我的工作", "layout_mode": "workspace"},
                    "zones": [],
                    "action_schema": {"actions": {}},
                    "meta": {
                        "parser_semantic_surface": {
                            "parser_contract": {"view_type": "tree"},
                            "view_semantics": {"source_view": "tree", "capability_flags": {"is_editable": True}},
                            "native_view": {"views": {"tree": {"layout": []}}},
                            "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
                        }
                    },
                }
            },
            scene_key="my_work.workspace",
            title="我的工作",
            product_key="my_work",
            capability="delivery.my_work.workspace",
            route="/my-work",
            diagnostics_ref="page.contract:test",
        )

        self.assertEqual((((payload.get("page") or {}).get("surface") or {}).get("view_type")), "tree")
        self.assertEqual(((payload.get("page") or {}).get("layout")), "list")
        self.assertIn("parser_semantic_surface", payload.get("governance") or {})

    def test_release_navigation_legacy_leaves_are_extension_registered(self):
        empty_payload = release_navigation_target.build_release_navigation_contract({"role_surface": {"role_code": "operator"}})
        empty_root = (empty_payload.get("nav") or [{}])[0]
        empty_groups = empty_root.get("children") or []

        release_navigation_target.register_legacy_release_navigation_leaf(
            key="release.fr1.project_intake",
            label="FR-1 项目立项",
            route="/s/projects.intake",
            scene_key="projects.intake",
            product_key="fr1",
        )
        release_navigation_target.register_legacy_release_navigation_leaf(
            key="release.fr1.project_intake",
            label="FR-1 项目立项",
            route="/s/projects.intake",
            scene_key="projects.intake",
            product_key="fr1",
        )
        payload = release_navigation_target.build_release_navigation_contract({"role_surface": {"role_code": "operator"}})
        root = (payload.get("nav") or [{}])[0]
        groups = root.get("children") or []
        leaves = (groups[0].get("children") if groups else []) or []

        self.assertEqual((empty_groups[0].get("children") if empty_groups else []) or [], [])
        self.assertEqual(len(leaves), 1)
        self.assertEqual(leaves[0].get("label"), "FR-1 项目立项")
        self.assertEqual(((leaves[0].get("meta") or {}).get("source_authority") or {}).get("kind"), "legacy_release_navigation_fallback")


if __name__ == "__main__":
    unittest.main()
