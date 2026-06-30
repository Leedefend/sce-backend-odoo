#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "addons/smart_core/app_config_engine/controllers/contract_api.py"


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_module(fake_request):
    odoo = _install_module("odoo")
    http_mod = _install_module(
        "odoo.http",
        request=fake_request,
        Controller=object,
        route=lambda *args, **kwargs: (lambda method: method),
    )
    odoo.http = http_mod

    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(ROOT / "addons/smart_core")]
    app_pkg = sys.modules.setdefault("odoo.addons.smart_core.app_config_engine", types.ModuleType("odoo.addons.smart_core.app_config_engine"))
    controllers_pkg = sys.modules.setdefault(
        "odoo.addons.smart_core.app_config_engine.controllers",
        types.ModuleType("odoo.addons.smart_core.app_config_engine.controllers"),
    )
    services_pkg = sys.modules.setdefault(
        "odoo.addons.smart_core.app_config_engine.services",
        types.ModuleType("odoo.addons.smart_core.app_config_engine.services"),
    )
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    app_pkg.__path__ = [str(ROOT / "addons/smart_core/app_config_engine")]
    controllers_pkg.__path__ = [str(ROOT / "addons/smart_core/app_config_engine/controllers")]
    services_pkg.__path__ = [str(ROOT / "addons/smart_core/app_config_engine/services")]
    core_pkg.__path__ = [str(ROOT / "addons/smart_core/core")]

    service_mod = _install_module("odoo.addons.smart_core.app_config_engine.services.contract_service")

    class _ContractService:
        def __init__(self, request_env):
            self.request_env = request_env

        def handle_request(self):
            raise RuntimeError("boom")

    service_mod.ContractService = _ContractService

    trace_mod = _install_module("odoo.addons.smart_core.core.trace")
    trace_mod.get_trace_id = lambda _headers: "trace_1"

    exceptions_mod = _install_module("odoo.addons.smart_core.core.exceptions")
    exceptions_mod.INTERNAL_ERROR = "INTERNAL_ERROR"
    exceptions_mod.DEFAULT_API_VERSION = "v1"
    exceptions_mod.DEFAULT_CONTRACT_VERSION = "v2"
    exceptions_mod.build_error_envelope = lambda **_kwargs: {
        "ok": False,
        "day": date(2026, 6, 30),
        "amount": Decimal("12.30"),
    }

    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.app_config_engine.controllers.contract_api",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class ContractApiResponseBoundaryTests(unittest.TestCase):
    def test_controller_fallback_response_serializes_projection_scalars(self):
        captured = {}

        def _make_response(body, headers=None, status=200):
            captured["body"] = body
            captured["headers"] = headers
            captured["status"] = status
            return captured

        fake_request = types.SimpleNamespace(
            env=types.SimpleNamespace(),
            httprequest=types.SimpleNamespace(headers={}),
            make_response=_make_response,
        )
        module = _load_module(fake_request)

        result = module.SmartCoreContractController().contract_get()

        self.assertEqual(result["status"], 500)
        payload = json.loads(result["body"].decode("utf-8"))
        self.assertEqual(payload["day"], "2026-06-30")
        self.assertEqual(payload["amount"], "12.30")


if __name__ == "__main__":
    unittest.main()
