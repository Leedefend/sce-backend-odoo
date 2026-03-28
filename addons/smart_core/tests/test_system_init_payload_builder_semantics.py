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
                },
                "released_scene_semantic_surface": {
                    "scene_key": "workspace.home",
                    "page_surface": {"view_type": "kanban", "semantic_view": {"source_view": "kanban"}},
                    "parser_semantic_surface": {"parser_contract": {"view_type": "kanban"}},
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
                                "mode": "faceted",
                            },
                            "meta": {"target": {"route": "/my-work"}},
                        }
                    ],
                    "meta": {"generated_by": "test"},
                },
            }
        )

        self.assertEqual((payload.get("semantic_runtime") or {}).get("view_type"), "kanban")
        self.assertEqual(((payload.get("nav_meta") or {}).get("semantic_source_view")), "kanban")
        scene = ((payload.get("scene_ready_contract_v1") or {}).get("scenes") or [])[0]
        self.assertEqual(scene.get("view_type"), "kanban")
        self.assertIn("parser_semantic_surface", scene)
        self.assertEqual(((scene.get("search_surface") or {}).get("mode")), "faceted")
        self.assertEqual((((scene.get("search_surface") or {}).get("searchpanel") or [])[0].get("name")), "stage_id")


if __name__ == "__main__":
    unittest.main()
