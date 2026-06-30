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
MODULE_PATH = ROOT / "addons/smart_construction_core/models/support/task_extend.py"


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_module():
    class _Api:
        @staticmethod
        def depends(*_args):
            return lambda method: method

        @staticmethod
        def model_create_multi(method):
            return method

    class _Fields:
        def __getattr__(self, _name):
            return lambda *args, **kwargs: None

    odoo = _install_module(
        "odoo",
        api=_Api(),
        fields=_Fields(),
        models=types.SimpleNamespace(Model=object),
    )
    exc_mod = _install_module("odoo.exceptions", UserError=type("UserError", (Exception,), {}))
    odoo.exceptions = exc_mod
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    construction_pkg = sys.modules.setdefault(
        "odoo.addons.smart_construction_core",
        types.ModuleType("odoo.addons.smart_construction_core"),
    )
    models_pkg = sys.modules.setdefault(
        "odoo.addons.smart_construction_core.models",
        types.ModuleType("odoo.addons.smart_construction_core.models"),
    )
    support_pkg = sys.modules.setdefault(
        "odoo.addons.smart_construction_core.models.support",
        types.ModuleType("odoo.addons.smart_construction_core.models.support"),
    )
    construction_pkg.__path__ = [str(ROOT / "addons/smart_construction_core")]
    models_pkg.__path__ = [str(ROOT / "addons/smart_construction_core/models")]
    support_pkg.__path__ = [str(ROOT / "addons/smart_construction_core/models/support")]
    state_guard = _install_module("odoo.addons.smart_construction_core.models.support.state_guard")
    state_guard.raise_guard = lambda *args, **kwargs: None

    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_construction_core.models.support.task_extend",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TaskExtendReadinessBoundaryTests(unittest.TestCase):
    def test_compute_readiness_serializes_projection_scalars(self):
        module = _load_module()
        task = types.SimpleNamespace(
            _get_readiness_state=lambda: (
                ["project_id", date(2026, 6, 30)],
                [{"amount": Decimal("12.30")}],
            )
        )

        module.ProjectTask._compute_readiness([task])

        self.assertEqual(task.readiness_status, "blocked")
        self.assertEqual(json.loads(task.readiness_missing_fields), ["project_id", "2026-06-30"])
        self.assertEqual(json.loads(task.readiness_blockers), [{"amount": "12.30"}])


if __name__ == "__main__":
    unittest.main()
