# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "core"


def _load_hash_utils():
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    core_pkg.__path__ = [str(CORE_DIR)]
    smart_core_pkg.core = core_pkg

    source_name = "odoo.addons.smart_core.core.source_authority"
    if source_name not in sys.modules:
        source_spec = importlib.util.spec_from_file_location(source_name, CORE_DIR / "source_authority.py")
        source_module = importlib.util.module_from_spec(source_spec)
        sys.modules[source_name] = source_module
        source_spec.loader.exec_module(source_module)

    module_name = "odoo.addons.smart_core.core.hash_utils"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, CORE_DIR / "hash_utils.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestHashUtilsBoundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_hash_utils()

    def test_stable_fingerprint_is_key_order_stable(self):
        left = self.module.stable_fingerprint({"b": 2, "a": 1})
        right = self.module.stable_fingerprint({"a": 1, "b": 2})

        self.assertEqual(left, right)

    def test_stable_fingerprint_serializes_projection_values(self):
        value = self.module.stable_fingerprint({"day": date(2026, 6, 30), "amount": Decimal("12.30")})

        self.assertRegex(value, r"^[0-9a-f]{32}$")


if __name__ == "__main__":
    unittest.main()
