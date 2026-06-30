# -*- coding: utf-8 -*-
import importlib.util
import re
import sys
import types
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
SMART_CORE_DIR = WORKSPACE_ROOT / "addons" / "smart_core"
SMART_CONSTRUCTION_DIR = WORKSPACE_ROOT / "addons" / "smart_construction_core"


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_module(module_name, path):
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _install_odoo_stubs():
    http_mod = _install_module(
        "odoo.http",
        request=types.SimpleNamespace(make_response=lambda *args, **kwargs: None),
        Controller=object,
        route=lambda *args, **kwargs: (lambda func: func),
    )
    exceptions_mod = _install_module("odoo.exceptions", AccessDenied=type("AccessDenied", (Exception,), {}))
    _install_module("odoo", fields=types.SimpleNamespace(), http=http_mod, exceptions=exceptions_mod)
    _install_module("odoo.addons")


def _install_smart_core_stubs():
    smart_core_pkg = _install_module("odoo.addons.smart_core")
    smart_core_pkg.__path__ = [str(SMART_CORE_DIR)]
    security_pkg = _install_module("odoo.addons.smart_core.security")
    security_pkg.__path__ = [str(SMART_CORE_DIR / "security")]
    core_pkg = _install_module("odoo.addons.smart_core.core")
    core_pkg.__path__ = [str(SMART_CORE_DIR / "core")]
    _install_module("odoo.addons.smart_core.security.auth", get_user_from_token=lambda: None)
    _install_module("odoo.addons.smart_core.security.platform_admin", user_is_platform_admin=lambda user: True)
    _install_module("odoo.addons.smart_core.core.trace", get_trace_id=lambda: "trace_unit")


def _install_construction_stubs():
    pkg = _install_module("smart_construction_api_under_test")
    pkg.__path__ = [str(SMART_CONSTRUCTION_DIR / "controllers")]
    utils_pkg = _install_module("smart_construction_api_under_test.utils")
    utils_pkg.__path__ = [str(SMART_CONSTRUCTION_DIR / "controllers" / "utils")]
    _install_module("smart_construction_api_under_test.utils.trace", get_trace_id=lambda: "trace_unit")


class TestApiServerTimeBoundaries(unittest.TestCase):
    def setUp(self):
        _install_odoo_stubs()

    def assert_utc_z(self, value):
        self.assertRegex(value, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertNotRegex(value, re.escape("+00:00"))

    def test_platform_ops_server_time_uses_utc_z_contract(self):
        _install_smart_core_stubs()
        module = _load_module(
            "odoo.addons.smart_core.controllers.platform_ops_controller",
            SMART_CORE_DIR / "controllers" / "platform_ops_controller.py",
        )

        self.assert_utc_z(module._server_time())

    def test_construction_api_server_time_uses_utc_z_contract(self):
        _install_construction_stubs()
        module = _load_module(
            "smart_construction_api_under_test.api_base",
            SMART_CONSTRUCTION_DIR / "controllers" / "api_base.py",
        )

        self.assert_utc_z(module._server_time())


if __name__ == "__main__":
    unittest.main()
