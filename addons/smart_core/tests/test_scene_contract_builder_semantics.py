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

target = _load_module(
    "odoo.addons.smart_core.core.scene_contract_builder",
    CORE_DIR / "scene_contract_builder.py",
)


class TestSceneContractBuilderSemantics(unittest.TestCase):
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
        self.assertIn("parser_semantic_surface", payload.get("governance") or {})


if __name__ == "__main__":
    unittest.main()
