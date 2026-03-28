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

semantic_bridge = _load_module(
    "odoo.addons.smart_core.core.system_init_scene_runtime_semantic_bridge",
    CORE_DIR / "system_init_scene_runtime_semantic_bridge.py",
)
core_pkg.system_init_scene_runtime_semantic_bridge = semantic_bridge
target = _load_module(
    "odoo.addons.smart_core.core.system_init_scene_runtime_surface_builder",
    CORE_DIR / "system_init_scene_runtime_surface_builder.py",
)


class _Env:
    company = types.SimpleNamespace(id=7)


class _SurfaceCtx:
    env = _Env()
    params = {}
    role_surface = {"landing_scene_key": "workspace.home", "role_code": "owner"}
    contract_mode = "default"
    scene_channel = "portal"
    nav_tree = []
    platform_minimum_surface_mode = False
    data = {
        "scenes": [{"key": "workspace.home"}],
        "nav_meta": {},
        "default_route": {"scene_key": "workspace.home"},
        "scene_version": "v1",
        "schema_version": "1.0.0",
    }

    @staticmethod
    def build_platform_minimum_nav_contract_fn():
        return {"nav": [], "default_route": {"scene_key": "workspace.home"}}

    @staticmethod
    def resolve_delivery_policy_runtime_fn(_env, _params):
        return {"surface": "default", "runtime_env": "dev", "enabled": False}

    @staticmethod
    def filter_delivery_scenes_fn(scenes, **_kwargs):
        return {"delivery_scenes": scenes, "meta": {"enabled": False}}

    @staticmethod
    def startup_scene_subset_resolver_fn(_data, **_kwargs):
        return ["workspace.home"]

    @staticmethod
    def filter_startup_scenes_for_preload_fn(scenes, _subset):
        return scenes

    @staticmethod
    def bind_scene_assets_fn(_env, scenes, **_kwargs):
        return {"scenes": scenes}

    @staticmethod
    def build_scene_ready_contract_fn(**_kwargs):
        return {
            "contract_version": "v1",
            "active_scene_key": "workspace.home",
            "scenes": [
                {
                    "scene": {"key": "workspace.home"},
                    "page": {"context": {"scene_key": "workspace.home"}},
                    "parser_semantic_surface": {
                        "parser_contract": {"view_type": "kanban"},
                        "view_semantics": {"source_view": "kanban", "capability_flags": {"can_create": True}},
                        "native_view": {"views": {"kanban": {"cards": []}}},
                        "semantic_page": {"kanban_semantics": {"lane_count": 3}},
                    },
                    "semantic_view": {"source_view": "kanban", "capability_flags": {"can_create": True}},
                    "semantic_page": {"kanban_semantics": {"lane_count": 3}},
                    "view_type": "kanban",
                    "search_surface": {"mode": "faceted", "searchpanel": [{"name": "stage_id"}]},
                    "permission_surface": {"allowed": False, "reason_code": "missing_capability"},
                    "workflow_surface": {"state_field": "state", "states": [{"key": "draft"}]},
                    "validation_surface": {"required_fields": ["name"]},
                }
            ],
        }

    @staticmethod
    def build_scene_nav_contract_fn(_payload):
        return {"nav": [{"key": "workspace.home"}], "source": "scene_contract_v1", "meta": {"count": 1}}


class TestSystemInitSceneRuntimeSemantics(unittest.TestCase):
    def test_runtime_surface_builder_projects_scene_ready_semantics(self):
        result = target.SystemInitSceneRuntimeSurfaceBuilder.apply(surface_ctx=_SurfaceCtx())
        data = result.get("data") or {}

        self.assertEqual((data.get("semantic_runtime") or {}).get("view_type"), "kanban")
        self.assertEqual((((data.get("semantic_runtime") or {}).get("semantic_view") or {}).get("source_view")), "kanban")
        self.assertEqual((((data.get("released_scene_semantic_surface") or {}).get("page_surface") or {}).get("view_type")), "kanban")
        self.assertEqual(((data.get("semantic_runtime") or {}).get("search_surface") or {}).get("mode"), "faceted")
        self.assertEqual(((data.get("semantic_runtime") or {}).get("permission_surface") or {}).get("reason_code"), "missing_capability")
        self.assertEqual(((data.get("semantic_runtime") or {}).get("workflow_surface") or {}).get("state_field"), "state")
        self.assertEqual((((data.get("semantic_runtime") or {}).get("validation_surface") or {}).get("required_fields") or [])[0], "name")
        self.assertEqual(((data.get("nav_meta") or {}).get("semantic_scene_key")), "workspace.home")


if __name__ == "__main__":
    unittest.main()
