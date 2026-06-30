#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "addons/smart_construction_core/controllers/scene_template_controller.py"


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_module():
    odoo = _install_module("odoo")
    http_mod = _install_module(
        "odoo.http",
        request=types.SimpleNamespace(),
        Controller=object,
        route=lambda *args, **kwargs: (lambda method: method),
    )
    odoo.http = http_mod
    odoo.fields = types.SimpleNamespace(Datetime=types.SimpleNamespace(now=lambda: "2026-01-01 00:00:00"))
    _install_module(
        "odoo.exceptions",
        AccessDenied=type("AccessDenied", (Exception,), {}),
        UserError=type("UserError", (Exception,), {}),
    )
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(ROOT / "addons/smart_core")]
    security_pkg = sys.modules.setdefault("odoo.addons.smart_core.security", types.ModuleType("odoo.addons.smart_core.security"))
    security_pkg.__path__ = [str(ROOT / "addons/smart_core/security")]
    auth_mod = _install_module("odoo.addons.smart_core.security.auth")
    auth_mod.get_user_from_token = lambda env, token: None
    platform_admin = _install_module("odoo.addons.smart_core.security.platform_admin")
    platform_admin.user_is_platform_admin = lambda env, user=None: False

    construction_pkg = sys.modules.setdefault(
        "odoo.addons.smart_construction_core",
        types.ModuleType("odoo.addons.smart_construction_core"),
    )
    controllers_pkg = sys.modules.setdefault(
        "odoo.addons.smart_construction_core.controllers",
        types.ModuleType("odoo.addons.smart_construction_core.controllers"),
    )
    construction_pkg.__path__ = [str(ROOT / "addons/smart_construction_core")]
    controllers_pkg.__path__ = [str(ROOT / "addons/smart_construction_core/controllers")]
    api_base = _install_module("odoo.addons.smart_construction_core.controllers.api_base")
    api_base.fail = lambda *args, **kwargs: {}
    api_base.fail_from_exception = lambda *args, **kwargs: {}
    api_base.ok = lambda *args, **kwargs: {}

    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_construction_core.controllers.scene_template_controller",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class SceneTemplateSerializationBoundaryTests(unittest.TestCase):
    def test_pack_hash_accepts_projection_scalars(self):
        module = _load_module()

        value = module._pack_hash(
            {
                "pack_meta": {"day": date(2026, 6, 30)},
                "capabilities": [{"key": "x", "amount": Decimal("12.30")}],
                "scenes": [],
            }
        )

        self.assertRegex(value, r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
