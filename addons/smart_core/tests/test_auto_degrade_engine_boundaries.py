# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from datetime import datetime
from pathlib import Path


RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime"


class _FakeDatetimeField:
    @staticmethod
    def now():
        return datetime(2026, 6, 30, 10, 30, 0)

    @staticmethod
    def to_datetime(value):
        return value

    @staticmethod
    def to_string(value):
        return value.strftime("%Y-%m-%d %H:%M:%S")


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_engine():
    _install_module("odoo", fields=types.SimpleNamespace(Datetime=_FakeDatetimeField))
    _install_module("odoo.addons")
    smart_core_pkg = _install_module("odoo.addons.smart_core")
    smart_core_pkg.__path__ = [str(RUNTIME_DIR.parent)]
    governance_pkg = _install_module("odoo.addons.smart_core.governance")
    governance_pkg.__path__ = [str(RUNTIME_DIR.parent / "governance")]
    utils_pkg = _install_module("odoo.addons.smart_core.utils")
    utils_pkg.__path__ = [str(RUNTIME_DIR.parent / "utils")]
    _install_module(
        "odoo.addons.smart_core.governance.scene_drift_engine",
        is_critical_drift_warn=lambda entry: False,
    )
    _install_module(
        "odoo.addons.smart_core.utils.contract_governance",
        is_truthy=lambda value: str(value).lower() in {"1", "true", "yes", "y"},
    )
    module_name = "odoo.addons.smart_core.runtime.auto_degrade_engine"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, RUNTIME_DIR / "auto_degrade_engine.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestAutoDegradeEngineBoundaries(unittest.TestCase):
    def test_recent_window_start_uses_odoo_datetime_contract(self):
        module = _load_engine()

        self.assertEqual(module._recent_window_start(minutes=1), "2026-06-30 10:29:00")
        self.assertEqual(module._recent_window_start(minutes=0), "2026-06-30 10:29:00")


if __name__ == "__main__":
    unittest.main()
