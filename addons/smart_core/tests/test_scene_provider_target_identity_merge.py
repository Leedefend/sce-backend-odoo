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

utils_pkg = sys.modules.setdefault("odoo.addons.smart_core.utils", types.ModuleType("odoo.addons.smart_core.utils"))
utils_pkg.__path__ = [str(CORE_DIR.parent / "utils")]
smart_core_pkg.utils = utils_pkg

extension_hooks = types.ModuleType("odoo.addons.smart_core.utils.extension_hooks")
extension_hooks.call_extension_hook_first = lambda env, hook_name, *args, **kwargs: {"projects.list"} if hook_name == "smart_core_critical_scene_target_overrides" else {}
sys.modules["odoo.addons.smart_core.utils.extension_hooks"] = extension_hooks
utils_pkg.extension_hooks = extension_hooks

registry_provider = types.ModuleType("odoo.addons.smart_core.core.scene_registry_provider")
registry_provider.get_schema_version = lambda env: "scene_registry_v1"
registry_provider.get_scene_version = lambda env: "scene_v1"
registry_provider.has_db_scenes = lambda env: True
registry_provider.load_scene_configs = lambda env, drift=None: []
sys.modules["odoo.addons.smart_core.core.scene_registry_provider"] = registry_provider
core_pkg.scene_registry_provider = registry_provider

target = _load_module(
    "odoo.addons.smart_core.core.scene_provider",
    CORE_DIR / "scene_provider.py",
)


class _FakeRecord:
    def __init__(self, record_id: int, model_name: str):
        self.id = record_id
        self._name = model_name


class _FakeEnv:
    def ref(self, xmlid: str, raise_if_not_found=False):
        mapping = {
            "smart_construction_core.action_sc_project_list": _FakeRecord(452, "ir.actions.act_window"),
            "smart_construction_core.menu_sc_root": _FakeRecord(265, "ir.ui.menu"),
        }
        return mapping.get(xmlid)


class TestSceneProviderTargetIdentityMerge(unittest.TestCase):
    def _provider_payload(self, scene_key, runtime_context=None):
        if scene_key != "projects.list":
            return {}
        return {
            "primary_action": {
                "action_xmlid": "smart_construction_core.action_sc_project_list",
            },
            "fallback_strategy": {
                "menu_xmlid": "smart_construction_core.menu_sc_root",
                "action_xmlid": "smart_construction_core.action_sc_project_list",
            },
        }

    def test_merge_missing_scenes_prefers_provider_identity_for_critical_scene(self):
        original_registry_load = target.registry_load_scene_configs
        original_provider_payload = target._resolve_scene_provider_payload
        original_extension_hook = target.call_extension_hook_first
        try:
            target.registry_load_scene_configs = lambda env: []
            target._resolve_scene_provider_payload = self._provider_payload
            target.call_extension_hook_first = lambda env, hook_name, *args, **kwargs: {"projects.list"} if hook_name == "smart_core_critical_scene_target_overrides" else {}

            rows = target.merge_missing_scenes_from_registry(
                _FakeEnv(),
                [
                    {
                        "code": "projects.list",
                        "name": "项目列表",
                        "target": {
                            "route": "/s/projects.list",
                            "action_id": 519,
                            "menu_id": 329,
                        },
                    }
                ],
                [],
            )
        finally:
            target.registry_load_scene_configs = original_registry_load
            target._resolve_scene_provider_payload = original_provider_payload
            target.call_extension_hook_first = original_extension_hook

        projects_list = rows[0]
        scene_target = projects_list.get("target") or {}
        self.assertEqual(scene_target.get("route"), "/s/projects.list")
        self.assertEqual(scene_target.get("action_xmlid"), "smart_construction_core.action_sc_project_list")
        self.assertEqual(scene_target.get("menu_xmlid"), "smart_construction_core.menu_sc_root")
        self.assertEqual(scene_target.get("action_id"), 452)
        self.assertEqual(scene_target.get("menu_id"), 265)

    def test_provider_identity_survives_stale_registry_numeric_target(self):
        original_registry_load = target.registry_load_scene_configs
        original_provider_payload = target._resolve_scene_provider_payload
        original_extension_hook = target.call_extension_hook_first
        try:
            target.registry_load_scene_configs = lambda env: [
                {
                    "code": "projects.list",
                    "name": "项目列表",
                    "target": {
                        "route": "/s/projects.list",
                        "action_id": 519,
                        "menu_id": 329,
                    },
                }
            ]
            target._resolve_scene_provider_payload = self._provider_payload
            target.call_extension_hook_first = lambda env, hook_name, *args, **kwargs: {"projects.list"} if hook_name == "smart_core_critical_scene_target_overrides" else {}

            rows = target.merge_missing_scenes_from_registry(
                _FakeEnv(),
                [
                    {
                        "code": "projects.list",
                        "name": "项目列表",
                        "target": {
                            "route": "/s/projects.list",
                            "action_id": 519,
                            "menu_id": 329,
                        },
                    }
                ],
                [],
            )
        finally:
            target.registry_load_scene_configs = original_registry_load
            target._resolve_scene_provider_payload = original_provider_payload
            target.call_extension_hook_first = original_extension_hook

        scene_target = rows[0].get("target") or {}
        self.assertEqual(scene_target.get("route"), "/s/projects.list")
        self.assertEqual(scene_target.get("action_xmlid"), "smart_construction_core.action_sc_project_list")
        self.assertEqual(scene_target.get("menu_xmlid"), "smart_construction_core.menu_sc_root")
        self.assertEqual(scene_target.get("action_id"), 452)
        self.assertEqual(scene_target.get("menu_id"), 265)


if __name__ == "__main__":
    unittest.main()
