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
http_mod = types.ModuleType("odoo.http")
http_mod.Controller = object
http_mod.route = lambda *args, **kwargs: (lambda func: func)
http_mod.request = types.SimpleNamespace()
sys.modules["odoo.http"] = http_mod
sys.modules["odoo"].http = http_mod

exceptions_mod = types.ModuleType("odoo.exceptions")
exceptions_mod.AccessDenied = type("AccessDenied", (Exception,), {})
sys.modules["odoo.exceptions"] = exceptions_mod

addons_pkg = sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
smart_core_pkg.__path__ = [str(SMART_CORE_DIR)]

trace_mod = types.ModuleType("odoo.addons.smart_core.core.trace")
trace_mod.get_trace_id = lambda headers=None: "trace-demo"
sys.modules["odoo.addons.smart_core.core.trace"] = trace_mod

menu_fact_service_mod = types.ModuleType("odoo.addons.smart_core.delivery.menu_fact_service")
menu_fact_service_mod.MenuFactService = object
sys.modules["odoo.addons.smart_core.delivery.menu_fact_service"] = menu_fact_service_mod

menu_delivery_convergence_mod = types.ModuleType("odoo.addons.smart_core.delivery.menu_delivery_convergence_service")
menu_delivery_convergence_mod.MenuDeliveryConvergenceService = object
sys.modules["odoo.addons.smart_core.delivery.menu_delivery_convergence_service"] = menu_delivery_convergence_mod

menu_target_interpreter_mod = types.ModuleType("odoo.addons.smart_core.delivery.menu_target_interpreter_service")
menu_target_interpreter_mod.MenuTargetInterpreterService = object
sys.modules["odoo.addons.smart_core.delivery.menu_target_interpreter_service"] = menu_target_interpreter_mod

auth_mod = types.ModuleType("odoo.addons.smart_core.security.auth")
auth_mod.get_user_from_token = lambda: None
sys.modules["odoo.addons.smart_core.security.auth"] = auth_mod

core_exceptions_mod = types.ModuleType("odoo.addons.smart_core.core.exceptions")
core_exceptions_mod.AUTH_REQUIRED = "AUTH_REQUIRED"
core_exceptions_mod.BAD_REQUEST = "BAD_REQUEST"
core_exceptions_mod.DEFAULT_API_VERSION = "v1"
core_exceptions_mod.DEFAULT_CONTRACT_VERSION = "v1"
core_exceptions_mod.build_error_envelope = lambda **kwargs: kwargs
sys.modules["odoo.addons.smart_core.core.exceptions"] = core_exceptions_mod

extension_hooks_mod = types.ModuleType("odoo.addons.smart_core.utils.extension_hooks")
extension_hooks_mod.call_extension_hook_first = lambda env, hook_name, *args, **kwargs: None
sys.modules["odoo.addons.smart_core.utils.extension_hooks"] = extension_hooks_mod

platform_menu_api = _load_module(
    "odoo.addons.smart_core.controllers.platform_menu_api",
    SMART_CORE_DIR / "controllers" / "platform_menu_api.py",
)


class _DummyRef:
    def __init__(self, record_id: int):
        self.id = record_id


class _DummyEnv:
    def __init__(self, refs=None):
        self._refs = dict(refs or {})

    def ref(self, xmlid, raise_if_not_found=False):
        _ = raise_if_not_found
        record_id = self._refs.get(str(xmlid or "").strip())
        if not record_id:
            return None
        return _DummyRef(int(record_id))


class TestPlatformMenuAPISceneMap(unittest.TestCase):
    def test_resolve_navigation_scene_map_merges_extension_payload(self):
        env = _DummyEnv(
            refs={
                "smart_enterprise_base.menu_enterprise_company": 31,
                "smart_enterprise_base.action_enterprise_company": 246,
            }
        )

        platform_menu_api.call_extension_hook_first = lambda env, hook_name, *args, **kwargs: {
            "menu_scene_map": {
                "smart_enterprise_base.menu_enterprise_company": "enterprise.company",
            },
            "action_xmlid_scene_map": {
                "smart_enterprise_base.action_enterprise_company": "enterprise.company",
            },
            "model_view_scene_map": {
                ("res.company", "form"): "enterprise.company",
            },
        }

        resolved = platform_menu_api._resolve_navigation_scene_map(env, {})

        self.assertEqual(resolved["menu_id_to_scene"]["31"], "enterprise.company")
        self.assertEqual(resolved["action_id_to_scene"]["246"], "enterprise.company")
        self.assertEqual(
            resolved["entries"],
            [
                {
                    "code": "enterprise.company",
                    "target": {
                        "model": "res.company",
                        "view_type": "form",
                    },
                }
            ],
        )

    def test_resolve_navigation_scene_map_preserves_explicit_payload(self):
        env = _DummyEnv(
            refs={
                "smart_enterprise_base.menu_enterprise_company": 31,
            }
        )

        platform_menu_api.call_extension_hook_first = lambda env, hook_name, *args, **kwargs: {
            "menu_scene_map": {
                "smart_enterprise_base.menu_enterprise_company": "enterprise.company",
            },
            "action_xmlid_scene_map": {},
            "model_view_scene_map": {
                ("res.company", "form"): "enterprise.company",
            },
        }

        resolved = platform_menu_api._resolve_navigation_scene_map(
            env,
            {
                "menu_id_to_scene": {"31": "explicit.company"},
                "entries": [
                    {
                        "code": "explicit.company",
                        "target": {
                            "model": "res.company",
                            "view_type": "form",
                        },
                    }
                ],
            },
        )

        self.assertEqual(resolved["menu_id_to_scene"]["31"], "explicit.company")
        self.assertEqual(resolved["entries"][0]["code"], "explicit.company")
        self.assertEqual(len(resolved["entries"]), 1)


if __name__ == "__main__":
    unittest.main()
