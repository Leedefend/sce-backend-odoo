# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


SMART_CORE_DIR = Path(__file__).resolve().parents[1]


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
smart_core_pkg.__path__ = [str(SMART_CORE_DIR)]
utils_pkg = sys.modules.setdefault("odoo.addons.smart_core.utils", types.ModuleType("odoo.addons.smart_core.utils"))
utils_pkg.__path__ = [str(SMART_CORE_DIR / "utils")]
extension_hooks = types.ModuleType("odoo.addons.smart_core.utils.extension_hooks")
extension_hooks.call_extension_hook_first = lambda *args, **kwargs: None
sys.modules["odoo.addons.smart_core.utils.extension_hooks"] = extension_hooks

target = _load_module(
    "odoo.addons.smart_core.identity.identity_resolver",
    SMART_CORE_DIR / "identity" / "identity_resolver.py",
)


class TestIdentityResolverEntryTarget(unittest.TestCase):
    def test_build_role_surface_exposes_landing_entry_target(self):
        resolver = target.IdentityResolver()
        role_surface = resolver.build_role_surface(set(), [], {"workspace.home"})

        self.assertEqual(role_surface.get("landing_scene_key"), "workspace.home")
        self.assertEqual(((role_surface.get("landing_entry_target") or {}).get("type")), "scene")
        self.assertEqual(((role_surface.get("landing_entry_target") or {}).get("scene_key")), "workspace.home")
        self.assertEqual(((role_surface.get("landing_entry_target") or {}).get("route")), "/s/workspace.home")

    def test_build_role_surface_merges_visible_nav_scene_candidates(self):
        resolver = target.IdentityResolver()
        role_surface = resolver.build_role_surface(
            set(),
            [
                {
                    "menu_id": 314,
                    "children": [],
                    "meta": {
                        "scene_key": "projects.ledger",
                        "route": "/s/projects.ledger?menu_id=314",
                    },
                },
                {
                    "menu_id": 317,
                    "children": [],
                    "entry_target": {
                        "type": "scene",
                        "scene_key": "cost.project_budget",
                        "route": "/s/cost.project_budget?menu_id=317",
                    },
                },
            ],
            {"workspace.home", "projects.ledger", "cost.project_budget"},
        )

        self.assertEqual(role_surface.get("landing_scene_key"), "workspace.home")
        self.assertEqual(
            role_surface.get("scene_candidates"),
            ["portal.dashboard", "workspace.home", "projects.ledger", "cost.project_budget"],
        )

    def test_build_role_surface_appends_available_scene_keys_when_nav_lacks_scene_identity(self):
        resolver = target.IdentityResolver()
        role_surface = resolver.build_role_surface(
            set(),
            [
                {
                    "menu_id": 317,
                    "children": [],
                    "meta": {
                        "action_id": 485,
                    },
                },
            ],
            {"workspace.home", "projects.ledger", "cost.project_budget"},
        )

        self.assertEqual(
            role_surface.get("scene_candidates"),
            ["portal.dashboard", "workspace.home", "cost.project_budget", "projects.ledger"],
        )

    def test_infer_default_route_from_nav_prefers_scene_entry_target(self):
        resolver = target.IdentityResolver()
        default_route = resolver.infer_default_route_from_nav([
            {
                "menu_id": 202,
                "children": [],
                "meta": {"scene_key": "projects.list", "action_id": 502, "model": "project.project", "record_id": 42},
            }
        ])

        self.assertEqual(default_route.get("scene_key"), "projects.list")
        self.assertEqual(default_route.get("route"), "/s/projects.list")
        self.assertEqual(((default_route.get("entry_target") or {}).get("scene_key")), "projects.list")
        self.assertEqual(((((default_route.get("entry_target") or {}).get("compatibility_refs") or {}).get("menu_id"))), 202)
        self.assertEqual(((((default_route.get("entry_target") or {}).get("record_entry") or {}).get("model"))), "project.project")
        self.assertEqual(((((default_route.get("entry_target") or {}).get("record_entry") or {}).get("record_id"))), 42)


if __name__ == "__main__":
    unittest.main()
