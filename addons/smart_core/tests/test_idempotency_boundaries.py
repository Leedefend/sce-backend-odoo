# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path


UTILS_DIR = Path(__file__).resolve().parents[1] / "utils"


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_idempotency():
    _install_module("odoo", fields=types.SimpleNamespace(Datetime=types.SimpleNamespace()))
    _install_module("odoo.addons")
    smart_core_pkg = _install_module("odoo.addons.smart_core")
    smart_core_pkg.__path__ = [str(UTILS_DIR.parent)]
    utils_pkg = _install_module("odoo.addons.smart_core.utils")
    utils_pkg.__path__ = [str(UTILS_DIR)]
    _install_module(
        "odoo.addons.smart_core.utils.reason_codes",
        REASON_IDEMPOTENCY_CONFLICT="IDEMPOTENCY_CONFLICT",
        failure_meta_for_reason=lambda reason: {"reason_code": reason},
    )

    module_name = "odoo.addons.smart_core.utils.idempotency"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, UTILS_DIR / "idempotency.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestIdempotencyBoundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_idempotency()

    def test_fingerprint_is_key_order_stable(self):
        left = self.module.build_idempotency_fingerprint({"b": 2, "a": 1})
        right = self.module.build_idempotency_fingerprint({"a": 1, "b": 2})

        self.assertEqual(left, right)

    def test_fingerprint_serializes_projection_values(self):
        value = self.module.build_idempotency_fingerprint(
            {"day": date(2026, 6, 30), "amount": Decimal("12.30")}
        )

        self.assertRegex(value, r"^[0-9a-f]{40}$")

    def test_fingerprint_normalizes_id_lists_before_hashing(self):
        left = self.module.build_idempotency_fingerprint({"ids": ["2", 1]}, normalize_id_keys=["ids"])
        right = self.module.build_idempotency_fingerprint({"ids": [1, "2"]}, normalize_id_keys=["ids"])

        self.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
