# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _Cursor:
    def __init__(self, fail=False):
        self.fail = fail
        self.rollback_calls = 0

    def rollback(self):
        self.rollback_calls += 1
        if self.fail:
            raise RuntimeError("rollback failed")


class _Logger:
    def __init__(self):
        self.calls = []

    def exception(self, message, *args):
        self.calls.append((message, args))


def _load_module(cursor):
    root = Path(__file__).resolve().parents[1]
    odoo_mod = types.ModuleType("odoo")
    http_mod = types.ModuleType("odoo.http")
    http_mod.request = types.SimpleNamespace(env=types.SimpleNamespace(cr=cursor))
    odoo_mod.http = http_mod

    addons_mod = types.ModuleType("odoo.addons")
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    core_mod = types.ModuleType("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    core_mod.__path__ = [str(root / "core")]
    sys.modules.update(
        {
            "odoo": odoo_mod,
            "odoo.http": http_mod,
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.core": core_mod,
        }
    )

    module_name = "odoo.addons.smart_core.core.request_transaction"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "core" / "request_transaction.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestRequestTransaction(unittest.TestCase):
    def test_rollback_request_env_returns_true_on_success(self):
        cursor = _Cursor()
        module = _load_module(cursor)

        self.assertTrue(module.rollback_request_env(reason="test", trace_id="trace"))
        self.assertEqual(cursor.rollback_calls, 1)

    def test_rollback_request_env_logs_and_returns_false_on_failure(self):
        cursor = _Cursor(fail=True)
        logger = _Logger()
        module = _load_module(cursor)

        self.assertFalse(module.rollback_request_env(logger, reason="test", trace_id="trace"))
        self.assertEqual(cursor.rollback_calls, 1)
        self.assertEqual(len(logger.calls), 1)
        self.assertIn("request env rollback failed", logger.calls[0][0])

    def test_rollback_request_env_accepts_explicit_request_object(self):
        stale_cursor = _Cursor()
        current_cursor = _Cursor()
        module = _load_module(stale_cursor)
        current_request = types.SimpleNamespace(env=types.SimpleNamespace(cr=current_cursor))

        self.assertTrue(module.rollback_request_env(request_obj=current_request))
        self.assertEqual(stale_cursor.rollback_calls, 0)
        self.assertEqual(current_cursor.rollback_calls, 1)


if __name__ == "__main__":
    unittest.main()
