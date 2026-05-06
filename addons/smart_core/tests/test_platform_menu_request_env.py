# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _FakeUser:
    id = 23


class _FakeEnv:
    def __init__(self):
        self.uid = None
        self.cr = types.SimpleNamespace(rollbacks=0)
        self.cr.rollback = lambda: setattr(self.cr, "rollbacks", self.cr.rollbacks + 1)

    def __call__(self, user=None):
        env = _FakeEnv()
        env.uid = getattr(user, "id", user)
        return env


class _FakeRequest:
    def __init__(self):
        self.env = _FakeEnv()
        self.uid = None


def _install_module(name, **attrs):
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod


def _load_controller(fake_request, user_provider=None):
    root = Path(__file__).resolve().parents[1]
    module_path = root / "controllers" / "platform_menu_api.py"

    class _Controller:
        pass

    class _AccessDenied(Exception):
        pass

    http_mod = _install_module("odoo.http", request=fake_request)
    odoo_mod = _install_module("odoo", http=http_mod)
    http_mod.Controller = _Controller
    http_mod.route = lambda *args, **kwargs: (lambda fn: fn)

    _install_module("odoo.exceptions", AccessDenied=_AccessDenied)
    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    smart_core_mod.__path__ = [str(root)]
    _install_module("odoo.addons.smart_core.controllers").__path__ = [str(root / "controllers")]

    _install_module("odoo.addons.smart_core.core.trace", get_trace_id=lambda headers: "trace")
    _install_module(
        "odoo.addons.smart_core.core.exceptions",
        AUTH_REQUIRED="AUTH_REQUIRED",
        BAD_REQUEST="BAD_REQUEST",
        INTERNAL_ERROR="INTERNAL_ERROR",
        DEFAULT_API_VERSION="v1",
        DEFAULT_CONTRACT_VERSION="1.0",
        build_error_envelope=lambda **kwargs: kwargs,
    )
    _install_module(
        "odoo.addons.smart_core.security.auth",
        get_user_from_token=user_provider or (lambda: _FakeUser()),
    )
    _install_module(
        "odoo.addons.smart_core.utils.extension_hooks",
        call_extension_hook_first=lambda *args, **kwargs: None,
    )

    for name, cls_name in (
        ("odoo.addons.smart_core.delivery.menu_fact_service", "MenuFactService"),
        ("odoo.addons.smart_core.delivery.menu_delivery_convergence_service", "MenuDeliveryConvergenceService"),
        ("odoo.addons.smart_core.delivery.menu_target_interpreter_service", "MenuTargetInterpreterService"),
    ):
        _install_module(name, **{cls_name: type(cls_name, (), {})})

    name = "odoo.addons.smart_core.controllers.platform_menu_api"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestPlatformMenuRequestEnv(unittest.TestCase):
    def test_resolve_request_env_updates_request_identity(self):
        fake_request = _FakeRequest()
        controller = _load_controller(fake_request)

        env = controller._resolve_request_env()

        self.assertIs(fake_request.env, env)
        self.assertEqual(fake_request.uid, 23)
        self.assertEqual(env.uid, 23)

    def test_rollback_request_env_rolls_back_current_cursor(self):
        fake_request = _FakeRequest()
        controller = _load_controller(fake_request)
        env = controller._resolve_request_env()

        controller._rollback_request_env()

        self.assertEqual(env.cr.rollbacks, 1)

    def test_resolve_request_env_rejects_missing_user_identity(self):
        fake_request = _FakeRequest()
        controller = _load_controller(fake_request, user_provider=lambda: None)

        with self.assertRaises(controller.AccessDenied):
            controller._resolve_request_env()


if __name__ == "__main__":
    unittest.main()
