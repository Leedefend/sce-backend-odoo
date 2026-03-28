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
    "odoo.addons.smart_core.core.runtime_page_parser_semantic_bridge",
    CORE_DIR / "runtime_page_parser_semantic_bridge.py",
)
core_pkg.runtime_page_parser_semantic_bridge = bridge_module
semantic_bridge_module = _load_module(
    "odoo.addons.smart_core.core.runtime_page_semantic_orchestration_bridge",
    CORE_DIR / "runtime_page_semantic_orchestration_bridge.py",
)
core_pkg.runtime_page_semantic_orchestration_bridge = semantic_bridge_module

page_contracts_builder = types.ModuleType("odoo.addons.smart_core.core.page_contracts_builder")


def _build_page_contracts(_data):
    return {
        "pages": {
            "home": {
                "page_orchestration_v1": {
                    "page": {"context": {}},
                    "render_hints": {},
                    "meta": {
                        "parser_semantic_surface": {
                        "parser_contract": {"view_type": "tree"},
                        "view_semantics": {"source_view": "tree", "capability_flags": {"is_editable": True}},
                        "native_view": {
                            "views": {
                                "tree": {"layout": []},
                                "search": {
                                    "filters": [{"name": "mine", "string": "我的"}],
                                    "group_bys": [{"name": "by_stage", "string": "按阶段", "group_by": "stage_id"}],
                                    "searchpanel": [{"name": "stage_id", "string": "阶段"}],
                                },
                            }
                        },
                        "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
                    }
                },
                }
            }
        }
    }


page_contracts_builder.build_page_contracts = _build_page_contracts
sys.modules["odoo.addons.smart_core.core.page_contracts_builder"] = page_contracts_builder
core_pkg.page_contracts_builder = page_contracts_builder

scene_contract_builder = types.ModuleType("odoo.addons.smart_core.core.scene_contract_builder")
scene_contract_builder.build_release_surface_scene_contract_from_page_contract = lambda *args, **kwargs: {"ok": True}
sys.modules["odoo.addons.smart_core.core.scene_contract_builder"] = scene_contract_builder
core_pkg.scene_contract_builder = scene_contract_builder

target = _load_module(
    "odoo.addons.smart_core.core.runtime_page_contract_builder",
    CORE_DIR / "runtime_page_contract_builder.py",
)


class TestRuntimePageContractBuilderSemantics(unittest.TestCase):
    def test_build_runtime_page_contracts_projects_parser_semantics(self):
        payload = target.build_runtime_page_contracts({"role_surface": {"role_code": "owner"}})
        home = (payload.get("pages") or {}).get("home") or {}

        self.assertEqual((home.get("runtime_context") or {}).get("view_type"), "tree")
        self.assertEqual((home.get("runtime_context") or {}).get("semantic_source_view"), "tree")
        self.assertIn("runtime_semantic_surface", home)
        self.assertTrue(
            ((((home.get("page_orchestration_v1") or {}).get("render_hints") or {}).get("runtime_semantic_view") or {}).get("capability_flags") or {}).get("is_editable")
        )
        self.assertEqual((home.get("runtime_context") or {}).get("runtime_mode"), "list_focus")
        self.assertEqual((home.get("runtime_context") or {}).get("search_mode"), "faceted")
        self.assertEqual((((home.get("page_orchestration_v1") or {}).get("render_hints") or {}).get("runtime_preferred_columns")), 2)
        self.assertEqual((((home.get("page_orchestration_v1") or {}).get("render_hints") or {}).get("runtime_search_profile")), "faceted")
        self.assertEqual(((((home.get("page_orchestration_v1") or {}).get("page") or {}).get("filters")) or [])[0]["kind"], "filter")
        self.assertEqual(
            [row.get("key") for row in (((home.get("page_orchestration_v1") or {}).get("page") or {}).get("global_actions") or [])],
            ["apply_filters", "reset_filters"],
        )


if __name__ == "__main__":
    unittest.main()
