# -*- coding: utf-8 -*-
import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class _BaseIntentHandler:
    def __init__(self, env=None, request=None, params=None, context=None):
        self.env = env
        self.request = request
        self.params = params or {}
        self.context = context or {}

    def err(self, code, message):
        return {"ok": False, "code": code, "error": {"code": code, "message": message}}


class _User:
    id = 7
    login = "svc_readonly"
    name = "Service User"
    token_version = 2

    def __bool__(self):
        return True


class _EmptyUser:
    def __bool__(self):
        return False


class _Users:
    def __init__(self):
        self.last_domain = None

    def sudo(self):
        return self

    def search(self, domain, limit=1):
        self.last_domain = domain
        if domain == [("login", "=", "svc_readonly")]:
            return _User()
        return _EmptyUser()


class _Env(dict):
    def __init__(self):
        super().__init__()
        self.users = _Users()

    def __getitem__(self, key):
        if key == "res.users":
            return self.users
        return super().__getitem__(key)


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    _install_module("odoo")
    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    security_mod = _install_module("odoo.addons.smart_core.security")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    security_mod.__path__ = [str(root / "security")]

    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)
    _install_module(
        "odoo.addons.smart_core.security.auth",
        generate_token=lambda uid, token_version=0: f"token:{uid}:{token_version}",
    )

    module_name = "odoo.addons.smart_core.handlers.session_bootstrap"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "session_bootstrap.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestSessionBootstrapBoundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def test_invalid_login_returns_bad_request(self):
        env = _Env()
        handler = self.module.SessionBootstrapHandler(env=env)

        with patch.dict(os.environ, {"ENV": "test", "SC_BOOTSTRAP_SECRET": "secret"}, clear=False):
            result = handler.handle(payload={"params": {"secret": "secret", "login": ["svc_readonly"]}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "login 无效")
        self.assertIsNone(env.users.last_domain)

    def test_valid_login_generates_token(self):
        env = _Env()
        handler = self.module.SessionBootstrapHandler(env=env)

        with patch.dict(os.environ, {"ENV": "test", "SC_BOOTSTRAP_SECRET": "secret"}, clear=False):
            result = handler.handle(payload={"params": {"secret": "secret", "login": "svc_readonly"}})

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["token"], "token:7:2")
        self.assertEqual(env.users.last_domain, [("login", "=", "svc_readonly")])


if __name__ == "__main__":
    unittest.main()
