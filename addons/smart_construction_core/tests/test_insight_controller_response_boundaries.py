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
MODULE_PATH = ROOT / "addons/smart_construction_core/controllers/insight_controller.py"


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
    construction_pkg = sys.modules.setdefault(
        "odoo.addons.smart_construction_core",
        types.ModuleType("odoo.addons.smart_construction_core"),
    )
    controllers_pkg = sys.modules.setdefault(
        "odoo.addons.smart_construction_core.controllers",
        types.ModuleType("odoo.addons.smart_construction_core.controllers"),
    )
    services_pkg = sys.modules.setdefault(
        "odoo.addons.smart_construction_core.services",
        types.ModuleType("odoo.addons.smart_construction_core.services"),
    )
    insight_pkg = sys.modules.setdefault(
        "odoo.addons.smart_construction_core.services.insight",
        types.ModuleType("odoo.addons.smart_construction_core.services.insight"),
    )
    construction_pkg.__path__ = [str(ROOT / "addons/smart_construction_core")]
    controllers_pkg.__path__ = [str(ROOT / "addons/smart_construction_core/controllers")]
    services_pkg.__path__ = [str(ROOT / "addons/smart_construction_core/services")]
    insight_pkg.__path__ = [str(ROOT / "addons/smart_construction_core/services/insight")]
    service_mod = _install_module("odoo.addons.smart_construction_core.services.insight.project_insight_service")
    service_mod.ProjectInsightService = type("ProjectInsightService", (), {})

    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_construction_core.controllers.insight_controller",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class InsightControllerResponseBoundaryTests(unittest.TestCase):
    def test_json_response_serializes_projection_scalars(self):
        captured = {}

        def _make_response(body, headers=None, status=200):
            captured["body"] = body
            captured["headers"] = headers
            captured["status"] = status
            return captured

        module = _load_module(types.SimpleNamespace(make_response=_make_response))

        result = module.InsightController()._json(
            {"ok": True, "day": date(2026, 6, 30), "amount": Decimal("12.30")},
            status=201,
        )

        self.assertEqual(result["status"], 201)
        payload = json.loads(result["body"])
        self.assertEqual(payload["day"], "2026-06-30")
        self.assertEqual(payload["amount"], "12.30")


if __name__ == "__main__":
    unittest.main()
