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

semantic_bridge_module = types.ModuleType(
    "odoo.addons.smart_core.core.system_init_scene_runtime_semantic_bridge"
)


def _identity_bridge(data, active_scene_key=""):
    return data


semantic_bridge_module.apply_system_init_scene_runtime_semantic_bridge = _identity_bridge
sys.modules[semantic_bridge_module.__name__] = semantic_bridge_module

builder = _load_module(
    "odoo.addons.smart_core.core.system_init_scene_runtime_surface_builder",
    CORE_DIR / "system_init_scene_runtime_surface_builder.py",
)
context_module = _load_module(
    "odoo.addons.smart_core.core.system_init_scene_runtime_surface_context",
    CORE_DIR / "system_init_scene_runtime_surface_context.py",
)


class _Company:
    id = 7


class _Env:
    company = _Company()


class TestSystemInitSceneRuntimeSurfaceBuilder(unittest.TestCase):
    def test_scene_nav_contract_kept_as_auxiliary_contract(self):
        legacy_nav = [
            {
                "key": "root:legacy",
                "label": "智能施工 2.0",
                "menu_id": 265,
                "children": [
                    {"key": "menu:project", "label": "项目管理", "menu_id": 277, "children": []},
                    {"key": "menu:contract", "label": "合同管理", "menu_id": 291, "children": []},
                ],
                "meta": {"menu_xmlid": "smart_construction_core.menu_sc_root"},
            }
        ]
        default_route = {
            "menu_id": 277,
            "scene_key": "projects.list",
            "route": "/s/projects.list",
            "reason": "menu_fallback",
        }
        scene_nav_contract = {
            "source": "scene_contract_v1",
            "nav": [
                {
                    "key": "root:scene_contract",
                    "label": "场景导航",
                    "menu_id": 700000001,
                    "children": [],
                    "meta": {"menu_xmlid": "scene.contract.root"},
                }
            ],
            "default_route": {
                "menu_id": 700000002,
                "scene_key": "projects.ledger",
                "route": "/workbench?scene=projects.ledger",
                "reason": "role_landing",
            },
            "meta": {"candidate_count": 3, "remaining_hidden": True},
        }

        surface_ctx = context_module.SystemInitSceneRuntimeSurfaceContext(
            env=_Env(),
            params={"scene": "web"},
            data={
                "nav": legacy_nav,
                "nav_meta": {"nav_source": "legacy_nav_v1"},
                "default_route": dict(default_route),
                "scenes": [{"code": "projects.list", "target": {"route": "/s/projects.list"}}],
                "scene_version": "v1",
                "schema_version": "1.0.0",
            },
            role_surface={"role_code": "executive", "landing_scene_key": "projects.list"},
            contract_mode="strict",
            scene_channel="stable",
            nav_tree=legacy_nav,
            platform_minimum_surface_mode=False,
            build_platform_minimum_nav_contract_fn=lambda: {},
            resolve_delivery_policy_runtime_fn=lambda env, params: {},
            filter_delivery_scenes_fn=lambda scenes, **kwargs: {"delivery_scenes": scenes, "meta": {"enabled": False}},
            startup_scene_subset_resolver_fn=lambda data, params=None: set(),
            filter_startup_scenes_for_preload_fn=lambda scenes, subset: scenes,
            bind_scene_assets_fn=lambda env, scenes, role_code=None, company_id=None: {"scenes": scenes},
            build_scene_ready_contract_fn=lambda **kwargs: {"scenes": kwargs.get("scenes") or []},
            build_scene_nav_contract_fn=lambda data: scene_nav_contract,
        )

        result = builder.SystemInitSceneRuntimeSurfaceBuilder.apply(surface_ctx=surface_ctx)
        data = result["data"]

        self.assertEqual(data.get("nav"), legacy_nav)
        self.assertEqual(data.get("default_route"), default_route)
        self.assertEqual(data.get("nav_legacy"), legacy_nav)
        self.assertEqual(data.get("nav_contract"), scene_nav_contract)
        self.assertEqual((data.get("nav_meta") or {}).get("nav_source"), "legacy_nav_v1")
        self.assertTrue((data.get("nav_meta") or {}).get("scene_nav_contract_available"))
        self.assertEqual(
            ((data.get("nav_meta") or {}).get("scene_nav_meta") or {}).get("candidate_count"),
            3,
        )


if __name__ == "__main__":
    unittest.main()
